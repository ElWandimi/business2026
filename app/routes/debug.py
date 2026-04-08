from flask import Blueprint, jsonify, current_app
import os

bp = Blueprint('debug', __name__)

@bp.route('/debug/routes')
def debug_routes():
    """List all registered routes"""
    routes = []
    for rule in current_app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'path': str(rule)
        })
    
    routes.sort(key=lambda x: x['path'])
    
    # Create HTML response
    html = '<h1>Registered Routes</h1>'
    html += '<table border="1" cellpadding="5" style="border-collapse: collapse;">'
    html += '<tr><th>Endpoint</th><th>Path</th><th>Methods</th></tr>'
    for route in routes:
        html += f'<tr>'
        html += f'<td>{route["endpoint"]}</td>'
        html += f'<td>{route["path"]}</td>'
        html += f'<td>{", ".join(route["methods"])}</td>'
        html += f'</tr>'
    html += '</table>'
    
    return html

@bp.route('/debug/blueprints')
def debug_blueprints():
    """List all registered blueprints"""
    blueprints = []
    for name, blueprint in current_app.blueprints.items():
        blueprints.append({
            'name': name,
            'url_prefix': blueprint.url_prefix
        })
    
    html = '<h1>Registered Blueprints</h1>'
    html += '<ul>'
    for bp in blueprints:
        html += f'<li><strong>{bp["name"]}:</strong> {bp["url_prefix"] or "/"}</li>'
    html += '</ul>'
    
    return html

@bp.route('/debug/images')
def debug_images():
    """Debug endpoint to check image paths"""
    from app.models.product import Product
    
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'products')
    files_in_folder = []
    if os.path.exists(upload_path):
        files_in_folder = os.listdir(upload_path)
    
    products = Product.query.all()
    
    html = '<h1>Image Debug Information</h1>'
    html += f'<p><strong>Upload directory:</strong> {upload_path}</p>'
    html += f'<p><strong>Directory exists:</strong> {os.path.exists(upload_path)}</p>'
    
    html += '<h2>Files in upload directory:</h2>'
    html += '<ul>'
    for f in files_in_folder:
        html += f'<li>{f}</li>'
    html += '</ul>'
    
    html += '<h2>Products and their images:</h2>'
    if products:
        for product in products:
            html += f'<h3>{product.name}</h3>'
            if product.images:
                html += '<ul>'
                for img in product.images:
                    filename = img.image_url.split('/')[-1]
                    file_path = os.path.join(upload_path, filename)
                    exists = os.path.exists(file_path)
                    status = '✅' if exists else '❌'
                    html += f'<li>{status} URL: {img.image_url} | File: {filename} | Exists: {exists}</li>'
                html += '</ul>'
            else:
                html += '<p>No images for this product</p>'
    else:
        html += '<p>No products found</p>'
    
    return html

@bp.route('/debug/health')
def health():
    """Simple health check"""
    return jsonify({
        'status': 'healthy',
        'message': 'Business2026 is running',
        'debug': True
    })