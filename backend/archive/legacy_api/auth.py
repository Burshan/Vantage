# api/auth.py - API routes עבור אימות ומשתמשים
import math
from flask import Blueprint, jsonify, request
# מחק את השורה הזו: from auth import require_tokens

def create_auth_blueprint(components):
    """יוצר Blueprint עבור API routes של אימות"""
    
    auth_bp = Blueprint('auth', __name__, url_prefix='/api')
    
    # קבלת הקומפוננטים
    db_manager = components['db_manager']
    require_auth = components['require_auth']
    
    @auth_bp.route('/user/profile')
    @require_auth
    def get_user_profile():
        """קבלת פרופיל משתמש עם מידע מלא"""
        try:
            user = request.user
            history = db_manager.get_user_history(user['id'], limit=5)
            aois = db_manager.get_user_aois(user['id'])
            
            # חישוב צריכה שבועית משוערת
            weekly_consumption = sum(
                math.ceil(7 / aoi['refresh_interval']) if aoi['auto_refresh_enabled'] else 0 
                for aoi in aois
            )
            
            return jsonify({
                'success': True,
                'user': user,
                'recent_history': history,
                'areas_of_interest': aois,
                'token_info': {
                    'tokens_remaining': user['tokens_remaining'],
                    'total_tokens_used': user['total_tokens_used'],
                    'subscription_tier': user['subscription_tier'],
                    'estimated_weekly_consumption': weekly_consumption
                }
            })
        except Exception as e:
            print(f"Error in get_user_profile: {e}")
            return jsonify({'error': f'שגיאה בקבלת פרופיל: {str(e)}'}), 500

    @auth_bp.route('/user/history')
    @require_auth  
    def get_user_history():
        """קבלת היסטוריית ניתוחים מלאה של המשתמש"""
        try:
            user = request.user
            limit = request.args.get('limit', 20, type=int)
            
            history = db_manager.get_user_history(user['id'], limit=limit)
            
            return jsonify({
                'success': True,
                'history': history,
                'total_analyses': len(history),
                'user_tokens': {
                    'tokens_remaining': user['tokens_remaining'],
                    'total_tokens_used': user['total_tokens_used']
                }
            })
        except Exception as e:
            print(f"Error in get_user_history: {e}")
            return jsonify({'error': f'שגיאה בקבלת היסטוריה: {str(e)}'}), 500

    @auth_bp.route('/user/tokens')
    @require_auth
    def get_user_tokens():
        """קבלת מידע מפורט על טוקנים וצריכה"""
        try:
            user = request.user
            aois = db_manager.get_user_aois(user['id'])
            
            # חישוב צריכה שבועית משוערת
            weekly_consumption = sum(
                math.ceil(7 / aoi['refresh_interval']) if aoi['auto_refresh_enabled'] else 0 
                for aoi in aois
            )
            
            return jsonify({
                'success': True,
                'token_info': {
                    'tokens_remaining': user['tokens_remaining'],
                    'total_tokens_used': user['total_tokens_used'],
                    'subscription_tier': user['subscription_tier'],
                    'estimated_weekly_consumption': weekly_consumption,
                    'estimated_weeks_remaining': (
                        user['tokens_remaining'] // weekly_consumption 
                        if weekly_consumption > 0 else float('inf')
                    )
                }
            })
        except Exception as e:
            print(f"Error in get_user_tokens: {e}")
            return jsonify({'error': f'שגיאה בקבלת מידע טוקנים: {str(e)}'}), 500
    
    return auth_bp