import json
import typer
from rich.console import Console
from pypipackagestats import get_package_stats, clear_cache, get_cache_info
from pypipackagestats.core.exceptions import PackageNotFoundError, APIError, PyPIStatsError
from pypipackagestats.output.formatters import format_rich, print_project_banner
from pypipackagestats.core.constants import DEFAULT_CACHE_TTL

app = typer.Typer()
console = Console()

@app.command()
def package(
    name: str = typer.Argument(..., help="Package name"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Disable cache"),
    cache_ttl: int = typer.Option(DEFAULT_CACHE_TTL, "--cache-ttl", help="Cache TTL in seconds"),
):
    """Get package statistics."""
    try:
        stats = get_package_stats(
            name, 
            no_cache=no_cache, 
            cache_ttl=cache_ttl
        )
        
        if json_output:
            console.print(json.dumps(stats.to_dict(), indent=2))
        else:
            format_rich(stats)
            
    except PackageNotFoundError as e:
        console.print(f"[red]Package '{e.package_name}' not found on PyPI[/red]")
        raise typer.Exit(1)
    except APIError as e:
        console.print(f"[red]API Error: {e}[/red]")
        raise typer.Exit(1)
    except PyPIStatsError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

@app.command("cache-clear")
def cache_clear_cmd():
    """Clear cache."""
    clear_cache()
    console.print("[green]✓ Cache cleared[/green]")

@app.command("cache-info")
def cache_info_cmd():
    """Show cache info."""
    info = get_cache_info()
    console.print(f"[cyan]Entries:[/cyan] {info['size']}")
    console.print(f"[cyan]Directory:[/cyan] {info['cache_dir']}")

def main():
    print_project_banner()
    app()

if __name__ == "__main__":
    main()
