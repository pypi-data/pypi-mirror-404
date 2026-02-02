"""CLI commands for managing webhook authentication keys."""

from __future__ import annotations

import sys

import typer
import questionary
from rich.table import Table
from rich.console import Console

from terminaluse.types import AgentApiKeyType
from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.cli.utils.client import get_authenticated_client
from terminaluse.lib.cli.utils.cli_utils import (
    get_agent_name,
    parse_agent_name,
    handle_questionary_cancellation,
    format_relative_time,
)

logger = make_logger(__name__)
console = Console()

keys = typer.Typer(no_args_is_help=True)

# Valid key types for webhook authentication
VALID_KEY_TYPES: list[AgentApiKeyType] = ["slack", "github"]


def _validate_key_type(key_type: str) -> AgentApiKeyType:
    """Validate and normalize key type."""
    normalized = key_type.lower()
    if normalized == "slack":
        return "slack"
    elif normalized == "github":
        return "github"
    else:
        raise typer.BadParameter(
            f"Invalid key type '{key_type}'. Valid options: {', '.join(VALID_KEY_TYPES)}"
        )


@keys.command("instructions")
def show_instructions(
    key_type: str = typer.Argument(..., help="Key type: slack or github"),
):
    """Show setup instructions for webhook authentication.

    Examples:
        tu keys instructions slack
        tu keys instructions github
    """
    validated_type = _validate_key_type(key_type)

    if validated_type == "slack":
        console.print("""
[bold cyan]Slack Webhook Authentication Setup[/bold cyan]

To verify incoming Slack webhooks, you need two things from your Slack app:

[bold]1. Find your App ID[/bold]
   • Go to [link=https://api.slack.com/apps/]https://api.slack.com/apps/[/link]
   • Select your app (or create one)
   • The App ID is shown at the top (e.g., [cyan]A01234567[/cyan])

[bold]2. Get your Signing Secret[/bold]
   • In your app settings, go to [bold]Basic Information[/bold]
   • Scroll to [bold]App Credentials[/bold]
   • Copy the [bold]Signing Secret[/bold]

[bold]3. Store the secret[/bold]
   Run:
   [dim]$[/dim] [green]tu keys add slack <APP_ID>[/green]

   You'll be prompted to enter the signing secret securely.

   Or provide it inline:
   [dim]$[/dim] [green]tu keys add slack A01234567 -s "your-signing-secret"[/green]

[bold]4. Configure your Slack app[/bold]
   • In Slack app settings, go to [bold]Event Subscriptions[/bold]
   • Set the Request URL to your webhook endpoint:
     [cyan]https://api.terminaluse.com/agents/forward/<namespace>/<agent>/<your-endpoint>[/cyan]
   • The endpoint path can be anything you define in your agent (e.g., [cyan]/slack[/cyan], [cyan]/webhooks/slack[/cyan])

Terminal Use will automatically verify the signature on incoming webhooks.
""")

    elif validated_type == "github":
        console.print("""
[bold cyan]GitHub Webhook Authentication Setup[/bold cyan]

[bold]1. Create a webhook in GitHub[/bold]
   • Go to your repository → Settings → Webhooks → Add webhook
   • Set the Payload URL to:
     [cyan]https://api.terminaluse.com/agents/forward/<namespace>/<agent>/<your-endpoint>[/cyan]
   • The endpoint path can be anything you define in your agent (e.g., [cyan]/github[/cyan], [cyan]/webhooks/github[/cyan])
   • Set Content type to [bold]application/json[/bold]
   • Enter a secret (GitHub will generate one, or create your own)
   • Select the events you want to receive
   • Save the webhook

[bold]2. Store the secret in Terminal Use[/bold]
   Run:
   [dim]$[/dim] [green]tu keys add github owner/repo[/green]

   You'll be prompted to enter the webhook secret securely.

   Or provide it inline:
   [dim]$[/dim] [green]tu keys add github owner/repo -s "your-webhook-secret"[/green]

   [dim]Note: Use the full repository name (e.g., [cyan]acme-corp/my-repo[/cyan])[/dim]

Terminal Use will automatically verify the [cyan]x-hub-signature-256[/cyan] header
on incoming webhooks using HMAC-SHA256.
""")


