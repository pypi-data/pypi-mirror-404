"""Aline Dashboard Header Widget with ASCII Logo."""

from textual.widgets import Static


class AlineHeader(Static):
    """Header widget displaying Aline ASCII logo and version."""

    DEFAULT_CSS = """
    AlineHeader {
        dock: top;
        min-height: 7;
        padding: 1 2;
        color: $text;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._version = self._get_version()

    def _get_version(self) -> str:
        """Get the Aline version."""
        try:
            from importlib.metadata import version

            return version("aline-ai")
        except Exception:
            return "0.4.1"

    def compose(self):
        """No children - we render directly."""
        return []

    def render(self) -> str:
        """Render the header content."""
        # 5-line solid ASCII art for "aline"
        line1 = "  ████╗ ██╗     ██╗███╗   ██╗███████╗"
        line2 = " ██╔══██╗██║     ██║████╗  ██║██╔════╝"
        line3 = " ███████║██║     ██║██╔██╗ ██║█████╗  "
        line4 = " ██╔══██║██║     ██║██║╚██╗██║██╔══╝  "
        line5 = " ██║  ██║███████╗██║██║ ╚████║███████╗"
        info = f"[dim]v{self._version} │ Shared Agent Context[/dim]"
        return f"{line1}\n{line2}\n{line3}\n{line4}\n{line5}  {info}"
