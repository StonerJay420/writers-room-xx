#!/usr/bin/env python3
"""
Writers Room X CLI - Command line interface for manuscript editing workflow.

This CLI provides commands for ingesting manuscripts, running agent passes,
and managing the Writers Room X system.
"""

import typer
import asyncio
from pathlib import Path
from typing import List, Optional
import json
import yaml
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import httpx
from datetime import datetime

# Initialize Typer app and Rich console
app = typer.Typer(name="writers-room", help="Writers Room X CLI for manuscript editing")
console = Console()

# Configuration
API_BASE_URL = "http://localhost:8000/api"
DEFAULT_DATA_DIR = Path("data")


@app.command()
def ingest(
    manuscript_dir: Optional[Path] = typer.Option(
        None, "--manuscript", "-m", help="Path to manuscript directory"
    ),
    codex_dir: Optional[Path] = typer.Option(
        None, "--codex", "-c", help="Path to codex directory"
    ),
    reindex: bool = typer.Option(
        False, "--reindex", help="Force reindexing of existing files"
    )
):
    """Ingest manuscript and codex files into the system."""
    
    if not manuscript_dir and not codex_dir:
        manuscript_dir = DEFAULT_DATA_DIR / "manuscript"
        codex_dir = DEFAULT_DATA_DIR / "codex"
    
    paths_to_index = []
    if manuscript_dir and manuscript_dir.exists():
        paths_to_index.append(str(manuscript_dir))
    if codex_dir and codex_dir.exists():
        paths_to_index.append(str(codex_dir))
    
    if not paths_to_index:
        console.print("[red]No valid directories found to ingest[/red]")
        raise typer.Exit(1)
    
    console.print(f"[blue]Ingesting files from: {', '.join(paths_to_index)}[/blue]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Indexing files...", total=None)
        
        try:
            response = httpx.post(
                f"{API_BASE_URL}/ingest/index",
                json={"paths": paths_to_index, "reindex": reindex},
                timeout=120.0
            )
            response.raise_for_status()
            
            result = response.json()
            progress.update(task, completed=True)
            
            console.print(f"[green]✓ Successfully indexed {result['scenes']} scenes and {result['chunks']} chunks[/green]")
            
        except httpx.RequestError as e:
            console.print(f"[red]✗ Failed to connect to API: {e}[/red]")
            raise typer.Exit(1)
        except httpx.HTTPStatusError as e:
            console.print(f"[red]✗ API error: {e.response.status_code} - {e.response.text}[/red]")
            raise typer.Exit(1)


@app.command()
def scenes(
    chapter: Optional[int] = typer.Option(None, "--chapter", "-c", help="Filter by chapter"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search in scene text"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format: table, json")
):
    """List available scenes with optional filtering."""
    
    params = {}
    if chapter:
        params["chapter"] = chapter
    if search:
        params["search"] = search
    
    try:
        response = httpx.get(f"{API_BASE_URL}/scenes", params=params)
        response.raise_for_status()
        
        scenes_data = response.json()
        
        if output_format == "json":
            console.print(json.dumps(scenes_data, indent=2))
            return
        
        # Create table output
        table = Table(title="Available Scenes")
        table.add_column("Scene ID", style="cyan")
        table.add_column("Chapter", style="magenta")
        table.add_column("Order", style="green")
        table.add_column("POV", style="yellow")
        table.add_column("Location", style="blue")
        
        for scene in scenes_data:
            table.add_row(
                scene["id"],
                str(scene["chapter"]),
                str(scene["order_in_chapter"]),
                scene.get("pov", "N/A"),
                scene.get("location", "N/A")
            )
        
        console.print(table)
        console.print(f"\n[blue]Found {len(scenes_data)} scenes[/blue]")
        
    except httpx.RequestError as e:
        console.print(f"[red]✗ Failed to connect to API: {e}[/red]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]✗ API error: {e.response.status_code}[/red]")
        raise typer.Exit(1)


