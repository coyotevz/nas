# -*- coding: utf-8 -*-

import re

def validate_cuit(cuit):
    """
    Validates CUIT (Argentina) - Clave Única de Identificación Tributaria
    from: http://python.org.ar/pyar/Recetario/ValidarCuit by Mariano Reingart
    """
    cuit = str(cuit).replace("-", "") # normalize
    # validaciones mínimas
    if not re.match(r'\d{11}$', cuit):
        return False

    base = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]

    # calculo digito verificador
    aux = sum([int(cuit[i])*base[i] for i in range(10)])
    aux = 11 - (aux % 11)

    if aux == 11:
        aux = 0
    elif aux == 10:
        aux = 9

    return aux == int(cuit[10])


def validate_cbu(cbu):
    """Validates CBU (Argentina) - Clave Bancaria Uniforme"""
    cbu = str(cbu).replate(" ", "") # normalize
    # validaciones minimas
    if not re.match(r'\d{22}$', cbu):
        return False

    # calculo digito verificador banco
    base = [7, 1, 3, 9, 7, 1, 3]
    aux = sum([int(cbu[i])*base[i] for i in range(7)])

    if (10 - (aux % 10)) != int(cbu[7]):
        return False

    # calculo digito verificador cuenta
    base = [3, 9, 7, 1, 3, 9, 7, 1, 3, 9, 7, 1, 3]
    aux = sum([int(cbu[i+8])*base[i] for i in range(13)])

    return (10 - (aux % 10)) == int(cbu[21])
