# app/routes/support.py
# app/routes/support.py
from flask import Blueprint, render_template, request, jsonify, session, current_app, url_for
from app import db
from app.models.support import SupportConversation, SupportMessage, SupportRating
from app.models.notification import Notification  # NEW
from app.services.email import send_support_confirmation, send_support_reply
from datetime import datetime
import uuid

bp = Blueprint('support', __name__, url_prefix='/support')

@bp.route('/start', methods=['POST'])
def start_conversation():
    """Start a new support conversation."""
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    order_number = data.get('order_number')
    
    if not name or not email:
        return jsonify({'error': 'Name and email are required'}), 400
    
    conv = SupportConversation(name=name, email=email, order_number=order_number)
    db.session.add(conv)
    db.session.commit()
    
    session['support_conv_id'] = conv.id
    send_support_confirmation(conv)
    
    return jsonify({'conversation_id': conv.id})

@bp.route('/send', methods=['POST'])
def send_message():
    """User sends a message."""
    conv_id = session.get('support_conv_id')
    if not conv_id:
        return jsonify({'error': 'No active conversation'}), 400
    
    data = request.get_json()
    message = data.get('message')
    if not message:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    conv = SupportConversation.query.get(conv_id)
    if not conv:
        return jsonify({'error': 'Conversation not found'}), 404
    
    msg = SupportMessage(conversation_id=conv.id, sender='user', message=message)
    db.session.add(msg)
    conv.updated_at = datetime.utcnow()
    db.session.commit()
    
    # ===== NOTIFICATION: New support message =====
    try:
        notif = Notification(
            type='new_support_message',
            title=f'New message from {conv.name}',
            message=message[:100] + ('...' if len(message) > 100 else ''),
            link=url_for('admin.support_dashboard')
        )
        db.session.add(notif)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Failed to create support notification: {e}")
    
    return jsonify({'success': True, 'message_id': msg.id, 'created_at': msg.created_at.isoformat()})

# ... rest of the support routes (status, messages, resolve, rate, etc.) remain unchanged ...

@bp.route('/messages', methods=['GET'])
def get_messages():
    """Poll for new messages (since a given timestamp)."""
    conv_id = session.get('support_conv_id')
    if not conv_id:
        return jsonify({'error': 'No active conversation'}), 400
    
    since = request.args.get('since')
    try:
        since_dt = datetime.fromisoformat(since) if since else datetime(1970,1,1)
    except:
        since_dt = datetime(1970,1,1)
    
    conv = SupportConversation.query.get(conv_id)
    if not conv:
        return jsonify({'error': 'Conversation not found'}), 404
    
    messages = SupportMessage.query.filter(
        SupportMessage.conversation_id == conv_id,
        SupportMessage.created_at > since_dt
    ).order_by(SupportMessage.created_at.asc()).all()
    
    return jsonify([{
        'id': m.id,
        'sender': m.sender,
        'message': m.message,
        'created_at': m.created_at.isoformat()
    } for m in messages])

@bp.route('/status')
def conversation_status():
    """Return current conversation status and details."""
    conv_id = session.get('support_conv_id')
    if not conv_id:
        return jsonify({'has_conversation': False})
    conv = SupportConversation.query.get(conv_id)
    if not conv:
        return jsonify({'has_conversation': False})
    return jsonify({
        'has_conversation': True,
        'conversation_id': conv.id,
        'status': conv.status,
        'name': conv.name,
        'email': conv.email,
        'order_number': conv.order_number,
        'rated': conv.rating is not None
    })

@bp.route('/resolve', methods=['POST'])
def resolve_conversation():
    """User marks conversation as resolved (optional)."""
    conv_id = session.get('support_conv_id')
    if not conv_id:
        return jsonify({'error': 'No active conversation'}), 400
    conv = SupportConversation.query.get(conv_id)
    if conv:
        conv.status = 'closed'
        db.session.commit()
        session.pop('support_conv_id', None)
    return jsonify({'success': True})

@bp.route('/rate/<int:conv_id>', methods=['POST'])
def rate_conversation(conv_id):
    """User submits a rating after conversation is closed."""
    data = request.get_json()
    rating = data.get('rating')
    feedback = data.get('feedback', '')
    
    # Convert rating to int if it's a string
    try:
        rating = int(rating)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'Rating must be a number'}), 400

    if not (1 <= rating <= 5):
        return jsonify({'success': False, 'error': 'Rating must be 1-5'}), 400

    conv = SupportConversation.query.get(conv_id)
    if not conv:
        return jsonify({'success': False, 'error': 'Conversation not found'}), 404

    # Check if already rated
    if conv.rating:
        return jsonify({'success': False, 'error': 'Already rated'}), 400

    rating_obj = SupportRating(conversation_id=conv.id, rating=rating, feedback=feedback)
    db.session.add(rating_obj)
    db.session.commit()
    return jsonify({'success': True})