@app.command()
def run_pass(
    scene_id: str = typer.Argument(help="Scene ID to process"),
    agents: List[str] = typer.Option(
        ["lore_archivist", "grim_editor", "tone_metrics"], 
        "--agent", "-a", 
        help="Agents to run (can be specified multiple times)"
    ),
    edge_intensity: int = typer.Option(0, "--edge", "-e", help="Edge intensity (0-10)"),
    save_artifacts: bool = typer.Option(True, "--save", help="Save patch artifacts to disk")
):
    """Run an agent pass on a specific scene."""
    
    console.print(f"[blue]Running pass on scene '{scene_id}' with agents: {', '.join(agents)}[/blue]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Processing scene...", total=None)
        
        try:
            response = httpx.post(
                f"{API_BASE_URL}/passes/run",
                json={
                    "scene_id": scene_id,
                    "agents": agents,
                    "edge_intensity": edge_intensity
                },
                timeout=300.0  # 5 minutes for agent processing
            )
            response.raise_for_status()
            
            result = response.json()
            progress.update(task, completed=True)
            
            # Display results
            console.print(f"[green]✓ Pass completed for scene '{scene_id}'[/green]")
            
            # Show variants
            variants = result.get("variants", {})
            for variant_name, variant_data in variants.items():
                console.print(f"\n[bold]{variant_name.upper()} VARIANT:[/bold]")
                console.print(f"  Agents: {', '.join(variant_data.get('agents', []))}")
                console.print(f"  Risk Level: {variant_data.get('risk_level', 'unknown')}")
                console.print(f"  Temperature: {variant_data.get('temperature', 'N/A')}")
                
                if variant_data.get("rationale"):
                    console.print(f"  Rationale: {len(variant_data['rationale'])} recommendations")
            
            # Show metrics summary
            reports = result.get("reports", {})
            if reports.get("metrics"):
                console.print(f"\n[bold]METRICS ANALYSIS:[/bold]")
                metrics = reports["metrics"]
                if "overall_assessment" in metrics:
                    console.print(f"  {metrics['overall_assessment']}")
            
            # Show canon findings
            if reports.get("canon_receipts"):
                receipts = reports["canon_receipts"]
                console.print(f"\n[bold]CANON VALIDATION:[/bold]")
                console.print(f"  Found {len(receipts)} canon references")
            
            if save_artifacts:
                console.print(f"\n[green]✓ Artifacts saved to artifacts/patches/{scene_id}/[/green]")
            
        except httpx.RequestError as e:
            console.print(f"[red]✗ Failed to connect to API: {e}[/red]")
            raise typer.Exit(1)
        except httpx.HTTPStatusError as e:
            console.print(f"[red]✗ API error: {e.response.status_code} - {e.response.text}[/red]")
            raise typer.Exit(1)


@app.command()
def view_scene(
    scene_id: str = typer.Argument(help="Scene ID to view"),
    show_metadata: bool = typer.Option(False, "--metadata", "-m", help="Show scene metadata")
):
    """View the content of a specific scene."""
    
    try:
        response = httpx.get(f"{API_BASE_URL}/scenes/{scene_id}")
        response.raise_for_status()
        
        scene_data = response.json()
        
        console.print(f"[bold cyan]Scene: {scene_data['id']}[/bold cyan]")
        console.print(f"[blue]Path: {scene_data['path']}[/blue]")
        
        if show_metadata:
            # Try to get metadata from scenes list
            metadata_response = httpx.get(f"{API_BASE_URL}/scenes")
            if metadata_response.status_code == 200:
                scenes = metadata_response.json()
                scene_meta = next((s for s in scenes if s["id"] == scene_id), None)
                if scene_meta:
                    console.print(f"\n[bold]Metadata:[/bold]")
                    console.print(f"  Chapter: {scene_meta['chapter']}")
                    console.print(f"  Order: {scene_meta['order_in_chapter']}")
                    console.print(f"  POV: {scene_meta.get('pov', 'N/A')}")
                    console.print(f"  Location: {scene_meta.get('location', 'N/A')}")
        
        console.print(f"\n[bold]Content:[/bold]")
        console.print(scene_data["text"])
        
    except httpx.RequestError as e:
        console.print(f"[red]✗ Failed to connect to API: {e}[/red]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]✗ Scene '{scene_id}' not found[/red]")
        else:
            console.print(f"[red]✗ API error: {e.response.status_code}[/red]")
        raise typer.Exit(1)


