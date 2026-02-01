import signal

import typer
from typing import Optional
from rich import print as rprint

from .repl import REPLSession


DEFAULT_MANIFEST_URL = "https://m87-md-prod-assets.s3.us-west-2.amazonaws.com/station/mds2/production_manifest.json"


app = typer.Typer(
    name="moondream-station",
    help="🌙 Model hosting and management CLI",
    rich_markup_mode="rich",
    add_completion=False,
)


@app.command()
def interactive(
    manifest: Optional[str] = typer.Option(
        DEFAULT_MANIFEST_URL, "--manifest", "-m", help="Manifest URL or local path"
    )
):
    """Start interactive REPL mode (default)"""
    session = REPLSession(manifest_source=manifest)
    session.start()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
    manifest: Optional[str] = typer.Option(
        DEFAULT_MANIFEST_URL, "--manifest", "-m", help="Manifest URL or local path"
    ),
    serve: bool = typer.Option(False, "--serve", help="Start server without entering REPL"),
    model: Optional[str] = typer.Option(None, "--model", help="Model to serve (used with --serve)"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Port to serve on (used with --serve)"),
):
    """🌙 Model hosting and management CLI"""
    if version:
        from . import __version__

        rprint(f"moondream-station version {__version__}")
        raise typer.Exit()

    if ctx.invoked_subcommand is not None:
        return

    if serve:
        _run_serve(manifest, model, port)
    else:
        session = REPLSession(manifest_source=manifest)
        session.start()


def _run_serve(manifest: str, model: Optional[str], port: Optional[int]):
    """Start the server directly without the REPL."""
    session = REPLSession(manifest_source=manifest)
    session.load_and_prepare(model_name=model)

    active_model = session.models.get_active_model()
    if not active_model:
        rprint("[red]Error: No model available to serve.[/red]")
        raise typer.Exit(1)

    serve_port = port or session.config.get("service_port", 2020)
    model_name = active_model.name

    session.service.start(model_name, serve_port)

    if not session.service.is_running():
        rprint("[red]Error: Failed to start service.[/red]")
        raise typer.Exit(1)

    rprint(f"[bold green]Server running[/bold green]")
    rprint(f"  Model:    {model_name}")
    rprint(f"  Endpoint: http://0.0.0.0:{serve_port}/v1")
    rprint(f"  Press Ctrl+C to stop.")

    try:
        signal.pause()
    except AttributeError:
        # signal.pause() not available on Windows
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        rprint("\n[bold]Shutting down...[/bold]")
        session.service.stop()
        rprint("[green]Server stopped.[/green]")


if __name__ == "__main__":
    app()