@keys.command("add")
def add_key(
    key_type: str = typer.Argument(..., help="Key type: slack or github"),
    name: str = typer.Argument(..., help="Key name (Slack app ID e.g. 'A01234567', or GitHub repo e.g. 'owner/repo')"),
    secret: str | None = typer.Option(None, "--secret", "-s", help="The signing secret (prompted if not provided)"),
    agent: str | None = typer.Option(None, "--agent", "-a", help="Agent name (defaults to config)"),
    config: str | None = typer.Option(None, "--config", "-c", help="Path to config file"),
):
    """Add a webhook authentication key for Slack or GitHub.

    The key is used to verify incoming webhooks from external services.
    Terminal Use automatically validates webhook signatures before forwarding
    requests to your agent.

    Examples:
        tu keys add slack A01234567                    # Interactive secret prompt
        tu keys add slack A01234567 -s "xoxb-..."     # With secret
        tu keys add github owner/repo -s "whsec_..."  # GitHub webhook secret
    """
    validated_key_type = _validate_key_type(key_type)
    agent_name = get_agent_name(agent, config)
    namespace_slug, agent_short = parse_agent_name(agent_name)
    client = get_authenticated_client()
    is_interactive = sys.stdin.isatty()

    # Get secret: from flag, stdin, or interactive prompt
    if secret is None:
        if not is_interactive:
            # Read from stdin (piped input)
            secret = sys.stdin.read().strip()
        else:
            # Interactive prompt
            secret_input = questionary.password(f"Enter {validated_key_type} signing secret:").ask()
            secret = handle_questionary_cancellation(secret_input, "secret input")

    if not secret:
        console.print("[red]Error:[/red] Secret cannot be empty")
        raise typer.Exit(1)

    try:
        response = client.agent_api_keys.create(
            name=name,
            agent_name=f"{namespace_slug}/{agent_short}",
            api_key=secret,
            api_key_type=validated_key_type,
        )

        console.print(f"[green]✓[/green] Added {validated_key_type} key '{name}' for agent {agent_name}")
        console.print(f"  Key ID: {response.id}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e!s}")
        logger.exception("Failed to add webhook key")
        raise typer.Exit(1) from e


@keys.command("ls")
def list_keys(
    agent: str | None = typer.Option(None, "--agent", "-a", help="Agent name (defaults to config)"),
    config: str | None = typer.Option(None, "--config", "-c", help="Path to config file"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """List webhook authentication keys.

    Examples:
        tu keys ls
        tu keys ls --json
    """
    agent_name = get_agent_name(agent, config)
    namespace_slug, agent_short = parse_agent_name(agent_name)
    client = get_authenticated_client()

    try:
        # Response is List[AgentAPIKey]
        api_keys = client.agent_api_keys.list(
            agent_name=f"{namespace_slug}/{agent_short}",
        )

        # Filter to only webhook keys (slack, github)
        webhook_keys = [k for k in api_keys if k.api_key_type in VALID_KEY_TYPES]

        if json_output:
            import json
            output = [
                {
                    "id": k.id,
                    "name": k.name,
                    "type": k.api_key_type,
                    "created_at": str(k.created_at) if k.created_at else None,
                }
                for k in webhook_keys
            ]
            typer.echo(json.dumps(output, default=str))
            return

        if not webhook_keys:
            console.print(f"No webhook keys found for agent '{agent_name}'.")
            console.print("\nAdd one with: tu keys add <slack|github> <name>")
            return

        table = Table(title=f"Webhook Keys for {agent_name}")
        table.add_column("ID", style="dim")
        table.add_column("TYPE", style="cyan")
        table.add_column("NAME")
        table.add_column("CREATED")

        for key in webhook_keys:
            created = format_relative_time(key.created_at)
            table.add_row(
                key.id[:12] + "..." if len(key.id) > 12 else key.id,
                key.api_key_type,
                key.name or "-",
                created,
            )

        console.print(table)
        console.print(f"\n{len(webhook_keys)} key(s)")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e!s}")
        logger.exception("Failed to list webhook keys")
        raise typer.Exit(1) from e


@keys.command("rm")
def remove_key(
    key_id: str = typer.Argument(..., help="Key ID to remove"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    agent: str | None = typer.Option(None, "--agent", "-a", help="Agent name (defaults to config)"),
    config: str | None = typer.Option(None, "--config", "-c", help="Path to config file"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Remove a webhook authentication key.

    Examples:
        tu keys rm abc123def456
        tu keys rm abc123def456 --yes
    """
    import json

    # Note: agent/config are accepted for consistency but not currently used
    # since key deletion is by key_id which is globally unique
    _ = agent, config  # Suppress unused warnings

    client = get_authenticated_client()
    is_interactive = sys.stdin.isatty()

    # Confirm deletion
    if not yes and not json_output:
        if not is_interactive:
            console.print("[red]Error:[/red] Cannot confirm deletion in non-interactive mode.")
            console.print("Use '--yes' or '-y' to skip confirmation prompts.")
            raise typer.Exit(1)
        confirm = questionary.confirm(
            f"Are you sure you want to delete key '{key_id}'?",
            default=False,
        ).ask()
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            raise typer.Exit(0)

    try:
        client.agent_api_keys.delete(id=key_id)

        if json_output:
            typer.echo(json.dumps({"deleted": True, "key_id": key_id}))
        else:
            console.print(f"[green]✓[/green] Removed key '{key_id}'")

    except Exception as e:
        if json_output:
            typer.echo(json.dumps({"deleted": False, "key_id": key_id, "error": str(e)}))
            raise typer.Exit(1) from e
        console.print(f"[red]Error:[/red] {e!s}")
        logger.exception("Failed to remove webhook key")
        raise typer.Exit(1) from e


# Add 'delete' as a hidden alias for 'rm'
keys.command("delete", hidden=True)(remove_key)
