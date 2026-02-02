from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table

from mediathek_py.client import Mediathek
from mediathek_py.exceptions import DownloadError, MediathekError
from mediathek_py.models import SortField, SortOrder
from mediathek_py.series import collect_series

console = Console()


def _sanitize_path_component(name: str) -> str:
    """Sanitize a string for use as a file or directory name."""
    return "".join(c if c.isalnum() or c in " -_" else "_" for c in name)


def _download_progress() -> Progress:
    """Create a Rich progress bar configured for file downloads."""
    return Progress(
        TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.1f}%",
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    )


def _format_duration(seconds: int | None) -> str:
    if seconds is None:
        return "live"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _format_timestamp(ts: int) -> str:
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M")


@click.group()
@click.version_option()
def cli():
    """MediathekViewWeb CLI - search and download German public broadcasting content."""


@cli.command()
@click.argument("query")
@click.option("--sort-by", type=click.Choice(["channel", "timestamp", "duration"]), default=None)
@click.option("--sort-order", type=click.Choice(["asc", "desc"]), default=None)
@click.option("--size", type=int, default=15, show_default=True)
@click.option("--offset", type=int, default=0)
@click.option("--future/--no-future", default=False)
@click.option("--everywhere", is_flag=True, help="Search all fields for unprefixed terms")
def search(query: str, sort_by: str | None, sort_order: str | None, size: int, offset: int, future: bool, everywhere: bool):
    """Search MediathekViewWeb. Supports prefix syntax: !channel #topic +title *description >min <max"""
    try:
        with Mediathek() as m:
            builder = m.build_from_string(query, search_everywhere=everywhere)
            if sort_by:
                builder = builder.sort_by(SortField(sort_by))
            if sort_order:
                builder = builder.sort_order(SortOrder(sort_order))
            builder = builder.size(size).offset(offset)
            if future:
                builder = builder.include_future(True)
            result = builder.execute()

        table = Table(title=f"Search results ({result.query_info.total_results} total)")
        table.add_column("#", style="dim", width=3)
        table.add_column("Channel", style="cyan")
        table.add_column("Topic", style="green")
        table.add_column("Title")
        table.add_column("Duration", justify="right")
        table.add_column("Date", style="dim")

        for i, item in enumerate(result.results, 1):
            table.add_row(
                str(i),
                item.channel,
                item.topic,
                item.title,
                _format_duration(item.duration),
                _format_timestamp(item.timestamp),
            )

        console.print(table)

    except MediathekError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@cli.command()
@click.argument("query")
@click.option("--everywhere", is_flag=True)
def info(query: str, everywhere: bool):
    """Show detailed info for the first search result."""
    try:
        with Mediathek() as m:
            result = m.search_by_string(query, search_everywhere=everywhere)

        if not result.results:
            console.print("[red]Error:[/red] No results found.")
            raise SystemExit(1)

        item = result.results[0]
        lines = [
            f"[bold]Channel:[/bold] {item.channel}",
            f"[bold]Topic:[/bold] {item.topic}",
            f"[bold]Title:[/bold] {item.title}",
            f"[bold]Duration:[/bold] {_format_duration(item.duration)}",
            f"[bold]Date:[/bold] {_format_timestamp(item.timestamp)}",
        ]
        if item.description:
            lines.append(f"[bold]Description:[/bold] {item.description}")
        lines.append(f"[bold]Website:[/bold] {item.url_website}")
        lines.append(f"[bold]Video:[/bold] {item.url_video}")
        if item.url_video_hd:
            lines.append(f"[bold]Video HD:[/bold] {item.url_video_hd}")
        if item.url_video_low:
            lines.append(f"[bold]Video Low:[/bold] {item.url_video_low}")
        if item.url_subtitle:
            lines.append(f"[bold]Subtitle:[/bold] {item.url_subtitle}")

        panel = Panel("\n".join(lines), title=item.title, expand=False)
        console.print(panel)

    except MediathekError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@cli.command()
@click.argument("query")
@click.option("--quality", type=click.Choice(["hd", "medium", "low"]), default="hd", show_default=True)
@click.option("--output", "-o", type=click.Path(), default=None, help="Output file path")
@click.option("--everywhere", is_flag=True)
def download(query: str, quality: str, output: str | None, everywhere: bool):
    """Download a video from search results."""
    try:
        with Mediathek() as m:
            result = m.search_by_string(query, search_everywhere=everywhere)

            if not result.results:
                console.print("[red]Error:[/red] No results found.")
                raise SystemExit(1)

            item = result.results[0]

            url = _select_video_url(item, quality)
            if url is None:
                console.print("[red]Error:[/red] No video URL available for this item.")
                raise SystemExit(1)

            if output is None:
                output = f"{_sanitize_path_component(item.title)}.mp4"

            output_path = Path(output)
            console.print(f"Downloading: [bold]{item.title}[/bold]")
            console.print(f"Quality: {quality} | URL: {url}")

            with _download_progress() as progress:
                task_id = progress.add_task("download", filename=output_path.name, total=None)

                def on_progress(downloaded: int, total: int | None) -> None:
                    if total:
                        progress.update(task_id, total=total, completed=downloaded)
                    else:
                        progress.update(task_id, completed=downloaded)

                m.download(url, output_path, progress_callback=on_progress)

            console.print(f"[green]Saved to:[/green] {output_path}")

    except DownloadError as e:
        console.print(f"[red]Error:[/red] {e.reason}")
        raise SystemExit(1)
    except MediathekError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@cli.command()
