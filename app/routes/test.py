from flask import Blueprint, jsonify

bp = Blueprint('test', __name__)

@bp.route('/test')
def test():
    return jsonify({'message': 'Test route works!'})

@bp.route('/test/models')
def test_models():
    try:
        from app.models.product import Product
        count = Product.query.count()
        return jsonify({'message': f'Product model works! Found {count} products'})
    except Exception as e:
        return jsonify({'error': str(e)})