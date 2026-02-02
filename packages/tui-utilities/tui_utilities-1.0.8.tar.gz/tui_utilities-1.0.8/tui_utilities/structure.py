from .console import print, input, clear_console
import sys
import traceback

def _choose_option(
    options,
    message = "Seleccione una opción:",
    selection_text = "Su elección: ",
    error = "La opción ingresada no es válida, intente nuevamente",
):
    print(f"{message}\n", bold = True)
    for key, option in options.items(): print([(f"{key}:", {"bold": True}), (f" {option}", {})])
    selection = input(f"\n{selection_text}", bold = True).upper()
    while selection not in options:
        print(f"\n{error}\n", color = "#ff0000")
        selection = input(f"\n{selection_text}", bold = True).upper()
    return selection

def menu(
    options_list,
    title,
    title_color = "#ffffff",
    title_bold = True,
    title_italic = False,
    title_underline = False,
    title_strike = False,
    title_reverse = False,
    title_alignment = "center",
    title_padding = 0,
    title_top_padding = None,
    title_right_padding = None,
    title_bottom_padding = None,
    title_left_padding = None,
    separator_length = 100,
    separator_color = "#ffffff",
    separator_aligment = "left",
    separator_padding = 0,
    separator_top_padding = None,
    separator_right_padding = None,
    separator_bottom_padding = None,
    separator_left_padding = None,
    message = "Seleccione una opción:",
    selection_text = "Su elección: ",
    error = "La opción ingresada no es válida, intente nuevamente"
):
    clear_console()
    print(
        object = title,
        color = title_color,
        bold = title_bold,
        italic = title_italic,
        underline = title_underline,
        strike = title_strike,
        reverse = title_reverse,
        alignment = title_alignment,
        padding = title_padding,
        top_padding = title_top_padding,
        right_padding = title_right_padding,
        bottom_padding = title_bottom_padding,
        left_padding = title_left_padding
    )
    separator(
        length = separator_length,
        color = separator_color,
        aligment = separator_aligment,
        padding = separator_padding,
        top_padding = separator_top_padding,
        right_padding = separator_right_padding,
        bottom_padding = separator_bottom_padding,
        left_padding = separator_left_padding
    )
    options = {}
    key = 1
    for option in options_list:
        match option:
            case "Atrás": options["A"] = option
            case "Salir": options["S"] = option
            case _:
                options[str(key)] = option
                key += 1
    return _choose_option(options, message, selection_text, error)

def confirm_exit(
    message = "¿Está seguro de querer salir?",
    selection_text = "Su elección: ",
    error = "La opción ingresada no es válida, intente nuevamente",
    options_text = ["Sí", "No"]
):
    options = {
        "1": options_text[0],
        "2": options_text[1]
    }
    selection = _choose_option(options, f"\n{message}", selection_text, error)
    if selection == "1": sys.exit()

def separator(
    length = 100,
    color = "#ffffff",
    aligment = "left",
    padding = 0,
    top_padding = None,
    right_padding = None,
    bottom_padding = None,
    left_padding = None
):
    print(object = "/" + "-" * length + "/",
        color = color,
        bold = True,
        alignment = aligment,
        padding = padding,
        top_padding = top_padding,
        right_padding = right_padding,
        bottom_padding = bottom_padding,
        left_padding = left_padding
    )

def error_message(
    message,
    error,
    separator_length = 100,
    separator_color = "#ffffff",
    separator_aligment = "left",
    separator_padding = 0,
    separator_top_padding = None,
    separator_right_padding = None,
    separator_bottom_padding = None,
    separator_left_padding = None
):
    print(f"{message}\n", color = "#ff0000", bold = True)
    separator(
        length = separator_length,
        color = separator_color,
        aligment = separator_aligment,
        padding = separator_padding,
        top_padding = separator_top_padding,
        right_padding = separator_right_padding,
        bottom_padding = separator_bottom_padding,
        left_padding = separator_left_padding
    )
    print(f"Error: {error}", bold = True)
    separator(
        length = separator_length,
        color = separator_color,
        aligment = separator_aligment,
        padding = separator_padding,
        top_padding = separator_top_padding,
        right_padding = separator_right_padding,
        bottom_padding = separator_bottom_padding,
        left_padding = separator_left_padding
    )
    print("Detalles:\n", bold = True)
    print(traceback.format_exc(), color = "#00bfff")
    separator(
        length = separator_length,
        color = separator_color,
        aligment = separator_aligment,
        padding = separator_padding,
        top_padding = separator_top_padding,
        right_padding = separator_right_padding,
        bottom_padding = separator_bottom_padding,
        left_padding = separator_left_padding
    )