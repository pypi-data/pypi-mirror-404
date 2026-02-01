"""twmux CLI entry point."""

import json as json_lib
from typing import Annotated

import typer
from rich import print as rprint

from twmux import __version__

app = typer.Typer(
    help="Race-condition-safe tmux wrapper for coding agents",
    no_args_is_help=True,
)

# Global options
json_output: bool = False
socket_name: str | None = None


@app.callback()
def main(
    json: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("-v", "--verbose", help="Verbose output")] = False,
    socket: Annotated[str | None, typer.Option("-L", "--socket", help="Socket name")] = None,
) -> None:
    """Configure global options."""
    global json_output, socket_name
    json_output = json
    socket_name = socket


def get_pane(target: str):
    """Resolve target to libtmux Pane object."""
    from libtmux import Server

    server = Server(socket_name=socket_name)

    # Handle pane ID directly (e.g., %5)
    if target.startswith("%"):
        for session in server.sessions:
            for window in session.windows:
                for pane in window.panes:
                    if pane.pane_id == target:
                        return pane
        raise typer.BadParameter(f"Pane not found: {target}")

    # Handle session:window.pane format
    parts = target.split(":")
    session_name = parts[0] if parts[0] else None

    # Find session
    if session_name:
        sessions = [s for s in server.sessions if s.session_name == session_name]
        if not sessions:
            raise typer.BadParameter(f"Session not found: {session_name}")
        session = sessions[0]
    else:
        session = server.sessions[0] if server.sessions else None
        if not session:
            raise typer.BadParameter("No tmux sessions found")

    # Parse window.pane
    if len(parts) > 1 and parts[1]:
        window_pane = parts[1].split(".")
        window_idx = int(window_pane[0]) if window_pane[0] else 0
        pane_idx = int(window_pane[1]) if len(window_pane) > 1 else 0

        window = session.windows[window_idx]
        return window.panes[pane_idx]

    return session.active_window.active_pane


def output_result(data: dict) -> None:
    """Output result in appropriate format."""
    if json_output:
        print(json_lib.dumps(data))
    else:
        for key, value in data.items():
            rprint(f"{key}: {value}")


@app.command()
def version() -> None:
    """Show version."""
    if json_output:
        print(json_lib.dumps({"version": __version__}))
    else:
        print(f"twmux {__version__}")


@app.command()
def send(
    text: Annotated[str, typer.Argument(help="Text to send")],
    target: Annotated[str, typer.Option("-t", "--target", help="Target pane")] = "",
    no_enter: Annotated[bool, typer.Option("--no-enter", help="Don't send Enter")] = False,
    delay: Annotated[float, typer.Option("--delay", help="Enter delay (seconds)")] = 0.05,
) -> None:
    """Send text to pane (race-condition safe)."""
    from twmux.lib.safe_input import send_safe

    pane = get_pane(target)
    result = send_safe(pane, text, enter=not no_enter, enter_delay=delay)

    output_result({"success": result.success, "attempts": result.attempts})

    if not result.success:
        raise typer.Exit(1)


@app.command(name="exec")
def exec_cmd(
    command: Annotated[str, typer.Argument(help="Command to execute")],
    target: Annotated[str, typer.Option("-t", "--target", help="Target pane")] = "",
    timeout: Annotated[float, typer.Option("--timeout", help="Timeout (seconds)")] = 30.0,
) -> None:
    """Execute command and capture output + exit code."""
    from twmux.lib.execution import execute

    pane = get_pane(target)
    result = execute(pane, command, timeout=timeout)

    output_result(
        {
            "output": result.output,
            "exit_code": result.exit_code,
            "timed_out": result.timed_out,
        }
    )


@app.command()
def capture(
    target: Annotated[str, typer.Option("-t", "--target", help="Target pane")] = "",
    lines: Annotated[int | None, typer.Option("-n", "--lines", help="Number of lines")] = None,
) -> None:
    """Capture pane content."""
    pane = get_pane(target)

    if lines:
        content = pane.capture_pane(start=-lines)
    else:
        content = pane.capture_pane()

    if json_output:
        print(json_lib.dumps({"content": content}))
    else:
        print("\n".join(content))


@app.command(name="wait-idle")
def wait_idle(
    target: Annotated[str, typer.Option("-t", "--target", help="Target pane")] = "",
    timeout: Annotated[float, typer.Option("--timeout", help="Timeout (seconds)")] = 30.0,
    interval: Annotated[float, typer.Option("--interval", help="Poll interval")] = 0.2,
) -> None:
    """Wait for pane output to stabilize."""
    from twmux.lib.safe_input import wait_for_idle

    pane = get_pane(target)
    result = wait_for_idle(pane, poll_interval=interval, timeout=timeout)

    output_result({"idle": result.idle, "elapsed": round(result.elapsed, 3)})

    if not result.idle:
        raise typer.Exit(1)


@app.command()
def interrupt(
    target: Annotated[str, typer.Option("-t", "--target", help="Target pane")] = "",
) -> None:
    """Send Ctrl+C to pane."""
    pane = get_pane(target)
    pane.send_keys("C-c", enter=False)

    output_result({"interrupted": True})


@app.command()
def launch(
    target: Annotated[str, typer.Option("-t", "--target", help="Target pane")] = "",
    command: Annotated[str | None, typer.Option("-c", "--command", help="Command to run")] = None,
    vertical: Annotated[bool, typer.Option("-v", "--vertical", help="Split vertically")] = False,
) -> None:
    """Create new pane (split current window)."""
    from libtmux.constants import PaneDirection

    pane = get_pane(target)

    direction = PaneDirection.Right if vertical else PaneDirection.Below
    new_pane = pane.split(direction=direction)

    if command:
        new_pane.send_keys(command, enter=True)

    output_result({"pane_id": new_pane.pane_id})


@app.command()
def kill(
    target: Annotated[str, typer.Option("-t", "--target", help="Target pane")] = "",
) -> None:
    """Kill pane."""
    pane = get_pane(target)
    pane.kill()

    output_result({"killed": True})


@app.command()
def escape(
    target: Annotated[str, typer.Option("-t", "--target", help="Target pane")] = "",
) -> None:
    """Send Escape key to pane."""
    pane = get_pane(target)
    pane.send_keys("Escape", enter=False)

    output_result({"escaped": True})


@app.command()
def status() -> None:
    """Show tmux state."""
    from libtmux import Server

    server = Server(socket_name=socket_name)

    sessions_data = []
    for session in server.sessions:
        windows_data = []
        for window in session.windows:
            panes_data = [{"pane_id": p.pane_id, "pane_index": p.pane_index} for p in window.panes]
            windows_data.append(
                {
                    "window_id": window.window_id,
                    "window_index": window.window_index,
                    "window_name": window.window_name,
                    "panes": panes_data,
                }
            )
        sessions_data.append(
            {
                "session_id": session.session_id,
                "session_name": session.session_name,
                "windows": windows_data,
            }
        )

    if json_output:
        print(json_lib.dumps({"sessions": sessions_data}, indent=2))
    else:
        for s in sessions_data:
            rprint(f"[bold]{s['session_name']}[/bold] ({s['session_id']})")
            for w in s["windows"]:
                rprint(f"  {w['window_index']}: {w['window_name']} ({w['window_id']})")
                for p in w["panes"]:
                    rprint(f"    .{p['pane_index']}: {p['pane_id']}")


if __name__ == "__main__":
    app()
