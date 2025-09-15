"""
Admin Token Management Controller
Handles admin-only token operations
"""
import logging
from flask import Blueprint, request, jsonify

from utils.decorators import require_auth, handle_errors
from utils.responses import success_response, error_response, not_found_response
from shared_db import db_manager

logger = logging.getLogger(__name__)

# Create blueprint
admin_token_bp = Blueprint('admin_tokens', __name__, url_prefix='/api/admin/tokens')


def require_admin(f):
    """Decorator to require admin permissions"""
    def decorated_function(*args, **kwargs):
        # For now, simple admin check - can be enhanced later
        user_dict = request.user
        
        # Simple admin check - you can enhance this with proper role system
        admin_emails = ['admin@vantage.com', 'omer.burshan1@gmail.com']  # Configure as needed
        if user_dict.get('email') not in admin_emails:
            return error_response(
                "Admin access required",
                "ADMIN_REQUIRED",
                403
            )
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


@admin_token_bp.route('/add', methods=['POST'])
@require_auth
@require_admin
@handle_errors
def add_tokens_to_user():
    """Add tokens to a user account"""
    admin_user = request.user
    data = request.get_json()
    
    # Validate required fields
    user_email = data.get('user_email')
    amount = data.get('amount')
    admin_note = data.get('note', '')
    
    if not user_email or not amount:
        return error_response("user_email and amount are required", "VALIDATION_ERROR", 400)
    
    if not isinstance(amount, int) or amount <= 0:
        return error_response("amount must be a positive integer", "VALIDATION_ERROR", 400)
    
    # Find user by email
    user = db_manager.get_user_by_email(user_email)
    if not user:
        return not_found_response(f"User with email {user_email} not found")
    
    # Add tokens
    result = db_manager.add_tokens_to_user(
        user_id=user['id'],
        amount=amount,
        transaction_type='admin_grant',
        admin_user_id=admin_user['id'],
        admin_note=f"Manual grant by admin: {admin_note}"
    )
    
    if result['success']:
        logger.info(f"Admin {admin_user['email']} added {amount} tokens to user {user_email}")
        return success_response(
            data=result,
            message=f"Successfully added {amount} tokens to {user_email}"
        )
    else:
        return error_response(result['message'], "TOKEN_OPERATION_FAILED", 500)


@admin_token_bp.route('/transactions', methods=['GET'])
@require_auth
@require_admin
@handle_errors
def get_all_transactions():
    """Get all token transactions (admin view)"""
    limit = request.args.get('limit', 100, type=int)
    
    transactions = db_manager.get_all_token_transactions(limit=limit)
    
    return success_response(
        data={'transactions': transactions, 'total_count': len(transactions)},
        message="Token transactions retrieved successfully"
    )


@admin_token_bp.route('/users/<int:user_id>/transactions', methods=['GET'])
@require_auth
@require_admin
@handle_errors
def get_user_transactions(user_id):
    """Get token transactions for a specific user"""
    limit = request.args.get('limit', 50, type=int)
    
    # Verify user exists
    user = db_manager.get_user_by_id(user_id)
    if not user:
        return not_found_response("User not found")
    
    transactions = db_manager.get_user_token_transactions(user_id, limit=limit)
    
    return success_response(
        data={
            'user': user,
            'transactions': transactions, 
            'total_count': len(transactions)
        },
        message=f"Token transactions for user {user['email']} retrieved successfully"
    )


@admin_token_bp.route('/bulk-grant', methods=['POST'])
@require_auth
@require_admin
@handle_errors
def bulk_grant_tokens():
    """Grant tokens to multiple users at once"""
    admin_user = request.user
    data = request.get_json()
    
    users = data.get('users', [])  # List of {email, amount} objects
    default_amount = data.get('default_amount', 10)
    admin_note = data.get('note', 'Bulk token grant')
    
    if not users:
        return error_response("users list is required", "VALIDATION_ERROR", 400)
    
    results = []
    errors = []
    
    for user_data in users:
        user_email = user_data.get('email')
        amount = user_data.get('amount', default_amount)
        
        if not user_email:
            errors.append({'email': 'missing', 'error': 'Email required'})
            continue
            
        # Find user
        user = db_manager.get_user_by_email(user_email)
        if not user:
            errors.append({'email': user_email, 'error': 'User not found'})
            continue
        
        # Add tokens
        result = db_manager.add_tokens_to_user(
            user_id=user['id'],
            amount=amount,
            transaction_type='admin_grant',
            admin_user_id=admin_user['id'],
            admin_note=f"Bulk grant: {admin_note}"
        )
        
        if result['success']:
            results.append({
                'email': user_email,
                'amount': amount,
                'new_balance': result['balance_after'],
                'transaction_id': result['transaction_id']
            })
        else:
            errors.append({'email': user_email, 'error': result['message']})
    
    logger.info(f"Admin {admin_user['email']} performed bulk token grant: {len(results)} successful, {len(errors)} errors")
    
    return success_response(
        data={
            'successful': results,
            'errors': errors,
            'summary': {
                'total_processed': len(users),
                'successful_count': len(results),
                'error_count': len(errors)
            }
        },
        message=f"Bulk token grant completed: {len(results)} successful, {len(errors)} errors"
    )