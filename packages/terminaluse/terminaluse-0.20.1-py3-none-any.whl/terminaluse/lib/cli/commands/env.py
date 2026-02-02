"""CLI commands for managing environment variables."""

from __future__ import annotations

import re
import sys
from typing import Annotated
from pathlib import Path

import typer
import questionary
from rich.table import Table
from rich.console import Console

from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.cli.utils.client import get_authenticated_client
from terminaluse.types import EnvVarValue
from terminaluse.lib.cli.utils.cli_utils import (
    get_agent_name,
    parse_agent_name,
    handle_questionary_cancellation,
)

logger = make_logger(__name__)
console = Console()

env = typer.Typer(no_args_is_help=True)

# Environment name aliases - maps user input to actual DB environment names
ENV_ALIASES = {
    "prod": "production",
    "production": "production",
    "prev": "preview",
    "preview": "preview",
    "all": "all",
}

# POSIX environment variable name pattern
POSIX_KEY_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$")


def _normalize_environment(env_name: str | None) -> str:
    """Normalize environment name using aliases."""
    if env_name is None:
        raise typer.BadParameter(
            "Environment is required. Valid options: prod, production, preview, prev, all"
        )
    normalized = ENV_ALIASES.get(env_name.lower())
    if normalized is None:
        raise typer.BadParameter(
            f"Invalid environment '{env_name}'. Valid options: prod, production, preview, prev, all"
        )
    return normalized


def _validate_key(key: str | None) -> None:
    """Validate environment variable key follows POSIX conventions."""
    if key is None:
        console.print("[red]Error:[/red] Environment variable key is required")
        raise typer.Exit(1)
    if not POSIX_KEY_PATTERN.match(key):
        console.print(
            f"[red]Error:[/red] Invalid key '{key}'. "
            "Keys must match POSIX pattern: [A-Z_][A-Z0-9_]* (uppercase letters, digits, underscores)"
        )
        raise typer.Exit(1)


def _get_environments_for_target(target: str) -> list[str]:
    """Get list of environment names for a target (all, production, or preview)."""
    if target == "all":
        return ["production", "preview"]
    return [target]




