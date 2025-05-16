import random
import requests

def convertir_moneda(precio_clp, moneda):
    try:
        # Aquí usaremos la API de ExchangeRate para obtener las tasas
        response = requests.get('https://v6.exchangerate-api.com/v6/5480eff1fd61e8c689460213/latest/CLP')
        data = response.json()
        
        # Validar si la moneda existe en la respuesta
        if moneda not in data['conversion_rates']:
            raise ValueError(f"Moneda {moneda} no encontrada en la API.")
        
        # Obtener la tasa de conversión
        tasa_cambio = data['conversion_rates'][moneda]
        return round(precio_clp * tasa_cambio, 2)
    
    except Exception as e:
        print(f"Error en la conversión: {e}")
        # Fallback a 900 CLP por USD si falla
        return round(precio_clp / 900, 2)
    
def simular_transaccion_transbank(monto):
    """
    Simula una transacción con Transbank.
    Devuelve un diccionario simulando éxito o error.
    """
    if random.random() < 0.9:  # 90% éxito
        return {
            "status": "AUTORIZADO",
            "codigo_autorizacion": random.randint(100000, 999999),
            "monto": monto
        }
    else:
        return {
            "status": "RECHAZADO",
            "error": "Transacción rechazada por Transbank"
        }    