pq-peek 🦆

A blazing fast, memory-efficient CLI tool to inspect large Parquet files directly in the terminal.
Built with *Polars*, *Typer*, and *Rich*. Managed via *uv*.

## Install (uv)

```bash
uv pip install pq-peek
```

## CLI usage

```bash
pq-peek schema /path/to/file.parquet
pq-peek head /path/to/file.parquet --n 5
pq-peek stats /path/to/file.parquet
```

## Module usage

```bash
python -m pq_peek schema /path/to/file.parquet
```

## Build and publish (uv)

```bash
uv build
uv publish
```

## Publishing notes

CI publishing uses GitHub's Trusted Publisher OIDC. See `PUBLISHING.md` for the full release steps.