import random
def convertir_a_usd(precio_clp, tasa_cambio=900):
    """
    Convierte un precio de CLP a USD usando una tasa fija.
    Puedes cambiar '900' por la tasa real si la quieres dinámica.
    """
    return round(precio_clp / tasa_cambio, 2)
    
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