@env.command("add")
def add_var(
    key: str = typer.Argument(..., help="Environment variable name (e.g., DATABASE_URL)"),
    value: str | None = typer.Option(None, "--value", "-v", help="Variable value (single line; use stdin for multiline)"),
    environment: str | None = typer.Option(None, "--environment", "-e", help="Target environment: prod, preview, or all"),
    secret: bool = typer.Option(False, "--secret", "-s", help="Mark as secret (write-only, cannot retrieve value)"),
    redeploy: bool = typer.Option(False, "--redeploy", help="Redeploy all matching branches (required in non-interactive with multiple branches)"),
    no_redeploy: bool = typer.Option(False, "--no-redeploy", help="Don't trigger redeploy after setting"),
    agent: str | None = typer.Option(None, "--agent", "-a", help="Agent name (defaults to config)"),
    config: str | None = typer.Option(None, "--config", "-c", help="Path to config file"),
):
    """Add or update an environment variable.

    Examples:
        tu env add DATABASE_URL                           # Interactive
        tu env add DATABASE_URL --value "postgres://..."  # With value
        tu env add API_KEY -v "sk-xxx" -e prod --secret   # Secret, prod only
        tu env add KEY -v "val" -e preview --redeploy     # Redeploy all preview branches
        echo "long value" | tu env add CERT -e all        # From stdin
    """
    _validate_key(key)
    agent_name = get_agent_name(agent, config)
    namespace_slug, agent_short = parse_agent_name(agent_name)
    client = get_authenticated_client()
    is_interactive = sys.stdin.isatty()

    # Get value: from flag, stdin, or interactive prompt
    if value is None:
        if not is_interactive:
            # Read from stdin (piped input)
            value = sys.stdin.read().strip()
        else:
            # Interactive prompt
            value_input = questionary.password(f"Enter value for {key}:").ask()
            value = handle_questionary_cancellation(value_input, "value input")

    if not value:
        console.print("[red]Error:[/red] Value cannot be empty")
        raise typer.Exit(1)

    # Get target environment(s)
    if environment is None:
        if not is_interactive:
            console.print("[red]Error:[/red] --environment is required in non-interactive mode")
            raise typer.Exit(1)
        # Interactive prompt with radio buttons
        env_choice = questionary.select(
            "Which environments?",
            choices=[
                questionary.Choice("All environments (Recommended)", value="all"),
                questionary.Choice("Production only", value="production"),
                questionary.Choice("Preview only", value="preview"),
            ],
        ).ask()
        environment = handle_questionary_cancellation(env_choice, "environment selection")

    target = _normalize_environment(environment)
    target_envs = _get_environments_for_target(target)

    try:
        # Step 1: Save secrets (without redeploy - we'll handle that separately)
        for env_name in target_envs:
            client.agents.environments.secrets.set(
                env_name=env_name,
                namespace_slug=namespace_slug,
                agent_name=agent_short,
                secrets={key: EnvVarValue(value=value, is_secret=secret)},
                redeploy=False,  # We handle redeploy separately
            )
            secret_indicator = " (secret)" if secret else ""
            console.print(f"[green]✓[/green] Added {key}{secret_indicator} to {env_name.capitalize()}")

        # Step 2: Handle redeploy if not skipped
        if no_redeploy:
            return

        # Collect all branches across target environments
        all_branches = []
        for env_name in target_envs:
            branches_response = client.agents.environments.branches.list(
                namespace_slug=namespace_slug,
                agent_name=agent_short,
                env_name=env_name,
            )
            for branch in branches_response.branches:
                all_branches.append({"env": env_name, "branch": branch})

        if not all_branches:
            # Zero branches - silent success
            return

        # Determine which branches to redeploy
        branches_to_redeploy = []

        if len(all_branches) == 1:
            # Single branch - auto-redeploy
            branches_to_redeploy = all_branches
        elif redeploy:
            # --redeploy flag: redeploy all
            branches_to_redeploy = all_branches
        elif is_interactive:
            # Interactive: show picker
            choices = [
                questionary.Choice(
                    f"All branches ({len(all_branches)})",
                    value="all"
                )
            ]
            for item in all_branches:
                branch = item["branch"]
                age = _format_age(branch.updated_at) if branch.updated_at else "unknown"
                git_hash = branch.current_version.git_hash[:7] if branch.current_version else "n/a"
                version_status = branch.current_version.status if branch.current_version else "no version"
                label = f"{branch.git_branch} ({version_status}) - {age} - {git_hash}"
                choices.append(questionary.Choice(label, value=branch.id))

            selected = questionary.checkbox(
                "Select branches to redeploy:",
                choices=choices,
            ).ask()

            if selected is None:
                console.print("[yellow]Cancelled[/yellow]")
                return

            if "all" in selected:
                branches_to_redeploy = all_branches
            else:
                branches_to_redeploy = [
                    item for item in all_branches
                    if item["branch"].id in selected
                ]
        else:
            # Non-interactive with multiple branches and no --redeploy flag
            console.print(f"[red]Error:[/red] Multiple branches found ({len(all_branches)})")
            console.print("  Use --redeploy to redeploy all, or --no-redeploy to skip")
            raise typer.Exit(1)

        # Step 3: Redeploy selected branches
        if not branches_to_redeploy:
            return

        redeploy_results = []
        for item in branches_to_redeploy:
            branch = item["branch"]
            try:
                result = client.branches.redeploy(branch_id=branch.id)
                redeploy_results.append({"branch": branch, "result": result, "error": None})
                console.print(f"[green]✓[/green] Redeployed {branch.git_branch} (version: {result.version_id[:12]})")
            except Exception as e:
                redeploy_results.append({"branch": branch, "result": None, "error": str(e)})
                console.print(f"[red]✗[/red] Failed to redeploy {branch.git_branch}: {e}")

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {e!s}")
        logger.exception("Failed to add environment variable")
        raise typer.Exit(1) from e