@click.argument("query")
@click.option("--season", "-s", type=int, default=None, help="Filter to a specific season")
@click.option("--episode", "-e", type=int, default=None, help="Filter to a specific episode number")
@click.option("--quality", type=click.Choice(["hd", "medium", "low"]), default="hd", show_default=True)
@click.option("--output", "-o", type=click.Path(), default=".", help="Output directory")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def batch(query: str, season: int | None, episode: int | None, quality: str, output: str, yes: bool):
    """Download all episodes of a series.

    QUERY is the show topic to search for. Use #topic prefix or plain text.
    Examples: '#Feuer & Flamme', 'tagesschau'
    """
    try:
        topic = query.removeprefix("#").strip()
        with Mediathek() as m:
            episodes = collect_series(m, topic)

            if not episodes:
                console.print("[red]Error:[/red] No episodes found with parseable season/episode info.")
                raise SystemExit(1)

            if season is not None:
                episodes = [ep for ep in episodes if ep.info.season == season]
                if not episodes:
                    console.print(f"[red]Error:[/red] No episodes found for season {season}.")
                    raise SystemExit(1)

            if episode is not None:
                episodes = [ep for ep in episodes if ep.info.episode == episode]
                if not episodes:
                    if season is not None:
                        console.print(f"[red]Error:[/red] No episode {episode} found in season {season}.")
                    else:
                        console.print(f"[red]Error:[/red] No episode {episode} found.")
                    raise SystemExit(1)

            # Preview table
            seasons_found = sorted(set(ep.info.season for ep in episodes))
            table = Table(title=f"Found {len(episodes)} episodes across {len(seasons_found)} season(s)")
            table.add_column("#", style="dim", width=3)
            table.add_column("Season", style="cyan")
            table.add_column("Episode", style="cyan")
            table.add_column("Title")
            table.add_column("Duration", justify="right")
            table.add_column("Date", style="dim")

            for i, ep in enumerate(episodes, 1):
                table.add_row(
                    str(i),
                    f"S{ep.info.season:02d}",
                    f"E{ep.info.episode:02d}",
                    ep.item.title,
                    _format_duration(ep.item.duration),
                    _format_timestamp(ep.item.timestamp),
                )

            console.print(table)

            if not yes:
                if not click.confirm(f"Download {len(episodes)} episodes?"):
                    return

            output_dir = Path(output) / _sanitize_path_component(episodes[0].item.topic)
            output_dir.mkdir(parents=True, exist_ok=True)

            downloaded_count = 0
            skipped_count = 0
            failures: list[tuple[str, str]] = []

            with _download_progress() as progress:
                for ep in episodes:
                    name = ep.filename()
                    filepath = output_dir / name

                    if filepath.exists():
                        console.print(f"[dim]Skipping (exists): {name}[/dim]")
                        skipped_count += 1
                        continue

                    url = _select_video_url(ep.item, quality)
                    if url is None:
                        failures.append((name, "No video URL available"))
                        continue

                    task_id = progress.add_task("download", filename=name, total=None)

                    def on_progress(downloaded: int, total: int | None, _tid: object = task_id) -> None:
                        if total:
                            progress.update(_tid, total=total, completed=downloaded)
                        else:
                            progress.update(_tid, completed=downloaded)

                    try:
                        m.download(url, filepath, progress_callback=on_progress)
                        downloaded_count += 1
                    except DownloadError as e:
                        progress.update(task_id, visible=False)
                        failures.append((name, e.reason))
                    except MediathekError as e:
                        progress.update(task_id, visible=False)
                        failures.append((name, str(e)))

        console.print()
        if failures:
            fail_table = Table(title="Failed downloads", title_style="red")
            fail_table.add_column("File", style="bold")
            fail_table.add_column("Reason")
            for fname, reason in failures:
                fail_table.add_row(fname, reason)
            console.print(fail_table)
            console.print()

        summary_style = "green" if not failures else "yellow" if downloaded_count else "red"
        console.print(
            f"[{summary_style}]Done:[/{summary_style}] {downloaded_count} downloaded, "
            f"{skipped_count} skipped, {len(failures)} failed"
        )

    except MediathekError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


def _select_video_url(item, quality: str) -> str | None:
    """Select video URL based on quality preference with fallback."""
    quality_map = {
        "hd": [item.url_video_hd, item.url_video, item.url_video_low],
        "medium": [item.url_video, item.url_video_hd, item.url_video_low],
        "low": [item.url_video_low, item.url_video, item.url_video_hd],
    }
    for url in quality_map.get(quality, []):
        if url:
            return url
    return None
