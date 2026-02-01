from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich import box
from pypipackagestats.core.metadata import get_project_metadata
from pypipackagestats.core.models import PackageStats
from pypipackagestats.output.utils import normalize_os_name, humanize_number, humanize_date, extract_repo_name
from pypipackagestats.core.constants import DATE_ISO_FORMAT_LENGTH


console = Console()


def format_rich(stats: PackageStats) -> None:
    """Format PackageStats using Rich console."""
    # Package info
    pkg = stats.package_info
    console.print(f"\n[bold cyan]{pkg.name}[/bold cyan]")
    console.print(f"{pkg.description or ''}")
    console.print(f"Version     : {pkg.version or 'Unknown'}")
    upload_time_str = pkg.upload_time[:DATE_ISO_FORMAT_LENGTH] if pkg.upload_time else None
    console.print(f"Upload time : {humanize_date(upload_time_str) if upload_time_str else 'Unknown'}")
    console.print(f"Author      : {pkg.author or 'Unknown'}")
    console.print(f"License     : {pkg.license or 'Unknown'}")
    console.print(f"Home page   : {pkg.home_page or 'Unknown'}")
    console.print(f"PyPI        : {pkg.pypi_url or 'Unknown'}\n")
    
    # Download stats
    table = Table(title="Downloads (excluding mirrors)", box=box.ROUNDED)
    table.add_column("Period", style="cyan")
    table.add_column("Downloads", style="green", justify="right")
    
    table.add_row("Last day", humanize_number(stats.downloads.last_day))
    table.add_row("Last week", humanize_number(stats.downloads.last_week))
    table.add_row("Last month", humanize_number(stats.downloads.last_month))
    table.add_row("Last 180 days", humanize_number(stats.downloads.last_180d))
    
    console.print(table)
    console.print()
    
    # Python versions
    if not stats.python_versions:
        console.print("[yellow]No Python version data available for last 30 days.[/yellow]\n")
    else:
        table = Table(title="Top Python versions (last 30 days)", box=box.ROUNDED)
        table.add_column("Version", style="cyan")
        table.add_column("Share", style="yellow", justify="right")
        table.add_column("Downloads", style="green", justify="right")
        
        for pv in stats.python_versions:
            version = "Unknown" if pv.category == "null" else pv.category
            table.add_row(
                version,
                f"{pv.percentage:.1f}%",
                humanize_number(pv.downloads)
            )
        
        console.print(table)
        console.print()
    
    # Operating systems
    if not stats.operating_systems:
        console.print("[yellow]No OS distribution data available for last 30 days.[/yellow]")
    else:
        table = Table(title="Top operating systems (last 30 days)", box=box.ROUNDED)
        table.add_column("OS", style="cyan")
        table.add_column("Share", style="yellow", justify="right")
        table.add_column("Downloads", style="green", justify="right")
        
        for os_stat in stats.operating_systems:
            table.add_row(
                normalize_os_name(os_stat.category),
                f"{os_stat.percentage:.1f}%",
                humanize_number(os_stat.downloads)
            )
        
        console.print(table)


def print_project_banner():
    banner_text = Text()
    project_metadata = get_project_metadata()
    
    repo_name = extract_repo_name(project_metadata.repository_url)
    
    # Mini Style (2 lines high)
    banner_text.append("\n █▀█ █▄█ █▀█ █   █▀█ █▀█ █▀▀ █▄▀ ▄▀█ █▀▀ █▀▀   █▀▀ ▀█▀ ▄▀█ ▀█▀ █▀", style="bold blue")
    banner_text.append("\n █▀▀  █  █▀▀ █   █▀▀ █▀█ █▄▄ █ █ █▀█ █▄█ ██▄   ▄██  █  █▀█  █  ▄█\n", style="bold blue")
    
    banner_text.append(f"Version : {project_metadata.version}\n", style="bold blue")
    banner_text.append(f"Author  : {project_metadata.author} ({project_metadata.author_url})\n", style="green")
    
    console.print(Panel(banner_text, expand=False, border_style="blue", title=repo_name or "Welcome", title_align="left"))