def _format_age(dt) -> str:
    """Format a datetime as a human-readable age string."""
    from datetime import datetime, timezone
    if dt is None:
        return "unknown"
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = now - dt
    if delta.days > 0:
        return f"{delta.days}d ago"
    hours = delta.seconds // 3600
    if hours > 0:
        return f"{hours}h ago"
    minutes = delta.seconds // 60
    return f"{minutes}m ago"


@env.command("ls")
def list_vars(
    environment: str | None = typer.Argument(None, help="Filter by environment: prod or preview"),
    show: bool = typer.Option(False, "--show", help="Show values for non-secret variables"),
    agent: str | None = typer.Option(None, "--agent", "-a", help="Agent name (defaults to config)"),
    config: str | None = typer.Option(None, "--config", "-c", help="Path to config file"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """List environment variables.

    Examples:
        tu env ls                # Cross-environment matrix view
        tu env ls --show         # Include values for non-secrets
        tu env ls prod           # Filter to production only
        tu env ls --json         # JSON output for scripting
    """
    agent_name = get_agent_name(agent, config)
    namespace_slug, agent_short = parse_agent_name(agent_name)
    client = get_authenticated_client()

    try:
        # Use cross-environment API for matrix view
        response = client.agents.secrets.list(
            agent_name=agent_short,
            namespace_slug=namespace_slug,
            include_values=show,
        )

        if json_output:
            import json
            typer.echo(json.dumps(response.dict(), default=str))
            return

        if not response.variables:
            console.print(f"No environment variables found for agent '{agent_name}'.")
            console.print("\nAdd one with: tu env add <KEY>")
            return

        # Filter by environment if specified
        if environment:
            target = _normalize_environment(environment)
            filtered_vars = [
                v for v in response.variables
                if any(e.env_name == target for e in v.environments)
            ]
        else:
            filtered_vars = response.variables

        if not filtered_vars:
            console.print(f"No environment variables found for environment '{environment}'.")
            return

        # Build table
        if environment:
            # Single environment view
            target = _normalize_environment(environment)
            table = Table(title=f"Environment Variables ({target.capitalize()})")
            table.add_column("NAME", style="cyan")
            table.add_column("TYPE")
            if show:
                table.add_column("VALUE")

            for var in filtered_vars:
                var_type = "Encrypted" if var.is_secret else "Plain"
                if show:
                    value_display = "<encrypted>" if var.is_secret else (var.value or "")
                    table.add_row(var.key, var_type, value_display)
                else:
                    table.add_row(var.key, var_type)
        else:
            # Cross-environment matrix view
            table = Table(title=f"Environment Variables for {agent_name}")
            table.add_column("NAME", style="cyan")
            table.add_column("PROD", justify="center")
            table.add_column("PREVIEW", justify="center")

            for var in filtered_vars:
                # Build env_name -> env_info lookup
                env_lookup = {e.env_name: e for e in var.environments}

                def get_env_display(env_info, show_values: bool) -> str:
                    """Get display value for an environment."""
                    if env_info is None:
                        return "✗"
                    if not show_values:
                        return "[green]✓[/green]"
                    if env_info.is_secret:
                        return "[dim]<encrypted>[/dim]"
                    return env_info.value if env_info.value else ""

                prod_val = get_env_display(env_lookup.get("production"), show)
                preview_val = get_env_display(env_lookup.get("preview"), show)

                table.add_row(var.key, prod_val, preview_val)

        console.print(table)
        console.print(f"\n{len(filtered_vars)} variable(s)")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e!s}")
        logger.exception("Failed to list environment variables")
        raise typer.Exit(1) from e


@env.command("get")
def get_var(
    key: str = typer.Argument(..., help="Environment variable name"),
    environment: str = typer.Option(..., "--environment", "-e", help="Environment: prod or preview"),
    agent: str | None = typer.Option(None, "--agent", "-a", help="Agent name (defaults to config)"),
    config: str | None = typer.Option(None, "--config", "-c", help="Path to config file"),
):
    """Get a single environment variable's value.

    Outputs just the raw value for scripting. Fails for secrets.

    Examples:
        tu env get DATABASE_URL -e prod
        DB_URL=$(tu env get DATABASE_URL -e preview)
    """
    agent_name = get_agent_name(agent, config)
    namespace_slug, agent_short = parse_agent_name(agent_name)
    target = _normalize_environment(environment)
    client = get_authenticated_client()

    try:
        # Get cross-environment list and find the specific key
        response = client.agents.secrets.list(
            agent_name=agent_short,
            namespace_slug=namespace_slug,
            include_values=True,
        )

        # Find the variable
        var = None
        for v in response.variables:
            if v.key == key:
                # Check if it exists in the target environment
                for env_info in v.environments:
                    if env_info.env_name == target:
                        var = v
                        break
                break

        if var is None:
            console.print(f"[red]Error:[/red] '{key}' not found in {target}")
            raise typer.Exit(1)

        if var.is_secret:
            console.print(f"[red]Error:[/red] Cannot retrieve secret values. '{key}' is marked as sensitive.")
            raise typer.Exit(1)

        # Output just the value
        typer.echo(var.value or "")

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {e!s}")
        logger.exception("Failed to get environment variable")
        raise typer.Exit(1) from e


@env.command("rm")
def remove_var(
    key: str = typer.Argument(..., help="Environment variable name to remove"),
    environment: str | None = typer.Option(None, "--environment", "-e", help="Environment: prod, preview, or all"),
    all_envs: bool = typer.Option(False, "--all", help="Remove from all environments (skip prompt)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    no_redeploy: bool = typer.Option(False, "--no-redeploy", help="Don't trigger redeploy after removal"),
    agent: str | None = typer.Option(None, "--agent", "-a", help="Agent name (defaults to config)"),
    config: str | None = typer.Option(None, "--config", "-c", help="Path to config file"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Remove an environment variable.

    Examples:
        tu env rm DATABASE_URL                    # Interactive prompt
        tu env rm DATABASE_URL -e prod            # Remove from prod only
        tu env rm DATABASE_URL --all              # Remove from all envs
        tu env rm DATABASE_URL --all -y           # Skip confirmation
    """
    agent_name = get_agent_name(agent, config)
    namespace_slug, agent_short = parse_agent_name(agent_name)
    client = get_authenticated_client()
    is_interactive = sys.stdin.isatty()

    # Determine target environments
    if all_envs:
        target_envs = ["production", "preview"]
    elif environment:
        target = _normalize_environment(environment)
        target_envs = _get_environments_for_target(target)
    else:
        if not is_interactive:
            console.print("[red]Error:[/red] --environment or --all is required in non-interactive mode")
            raise typer.Exit(1)
        # Interactive prompt
        env_choice = questionary.select(
            f"Remove '{key}' from which environments?",
            choices=[
                questionary.Choice("All environments", value="all"),
                questionary.Choice("Production only", value="production"),
                questionary.Choice("Preview only", value="preview"),
            ],
        ).ask()
        env_choice = handle_questionary_cancellation(env_choice, "environment selection")
        target_envs = _get_environments_for_target(env_choice)

    # Confirm deletion
    if not yes and not json_output:
        if not is_interactive:
            console.print("[red]Error:[/red] Cannot confirm deletion in non-interactive mode.")
            console.print("Use '--yes' or '-y' to skip confirmation prompts.")
            raise typer.Exit(1)
        env_display = ", ".join(e.capitalize() for e in target_envs)
        confirm = questionary.confirm(
            f"Remove '{key}' from {env_display}?",
            default=False,
        ).ask()
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            raise typer.Exit(0)

    try:
        results = []
        for env_name in target_envs:
            try:
                response = client.agents.environments.secrets.delete(
                    key=key,
                    env_name=env_name,
                    namespace_slug=namespace_slug,
                    agent_name=agent_short,
                    redeploy=not no_redeploy,
                )
                results.append({"environment": env_name, "deleted": response.deleted, "error": None})
            except Exception as e:
                results.append({"environment": env_name, "deleted": False, "error": str(e)})

        if json_output:
            import json
            typer.echo(json.dumps(results, default=str))
        else:
            for r in results:
                if r["deleted"]:
                    console.print(f"[green]\u2713[/green] Removed {key} from {r['environment'].capitalize()}")
                elif r["error"]:
                    console.print(f"[yellow]\u26a0[/yellow] Could not remove {key} from {r['environment']}: {r['error']}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e!s}")
        logger.exception("Failed to remove environment variable")
        raise typer.Exit(1) from e


# Add 'delete' as a hidden alias for 'rm'
env.command("delete", hidden=True)(remove_var)


@env.command("pull")
def pull_vars(
    file: str = typer.Argument(".env.local", help="Output file path"),
    environment: str = typer.Option("preview", "--environment", "-e", help="Source environment (default: preview)"),
    agent: str | None = typer.Option(None, "--agent", "-a", help="Agent name (defaults to config)"),
    config: str | None = typer.Option(None, "--config", "-c", help="Path to config file"),
):
    """Download environment variables to a local .env file.

    Secrets are included as empty placeholders.

    Examples:
        tu env pull                           # Writes to .env.local from preview
        tu env pull .env.development          # Custom filename
        tu env pull -e prod .env.production   # Pull from production
    """
    agent_name = get_agent_name(agent, config)
    namespace_slug, agent_short = parse_agent_name(agent_name)
    target = _normalize_environment(environment)
    client = get_authenticated_client()

    try:
        # Get variables for the target environment with values
        response = client.agents.environments.secrets.list(
            env_name=target,
            namespace_slug=namespace_slug,
            agent_name=agent_short,
            include_values=True,
        )

        if not response.env_vars:
            console.print(f"No environment variables found in {target}.")
            return

        # Build .env file content
        lines = [f"# Environment variables pulled from {target}"]
        lines.append(f"# Agent: {agent_name}")
        lines.append("")

        for var in response.env_vars:
            if var.is_secret:
                # Secret: empty placeholder
                lines.append(f"{var.key}=")
            else:
                # Non-secret: include value
                value = var.value or ""
                # Escape special characters and quote if needed
                if "\n" in value or '"' in value or "'" in value or " " in value:
                    value = f'"{value}"'
                lines.append(f"{var.key}={value}")

        # Write to file
        output_path = Path(file)
        output_path.write_text("\n".join(lines) + "\n")

        console.print(f"[green]\u2713[/green] Downloaded {len(response.env_vars)} variable(s) to {file}")

        # Count secrets
        secret_count = sum(1 for s in response.env_vars if s.is_secret)
        if secret_count > 0:
            console.print(f"  {secret_count} secret(s) written as empty placeholders")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e!s}")
        logger.exception("Failed to pull environment variables")
        raise typer.Exit(1) from e


@env.command("import")
def import_vars(
    file: str = typer.Argument(..., help="Path to .env file"),
    environment: str | None = typer.Option(None, "--environment", "-e", help="Target environment: prod, preview, or all"),
    secret: Annotated[list[str] | None, typer.Option("--secret", "-s", help="Mark key as secret (can be repeated)")] = None,
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing values (default: fail on conflict)"),
    no_redeploy: bool = typer.Option(False, "--no-redeploy", help="Don't trigger redeploy after import"),
    agent: str | None = typer.Option(None, "--agent", "-a", help="Agent name (defaults to config)"),
    config: str | None = typer.Option(None, "--config", "-c", help="Path to config file"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Bulk import environment variables from a .env file.

    Examples:
        tu env import .env.production -e prod
        tu env import .env -e all --secret API_KEY --secret DB_PASSWORD
        tu env import .env -e prod --force    # Overwrite existing
    """
    agent_name = get_agent_name(agent, config)
    namespace_slug, agent_short = parse_agent_name(agent_name)
    is_interactive = sys.stdin.isatty()

    # Get target environment(s)
    if environment is None:
        if not is_interactive:
            console.print("[red]Error:[/red] --environment is required in non-interactive mode")
            raise typer.Exit(1)
        # Interactive prompt with radio buttons
        env_choice = questionary.select(
            "Which environments?",
            choices=[
                questionary.Choice("All environments (Recommended)", value="all"),
                questionary.Choice("Production only", value="production"),
                questionary.Choice("Preview only", value="preview"),
            ],
        ).ask()
        environment = handle_questionary_cancellation(env_choice, "environment selection")

    target = _normalize_environment(environment)
    target_envs = _get_environments_for_target(target)
    secret_keys = set(secret or [])
    client = get_authenticated_client()

    # Parse .env file
    env_file = Path(file)
    if not env_file.exists():
        console.print(f"[red]Error:[/red] File not found: {file}")
        raise typer.Exit(1)

    variables: dict[str, str] = {}
    try:
        for line in env_file.read_text().splitlines():
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            # Parse KEY=value
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            # Remove surrounding quotes
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            # Validate key
            _validate_key(key)
            variables[key] = value
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to parse {file}: {e}")
        raise typer.Exit(1) from e

    if not variables:
        console.print(f"[yellow]Warning:[/yellow] No variables found in {file}")
        return

    # Check for conflicts if not forcing
    if not force:
        all_conflicts: dict[str, set[str]] = {}
        for env_name in target_envs:
            try:
                existing = client.agents.environments.secrets.list(
                    env_name=env_name,
                    namespace_slug=namespace_slug,
                    agent_name=agent_short,
                )
                existing_keys = {s.key for s in (existing.env_vars or [])}
                conflicts = set(variables.keys()) & existing_keys
                if conflicts:
                    all_conflicts[env_name] = conflicts
            except Exception:
                pass  # Environment might not exist yet, that's OK

        if all_conflicts:
            # Show conflicts to user
            for env_name, conflicts in all_conflicts.items():
                console.print(f"[yellow]Conflicting keys in {env_name}:[/yellow] {', '.join(sorted(conflicts))}")

            if is_interactive:
                # Ask user if they want to overwrite
                overwrite = questionary.confirm(
                    "Do you want to overwrite existing values?",
                    default=False,
                ).ask()
                if overwrite is None:
                    console.print("[yellow]Cancelled[/yellow]")
                    raise typer.Exit(0)
                if not overwrite:
                    console.print("[yellow]Import cancelled[/yellow]")
                    raise typer.Exit(0)
                # User confirmed, proceed with overwrite
            else:
                console.print("[red]Error:[/red] Use --force to overwrite existing values")
                raise typer.Exit(1)

    try:
        results = []
        for env_name in target_envs:
            # Build secrets dict
            secrets_dict = {
                key: EnvVarValue(value=value, is_secret=key in secret_keys)
                for key, value in variables.items()
            }
            response = client.agents.environments.secrets.set(
                env_name=env_name,
                namespace_slug=namespace_slug,
                agent_name=agent_short,
                secrets=secrets_dict,
                redeploy=not no_redeploy,
            )
            results.append({"environment": env_name, "count": len(variables), "response": response})

        if json_output:
            import json
            typer.echo(json.dumps([{"environment": r["environment"], "imported": r["count"]} for r in results], default=str))
        else:
            for r in results:
                console.print(f"[green]\u2713[/green] Imported {r['count']} variable(s) to {r['environment'].capitalize()}")
            if secret_keys:
                console.print(f"  {len(secret_keys)} key(s) marked as secrets: {', '.join(sorted(secret_keys))}")
            if not no_redeploy:
                console.print("  Redeploy triggered for affected environments")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e!s}")
        logger.exception("Failed to import environment variables")
        raise typer.Exit(1) from e
