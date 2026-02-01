"""List command - Display available skills."""

import click
from rich.console import Console
from rich.table import Table

from ask.utils.skill_registry import get_all_skills

console = Console()


@click.command(name="list")
@click.option("--category", "-c", help="Filter by category")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed info")
def list_cmd(category: str, verbose: bool):
    """List all available skills."""
    skills = get_all_skills()
    
    if category:
        skills = [s for s in skills if s.get("category") == category]
    
    if not skills:
        console.print("[yellow]No skills found.[/yellow]")
        if category:
            console.print(f"[dim]Try removing the --category filter.[/dim]")
        return
    
    table = Table(title="📦 Available Skills", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="white")
    table.add_column("Category", style="dim")
    table.add_column("Version", style="green")
    table.add_column("Description", style="dim", max_width=50)
    
    if verbose:
        table.add_column("Tags", style="magenta")
        table.add_column("Agents", style="blue")
    
    for skill in sorted(skills, key=lambda s: (s.get("category", ""), s.get("name", ""))):
        row = [
            skill.get("name", "unknown"),
            skill.get("category", "—"),
            skill.get("version", "—"),
            skill.get("description", "—")[:50],
        ]
        
        if verbose:
            row.append(", ".join(skill.get("tags", [])) or "—")
            row.append(", ".join(skill.get("agents", [])) or "—")
        
        table.add_row(*row)
    
    console.print()
    console.print(table)
    console.print(f"\n[dim]Total: {len(skills)} skill(s)[/dim]")
