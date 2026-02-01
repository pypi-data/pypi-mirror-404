from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

import questionary
import typer
from jinja2 import Environment, FileSystemLoader
from rich.console import Console
from rich.panel import Panel

from terminaluse.lib.utils.logging import make_logger

logger = make_logger(__name__)
console = Console()

# Get the templates directory relative to this file
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class TemplateType(str, Enum):
    TEMPORAL = "temporal"
    DEFAULT = "default"


def render_template(template_path: str, context: Dict[str, Any], template_type: TemplateType) -> str:
    """Render a template with the given context"""
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR / template_type.value))
    template = env.get_template(template_path)
    return template.render(**context)


def create_project_structure(path: Path, context: Dict[str, Any], template_type: TemplateType, use_uv: bool):
    """Create the project structure from templates"""
    # Create project directory
    project_dir: Path = path / context["project_name"]
    project_dir.mkdir(parents=True, exist_ok=True)

    # Create src/ directory for agent code
    code_dir: Path = project_dir / "src"
    code_dir.mkdir(parents=True, exist_ok=True)

    # Create __init__.py
    (code_dir / "__init__.py").touch()

    # Define source files based on template type
    source_files = {
        TemplateType.TEMPORAL: ["agent.py", "workflow.py", "run_worker.py"],
        TemplateType.DEFAULT: ["agent.py"],
    }[template_type]

    # Create src/ files
    for template in source_files:
        template_path = f"src/{template}.j2"
        output_path = code_dir / template
        output_path.write_text(render_template(template_path, context, template_type))

    # Create root files
    root_templates = {
        ".dockerignore.j2": ".dockerignore",
        "config.yaml.j2": "config.yaml",
        "README.md.j2": "README.md",
    }

    # Add package management file based on uv choice
    if use_uv:
        root_templates["pyproject.toml.j2"] = "pyproject.toml"
        root_templates["Dockerfile-uv.j2"] = "Dockerfile"
    else:
        root_templates["requirements.txt.j2"] = "requirements.txt"
        root_templates["Dockerfile.j2"] = "Dockerfile"

    for template, output in root_templates.items():
        output_path = project_dir / output
        output_path.write_text(render_template(template, context, template_type))

    console.print(f"\n[green]✓[/green] Created project structure at: {project_dir}")


def get_project_context(answers: Dict[str, Any], project_path: Path, manifest_root: Path) -> Dict[str, Any]:  # noqa: ARG001
    """Get the project context from user answers"""
    # Use agent_directory_name as project_name
    project_name = answers["agent_directory_name"].replace("-", "_")

    # Now, this is actually the exact same as the project_name because we changed the build root to be ../
    project_path_from_build_root = project_name

    # Use the already-parsed namespace and agent short name from answers
    agent_short_name = answers["agent_short_name"]

    return {
        **answers,
        "project_name": project_name,
        "workflow_class": "".join(word.capitalize() for word in agent_short_name.split("-")) + "Workflow",
        "workflow_name": agent_short_name,
        "queue_name": project_name + "_queue",
        "project_path_from_build_root": project_path_from_build_root,
    }


def validate_slug(text: str) -> bool:
    """Validate a slug (lowercase alphanumeric with hyphens)"""
    return bool(len(text) >= 1 and text.replace("-", "").isalnum() and text.islower())


