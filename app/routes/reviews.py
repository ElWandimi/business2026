from flask import Blueprint, render_template, request, jsonify, url_for, flash, redirect
from flask_login import login_required, current_user
from app import db
from sqlalchemy import func
from app.models.product import Product
from app.models.review import Review, ReviewHelpful

bp = Blueprint('reviews', __name__)

@bp.route('/product/<int:product_id>/reviews')
def product_reviews(product_id):
    """Get all reviews for a product (JSON)"""
    product = Product.query.get_or_404(product_id)
    
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'recent')  # recent, helpful, highest, lowest
    
    query = Review.query.filter_by(product_id=product_id, is_approved=True)
    
    if sort == 'helpful':
        query = query.order_by(Review.helpful_count.desc(), Review.created_at.desc())
    elif sort == 'highest':
        query = query.order_by(Review.rating.desc(), Review.created_at.desc())
    elif sort == 'lowest':
        query = query.order_by(Review.rating.asc(), Review.created_at.desc())
    else:  # recent
        query = query.order_by(Review.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=5, error_out=False)
    reviews = pagination.items
    
    # Get statistics
    stats = db.session.query(
        func.count(Review.id).label('total'),
        func.avg(Review.rating).label('average'),
        func.sum(case([(Review.rating == 5, 1)], else_=0)).label('five_star'),
        func.sum(case([(Review.rating == 4, 1)], else_=0)).label('four_star'),
        func.sum(case([(Review.rating == 3, 1)], else_=0)).label('three_star'),
        func.sum(case([(Review.rating == 2, 1)], else_=0)).label('two_star'),
        func.sum(case([(Review.rating == 1, 1)], else_=0)).label('one_star')
    ).filter(Review.product_id == product_id, Review.is_approved == True).first()
    
    return jsonify({
        'reviews': [{
            'id': r.id,
            'rating': r.rating,
            'title': r.title,
            'comment': r.comment,
            'user': r.user.username,
            'user_id': r.user_id,
            'is_verified': r.is_verified,
            'helpful_count': r.helpful_count,
            'time_ago': r.time_ago,
            'created_at': r.created_at.isoformat(),
            'current_user_helpful': current_user.is_authenticated and ReviewHelpful.query.filter_by(
                review_id=r.id, user_id=current_user.id).first() is not None
        } for r in reviews],
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev,
        'page': page,
        'total': pagination.total,
        'stats': {
            'total': stats.total or 0,
            'average': round(stats.average or 0, 1),
            'five_star': stats.five_star or 0,
            'four_star': stats.four_star or 0,
            'three_star': stats.three_star or 0,
            'two_star': stats.two_star or 0,
            'one_star': stats.one_star or 0
        }
    })

@bp.route('/product/<int:product_id>/review/add', methods=['POST'])
@login_required
def add_review(product_id):
    """Add a new review"""
    product = Product.query.get_or_404(product_id)
    
    # Check if user already reviewed
    existing = Review.query.filter_by(product_id=product_id, user_id=current_user.id).first()
    if existing:
        return jsonify({'error': 'You have already reviewed this product'}), 400
    
    # Check if user purchased the product (verified purchase)
    from app.models.order import Order, OrderItem
    purchased = db.session.query(OrderItem).join(Order).filter(
        OrderItem.product_id == product_id,
        Order.user_id == current_user.id,
        Order.payment_status == 'paid'
    ).first() is not None
    
    data = request.get_json()
    
    review = Review(
        product_id=product_id,
        user_id=current_user.id,
        rating=data['rating'],
        title=data.get('title', ''),
        comment=data.get('comment', ''),
        is_verified=purchased,
        is_approved=True  # Auto-approve, or set to False for admin approval
    )
    
    db.session.add(review)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Review added successfully!'})

@bp.route('/review/<int:review_id>/helpful', methods=['POST'])
@login_required
def mark_helpful(review_id):
    """Mark a review as helpful"""
    review = Review.query.get_or_404(review_id)
    
    # Check if already voted
    vote = ReviewHelpful.query.filter_by(review_id=review_id, user_id=current_user.id).first()
    
    if vote:
        # Remove vote
        db.session.delete(vote)
        review.helpful_count -= 1
        db.session.commit()
        return jsonify({'success': True, 'helpful': False, 'count': review.helpful_count})
    else:
        # Add vote
        vote = ReviewHelpful(review_id=review_id, user_id=current_user.id)
        db.session.add(vote)
        review.helpful_count += 1
        db.session.commit()
        return jsonify({'success': True, 'helpful': True, 'count': review.helpful_count})

@bp.route('/review/<int:review_id>/edit', methods=['POST'])
@login_required
def edit_review(review_id):
    """Edit a review"""
    review = Review.query.get_or_404(review_id)
    
    if review.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    
    review.rating = data['rating']
    review.title = data.get('title', '')
    review.comment = data.get('comment', '')
    review.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Review updated successfully!'})

@bp.route('/review/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_review(review_id):
    """Delete a review"""
    review = Review.query.get_or_404(review_id)
    
    if review.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Permission denied'}), 403
    
    db.session.delete(review)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Review deleted successfully!'})

# Admin routes for review moderation
@bp.route('/admin/reviews')
@login_required
def admin_reviews():
    """Admin review management"""
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'pending')
    
    query = Review.query
    
    if status == 'pending':
        query = query.filter_by(is_approved=False)
    elif status == 'approved':
        query = query.filter_by(is_approved=True)
    
    reviews = query.order_by(Review.created_at.desc()).paginate(page=page, per_page=20)
    
    return render_template('admin/reviews.html', reviews=reviews, status=status)

@bp.route('/admin/review/<int:review_id>/approve', methods=['POST'])
@login_required
def approve_review(review_id):
    """Approve a review"""
    if not current_user.is_admin:
        return jsonify({'error': 'Permission denied'}), 403
    
    review = Review.query.get_or_404(review_id)
    review.is_approved = not review.is_approved
    db.session.commit()
    
    return jsonify({'success': True, 'approved': review.is_approved})

# Helper function for conditional sum in SQLAlchemy
def case(whens, else_=None):
    from sqlalchemy import case as sqlalchemy_case
    return sqlalchemy_case(whens, else_=else_)