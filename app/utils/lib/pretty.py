from tabulate import tabulate

def pretty_print_dict(data):
    """
    Imprime un diccionario en formato de tabla para mostrar sus claves y valores de forma legible.
    
    :param data: Diccionario con los datos a imprimir.
    """
    if not isinstance(data, dict):
        raise ValueError("El argumento proporcionado debe ser un diccionario.")
    
    # Convertir el diccionario en una lista de pares clave-valor
    table_data = [[key, value] for key, value in data.items()]
    
    # Usar tabulate para imprimir el diccionario en formato de tabla
    print(tabulate(table_data, headers=["Clave", "Valor"], tablefmt="grid"))


