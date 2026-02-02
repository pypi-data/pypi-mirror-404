from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.console import Console

if TYPE_CHECKING:
    pass

console = Console()


def _get_logger():
    """Lazy logger creation to avoid import overhead at module load."""
    from terminaluse.lib.utils.logging import make_logger

    return make_logger(__name__)


def deploy(
    config: str = typer.Option("config.yaml", "--config", "-c", help="Path to the config file"),
    tag: str | None = typer.Option(None, help="Override the image tag (default: git commit hash)"),
    branch: str | None = typer.Option(None, help="Override git branch (default: auto-detect)"),
    skip_build: bool = typer.Option(False, help="Skip image build, use existing image"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show docker build output"),
):
    """Deploy an agent to the tu platform.

    This command:
    1. Reads the manifest and detects git info
    2. Validates authentication and namespace access
    3. Gets registry credentials from the platform
    4. Builds and pushes the Docker image
    5. Triggers deployment via platform API
    6. Polls for deployment completion
    """
    import questionary
    from rich.panel import Panel

    from terminaluse.lib.cli.handlers.agent_handlers import build_agent
    from terminaluse.lib.cli.handlers.deploy_handlers import (
        DeploymentError,
        build_deploy_config,
        check_dockerfile_exists,
        docker_login,
        docker_logout,
        poll_deployment_status,
        validate_docker_running,
    )
    from terminaluse.lib.cli.utils.cli_utils import handle_questionary_cancellation, require_interactive_or_flag
    from terminaluse.lib.cli.utils.client import get_authenticated_client
    from terminaluse.lib.cli.utils.credentials import get_stored_credentials
    from terminaluse.lib.cli.utils.git_utils import detect_git_author, detect_git_info, generate_image_tag
    from terminaluse.lib.sdk.config.agent_manifest import AgentManifest
    from terminaluse.lib.sdk.config.deployment_config import EnvironmentDeploymentConfig

    logger = _get_logger()
    console.print(Panel.fit("🚀 [bold blue]Deploy Agent[/bold blue]", border_style="blue"))

    try:
        # =================================================================
        # Phase 1: Initialization
        # =================================================================

        # 1.1 Validate config exists
        config_path = Path(config)
        if not config_path.exists():
            console.print("[red]Error:[/red] config.yaml not found in current directory")
            raise typer.Exit(1)

        # Load config
        config_obj = AgentManifest.from_yaml(str(config_path))

        # Agent name format is "namespace/agent-name"
        # Extract namespace and short name using existing properties
        full_name = config_obj.agent.name
        try:
            namespace = config_obj.agent.namespace_slug
            agent_name = config_obj.agent.short_name
        except (IndexError, AttributeError):
            console.print(f"[red]Error:[/red] Invalid agent name format: '{full_name}'")
            console.print("  Expected format: 'namespace/agent-name' (e.g., 'acme-corp/my-agent')")
            raise typer.Exit(1)

        console.print(f"[green]✓[/green] Loaded config: {full_name}")

        # 1.2 Detect git info
        git_info = detect_git_info(str(config_path.parent))
        git_author = detect_git_author(str(config_path.parent))
        if git_info.is_git_repo:
            console.print(f"[green]✓[/green] Git repo detected: {git_info.branch or 'detached HEAD'}")
            if git_info.is_dirty:
                console.print("[yellow]⚠ Warning:[/yellow] You have uncommitted changes.")
                console.print("  The deployed image will include these uncommitted changes.")
                if not yes:
                    # Ensure we're in interactive mode before prompting
                    require_interactive_or_flag(yes, "--yes", "confirm deploy with uncommitted changes")
                    proceed = questionary.confirm("Deploy anyway?").ask()
                    proceed = handle_questionary_cancellation(proceed, "dirty repo confirmation")
                    if not proceed:
                        console.print("Deployment cancelled")
                        raise typer.Exit(0)
        else:
            console.print("[yellow]⚠[/yellow] Not a git repository, using timestamp-based tag")

        # 1.3 Validate authentication and initialize client
        client = get_authenticated_client()

        # 1.4 Validate namespace access (uses auto-generated API)
        try:
            client.namespaces.retrieve_by_slug(namespace)
        except Exception as e:
            # After SDK regeneration, this will be proper NotFoundError/ForbiddenError
            error_msg = str(e).lower()
            if "404" in error_msg or "not found" in error_msg:
                console.print(f"[red]Error:[/red] Namespace '{namespace}' not found")
            elif "403" in error_msg or "forbidden" in error_msg:
                console.print(f"[red]Error:[/red] You don't have access to namespace '{namespace}'")
            else:
                console.print(f"[red]Error:[/red] Failed to validate namespace: {e}")
            raise typer.Exit(1) from e

        # =================================================================
        # Phase 2: Registry Authentication
        # =================================================================

        try:
            registry_auth = client.registry.auth(namespace=namespace)
        except Exception as e:
            console.print(f"[red]Error:[/red] Failed to get registry credentials: {e}")
            raise typer.Exit(1) from e

        # Determine effective branch early (needed for env resolution)
        effective_branch = branch or git_info.branch or "main"

        # =================================================================
        # Phase 2.5: Resolve Environment
        # =================================================================

        console.print(f"\nResolving environment for branch '{effective_branch}'...")
        assume_production = False
        try:
            resolved_env = client.agents.environments.resolve_env(
                agent_name=agent_name,
                namespace_slug=namespace,
                branch=effective_branch,
            )
            console.print(f"[green]✓[/green] Resolved environment: {resolved_env.environment.name}")
        except Exception:
            # Environment resolution fails for new agents - this is expected
            # Use branch name to determine config: main → production, others → preview
            if effective_branch == "main":
                console.print("  Using production config (branch is 'main')")
                assume_production = True
            else:
                console.print(f"  Using preview config (branch '{effective_branch}' is not 'main')")
            resolved_env = None

        # Get deployment config for resolved environment
        env_config: EnvironmentDeploymentConfig
        is_prod_config = (resolved_env and resolved_env.environment.is_prod) or assume_production
        if config_obj.deployment:
            if is_prod_config:
                env_config = config_obj.deployment.production
            else:
                # Fallback to preview for any non-production environment
                env_config = config_obj.deployment.preview
                if resolved_env and resolved_env.environment.name != "preview":
                    console.print(
                        f"[yellow]⚠[/yellow] No '{resolved_env.environment.name}' config in config file, using preview"
                    )

            # Only print config details if we resolved the environment (otherwise we already explained)
            if resolved_env:
                config_name = "production" if is_prod_config else "preview"
                console.print(f"  Using {config_name} config (replicaCount={env_config.replicaCount})")
            else:
                console.print(f"  replicaCount={env_config.replicaCount}")
        else:
            # No deployment section, use defaults
            env_config = EnvironmentDeploymentConfig()
            console.print("  Using default config (no deployment section in config file)")

        # =================================================================
        # Phase 3: Build Image
        # =================================================================

        # Determine image tag
        image_tag = tag or generate_image_tag(git_info)

        # Build full image URL
        full_image = f"{registry_auth.registry_url}/{registry_auth.repository}/{namespace}/{agent_name}:{image_tag}"

        console.print("\n[bold]Build Configuration:[/bold]")
        console.print(f"  Agent: {full_name}")
        console.print(f"  Branch: {effective_branch}")
        if git_info.commit_hash:
            console.print(f"  Commit: {git_info.commit_hash[:12]}")

        if not skip_build:
            # Validate Docker is running
            if not validate_docker_running():
                console.print("[red]Error:[/red] Docker is not running. Please start Docker.")
                raise typer.Exit(1)

            # Validate Dockerfile exists
            if not check_dockerfile_exists(str(config_path)):
                console.print("[red]Error:[/red] Dockerfile not found in current directory")
                raise typer.Exit(1)

            # Docker login with platform-provided token
            docker_login(
                registry=registry_auth.registry_url,
                username=registry_auth.username,
                password=registry_auth.token,
            )

            # Build and push image
            console.print("\nBuilding and pushing image...")
            try:
                build_agent(
                    config_path=str(config_path),
                    registry_url=registry_auth.registry_url,
                    repository_name=f"{registry_auth.repository}/{namespace}/{agent_name}",
                    tag=image_tag,
                    push=True,
                    platforms=["linux/amd64", "linux/arm64"],
                    verbose=verbose,
                )
                console.print(f"[green]✓[/green] Built and pushed: {full_name}:{image_tag}")
            except Exception as e:
                console.print(f"[red]Error:[/red] Docker build failed: {e}")
                raise typer.Exit(1) from e
            finally:
                # Logout from registry
                docker_logout(registry_auth.registry_url)
        else:
            console.print("\n[yellow]Skipping build[/yellow] (--skip-build)")

        # =================================================================
        # Phase 5: Trigger Deployment
        # =================================================================

        console.print(f"\nDeploying to {namespace}/{agent_name}@{effective_branch}...")

        # Build deployment config from resolved environment config
        deploy_config = build_deploy_config(env_config, is_production=is_prod_config)

        # Show task stickiness setting
        are_tasks_sticky = deploy_config.get("are_tasks_sticky", False)
        sticky_behavior = (
            "tasks stay on old version" if are_tasks_sticky else "tasks migrate to new latest deployed version"
        )
        sticky_color = "green" if are_tasks_sticky else "dim"
        console.print(f"  Task stickiness: [{sticky_color}]{are_tasks_sticky}[/{sticky_color}] ({sticky_behavior})")

        # Get author info from git or stored credentials
        stored_creds = get_stored_credentials()
        author_email = git_author.email or (stored_creds.email if stored_creds else None) or "unknown"
        author_name = git_author.name or (stored_creds.email if stored_creds else None) or "Unknown"

        # Get sdk_type from manifest (default to claude_agent_sdk)
        sdk_type = getattr(config_obj.agent, "sdk_type", None) or "claude_agent_sdk"

        try:
            # Trigger deployment via platform API (uses auto-generated API)
            deploy_response = client.agents.deploy(
                agent_name=full_name,  # namespace/agent-name format
                author_email=author_email,
                author_name=author_name,
                branch=effective_branch,
                git_hash=git_info.commit_hash or image_tag,
                git_message=git_info.commit_message,
                image_url=full_image,
                is_dirty=git_info.is_dirty,
                replicas=deploy_config.get("replicas", 1),
                resources=deploy_config.get("resources"),
                are_tasks_sticky=deploy_config.get("are_tasks_sticky"),
                acp_type="async",  # Always use async ACP
                sdk_type=sdk_type,  # type: ignore[arg-type]
            )

            console.print(f"  Agent ID: {deploy_response.agent_id}")
            console.print(f"  Version ID: {deploy_response.version_id}")

        except Exception as e:
            console.print(f"[red]Error:[/red] Deployment failed: {e}")
            raise typer.Exit(1) from e

        # =================================================================
        # Phase 9: Poll and Complete
        # =================================================================

        console.print()
        try:
            status = poll_deployment_status(
                client,
                deploy_response.branch_id,
                timeout=300,  # 5 minutes
                interval=2,
            )

            # Get version status from the branch's current_version
            version_status = status.current_version.status.lower() if status.current_version else "unknown"
            if version_status == "active":
                console.print(f"\n[bold green]✓ Deployed version {image_tag}[/bold green]")
                console.print("\nYour agent is live:")
                console.print(f"  Agent:  {namespace}/{agent_name}")
                console.print(f"  Branch: {effective_branch}")

                # Show next steps
                console.print("\n[bold]Next steps:[/bold]")
                console.print("  1. Create a project:")
                console.print(f'     tu projects create --namespace {namespace} --name "my-project"')
                console.print("  2. Create a task:")
                console.print('     tu tasks create --message "hello, world" --project <project_id>')
            else:
                console.print(f"\n[red]✗ Deployment failed with status: {version_status}[/red]")

                # Fetch failure details from version
                version_id = deploy_response.version_id
                try:
                    version_detail = client.versions.retrieve(version_id)
                    diag = getattr(version_detail, "failure_diagnostics", None)
                    if diag:
                        console.print(f"\n[bold red]{diag.get('title', 'Deployment failed')}[/bold red]")
                        console.print(f"  {diag.get('description', '')}")
                        if diag.get("action"):
                            console.print(f"\n[bold]Suggested action:[/bold] {diag['action']}")
                    elif getattr(version_detail, "failure_reason", None):
                        console.print(f"\n[bold red]Failure reason:[/bold red] {version_detail.failure_reason}")
                except Exception:
                    pass  # Best-effort, don't fail the CLI if fetch fails

                # Show trace ID for internal log correlation
                trace_id = getattr(deploy_response, "trace_id", None)
                if trace_id:
                    console.print(f"\n[dim]Trace ID: {trace_id}[/dim]")

                raise typer.Exit(1)

        except DeploymentError as e:
            console.print(f"\n[red]✗ {str(e)}[/red]")
            trace_id = getattr(deploy_response, "trace_id", None)
            if trace_id:
                console.print(f"\n[dim]Trace ID: {trace_id}[/dim]")
            raise typer.Exit(1) from e

    except DeploymentError as e:
        console.print(f"[red]Deployment failed:[/red] {str(e)}")
        logger.exception("Deployment failed")
        raise typer.Exit(1) from e
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {str(e)}")
        logger.exception("Unexpected error during deployment")
        raise typer.Exit(1) from e