@app.command()
def status():
    """Check system status and health."""
    
    console.print("[blue]Checking Writers Room X system status...[/blue]")
    
    # Check API connectivity
    try:
        response = httpx.get("http://localhost:8000/", timeout=10.0)
        response.raise_for_status()
        console.print("[green]✓ API server is running[/green]")
    except (httpx.RequestError, httpx.HTTPStatusError):
        console.print("[red]✗ API server is not responding[/red]")
        raise typer.Exit(1)
    
    # Check service statuses
    services = ["ingest", "passes", "patches"]
    
    for service in services:
        try:
            response = httpx.get(f"{API_BASE_URL}/{service}/", timeout=5.0)
            if response.status_code == 200:
                console.print(f"[green]✓ {service.title()} service ready[/green]")
            else:
                console.print(f"[yellow]⚠ {service.title()} service status unknown[/yellow]")
        except:
            console.print(f"[red]✗ {service.title()} service unavailable[/red]")
    
    # Check data directories
    data_dirs = [DEFAULT_DATA_DIR / "manuscript", DEFAULT_DATA_DIR / "codex"]
    for data_dir in data_dirs:
        if data_dir.exists():
            md_files = list(data_dir.glob("*.md"))
            console.print(f"[green]✓ {data_dir.name} directory: {len(md_files)} files[/green]")
        else:
            console.print(f"[yellow]⚠ {data_dir.name} directory not found[/yellow]")


@app.command()
def metrics(
    scene_id: str = typer.Argument(help="Scene ID to analyze"),
    save_report: bool = typer.Option(False, "--save", help="Save metrics report to file")
):
    """Analyze metrics for a specific scene."""
    
    console.print(f"[blue]Analyzing metrics for scene '{scene_id}'...[/blue]")
    
    try:
        # Get scene content
        scene_response = httpx.get(f"{API_BASE_URL}/scenes/{scene_id}")
        scene_response.raise_for_status()
        scene_data = scene_response.json()
        
        # Run tone metrics analysis
        metrics_response = httpx.post(
            f"{API_BASE_URL}/passes/run",
            json={
                "scene_id": scene_id,
                "agents": ["tone_metrics"],
                "edge_intensity": 0
            },
            timeout=60.0
        )
        metrics_response.raise_for_status()
        
        result = metrics_response.json()
        metrics_data = result.get("reports", {}).get("metrics", {})
        
        if not metrics_data:
            console.print("[red]✗ No metrics data available[/red]")
            raise typer.Exit(1)
        
        # Display metrics in a table
        table = Table(title=f"Metrics Analysis - {scene_id}")
        table.add_column("Metric", style="cyan")
        table.add_column("Score", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Recommendation", style="yellow")
        
        metrics_before = metrics_data.get("metrics_before", {})
        for metric_name, metric_data in metrics_before.items():
            status_color = {
                "within_target": "green",
                "above_target": "red", 
                "below_target": "red"
            }.get(metric_data.get("status", ""), "white")
            
            table.add_row(
                metric_data.get("name", metric_name),
                f"{metric_data.get('score', 0):.2f}",
                f"[{status_color}]{metric_data.get('status', 'unknown')}[/{status_color}]",
                metric_data.get("recommendation", "N/A")
            )
        
        console.print(table)
        
        # Show overall assessment
        if "overall_assessment" in metrics_data:
            console.print(f"\n[bold]Overall Assessment:[/bold] {metrics_data['overall_assessment']}")
        
        # Show readability grade
        if "readability_grade" in metrics_data:
            console.print(f"[bold]Readability Grade:[/bold] {metrics_data['readability_grade']}")
        
        # Save report if requested
        if save_report:
            report_file = Path(f"reports/{scene_id}_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            report_file.parent.mkdir(exist_ok=True)
            
            with open(report_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            
            console.print(f"[green]✓ Report saved to {report_file}[/green]")
            
    except httpx.RequestError as e:
        console.print(f"[red]✗ Failed to connect to API: {e}[/red]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]✗ API error: {e.response.status_code}[/red]")
        raise typer.Exit(1)


@app.command()
def agents():
    """List available agents and their capabilities."""
    
    try:
        response = httpx.get(f"{API_BASE_URL}/passes/status")
        response.raise_for_status()
        
        status_data = response.json()
        
        console.print("[bold cyan]Available Agents[/bold cyan]")
        
        core_agents = status_data.get("core_agents", [])
        if core_agents:
            console.print(f"\n[bold]Core Agents:[/bold]")
            for agent in core_agents:
                console.print(f"  • {agent}")
        
        creative_agents = status_data.get("creative_agents", [])
        if creative_agents:
            console.print(f"\n[bold]Creative Agents:[/bold]")
            for agent in creative_agents:
                console.print(f"  • {agent}")
        
        console.print(f"\n[blue]Use agents with: writers-room run-pass SCENE_ID --agent AGENT_NAME[/blue]")
        
    except httpx.RequestError as e:
        console.print(f"[red]✗ Failed to connect to API: {e}[/red]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]✗ API error: {e.response.status_code}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()