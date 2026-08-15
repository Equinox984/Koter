"""Main CLI for Koter using argparse."""

import argparse
import sys

from .commands import COMMANDS, dispatch_command, parse_cli_args
from .models import ResultKind
from .render import render_result, render_search_results


def create_parser() -> argparse.ArgumentParser:
    """Creates the argparse parser from the command registry."""
    parser = argparse.ArgumentParser(
        prog="koter",
        description="Koter - Offline Markdown note-taking CLI"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Register only main commands (not aliases)
    seen = set()
    for name, cmd in sorted(COMMANDS.items()):
        if cmd.name in seen:
            continue
        seen.add(cmd.name)
        
        sub = subparsers.add_parser(cmd.name, help=cmd.help_text, aliases=cmd.aliases)
        
        # Add arguments according to definition
        if cmd.args:
            for arg in cmd.args:
                if arg.startswith("--"):
                    # Optional argument
                    arg_name = arg[2:]
                    sub.add_argument(f"--{arg_name}", dest=arg_name, nargs='?', 
                                    const=True, default=None)
                else:
                    # Positional argument
                    sub.add_argument(arg)
    
    return parser


def main():
    """Main entry point."""
    # First try with argparse for --help
    parser = create_parser()
    
    # Filter sys.argv to remove python -m options
    # python -m koter list -> sys.argv may be ['/workspace/src/koter/__main__.py', 'list']
    cli_args = sys.argv[1:]
    # Remove flags like -m, --module if they appear
    cli_args = [a for a in cli_args if a not in ('-m', '--module')]
    # If first argument is module name, skip it
    if cli_args and cli_args[0] == 'koter':
        cli_args = cli_args[1:]
    
    # If no arguments, enter interactive mode (TUI)
    if len(cli_args) == 0:
        from .tui import run_tui
        run_tui()
        return
    
    args = parser.parse_args(cli_args)
    
    # Handle case without subcommand
    if not hasattr(args, 'command') or not getattr(args, 'command', None):
        parser.print_help()
        return
    
    # Execute command using already extracted value
    cmd_name = args.command
    cmd_args = vars(args)
    cmd_args.pop('command', None)
    
    # Clean None values and help attribute if exists
    cmd_args = {k: v for k, v in cmd_args.items() if v is not None and k != 'help'}
    
    # Execute command
    result = dispatch_command(cmd_name, cmd_args)
    
    # Render output
    if result.kind == ResultKind.ERROR:
        lines = render_result(result)
        for line in lines:
            print(line, file=sys.stderr)
        sys.exit(1)
    
    elif result.kind == ResultKind.NOTES:
        notes = result.data or []
        if notes:
            for note in notes:
                pin = "★ " if note.pinned else "  "
                title = f"{pin}{note.title}"
                
                parts = []
                if note.modified:
                    parts.append(note.modified)
                if note.tags:
                    tags_str = ','.join(note.tags)
                    parts.append(f"[{tags_str}]")
                
                print(title)
                if parts:
                    print(f"  {'  '.join(parts)}")
        else:
            print("No notes.")
    
    elif result.kind == ResultKind.TEXT:
        print(result.data)
    
    elif result.kind == ResultKind.MESSAGE:
        print(result.message)


if __name__ == "__main__":
    main()
