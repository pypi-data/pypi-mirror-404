"""Job management commands."""

import click
from rich.console import Console
from pathlib import Path

from dremio_cli.config import ProfileManager
from dremio_cli.client.factory import create_client
from dremio_cli.formatters.table import format_as_table
from dremio_cli.formatters.json import format_as_json
from dremio_cli.formatters.yaml import format_as_yaml

console = Console()


@click.group()
def job() -> None:
    """Job management operations."""
    pass


@job.command("list")
@click.option("--max-results", type=int, help="Maximum number of results to return")
@click.option("--filter", "filter_expr", help="Filter expression (e.g., 'state=COMPLETED')")
@click.option("--sort", help="Sort field (prefix with - for descending, e.g., '-submittedAt')")
@click.pass_context
def list_jobs(ctx, max_results: int, filter_expr: str, sort: str) -> None:
    """List jobs.
    
    Examples:
        dremio job list
        dremio job list --max-results 50
        dremio job list --filter "state=COMPLETED"
        dremio job list --sort "-submittedAt"
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        # List jobs
        if hasattr(client, 'list_jobs'):
            with console.status(f"[bold green]Fetching jobs from {profile_name}..."):
                data = client.list_jobs(
                    max_results=max_results,
                    filter_expr=filter_expr,
                    sort=sort
                )
        else:
            console.print("[red]Job listing not supported for this profile type[/red]")
            raise click.Abort()
        
        # Format output
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(data))
        elif output_format == "yaml":
            console.print(format_as_yaml(data))
        else:
            # Display as table
            jobs = data.get("jobs", [])
            if jobs:
                format_as_table(jobs, title=f"Jobs ({profile_name})")
            else:
                console.print("[yellow]No jobs found[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@job.command("get")
@click.argument("job_id")
@click.pass_context
def get_job(ctx, job_id: str) -> None:
    """Get job details by ID.
    
    Examples:
        dremio job get 2c8a1234-5678-90ab-cdef-1234567890ab
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        # Get job
        with console.status(f"[bold green]Fetching job {job_id}..."):
            data = client.get_job(job_id)
        
        # Format output
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(data))
        elif output_format == "yaml":
            console.print(format_as_yaml(data))
        else:
            format_as_table(data, title=f"Job: {job_id}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@job.command("results")
@click.argument("job_id")
@click.option("--limit", type=int, help="Maximum number of rows to return")
@click.option("--offset", type=int, help="Offset for pagination")
@click.pass_context
def get_job_results(ctx, job_id: str, limit: int, offset: int) -> None:
    """Get job results.
    
    Examples:
        dremio job results 2c8a1234-5678-90ab-cdef-1234567890ab
        dremio job results 2c8a1234-5678-90ab-cdef-1234567890ab --limit 100
        dremio job results 2c8a1234-5678-90ab-cdef-1234567890ab --limit 100 --offset 100
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        # Get job results
        with console.status(f"[bold green]Fetching results for job {job_id}..."):
            data = client.get_job_results(job_id, limit=limit, offset=offset)
        
        # Format output
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(data))
        elif output_format == "yaml":
            console.print(format_as_yaml(data))
        else:
            # Display rows as table
            rows = data.get("rows", [])
            if rows:
                format_as_table(rows, title=f"Job Results: {job_id}")
                
                # Show pagination info
                row_count = data.get("rowCount", len(rows))
                console.print(f"\n[dim]Showing {len(rows)} of {row_count} rows[/dim]")
            else:
                console.print("[yellow]No results found[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@job.command("cancel")
@click.argument("job_id")
@click.confirmation_option(prompt="Are you sure you want to cancel this job?")
@click.pass_context
def cancel_job(ctx, job_id: str) -> None:
    """Cancel a running job.
    
    Examples:
        dremio job cancel 2c8a1234-5678-90ab-cdef-1234567890ab
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        # Cancel job
        with console.status(f"[bold yellow]Canceling job {job_id}..."):
            client.cancel_job(job_id)
        
        console.print(f"[green]✓[/green] Job {job_id} canceled successfully")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@job.command("profile")
@click.argument("job_id")
@click.option("--download", type=click.Path(), help="Download profile to file")
@click.pass_context
def get_job_profile(ctx, job_id: str, download: str) -> None:
    """Get job profile for performance analysis.
    
    Examples:
        dremio job profile 2c8a1234-5678-90ab-cdef-1234567890ab
        dremio job profile 2c8a1234-5678-90ab-cdef-1234567890ab --download profile.zip
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        # Get job profile
        if hasattr(client, 'get_job_profile'):
            with console.status(f"[bold green]Fetching profile for job {job_id}..."):
                data = client.get_job_profile(job_id)
            
            if download:
                # Save to file
                Path(download).write_bytes(data if isinstance(data, bytes) else data.encode())
                console.print(f"[green]✓[/green] Profile saved to {download}")
            else:
                # Display profile info
                output_format = ctx.obj.output_format
                if output_format == "json":
                    console.print(format_as_json(data))
                elif output_format == "yaml":
                    console.print(format_as_yaml(data))
                else:
                    console.print(data)
        else:
            console.print("[red]Job profile not supported for this profile type[/red]")
            raise click.Abort()
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@job.command("reflections")
@click.argument("job_id")
@click.pass_context
def get_job_reflections(ctx, job_id: str) -> None:
    """Get reflection information for a job.
    
    Examples:
        dremio job reflections 2c8a1234-5678-90ab-cdef-1234567890ab
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        # Get job reflections
        if hasattr(client, 'get_job_reflections'):
            with console.status(f"[bold green]Fetching reflections for job {job_id}..."):
                data = client.get_job_reflections(job_id)
            
            # Format output
            output_format = ctx.obj.output_format
            
            if output_format == "json":
                console.print(format_as_json(data))
            elif output_format == "yaml":
                console.print(format_as_yaml(data))
            else:
                format_as_table(data, title=f"Job Reflections: {job_id}")
        else:
            console.print("[red]Job reflections not supported for this profile type[/red]")
            raise click.Abort()
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()
@job.command("analyze")
@click.argument("job_id")
@click.pass_context
def analyze_job(ctx, job_id: str) -> None:
    """Analyze job performance.
    
    Examples:
        dremio job analyze <job-id>
    """
    try:
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            return
            
        client = create_client(profile)
        
        with console.status(f"[bold green]Analyzing job {job_id}..."):
            job = client.get_job(job_id)
            
            # Basic info
            state = job.get("jobState")
            start = job.get("startTime")
            end = job.get("endTime")
            
            # Stats (structure varies between Cloud/Software versions)
            # Safe access to stats
            stats = job.get("stats", {}) 
            
            # Provide insights
            from rich.panel import Panel
            from rich.columns import Columns
            
            # Duration
            duration = "N/A"
            if start and end:
                # Basic duration calc if not in stats (assuming epoch ms)
                try: 
                    diff = (int(end) - int(start)) / 1000.0
                    duration = f"{diff:.2f}s"
                except:
                    pass
            
            # Input/Output
            input_bytes = stats.get("inputBytes", 0)
            output_bytes = stats.get("outputBytes", 0)
            
            # Simple insights
            insights = []
            if state != "COMPLETED":
                insights.append(f"[red]Job did not complete ({state})[/red]")
                
            input_records = stats.get("inputRecords", 0)
            output_records = stats.get("outputRecords", 0)
            if input_records > 0 and output_records > 0:
                reduction = (1 - (output_records / input_records)) * 100
                insights.append(f"[green]Data Reduction: {reduction:.1f}%[/green]")
                
            # Display
            console.print(Panel(f"""
[bold]Job ID[/bold]: {job_id}
[bold]State[/bold]: {state}
[bold]Duration[/bold]: {duration}
[bold]User[/bold]: {job.get('user', 'N/A')}
            """, title="Job Summary", border_style="cyan"))
            
            if insights:
                console.print(Panel("\n".join(insights), title="Insights", border_style="yellow"))
                
            # Raw stats table
            from rich.table import Table
            t = Table(title="Metrics", show_header=False)
            t.add_row("Input Records", str(input_records))
            t.add_row("Output Records", str(output_records))
            t.add_row("Memory Used", f"{stats.get('memoryAllocation', 0)} bytes")
            console.print(t)
            
    except Exception as e:
        console.print(f"[red]Analysis failed: {e}[/red]")
