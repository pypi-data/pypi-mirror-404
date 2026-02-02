from .console import print, input, clear_console, wait_for_key
from .structure import error_message
from importlib.resources import files
import requests
import re
from datetime import datetime

TLDS_LIST = files("tui_utilities.tlds").joinpath("tlds.txt")

_email_pattern = None

def _get_tlds():
    url = "https://data.iana.org/TLD/tlds-alpha-by-domain.txt"
    try:
        response = requests.get(url, timeout = 10)
        response.raise_for_status()
        tlds = [tld.lower() for tld in response.text.splitlines()[1:]]
        if tlds: _export_tlds(tlds)
        return tlds
    except requests.RequestException as error:
        error_message(
            "Error al obtener la lista de TLDs actualizada. Se intentará importar la lista de TLDs guardada localmente, de existir una.",
            error
        )
        wait_for_key()
        return _import_tlds()

def _import_tlds():
    try:
        with TLDS_LIST.open("r", encoding = "utf-8") as saved_tlds: return [tld.strip() for tld in saved_tlds]
    except Exception as error:
        error_message(
            "Error al importar la lista de TLDs guardada localmente. No se podrá verificar la validez de las TLDs en los correos electrónicos, sino tan solo su sintaxis.",
            error
        )
        wait_for_key()
        return []

def _export_tlds(tlds):
    try:
        with TLDS_LIST.open("w", encoding = "utf-8") as saved_tlds: saved_tlds.write("\n".join(tlds))
    except Exception as error:
        error_message("Error al exportar la lista de TLDs.", error)
        wait_for_key()

def _build_email_pattern():
    global _email_pattern
    if _email_pattern is not None: return _email_pattern
    tlds = _get_tlds()
    if tlds: tld_pattern = "|".join(sorted(tlds, key = len, reverse = True))
    else: tld_pattern = r"[a-zA-Z]{2,63}"
    _email_pattern = re.compile(
        r"^(?P<local>[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+"
        r"(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*)@"
        r"(?P<dominio>(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"
        r"(?:" + tld_pattern + r"))$",
        re.IGNORECASE
    )
    return _email_pattern

def check_if_empty(list, message = "La lista está vacía"):
    if not list:
        clear_console()
        print(object = message, color = "#ff0000")
        wait_for_key()
        return True
    return False

def validate_string(
    message = "Ingrese un texto: ",
    error = "El texto no puede estar vacío, intente nuevamente"
):
    while True:
        string = input(text = message, bold = True)
        if string: return string
        print(object = f"\n{error}\n", color = "#ff0000")

def validate_integer(
    message = "Ingrese un número: ",
    blank_error = "El número no puede estar vacío",
    invalid_error = "El número ingresado no es válido, intente nuevamente"
):
    pattern = re.compile(r"^(?:\d{1,3}(?:\.\d{3})*|\d+)$")
    while True:
        integer = input(text = message, bold = True)
        if not integer:
            print(object = f"\n{blank_error}\n", color = "#ff0000")
            continue
        if pattern.match(integer):
            unformatted_integer = integer.replace(".", "")
            return int(unformatted_integer)
        else: print(object = f"\n{invalid_error}\n", color = "#ff0000")

def validate_double(
    message = "Ingrese un número: ",
    blank_error = "El número no puede estar vacío",
    invalid_error = "El número ingresado no es válido, intente nuevamente"
):
    pattern = re.compile(r"^(?:\d{1,3}(?:\.\d{3})*|\d+)(?:,(\d{1,2}))?$")
    while True:
        double = input(text = message, bold = True)
        if not double:
            print(object = f"\n{blank_error}\n", color = "#ff0000")
            continue
        if pattern.match(double):
            unformatted_double = double.replace(".", "").replace(",", ".")
            return float(unformatted_double)
        else: print(object = f"\n{invalid_error}\n", color = "#ff0000")

def validate_date(
    message = "Ingrese una fecha: ",
    blank_error = "La fecha no puede estar vacía",
    invalid_error = "La fecha ingresada no es válida, intente nuevamente"
):
    pattern = re.compile(r"^(0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/(\d{4}|\d{1,2}\.\d{3}) - ([01]\d|2[0-3]):[0-5]\d$")
    while True:
        date_string = input(text = message, bold = True)
        if not date_string:
            print(object = f"\n{blank_error}\n", color = "#ff0000")
            continue
        if pattern.match(date_string):
            date_part, time_part = date_string.split(" - ")
            date_part = date_part.replace(".", "")
            return datetime.strptime(f"{date_part} - {time_part}", "%d/%m/%Y - %H:%M")
        else: print(object = f"\n{invalid_error}\n", color = "#ff0000")

def validate_id(
    message = "Ingrese un número de D.N.I.: ",
    blank_error = "El número de D.N.I. no puede estar vacío",
    invalid_error = "El número de D.N.I. ingresado no es válido, intente nuevamente"
):
    pattern = re.compile(r"^(?:\d{8}|(?:\d{1,2}\.\d{3}\.\d{3}))$")
    while True:
        id = input(text = message, bold = True)
        if not id:
            print(object = f"\n{blank_error}\n", color = "#ff0000")
            continue
        if pattern.match(id): return id
        else: print(object = f"\n{invalid_error}\n", color = "#ff0000")

def validate_cellphone_number(
    message = "Ingrese un número telefónico: ",
    blank_error = "El número telefónico no puede estar vacío",
    invalid_error = "El número telefónico ingresado no es válido, intente nuevamente"
):
    pattern = re.compile(r"^\d{4}\s*-?\s*\d{6}$")
    while True:
        cellphone_number = input(text = message, bold = True)
        if not cellphone_number:
            print(object = f"\n{blank_error}\n", color = "#ff0000")
            continue
        if pattern.match(cellphone_number): return cellphone_number
        else: print(object = f"\n{invalid_error}\n", color = "#ff0000")

def validate_email(
    message = "Ingrese el correo electrónico: ",
    blank_error = "El correo electrónico no puede estar vacío",
    invalid_error = "El correo electrónico ingresado no es válido, intente nuevamente"
):
    pattern = _build_email_pattern()
    while True:
        email = input(text = message, bold = True)
        if not email:
            print(object = f"\n{blank_error}\n", color = "#ff0000")
            continue
        if pattern.match(email): return email
        print(object = f"\n{invalid_error}\n", color = "#ff0000")