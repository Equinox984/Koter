"""TUI modo interactivo para Koter (vim mode)."""

import curses
import shlex
from typing import Optional

from .commands import COMMANDS, dispatch_command
from .storage import list_notes, get_note
from .config import load_config


class TUI:
    """Interfaz de texto interactiva."""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.notes = []
        self.selected = 0
        self.scroll_offset = 0
        self.mode = "normal"  # normal, command
        self.command_buffer = ""
        self.message = ""
        self.running = True
        
        # Configurar curses
        curses.curs_set(0)  # Ocultar cursor
        self.stdscr.keypad(True)
        self.stdscr.clear()
        
        # Colores mono por defecto
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_WHITE, -1)  # normal
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)  # selected
        curses.init_pair(3, curses.COLOR_YELLOW, -1)  # accent
        curses.init_pair(4, curses.COLOR_RED, -1)  # error
        
    def refresh_notes(self):
        """Recarga la lista de notas."""
        self.notes = list_notes()
    
    def draw(self):
        """Dibuja la interfaz."""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        # Título
        title = " KOTER - Notas "
        self.stdscr.attron(curses.A_BOLD)
        try:
            self.stdscr.addstr(0, 0, title[:width-1])
        except curses.error:
            pass
        self.stdscr.attroff(curses.A_BOLD)
        
        # Línea separadora
        try:
            self.stdscr.addstr(1, 0, "─" * (width - 1))
        except curses.error:
            pass
        
        # Lista de notas
        start_row = 2
        visible_rows = height - 4  # Reservar espacio para mensaje y comando
        
        for i, note in enumerate(self.notes[self.scroll_offset:self.scroll_offset + visible_rows]):
            row = start_row + i
            if row >= height - 2:
                break
            
            pin = "★ " if note.pinned else "  "
            line = f"{pin}{note.title}"
            
            if i + self.scroll_offset == self.selected:
                self.stdscr.attron(curses.A_REVERSE)
                try:
                    self.stdscr.addstr(row, 0, line[:width-1].ljust(width-1))
                except curses.error:
                    pass
                self.stdscr.attroff(curses.A_REVERSE)
            else:
                try:
                    self.stdscr.addstr(row, 0, line[:width-1])
                except curses.error:
                    pass
        
        # Mensaje de estado
        if self.message:
            try:
                self.stdscr.addstr(height - 2, 0, self.message[:width-1], curses.color_pair(4))
            except curses.error:
                pass
        
        # Línea de comandos
        if self.mode == "command":
            cmd_line = f":{self.command_buffer}"
            try:
                self.stdscr.addstr(height - 1, 0, cmd_line[:width-1])
                self.stdscr.move(height - 1, len(cmd_line))
            except curses.error:
                pass
        
        self.stdscr.refresh()
    
    def execute_command(self, cmd_str: str):
        """Ejecuta un comando desde la línea de comandos."""
        if not cmd_str.strip():
            return
        
        # Comandos especiales del TUI
        if cmd_str == "q":
            self.running = False
            return
        
        if cmd_str == "h" or cmd_str == "?":
            self.message = ":q salir, :h ayuda, j/k navegar, Enter editar"
            return
        
        # Tokenizar con shlex
        try:
            tokens = shlex.split(cmd_str)
        except ValueError as e:
            self.message = f"Error: {e}"
            return
        
        if not tokens:
            return
        
        cmd_name = tokens[0]
        
        # Parsear argumentos
        args = {}
        positional = []
        
        cmd_def = COMMANDS.get(cmd_name)
        if cmd_def and cmd_def.args:
            expected = cmd_def.args
            pos_idx = 0
            i = 1
            while i < len(tokens):
                tok = tokens[i]
                if tok.startswith("--"):
                    key = tok[2:]
                    if i + 1 < len(tokens) and not tokens[i + 1].startswith("--"):
                        args[key] = tokens[i + 1]
                        i += 2
                    else:
                        args[key] = True
                        i += 1
                else:
                    positional.append(tok)
                    i += 1
            
            # Asignar posicionales
            if expected:
                for idx, arg_name in enumerate(expected):
                    if not arg_name.startswith("--"):
                        if idx < len(positional):
                            args[arg_name] = positional[idx]
        
        # Ejecutar
        result = dispatch_command(cmd_name, args)
        
        if result:
            if result.kind.value == "message":
                self.message = result.message
            elif result.kind.value == "error":
                self.message = f"Error: {result.message}"
            elif result.kind.value == "notes":
                self.message = f"{len(result.data or [])} notas"
            elif result.kind.value == "text":
                self.message = result.data[:50] if result.data else ""
        
        # Recargar lista si es necesario
        self.refresh_notes()
    
    def handle_input(self, key):
        """Maneja entrada de teclado."""
        if self.mode == "command":
            if key == 27:  # ESC
                self.mode = "normal"
                self.command_buffer = ""
            elif key in (curses.KEY_ENTER, 10, 13):
                self.execute_command(self.command_buffer)
                self.mode = "normal"
                self.command_buffer = ""
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                self.command_buffer = self.command_buffer[:-1]
            elif 32 <= key <= 126:
                self.command_buffer += chr(key)
            return
        
        # Modo normal
        if key == ord('q'):
            self.running = False
        elif key == ord(':'):
            self.mode = "command"
            self.command_buffer = ""
        elif key == ord('j') or key == curses.KEY_DOWN:
            if self.selected < len(self.notes) - 1:
                self.selected += 1
                # Auto-scroll
                if self.selected >= self.scroll_offset + self.stdscr.getmaxyx() - 4:
                    self.scroll_offset = self.selected - (self.stdscr.getmaxyx() - 5)
        elif key == ord('k') or key == curses.KEY_UP:
            if self.selected > 0:
                self.selected -= 1
                if self.selected < self.scroll_offset:
                    self.scroll_offset = self.selected
        elif key == ord('g'):
            self.selected = 0
            self.scroll_offset = 0
        elif key == ord('G'):
            self.selected = len(self.notes) - 1
            self.scroll_offset = max(0, len(self.notes) - (self.stdscr.getmaxyx() - 4))
        elif key == ord('p'):
            # Pin/unpin (para Fase 1)
            if self.notes:
                self.message = "Comando pin no implementado aún"
        elif key == ord('d'):
            # Delete (para Fase 2)
            if self.notes:
                self.message = "Comando rm no implementado aún"
        elif key in (curses.KEY_ENTER, 10, 13):
            # Editar nota seleccionada
            if self.notes:
                note = self.notes[self.selected]
                from .commands import open_editor
                open_editor(note.path)
                self.refresh_notes()
                self.message = f"Nota '{note.title}' editada"
        elif key == ord('/'):
            # Búsqueda (para Fase 2)
            self.mode = "command"
            self.command_buffer = "search "
    
    def run(self):
        """Bucle principal del TUI."""
        self.refresh_notes()
        
        while self.running:
            self.draw()
            try:
                key = self.stdscr.getch()
                self.handle_input(key)
            except KeyboardInterrupt:
                break
        
        self.message = "Saliendo..."


def run_tui():
    """Función principal para iniciar el TUI."""
    def wrapper(stdscr):
        tui = TUI(stdscr)
        tui.run()
    
    curses.wrapper(wrapper)
