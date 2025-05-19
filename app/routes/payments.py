from flask import Blueprint, render_template, request, redirect, url_for
from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.options import WebpayOptions
from transbank.common.integration_type import IntegrationType
from flask import current_app
bp = Blueprint('payments', __name__)

# Configuración de Transbank para modo TEST
options = WebpayOptions(
    commerce_code='597055555532',
    api_key='579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C',
    integration_type=IntegrationType.TEST
)
transaction = Transaction(options)

@bp.route('/pagar', methods=['GET', 'POST'])
def iniciar_pago():
    if request.method == 'GET':
        # Muestra la vista para confirmar el pago
        sucursal = request.args.get('sucursal')
        cantidad = int(request.args.get('cantidad', 1))
        moneda = request.args.get('moneda')
        total = int(request.args.get('total', 0))

        return render_template('pagar.html',
                               sucursal=sucursal,
                               cantidad=cantidad,
                               moneda=moneda,
                               total=total)

    elif request.method == 'POST':
        # Aquí ya se confirma y se llama a Transbank
        sucursal = request.form.get('sucursal')
        cantidad = int(request.form.get('cantidad'))
        total = int(request.form.get('total'))

        buy_order = f"orden_{sucursal}_{cantidad}"
        session_id = f"session_{sucursal}"
        return_url = url_for('payments.resultado_pago', _external=True)

        response = transaction.create(buy_order, session_id, total, return_url)
        return redirect(response.get('url') + '?token_ws=' + response.get('token'))
    

from ..models import Sucursal
from .. import db

@bp.route('/resultado', endpoint='resultado_pago')
def resultado_pago():
    token_ws = request.args.get('token_ws')
    if not token_ws:
        return "No se recibió token_ws", 400

    response = transaction.commit(token_ws)
    current_app.logger.info(f"Respuesta Transbank: {response}")

    if response.get('status') == 'AUTHORIZED' and response.get('response_code') == 0:
        buy_order = response.get('buy_order')
        current_app.logger.info(f"Buy order: {buy_order}")

        try:
            _, sucursal_nombre, cantidad_str = buy_order.split('_')
            cantidad = int(cantidad_str)
        except Exception as e:
            current_app.logger.error(f"Error parseando buy_order: {e}")
            return f"Error al interpretar buy_order: {e}", 500

        sucursal = Sucursal.query.filter_by(nombre=sucursal_nombre).first()
        if not sucursal:
            current_app.logger.error("Sucursal no encontrada para descuento")
            return "Sucursal no encontrada para descuento de stock", 404

        if sucursal.cantidad < cantidad:
            current_app.logger.error("Stock insuficiente para descuento")
            return "Stock insuficiente al momento de descontar", 400

        sucursal.cantidad -= cantidad
        db.session.commit()
        current_app.logger.info(f"Stock descontado: {cantidad} de {sucursal_nombre}, nuevo stock: {sucursal.cantidad}")

    else:
        current_app.logger.warning(f"Pago no aprobado, status: {response.get('status')}")

    return render_template('resultado.html', response=response)
