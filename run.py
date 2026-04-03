"""Entry point for the Cloud Cost Negotiator agent.

Usage:
    python run.py                # Full pipeline: analyze + negotiate
    python run.py --analyze-only # Just the ReAct agent analysis
    python run.py --negotiate-only # Just the negotiation sim
"""

import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from src.agent import run_agent
from src.negotiation_sim import run_negotiation

console = Console()

DEFAULT_BILL_PATH = str(Path(__file__).parent / "mock_data" / "aws_bill.json")


def main():
    parser = argparse.ArgumentParser(description="AWS Cloud Cost Negotiator Agent")
    parser.add_argument("--bill", default=DEFAULT_BILL_PATH, help="Path to AWS bill JSON")
    parser.add_argument("--analyze-only", action="store_true", help="Only run bill analysis")
    parser.add_argument("--negotiate-only", action="store_true", help="Only run negotiation sim")
    args = parser.parse_args()

    console.print()
    console.print(Panel(
        "[bold white]AWS CLOUD COST NEGOTIATOR[/bold white]\n"
        "[dim]A ReAct agent that analyzes your bill, finds savings, and negotiates for you[/dim]",
        style="bold blue",
        padding=(1, 4),
    ))

    if args.negotiate_only:
        run_negotiation()
        return

    # --- Step 1: ReAct Agent ---
    console.print()
    console.print(f"[bold cyan]{'='*60}[/bold cyan]")
    console.print(f"[bold cyan]  AGENT: ANALYZING BILL & BUILDING STRATEGY[/bold cyan]")
    console.print(f"[bold cyan]{'='*60}[/bold cyan]")
    console.print(f"[dim]Bill: {args.bill}[/dim]")
    console.print()

    agent_output = run_agent(args.bill)

    console.print()
    console.print(f"[bold cyan]{'='*60}[/bold cyan]")
    console.print(f"[bold cyan]  AGENT OUTPUT[/bold cyan]")
    console.print(f"[bold cyan]{'='*60}[/bold cyan]")
    console.print()
    console.print(Markdown(agent_output))

    # --- Step 2: Negotiation Sim ---
    if not args.analyze_only:
        console.print()
        console.print(f"[bold cyan]{'='*60}[/bold cyan]")
        console.print(f"[bold cyan]  LIVE NEGOTIATION SIMULATION[/bold cyan]")
        console.print(f"[bold cyan]{'='*60}[/bold cyan]")
        console.print("[bold]Two AI agents negotiate your cloud bill...[/bold]")
        console.print()
        run_negotiation()

    console.print()
    console.print(Panel(
        "[bold green]DONE![/bold green] Your cloud cost analysis is complete.",
        style="green",
    ))


if __name__ == "__main__":
    main()