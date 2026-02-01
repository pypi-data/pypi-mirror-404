"""
Project CLI handlers for managing projects.

This module provides core project-related logic for the CLI.
"""

from __future__ import annotations

from terminaluse import TerminalUse
from terminaluse.types import Project
from terminaluse.lib.utils.logging import make_logger

logger = make_logger(__name__)


class ProjectError(Exception):
    """Base exception for project operations."""

    pass


def resolve_namespace_id_from_slug(client: TerminalUse, namespace_slug: str) -> str:
    """
    Resolve a namespace slug to its ID.

    Args:
        client: The TerminalUse client instance
        namespace_slug: Namespace slug to look up

    Returns:
        namespace_id from the namespace

    Raises:
        ProjectError: If namespace cannot be found
    """
    try:
        namespace = client.namespaces.retrieve_by_slug(namespace_slug)
        return namespace.id
    except Exception as e:
        raise ProjectError(f"Namespace '{namespace_slug}' not found: {e}") from e


def format_project_summary(project: Project) -> str:
    """
    Format project details as human-readable summary.

    Args:
        project: Project object

    Returns:
        Formatted string summary
    """
    lines = []
    lines.append(f"Project:     {project.id}")
    lines.append(f"Name:        {project.name}")
    lines.append(f"Namespace:   {project.namespace_id}")
    lines.append(f"Description: {project.description or '(none)'}")

    # Format created timestamp
    if project.created_at:
        created_str = project.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
    else:
        created_str = "unknown"
    lines.append(f"Created:     {created_str}")
    lines.append(f"Created By:  {project.created_by}")

    return "\n".join(lines)


def format_projects_table(
    projects: list[Project],
    namespace_slug: str | None = None,
) -> str:
    """
    Format list of projects as a table.

    Args:
        projects: List of Project objects
        namespace_slug: Optional namespace slug for display context

    Returns:
        Formatted table string
    """
    if not projects:
        if namespace_slug:
            return f"No projects found for namespace '{namespace_slug}'"
        return "No projects found"

    lines = []
    if namespace_slug:
        lines.append(f"Projects for namespace '{namespace_slug}':\n")
    else:
        lines.append("Projects:\n")

    # Header
    lines.append(f"  {'ID':<36}  {'Name':<20}  {'Description':<24}  {'Created':<16}")

    for project in projects:
        proj_id = project.id[:36] if len(project.id) > 36 else project.id
        name = (project.name or "(unnamed)")[:20]
        description = (project.description or "")[:24]

        if project.created_at:
            created = project.created_at.strftime("%Y-%m-%d %H:%M")
        else:
            created = "unknown"

        lines.append(f"  {proj_id:<36}  {name:<20}  {description:<24}  {created:<16}")

    lines.append(f"\nTotal: {len(projects)} project(s)")
    return "\n".join(lines)
