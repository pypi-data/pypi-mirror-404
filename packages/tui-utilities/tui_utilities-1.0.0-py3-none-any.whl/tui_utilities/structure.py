from .console import print, input
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
    *options_list,
    message,
    selection_text = "Su elección: ",
    error = "La opción ingresada no es válida, intente nuevamente"
):
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

def separator(length = 100): print("/" + "-" * length + "/", bold = True)

def error_message(message, error):
    print(f"{message}\n", color = "#ff0000", bold = True)
    separator()
    print(f"Error: {error}", bold = True)
    separator()
    print("Detalles:\n", bold = True)
    print(traceback.format_exc(), color = "#00bfff")
    separator()