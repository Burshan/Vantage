"""
Authentication and error handling decorators
"""
import logging
from functools import wraps
from flask import request, jsonify
from config import Config

logger = logging.getLogger(__name__)


class ClerkAuthenticator:
    def __init__(self, clerk_secret_key):
        self.clerk_secret_key = clerk_secret_key
    
    def verify_token(self, token):
        """Verify Clerk JWT token"""
        try:
            import jwt
            
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            # In production, use proper signature verification
            options = {"verify_signature": False} if Config.DEBUG else {}
            
            decoded = jwt.decode(
                token,
                self.clerk_secret_key,
                algorithms=["RS256"],
                options=options
            )
            
            return decoded
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {str(e)}")
            return None


# Initialize authenticator
clerk_auth = ClerkAuthenticator(Config.CLERK_SECRET_KEY)


def require_auth(f):
    """Enhanced authentication decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)
            
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                'error': 'No authorization token provided',
                'code': 'NO_AUTH_HEADER'
            }), 401
        
        try:
            user_data = clerk_auth.verify_token(auth_header)
            if not user_data:
                return jsonify({
                    'error': 'Invalid or expired token',
                    'code': 'INVALID_TOKEN'
                }), 401
            
            logger.info(f"Auth successful for: {user_data.get('sub')}")
            
            # Log successful authentication
            logger.info(f"User authenticated: {user_data.get('email')} (Clerk ID: {user_data.get('sub')})")
            
            # Get or create user in database
            from shared_db import db_manager
            
            user = db_manager.get_or_create_user(
                clerk_user_id=user_data.get('sub'),
                email=user_data.get('email'),
                first_name=user_data.get('given_name') or user_data.get('first_name'),
                last_name=user_data.get('family_name') or user_data.get('last_name')
            )
            
            logger.debug(f"Request user: {user}")
            request.user = user
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return jsonify({
                'error': 'Authentication failed',
                'code': 'AUTH_ERROR'
            }), 401
    
    return decorated_function


def handle_errors(f):
    """Global error handling decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Validation error in {f.__name__}: {str(e)}")
            return jsonify({
                'error': 'Invalid input',
                'message': str(e),
                'code': 'VALIDATION_ERROR'
            }), 400
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}")
            return jsonify({
                'error': 'Internal server error',
                'message': str(e) if Config.DEBUG else 'Something went wrong',
                'code': 'INTERNAL_ERROR'
            }), 500
    
    return decorated_function