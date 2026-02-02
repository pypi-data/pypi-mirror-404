# TUI Utilities

Personal-use console utilities library providing styled terminal interaction, structured menus, robust input validation, formatting helpers, and Spanish-oriented user experience.

/----------------------------------------------------------------------------------------------------/

## Purpose

This library is designed for console-based applications that need:

- Clean TUI

- Structured Spanish-language user interaction

- Robust validation

- Consistent formatting

/----------------------------------------------------------------------------------------------------/

## Dependencies

Standard library modules are used where possible; only external dependencies are listed:

- rich

- readchar

- requests

/----------------------------------------------------------------------------------------------------/

## Features

/----------------------------------------------------------------------------------------------------/

### Console Utilities (console)

Styled terminal interaction built on rich:

- print(): styled print function built on rich, supporting text styles, alignment, padding, and per-segment styling.

- input(): styled input function built on rich, supporting text styles and automatically trimming whitespaces.

- clear_console(): clears the terminal screen (Windows/Linux compatible).

- wait_for_key(): pauses execution until the user presses a key.

/----------------------------------------------------------------------------------------------------/

### Structure Utilities (structure)

Tools for building structures in console applications:

- menu(): creates interactive selection menus with automatic numbering and special options like "Go back" and "Exit".

- confirm_exit(): confirmation dialog that exits the program safely.

- separator(): prints a styled visual separator line.

- error_message(): displays formatted error information including:

    - Custom message

    - Exception details

    - Full traceback

/----------------------------------------------------------------------------------------------------/

### Input Validation (validation)

Interactive validation utilities for user input.

- check_if_empty(): checks if a list is empty and displays an error screen.

- validate_string(): ensures non-empty string input.

- validate_integer(): validates integers (uses Continental European numeric format).

- validate_double(): validates decimal numbers (uses Continental European numeric format).

- validate_date(): validates date and time input (uses Day–Month–Year date format with 24-hour time).

- validate_id(): validates Argentinian national ID numbers.

- validate_cellphone_number(): validates cellphone numbers (uses Argentinian format).

- validate_email(): validates e-mail addresses using an official TLDs list (from IANA's website) or syntax fallback (in case of not having an internet connection or a locally imported list of TLDs).

/----------------------------------------------------------------------------------------------------/

### Formatting Helpers (format)

Utilities for applying consistent formatting:

- decimal_format(): applies Continental European numeric formatting.

- id_format(): formats Argentinian national ID numbers.

- cellphone_number_format(): formats cellphone numbers (uses Argentinian format).

/----------------------------------------------------------------------------------------------------/

## Installation

pip install tui_utilities

/----------------------------------------------------------------------------------------------------/

## Update

pip install -U tui_utilities