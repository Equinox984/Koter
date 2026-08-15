"""CLI principal para Koter usando argparse."""

import argparse
import sys

from .commands import COMMANDS, dispatch_command, parse_cli_args
from .models import ResultKind
from .render import render_result, render_search_results


def create_parser() -> argparse.ArgumentParser:
    """Crea el parser de argparse desde el registro de comandos."""
    parser = argparse.ArgumentParser(
        prog="koter",
        description="Koter - Offline Markdown note-taking CLI"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")
    
    # Registrar solo comandos principales (no aliases)
    seen = set()
    for name, cmd in sorted(COMMANDS.items()):
        if cmd.name in seen:
            continue
        seen.add(cmd.name)
        
        sub = subparsers.add_parser(cmd.name, help=cmd.help_text, aliases=cmd.aliases)
        
        # Agregar argumentos según definición
        if cmd.args:
            for arg in cmd.args:
                if arg.startswith("--"):
                    # Argumento opcional
                    arg_name = arg[2:]
                    sub.add_argument(f"--{arg_name}", dest=arg_name, nargs='?', 
                                    const=True, default=None)
                else:
                    # Argumento posicional
                    sub.add_argument(arg)
    
    return parser


def main():
    """Punto de entrada principal."""
    # Primero intentar con argparse para --help
    parser = create_parser()
    
    # Filtrar sys.argv para remover opciones de python -m
    # python -m koter list -> sys.argv puede ser ['/workspace/src/koter/__main__.py', 'list']
    cli_args = sys.argv[1:]
    # Remover flags como -m, --module si aparecen
    cli_args = [a for a in cli_args if a not in ('-m', '--module')]
    # Si el primer argumento es el nombre del módulo, saltarlo
    if cli_args and cli_args[0] == 'koter':
        cli_args = cli_args[1:]
    
    # Si no hay argumentos, entrar en modo interactivo (TUI)
    if len(cli_args) == 0:
        from .tui import run_tui
        run_tui()
        return
    
    args = parser.parse_args(cli_args)
    
    # Manejar caso sin subcomando
    if not hasattr(args, 'command') or not getattr(args, 'command', None):
        parser.print_help()
        return
    
    # Ejecutar comando usando el valor ya extraído
    cmd_name = args.command
    cmd_args = vars(args)
    cmd_args.pop('command', None)
    
    # Limpiar valores None y el atributo help si existe
    cmd_args = {k: v for k, v in cmd_args.items() if v is not None and k != 'help'}
    
    # Ejecutar comando
    result = dispatch_command(cmd_name, cmd_args)
    
    # Renderizar salida
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
            print("No hay notas.")
    
    elif result.kind == ResultKind.TEXT:
        print(result.data)
    
    elif result.kind == ResultKind.MESSAGE:
        print(result.message)


if __name__ == "__main__":
    main()
