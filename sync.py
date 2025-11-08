#!/usr/bin/env python3
"""
sync — terminal nano-like editor with syntax highlighting and EOL format selection
Usage: sync [filename]
"""

import sys
import os
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit
from prompt_toolkit.widgets import TextArea, Label
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.shortcuts import input_dialog, message_dialog
from prompt_toolkit.styles import Style
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

# Supported languages (subset of top 30)
SUPPORTED_LANGS = [
    "python", "javascript", "typescript", "html", "css", "bash", "c", "cpp", "rust",
    "java", "go", "ruby", "php", "csharp", "swift", "kotlin", "scala", "perl", "lua",
    "haskell", "elixir", "r", "dart", "sql", "fortran", "erlang"
]

# Default style
style = Style.from_dict({
    "status": "reverse",
    "key": "bold underline",
})

# Determine file to open
filename = sys.argv[1] if len(sys.argv) > 1 else None
text = ""
if filename and os.path.exists(filename):
    with open(filename, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

# Detect language by extension
def detect_lang(fname):
    if not fname:
        return "python"
    ext = os.path.splitext(fname)[1].lower().lstrip(".")
    return {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "html": "html",
        "css": "css",
        "c": "c",
        "cpp": "cpp",
        "cc": "cpp",
        "rs": "rust",
        "java": "java",
        "go": "go",
        "sh": "bash",
    }.get(ext, "python")

def lexer_for(lang):
    try:
        return PygmentsLexer(get_lexer_by_name(lang))
    except ClassNotFound:
        return None

current_lang = detect_lang(filename)
editor = TextArea(text=text, scrollbar=True, line_numbers=True, lexer=lexer_for(current_lang), focus_on_click=True)

# --- End-of-line formats ---
EOL_FORMATS = {
    "unix": "\n",
    "dos": "\r\n",
    "mac": "\r",
}
current_eol = "unix"

# --- Status bar ---
def status_text():
    name = filename if filename else "[No Name]"
    dirty = "*" if editor.buffer.document.is_dirty else ""
    return f" sync | {name}{dirty} | {current_lang} | EOL: {current_eol.upper()} | Ctrl+O Save | Ctrl+X Exit | Alt+L Lang "

status_bar = Label(lambda: status_text(), style="class:status")

# --- Key bindings ---
kb = KeyBindings()

@kb.add("c-o")
def _(event):
    """Save file"""
    global filename, current_eol
    if not filename:
        fname = input_dialog(title="Save As", text="Enter filename:").run()
        if not fname:
            return
        filename = fname

    eol_choice = input_dialog(
        title="Select Line Ending",
        text="Choose format: unix (LF), dos (CRLF), mac (CR)\nEnter: unix/dos/mac"
    ).run()

    if eol_choice and eol_choice.lower() in EOL_FORMATS:
        current_eol = eol_choice.lower()

    try:
        content = editor.text.replace("\n", EOL_FORMATS[current_eol])
        with open(filename, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        message_dialog(title="Saved", text=f"File saved as {filename} ({current_eol.upper()})").run()
    except Exception as e:
        message_dialog(title="Error", text=str(e)).run()

@kb.add("c-x")
def _(event):
    """Exit editor"""
    if editor.buffer.document.is_dirty:
        ans = input_dialog(title="Exit", text="Unsaved changes. Save before exit? (y/n)").run()
        if ans and ans.lower() == "y":
            kb.get_bindings_for_keys(("c-o",))[0].handler(event)
    event.app.exit()

@kb.add("escape", "l")
def _(event):
    """Change syntax highlighting language"""
    choice = input_dialog(title="Language", text="Enter language (e.g. python, html, c++):").run()
    if not choice:
        return
    choice = choice.lower()
    if choice in SUPPORTED_LANGS:
        editor.lexer = lexer_for(choice)
        global current_lang
        current_lang = choice
    else:
	message_dialog(title="Error", text="Unknown language").run()

# Layout
root = HSplit([editor, status_bar])
layout = Layout(root)

# App
app = Application(
    layout=layout,
    key_bindings=kb,
    full_screen=True,
    mouse_support=True,
    style=style,
)

def main():
    app.run()

if name == "__main__":
    main()
