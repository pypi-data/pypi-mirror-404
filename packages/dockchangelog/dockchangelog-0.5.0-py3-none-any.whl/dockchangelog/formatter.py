"""
Format and display output using Rich.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .github_client import Release
from .parser import ParsedNotes, ReleaseNotesParser


class OutputFormatter:
    """Format output for terminal display."""
    
    def __init__(self, console: Console = None):
        """
        Initialize formatter.
        
        Args:
            console: Rich console instance. Creates new one if None.
        """
        self.console = console or Console()
        self.parser = ReleaseNotesParser()
    
    def show_header(self):
        """Display tool header."""
        self.console.print()
        self.console.print("[bold blue]dockchangelog[/bold blue] - checking for updates...")
        self.console.print()
    
    def show_service_update(
        self,
        service_name: str,
        current_version: str,
        latest_release: Release,
        has_update: bool,
    ):
        """
        Display information about a service update.
        
        Args:
            service_name: Name of the service
            current_version: Current version/tag
            latest_release: Latest release from GitHub
            has_update: Whether an update is available
        """
        if not has_update:
            self.console.print(f"✓ [green]{service_name}[/green]: up to date")
            return
        
        # Show update available
        self.console.print()
        self.console.print(f"⚠  [yellow]{service_name}[/yellow]: [bold]update available[/bold]")
        self.console.print(f"   Current: [dim]{current_version}[/dim]")
        self.console.print(f"   Latest:  [cyan]{latest_release.tag}[/cyan]")
        
        # Show published date
        pub_date = latest_release.get_published_date()
        if pub_date:
            self.console.print(f"   Published: [dim]{pub_date.strftime('%Y-%m-%d')}[/dim]")
        
        # Parse and show release notes
        if latest_release.body:
            parsed = self.parser.parse(latest_release.body)
            self._show_release_notes(parsed)
        
        # Show URL
        self.console.print(f"   [dim][link={latest_release.html_url}]{latest_release.html_url}[/link][/dim]")
    
    def _show_release_notes(self, notes: ParsedNotes):
        """Display parsed release notes."""
        if notes.is_empty():
            return
        
        self.console.print()
        
        # Show breaking changes first (most important)
        if notes.breaking:
            self.console.print("   [bold red]⚠️  Breaking Changes:[/bold red]")
            for item in notes.breaking:
                self.console.print(f"      • {item}")
            self.console.print()
        
        # Show security updates
        if notes.security:
            self.console.print("   [bold yellow]🔒 Security:[/bold yellow]")
            for item in notes.security:
                self.console.print(f"      • {item}")
            self.console.print()
        
        # Show features
        if notes.features:
            self.console.print("   [bold green]✨ Features:[/bold green]")
            for item in notes.features:
                self.console.print(f"      • {item}")
            self.console.print()
        
        # Show fixes
        if notes.fixes:
            self.console.print("   [bold blue]🐛 Fixes:[/bold blue]")
            for item in notes.fixes:
                self.console.print(f"      • {item}")
            self.console.print()
        
        # Show dependencies (collapsed)
        if notes.dependencies:
            self.console.print(f"   [dim]📦 Dependencies: {len(notes.dependencies)} updates[/dim]")
    
    def show_summary(self, total_services: int, services_with_updates: int):
        """
        Display summary of check results.
        
        Args:
            total_services: Total number of services checked
            services_with_updates: Number of services with updates available
        """
        self.console.print()
        self.console.print("─" * 60)
        
        if services_with_updates == 0:
            self.console.print("[green]✓ All services are up to date![/green]")
        else:
            self.console.print(
                f"Found [yellow]{services_with_updates}[/yellow] "
                f"update{'s' if services_with_updates != 1 else ''} available"
            )
            self.console.print()
            self.console.print("[dim]To update manually:[/dim]")
            self.console.print("  cd <service-directory>")
            self.console.print("  docker compose pull")
            self.console.print("  docker compose up -d")
        
        self.console.print()
    
    def show_error(self, message: str):
        """Display an error message."""
        self.console.print(f"[red]✗ Error:[/red] {message}")
    
    def show_warning(self, message: str):
        """Display a warning message."""
        self.console.print(f"[yellow]⚠  Warning:[/yellow] {message}")
    
    def show_no_services_found(self):
        """Display message when no services are found."""
        self.console.print()
        self.console.print("[yellow]⚠  No Docker Compose services found[/yellow]")
        self.console.print()
        self.console.print("Make sure you're in a directory with compose.yml files,")
        self.console.print("or specify --compose-dir to point to your compose files.")
        self.console.print()
