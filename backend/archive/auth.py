# auth.py - מודול אימות משתמשים
import jwt
from functools import wraps
from flask import request, jsonify
from database import DatabaseManager

class ClerkAuthenticator:
    """מחלקה לאימות Clerk JWT"""
    
    def __init__(self, clerk_secret_key):
        self.clerk_secret_key = clerk_secret_key
    
    def verify_token(self, token):
        """אימות Clerk JWT token"""
        try:
            # הסר את הקידומת 'Bearer ' אם קיימת
            if token.startswith('Bearer '):
                token = token[7:]
            
            # פענח JWT token
            decoded = jwt.decode(
                token,
                self.clerk_secret_key,
                algorithms=["RS256"],
                options={"verify_signature": False}  # לפיתוח - הפעל אימות חתימה בפרודקשן
            )
            
            return decoded
        except jwt.ExpiredSignatureError:
            print("Token פג תוקף")
            return None
        except jwt.InvalidTokenError as e:
            print(f"Token לא תקין: {e}")
            return None

def create_auth_decorator(clerk_authenticator, db_manager):
    """יוצר decorator לאימות"""
    
    def require_auth(f):
        """Decorator לאימות - דורש הזדהות למשתמש"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # בדוק headers של authorization
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({'error': 'חסר טוקן הזדהות'}), 401
            
            # אמת את הטוקן
            user_data = clerk_authenticator.verify_token(auth_header)
            if not user_data:
                return jsonify({'error': 'טוקן לא תקין או פג תוקף'}), 401
            
            # קבל או צור משתמש בבסיס הנתונים
            try:
                user = db_manager.get_or_create_user(
                    clerk_user_id=user_data.get('sub'),
                    email=user_data.get('email'),
                    first_name=user_data.get('given_name'),
                    last_name=user_data.get('family_name')
                )
                
                # הוסף את המשתמש ל-request
                request.user = user
                return f(*args, **kwargs)
                
            except Exception as e:
                print(f"שגיאה ביצירת/קבלת משתמש: {e}")
                return jsonify({'error': 'שגיאה באימות משתמש'}), 500
        
        return decorated_function
    
    return require_auth

def require_tokens(tokens_needed=1):
    """Decorator שבודק שיש מספיק טוקנים"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = getattr(request, 'user', None)
            if not user:
                return jsonify({'error': 'משתמש לא מאומת'}), 401
            
            if user['tokens_remaining'] < tokens_needed:
                return jsonify({
                    'error': f'אין מספיק טוקנים. נדרש: {tokens_needed}, זמין: {user["tokens_remaining"]}',
                    'tokens_remaining': user['tokens_remaining']
                }), 402
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator שדורש הרשאות אדמין (לעתיד)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = getattr(request, 'user', None)
        if not user:
            return jsonify({'error': 'משתמש לא מאומת'}), 401
        
        # כרגע כל משתמש יכול - בעתיד אפשר להוסיף לוגיקה של הרשאות
        # if user.get('role') != 'admin':
        #     return jsonify({'error': 'נדרשות הרשאות אדמין'}), 403
        
        return f(*args, **kwargs)
    return decorated_function