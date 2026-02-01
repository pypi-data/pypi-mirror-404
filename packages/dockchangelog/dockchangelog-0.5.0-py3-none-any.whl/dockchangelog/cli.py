"""
Command-line interface for dockchangelog.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from . import __version__
from .checker import DockerChecker
from .config import Config, create_example_config, load_config
from .formatter import OutputFormatter
from .github_client import GitHubClient
from .mapper import ImageMapper
from .update_checker import check_for_updates

app = typer.Typer(
    name="dockchangelog",
    help="check docker updates with github release notes",
    add_completion=False,
)

console = Console()


@app.command()
def check(
    compose_dir: Optional[Path] = typer.Option(
        None,
        "--compose-dir",
        "-d",
        help="directory containing compose files (default: current directory)",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="path to config file",
    ),
    service: Optional[str] = typer.Option(
        None,
        "--service",
        "-s",
        help="check specific service only",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="disable cache for GitHub API responses",
    ),
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="show all results at once (no pausing between services)",
    ),
    include_stopped: bool = typer.Option(
        False,
        "--include-stopped",
        help="include stopped containers (by default only shows running)",
    ),
    use_sudo: bool = typer.Option(
        False,
        "--sudo",
        help="use sudo for docker commands",
    ),
):
    """
    check for docker image updates and show release notes
    
    This is the main command - it's safe and read-only.
    By default, pauses after each service with updates.
    """
    # Load configuration
    config = load_config(config_file)
    
    # Use interactive mode if stdout is a terminal and not disabled
    interactive = not no_interactive and console.is_terminal
    
    # Initialize components
    checker = DockerChecker(compose_dir, use_sudo=use_sudo)
    github = GitHubClient(
        token=config.github_token,
        cache_dir=None if no_cache else config.cache.path,
    )
    mapper = ImageMapper(config)
    formatter = OutputFormatter(console)
    
    # Show header
    formatter.show_header()
    
    # Check for updates (non-blocking, shows notification if available)
    update_info = check_for_updates()
    if update_info:
        current, latest, update_cmd = update_info
        console.print()
        console.print(f"[yellow]⚡ Update available:[/yellow] [dim]{current}[/dim] → [bold green]{latest}[/bold green]")
        console.print(f"[dim]Run:[/dim] [cyan]{update_cmd}[/cyan]")
        console.print()
    
    # Find and parse compose files
    services = checker.get_all_services()
    
    if not services:
        formatter.show_no_services_found()
        raise typer.Exit(0)
    
    # Filter to only running services by default
    if not include_stopped:
        services = [s for s in services if s.is_running()]
        if not services:
            console.print("[yellow]⚠  No running services found[/yellow]")
            console.print()
            console.print("Use --include-stopped to check all services")
            raise typer.Exit(0)
    
    # Filter to specific service if requested
    if service:
        services = [s for s in services if s.name == service]
        if not services:
            formatter.show_error(f"service '{service}' not found")
            raise typer.Exit(1)
    
    # Sort services alphabetically by name
    services = sorted(services, key=lambda s: s.name.lower())
    
    # Check each service
    services_with_updates = 0
    services_checked = 0
    tagged_for_update = []  # Store services marked for update
    
    for svc in services:
        # Map to GitHub repo
        repo = mapper.map(svc)
        
        if not repo:
            console.print(f"[dim]• {svc.name}: no github mapping found[/dim]")
            continue
        
        # Get latest release
        release = github.get_latest_release(repo)
        
        if not release:
            console.print(f"[dim]• {svc.name}: no releases found for {repo}[/dim]")
            continue
        
        # Get the ACTUAL running version (not what's in compose file)
        # This handles cases where compose uses 'latest' but we want real version
        running_version = svc.get_running_image_version()
        
        # Determine what version we're comparing
        # Priority: running image version > compose file tag
        current_version = running_version if running_version else svc.image.tag
        
        # Compare versions (normalize by removing 'v' prefix if present)
        def normalize_version(v: str) -> str:
            """Remove 'v' prefix and clean up version string."""
            v = v.strip().lower()
            if v.startswith('v'):
                v = v[1:]
            return v
        
        current_normalized = normalize_version(current_version)
        release_normalized = normalize_version(release.tag)
        
        # Handle major version tags (e.g., "2" tracking latest "2.x.x")
        # If current is a major version like "2" and latest starts with "2.", 
        # consider them matching (user is intentionally tracking that major version)
        def is_major_version_match(current: str, latest: str) -> bool:
            """Check if current is a major version tag tracking the latest release."""
            # Check if current looks like a major version (just digits, optionally with .0)
            if current.replace('.0', '').replace('.', '').isdigit() and len(current.split('.')) <= 2:
                # Check if latest starts with current major version
                latest_parts = latest.split('.')
                current_parts = current.split('.')
                
                # If current is "2" or "2.0", check if latest is "2.x.x"
                if len(current_parts) >= 1 and len(latest_parts) >= 1:
                    if current_parts[0] == latest_parts[0]:
                        # If current is just major (like "2"), it matches "2.x.x"
                        if len(current_parts) == 1:
                            return True
                        # If current is "2.0", check if latest is "2.0.x"
                        if len(current_parts) == 2 and len(latest_parts) >= 2:
                            if current_parts[1] == latest_parts[1]:
                                return True
            return False
        
        # Check if update available
        if current_normalized == release_normalized:
            has_update = False
        elif is_major_version_match(current_normalized, release_normalized):
            has_update = False  # Already tracking this major version
        else:
            has_update = True
        
        # Show results (display original versions, not normalized)
        formatter.show_service_update(svc.name, current_version, release, has_update)
        
        if has_update:
            services_with_updates += 1
            services_checked += 1
            
            # In interactive mode, pause after showing each service with updates
            if interactive:
                console.print()
                console.print("[dim]Press [bold]u[/bold] to mark for update, [bold]Enter[/bold] to skip, [bold]Ctrl+C[/bold] to stop...[/dim] ", end="")
                try:
                    response = input().strip().lower()
                    if response == 'u':
                        tagged_for_update.append({
                            'name': svc.name,
                            'compose_file': svc.compose_file,
                            'current': current_version,
                            'latest': release.tag,
                        })
                        console.print(f"[green]✓[/green] {svc.name} marked for update")
                except (KeyboardInterrupt, EOFError):
                    console.print("\n")
                    break
                console.print()  # Add spacing after continue
    
    # Show summary
    formatter.show_summary(len(services), services_with_updates)
    
    # If services were tagged, show them and provide update commands
    if tagged_for_update:
        console.print()
        console.print("[bold cyan]Services marked for update:[/bold cyan]")
        console.print()
        
        for item in tagged_for_update:
            console.print(f"  • [yellow]{item['name']}[/yellow]")
            console.print(f"    {item['current']} → {item['latest']}")
            console.print(f"    [dim]{item['compose_file']}[/dim]")
        
        console.print()
        console.print("[bold]To update these services, run:[/bold]")
        console.print()
        
        # Group by compose file for batch updating
        by_compose = {}
        for item in tagged_for_update:
            compose_file = str(item['compose_file'])
            if compose_file not in by_compose:
                by_compose[compose_file] = []
            by_compose[compose_file].append(item['name'])
        
        # Sort compose files alphabetically
        sorted_compose_files = sorted(by_compose.items())
        
        # Create a single bash script
        console.print("[dim]# Copy and paste this script:[/dim]")
        console.print()
        
        sudo_prefix = "sudo " if use_sudo else ""
        
        commands = []
        for compose_file, service_names in sorted_compose_files:
            compose_dir = Path(compose_file).parent
            services_str = ' '.join(sorted(service_names))  # Also sort service names
            commands.append(f"cd {compose_dir} && {sudo_prefix}docker compose pull {services_str} && {sudo_prefix}docker compose up -d {services_str}")
        
        # Join commands with && \ but not on the last one
        for i, cmd in enumerate(commands):
            if i < len(commands) - 1:
                console.print(f"{cmd} && \\")
            else:
                console.print(cmd)  # No trailing && \ on the last command
        
        console.print()
        console.print("[dim]# Or save to a file and run:[/dim]")
        console.print("[dim]# dockchangelog check > /tmp/updates.sh && bash /tmp/updates.sh[/dim]")
        console.print()
    
    # Exit code: 0 if up to date, 1 if updates available
    raise typer.Exit(0 if services_with_updates == 0 else 1)


@app.command()
def init(
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="output path for config file (default: ./config.yml)",
    ),
):
    """
    create example configuration file
    """
    output_path = output or Path("config.yml")
    
    if output_path.exists():
        overwrite = typer.confirm(f"{output_path} already exists. overwrite?")
        if not overwrite:
            console.print("cancelled")
            raise typer.Exit(0)
    
    # Create config
    config_content = create_example_config()
    output_path.write_text(config_content)
    
    console.print(f"[green]✓[/green] created config file: {output_path}")
    console.print()
    console.print("edit this file to add image mappings and settings")


@app.command()
def version():
    """
    show version information
    """
    console.print(f"dockchangelog version {__version__}")


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
