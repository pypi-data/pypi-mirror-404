from rich.console import Console
from rich.text import Text
from rich.align import Align
from rich.padding import Padding
import os
import readchar

_console = Console()

def _style(
    text,
    color = "#ffffff",
    bold = False,
    italic = False,
    underline = False,
    strike = False,
    reverse = False,
    alignment = "left",
    padding = 0,
    top_padding = None,
    right_padding = None,
    bottom_padding = None,
    left_padding = None,
    plain_text = False
):
    def apply_text_styles(text):
        message = Text()
        if isinstance(text, str):
            style_parts = [color]
            if bold: style_parts.append("bold")
            if italic: style_parts.append("italic")
            if underline: style_parts.append("underline")
            if strike: style_parts.append("strike")
            if reverse: style_parts.append("reverse")
            style = " ".join(style_parts)
            current_segment = ""
            for character in text:
                if character == " ":
                    if current_segment:
                        message.append(current_segment, style = style)
                        current_segment = ""
                    message.append(" ")
                else: current_segment += character
            if current_segment: message.append(current_segment, style=style)
            return message
        elif isinstance(text, list):
            for segment, segment_style in text:
                style_parts = [segment_style.get("color", color)]
                if segment_style.get("bold"): style_parts.append("bold")
                if segment_style.get("italic"): style_parts.append("italic")
                if segment_style.get("underline"): style_parts.append("underline")
                if segment_style.get("strike"): style_parts.append("strike")
                if segment_style.get("reverse"): style_parts.append("reverse")
                style = " ".join(style_parts)
                current_segment = ""
                for character in segment:
                    if character == " ":
                        if current_segment:
                            message.append(current_segment, style = style)
                            current_segment = ""
                        message.append(" ")
                    else: current_segment += character
                if current_segment: message.append(current_segment, style = style)
            return message
    
    def apply_alignment(message): return Align(message, alignment)
    
    def apply_padding(message):
        final_padding = (
            top_padding if top_padding is not None else padding,
            (right_padding if right_padding is not None else padding) * 2,
            bottom_padding if bottom_padding is not None else padding,
            (left_padding if left_padding is not None else padding) * 2
        )
        return Padding(message, final_padding)
    
    message = apply_text_styles(text)
    if plain_text: return message
    message = apply_alignment(message)
    message = apply_padding(message)
    return message

def print(
    object = "",
    color = "#ffffff",
    bold = False,
    italic = False,
    underline = False,
    strike = False,
    reverse = False,
    alignment = "left",
    padding = 0,
    top_padding = None,
    right_padding = None,
    bottom_padding = None,
    left_padding = None,
    plain_text = False,
    *args,
    **kwargs
):
    if isinstance(object, (str, list)): object = _style(
        text = object,
        color = color,
        bold = bold,
        italic = italic,
        underline = underline,
        strike = strike,
        reverse = reverse,
        alignment = alignment,
        padding = padding,
        top_padding = top_padding,
        right_padding = right_padding,
        bottom_padding = bottom_padding,
        left_padding = left_padding,
        plain_text = plain_text
    )
    _console.print(object, *args, **kwargs)

def input(
    text = "",
    color = "#ffffff",
    bold = False,
    italic = False,
    underline = False,
    strike = False,
    reverse = False
):
    return _console.input(_style(
        text = text,
        color = color,
        bold = bold,
        italic = italic,
        underline = underline,
        strike = strike,
        reverse = reverse,
        plain_text = True
    )).strip()

def clear_console(): os.system("cls" if os.name == "nt" else "clear")

def wait_for_key(
    text = "\nPulse cualquier tecla para continuar...",
    color = "#ffffff",
    bold = False,
    italic = False,
    underline = False,
    strike = False,
    reverse = False,
    alignment = "left",
    padding = 0,
    top_padding = None,
    right_padding = None,
    bottom_padding = None,
    left_padding = None,
    plain_text = False
):
    print(
        object = text,
        color = color,
        bold = bold,
        italic = italic,
        underline = underline,
        strike = strike,
        reverse = reverse,
        alignment = alignment,
        padding = padding,
        top_padding = top_padding,
        right_padding = right_padding,
        bottom_padding = bottom_padding,
        left_padding = left_padding,
        plain_text = plain_text
    )
    readchar.readkey()