def init(
    namespace: Optional[str] = typer.Option(
        None,
        "--namespace",
        "-ns",
        help="Namespace slug (e.g., 'acme-corp')",
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Agent name (e.g., 'my-agent')",
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="Agent description",
    ),
    template: str = typer.Option(
        "default",
        "--template",
        "-t",
        help="Template type: 'default' or 'temporal'",
    ),
    no_uv: bool = typer.Option(
        False,
        "--no-uv",
        help="Use pip instead of uv for package management",
    ),
):
    """Initialize a new agent project.

    Can be run interactively (no arguments) or non-interactively with --namespace and --name.

    Examples:
        tu init                                    # Interactive mode
        tu init -ns acme-corp -n my-agent          # Non-interactive mode
        tu init -ns test -n hello-world -d "My first agent"
    """
    # Determine if we have enough args for non-interactive mode
    non_interactive = namespace is not None and name is not None

    if not non_interactive:
        # Check for interactive mode - init requires user input
        if not sys.stdin.isatty():
            console.print(
                "[red]Error:[/red] The 'init' command requires interactive mode or --namespace and --name arguments."
            )
            console.print("Usage: tu init --namespace <namespace> --name <agent-name>")
            console.print("   or: tu init  (for interactive mode)")
            raise typer.Exit(1)

        console.print(
            Panel.fit(
                "[bold blue]Create New Agent[/bold blue]",
                border_style="blue",
            )
        )
        console.print()

        def validate_slug_questionary(text: str) -> bool | str:
            """Validate a slug for questionary (returns error message on failure)"""
            if not validate_slug(text):
                return "Invalid format. Use only lowercase letters, numbers, and hyphens (e.g., 'acme-corp')"
            return True

        # Question 1: Namespace slug (required)
        namespace = questionary.text(
            "Namespace slug (e.g., 'acme-corp'):",
            validate=validate_slug_questionary,
        ).ask()
        if not namespace:
            return

        # Question 2: Agent name (required)
        name = questionary.text(
            "Agent name (e.g., 'my-agent'):",
            validate=validate_slug_questionary,
        ).ask()
        if not name:
            return

        # Question 3: Description (optional with default)
        description = questionary.text("Description (optional):", default="My agent").ask()
        if description is None:
            return
    else:
        # Non-interactive mode - validate inputs
        # namespace and name are guaranteed non-None here (checked in non_interactive condition)
        assert namespace is not None
        assert name is not None

        if not validate_slug(namespace):
            console.print(
                f"[red]Error:[/red] Invalid namespace '{namespace}'. Use only lowercase letters, numbers, and hyphens."
            )
            raise typer.Exit(1)

        if not validate_slug(name):
            console.print(
                f"[red]Error:[/red] Invalid agent name '{name}'. Use only lowercase letters, numbers, and hyphens."
            )
            raise typer.Exit(1)

        if description is None:
            description = "My agent"

        console.print(
            Panel.fit(
                "[bold blue]Create New Agent[/bold blue]",
                border_style="blue",
            )
        )

    # Validate template type
    try:
        template_type = TemplateType(template.lower())
    except ValueError:
        console.print(f"[red]Error:[/red] Invalid template '{template}'. Use 'default' or 'temporal'.")
        raise typer.Exit(1)

    # Combine into full agent name
    agent_name = f"{namespace}/{name}"
    namespace_slug = namespace
    agent_short_name = name

    # Use sensible defaults
    project_path_str = "."
    # Use the agent short name for directory
    agent_directory_name = agent_short_name
    use_uv = not no_uv

    answers: Dict[str, Any] = {
        "template_type": template_type,
        "project_path": project_path_str,
        "agent_name": agent_name,
        "namespace_slug": namespace_slug,
        "agent_short_name": agent_short_name,
        "agent_directory_name": agent_directory_name,
        "description": description,
        "use_uv": use_uv,
    }

    # Derive all names from agent_directory_name and path
    project_path = Path(project_path_str).resolve()
    manifest_root = Path("../../")

    # Get project context
    context = get_project_context(answers, project_path, manifest_root)
    context["template_type"] = template_type.value
    context["use_uv"] = use_uv

    # Create project structure
    create_project_structure(project_path, context, template_type, use_uv)

    # Show success message with quick start
    console.print()
    console.print(f"[bold green]Created {context['project_name']}/[/bold green]")
    console.print()

    # Simple next steps
    console.print("[bold]Get started:[/bold]")
    console.print(f"  [cyan]cd {context['project_name']}[/cyan]")
    console.print("  [cyan]uv venv && uv sync && source .venv/bin/activate[/cyan]")
    console.print("  [cyan]tu deploy[/cyan]")
    console.print()

    console.print("[dim]Edit [yellow]src/agent.py[/yellow] to customize your agent.[/dim]")
    console.print("[dim]Docs: https://docs.terminaluse.com[/dim]")
    console.print()
