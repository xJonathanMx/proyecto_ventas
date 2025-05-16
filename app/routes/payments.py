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
    
    # Verificamos si el estado de la transacción es 'AUTHORIZED'
    if response.get('status') == 'AUTHORIZED':
        # Obtener los datos de la transacción
        buy_order = response.get('buy_order')
        sucursal_nombre = buy_order.split("_")[1]
        cantidad_comprada = int(buy_order.split("_")[2])
        
        # Buscar la sucursal en la base de datos
        sucursal = Sucursal.query.filter_by(nombre=sucursal_nombre).first()
        
        if sucursal:
            if sucursal.cantidad >= cantidad_comprada:
                sucursal.cantidad -= cantidad_comprada
                db.session.commit()
            else:
                return f"No hay suficiente stock en la sucursal {sucursal_nombre}", 400
        
    return render_template('resultado.html', response=response)

