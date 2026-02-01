def decimal_format(number):
    if isinstance(number, float) and number.is_integer(): number = int(number)
    return f"{number:,}".replace(",", "X").replace(".", ",").replace("X", ".")

def id_format(id_string):
    if "." in id_string: return id_string
    elif len(id_string) == 8: return f"{id_string[0:2]}.{id_string[2:5]}.{id_string[5:8]}"
    elif len(id_string) == 7: return f"{id_string[0:1]}.{id_string[1:4]}.{id_string[4:7]}"

def cellphone_number_format(cellphone_number):
    formated_cellphone_number = "".join(filter(str.isdigit, cellphone_number))
    return f"{formated_cellphone_number[0:4]} - {formated_cellphone_number[4:10]}"