from flask import Blueprint, jsonify, request
from ..models import Sucursal
from .. import db
from ..utils import convertir_moneda  
from ..utils import simular_transaccion_transbank
from flask import Response
import time
import threading

api = Blueprint('api', __name__)

@api.route('/stock', methods=['GET'])
def get_stock():
    sucursales = Sucursal.query.all()
    return jsonify([s.to_dict() for s in sucursales])

@api.route('/venta', methods=['POST'])
def procesar_venta():
    data = request.json
    nombre = data.get("sucursal")
    cantidad = int(data.get("cantidad", 0))

    sucursal = Sucursal.query.filter_by(nombre=nombre).first()
    if not sucursal:
        return jsonify({"error": "Sucursal no encontrada"}), 404

    if sucursal.cantidad < cantidad:
        return jsonify({"error": "Stock insuficiente"}), 400

    sucursal.cantidad -= cantidad
    db.session.commit()

    if sucursal.cantidad == 0:
        print(f"⚠️ Stock bajo en {nombre}")  # Para SSE luego

    return jsonify({"message": "Venta realizada", "stock_restante": sucursal.cantidad})
# Lista de mensajes SSE
eventos_sse = []

@api.route('/eventos')
def stream_eventos():
    def event_stream():
        prev_len = 0
        while True:
            if len(eventos_sse) > prev_len:
                mensaje = eventos_sse[-1]
                yield f"data: {mensaje}\n\n"
                prev_len = len(eventos_sse)
            time.sleep(1)
    return Response(event_stream(), mimetype='text/event-stream')
@api.route('/venta_con_transbank', methods=['POST'])
def venta_con_transbank():
    data = request.json
    nombre = data.get("sucursal")
    cantidad = int(data.get("cantidad", 0))

    sucursal = Sucursal.query.filter_by(nombre=nombre).first()
    if not sucursal:
        return jsonify({"error": "Sucursal no encontrada"}), 404

    if sucursal.cantidad < cantidad:
        return jsonify({"error": "Stock insuficiente"}), 400

    monto = cantidad * sucursal.precio

    # 🧪 Simular paso por Transbank
    resultado = simular_transaccion_transbank(monto)

    if resultado["status"] != "AUTORIZADO":
        return jsonify({"error": resultado["error"]}), 402  # Payment Required

    # ✅ Descontar stock
    sucursal.cantidad -= cantidad
    db.session.commit()

    # 🚨 Si stock queda en 0, enviar mensaje SSE
    if sucursal.cantidad == 0:
        mensaje = f"⚠️ Stock Bajo en {sucursal.nombre}"
        eventos_sse.append(mensaje)

    return jsonify({
        "message": "Venta exitosa",
        "codigo_autorizacion": resultado["codigo_autorizacion"],
        "monto_pagado": monto,
        "stock_restante": sucursal.cantidad
    })

# 🔁 Nuevo endpoint para conversión a USD
@api.route('/convertir_usd', methods=['POST'])
def convertir_usd():
    data = request.json
    precio_clp = data.get("precio_clp")
    moneda = data.get("moneda", "USD")  # Si no envían moneda, por defecto USD.

    if precio_clp is None:
        return jsonify({"error": "precio_clp es requerido"}), 400

    try:
        precio_clp = float(precio_clp)
    except ValueError:
        return jsonify({"error": "precio_clp debe ser numérico"}), 400

    # Realizamos la conversión con la moneda seleccionada
    precio_convertido = convertir_moneda(precio_clp, moneda)

    return jsonify({
        "clp": precio_clp,
        "moneda": moneda,
        "valor_convertido": precio_convertido
    })
def descontar_stock(sucursal_nombre, cantidad):
    sucursal = Sucursal.query.filter_by(nombre=sucursal_nombre).first()
    if not sucursal:
        return False, "Sucursal no encontrada"
    if sucursal.cantidad < cantidad:
        return False, "Stock insuficiente"

    sucursal.cantidad -= cantidad
    db.session.commit()
    return True, "Stock descontado"
mensaje_enviado = None
@api.route('/notificar_stock', methods=['POST'])
def notificar_stock():
    global mensaje_enviado
    data = request.json
    mensaje = data.get("mensaje")

    # ✅ Validar si el mensaje ya fue enviado para evitar duplicación
    if mensaje and mensaje != mensaje_enviado:
        eventos_sse.append(mensaje)
        mensaje_enviado = mensaje

    return jsonify({"message": "Notificación enviada"}), 200


