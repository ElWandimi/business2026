from flask import Blueprint, jsonify

bp = Blueprint('test_payment', __name__)

@bp.route('/test/payment/success')
def test_success():
    return jsonify({
        'message': 'Payment success endpoint is working',
        'params': dict(request.args)
    })