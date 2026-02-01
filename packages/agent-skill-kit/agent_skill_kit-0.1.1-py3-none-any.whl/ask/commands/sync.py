"""Sync command - Synchronize all skills to all agents."""

import click
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from ask.utils.skill_registry import get_all_skills
from ask.utils.filesystem import get_adapter
from ask.utils.agent_registry import get_available_agents, get_agent_scopes

console = Console()


@click.command()
@click.argument("target", type=click.Choice(["all"]))
def sync(target: str):
    """Sync all skills to all agents.
    
    TARGET must be 'all' to sync to all supported agents.
    
    Prompts for local or global destination.
    
    Examples:
    
        ask sync all
    """
    skills = get_all_skills()
    
    if not skills:
        console.print("[yellow]No skills found to sync.[/yellow]")
        return
    
    agents = get_available_agents()
    
    if not agents:
        console.print("[yellow]No agents found.[/yellow]")
        return
    
    # Ask for scope first
    console.print(f"\n[bold]📦 Syncing {len(skills)} skill(s) to {len(agents)} agent(s)[/bold]\n")
    console.print("[bold]Choose destination:[/bold]")
    console.print("  [dim]0[/dim] Cancel")
    console.print("  [green]1[/green] Global (user home directory)")
    console.print("  [cyan]2[/cyan] Local (project directory)")
    
    choice_num = Prompt.ask(
        "Enter choice",
        choices=["0", "1", "2"],
        default="2"
    )
    
    if choice_num == "0":
        console.print("[yellow]Cancelled.[/yellow]")
        raise click.Abort()
    
    use_global = (choice_num == "1")
    scope_name = "global" if use_global else "local"
    
    console.print(f"\n[bold]Syncing to {scope_name}...[/bold]\n")
    
    # Results tracking
    results = {agent: {"copied": 0, "skipped": 0, "failed": 0} for agent in agents}
    
    for agent in agents:
        adapter = get_adapter(agent, use_global=use_global)
        if not adapter:
            console.print(f"[yellow]⚠️  No adapter for {agent}, skipping[/yellow]")
            continue
        
        compatible_skills = [s for s in skills if agent in s.get("agents", [])]
        
        for skill in compatible_skills:
            try:
                result = adapter.copy_skill(skill)
                
                if result["status"] == "copied":
                    results[agent]["copied"] += 1
                elif result["status"] == "conflict":
                    results[agent]["skipped"] += 1
                    
            except Exception as e:
                results[agent]["failed"] += 1
                console.print(f"[red]  ✗ {skill['name']} → {agent}: {e}[/red]")
    
    # Summary table
    table = Table(title="Sync Summary", show_header=True, header_style="bold")
    table.add_column("Agent", style="cyan")
    table.add_column("Copied", style="green", justify="right")
    table.add_column("Skipped", style="yellow", justify="right")
    table.add_column("Failed", style="red", justify="right")
    
    for agent, counts in results.items():
        table.add_row(
            agent,
            str(counts["copied"]),
            str(counts["skipped"]),
            str(counts["failed"])
        )
    
    console.print()
    console.print(table)
