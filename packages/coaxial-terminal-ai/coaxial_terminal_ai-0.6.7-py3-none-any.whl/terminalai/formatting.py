"""Formatting and display utilities for TerminalAI."""
import re
import argparse
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from terminalai.color_utils import colorize_ai
from terminalai.command_extraction import is_likely_command
import os
import sys

def print_ai_answer_with_rich(ai_response, to_stderr=False):
    """Print the AI response with clean, minimal formatting."""
    console = Console(file=sys.stderr if to_stderr else None, force_terminal=True if to_stderr else False)
    home = os.path.expanduser("~")

    def home_replace(text):
        return re.sub(rf"{re.escape(home)}", "~", text)

    code_block_pattern = re.compile(r'```(bash|sh)?\n?([\s\S]*?)```')
    last_end = 0

    # If there are no code blocks, just print the text nicely
    if not code_block_pattern.search(ai_response):
        if ai_response.strip():
            console.print(f"\n[cyan]{home_replace(ai_response.strip())}[/cyan]\n")
        return

    for match in code_block_pattern.finditer(ai_response):
        # Print text before code block
        before = ai_response[last_end:match.start()]
        if before.strip():
            console.print(f"\n[cyan]{home_replace(before.strip())}[/cyan]")

        # Print command in a nice panel
        code = match.group(2)
        for line in code.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            if is_likely_command(stripped):
                console.print(Panel(Syntax(home_replace(stripped), "bash", theme="monokai", line_numbers=False),
                                   title="Command", border_style="yellow", expand=False))
        
        last_end = match.end()

    # Print text after last code block
    after = ai_response[last_end:]
    if after.strip():
        console.print(f"\n[cyan]{home_replace(after.strip())}[/cyan]\n")

class ColoredHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom argparse formatter with colored output."""
    def __init__(self, prog):
        super().__init__(prog, max_help_position=42)

    def _format_action(self, action):
        # Format the help with color codes
        result = super()._format_action(action)
        result = result.replace('usage:', '\033[1;36musage:\033[0m')
        result = result.replace('positional arguments:', '\033[1;33mpositional arguments:\033[0m')
        result = result.replace('options:', '\033[1;33moptions:\033[0m')

        # Highlight option strings (e.g., -h, --help)
        for opt_str in action.option_strings:
            result = result.replace(opt_str, f'\033[1;32m{opt_str}\033[0m')

        return result

class ColoredDescriptionFormatter(ColoredHelpFormatter):
    """Help formatter with colored description."""
    def __init__(self, prog):
        super().__init__(prog)
        self._prog_prefix = prog

    def format_help(self):
        help_text = super().format_help()

        # Description color
        if self._prog_prefix:
            desc_start = help_text.find(self._prog_prefix)
            if desc_start > 0:
                desc_text = help_text[desc_start:]
                color_desc = f'\033[1;36m{desc_text}\033[0m'
                help_text = help_text[:desc_start] + color_desc

        return help_text