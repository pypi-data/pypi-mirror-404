from pathlib import Path

import polars as pl
import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="A fast CLI tool to inspect Parquet files")
console = Console()

def get_scan(file_path: Path) -> pl.LazyFrame:
    verify_path(file_path)
    return pl.scan_parquet(file_path)

def verify_path(file_path: Path):
    """
    Verifies that the file exists and checks the correct ending 
    """
    if not file_path.exists():
        rprint(f"[bold red]Error:[/bold red] File was not found: '{file_path}'")
        raise typer.Exit(code=1)
    if file_path.suffix != ".parquet":
        rprint("[bold yellow]Warning:[/bold yellow] File does not end with '.parquet'")

@app.command()
def schema(file_path: Path):
    """
    Displays the schema (column names, types) of the parquet file
    Uses Lazy Loading (scan_parquet) to save memory
    """
    try:
        file = get_scan(file_path)
        schema = file.collect_schema()

        table = Table(title=f"Schema: {file_path.name}")
        table.add_column("Column name", style="cyan", no_wrap=True)
        table.add_column("Type", style="magenta")

        for name, dtype in schema.items():
            table.add_row(name, str(dtype))

        console.print(table)
        rprint(f"\n[green]Amount of columns:[/green] {len(schema)}")
    except Exception as failure:
        rprint(f"[bold red]Failure while reading the parquet file:[/bold red] {failure}")
        raise typer.Exit(code=1)

@app.command()
def head(file_path: Path, n: int = typer.Option(5, help="Amount of rows")):
    """
    Displays the first n rows of the parquet file
    """
    try:
        file = get_scan(file_path)
        df = file.limit(n).collect()

        if df.is_empty():
            rprint("[yellow]File is empty.[/yellow]")
            return
        
        table = Table(title=f"Preview {file_path.name} ({n} rows)")

        for column in df.columns:
            table.add_column(column, overflow="fold")

        for row in df.iter_rows():
            str_row = [str(x) for x in row]
            table.add_row(*str_row)
        
        console.print(table)
    except Exception as failure:
        rprint(f"[bold red]Failure while reading the parquet file:[/bold red] {failure}")
        raise typer.Exit(code=1)



@app.command()
def stats(file_path: Path):
    """
    Displays stats of the parquet file (min, max, nulls)
    Uses Polars Query Engine for parallel computation
    """
    try:
        with console.status("[bold green]Calculating stats...[/bold green]"):
            file = get_scan(file_path)

            stats_df = file.describe()

        console.print(stats_df)

    except Exception as failure:
        rprint(f"[bold red]Failure while calculating stats:[/bold red] {failure}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()