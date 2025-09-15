# api/aoi.py - API routes עבור ניהול אזורי עניין (AOI)
from flask import Blueprint, jsonify, request

def create_aoi_blueprint(components):
    """יוצר Blueprint עבור API routes של AOI"""
    
    aoi_bp = Blueprint('aoi', __name__, url_prefix='/api')
    
    # קבלת הקומפוננטים
    db_manager = components['db_manager']
    require_auth = components['require_auth']
    satellite_processor = components['satellite_processor']
    
    @aoi_bp.route('/aoi', methods=['GET'])
    @require_auth
    def get_areas_of_interest():
        """קבלת כל אזורי העניין של המשתמש"""
        try:
            user = request.user
            aois = db_manager.get_user_aois(user['id'])
            
            return jsonify({
                'success': True,
                'areas_of_interest': aois,
                'total_count': len(aois)
            })
        except Exception as e:
            print(f"Error in get_areas_of_interest: {e}")
            return jsonify({'error': f'שגיאה בקבלת אזורי עניין: {str(e)}'}), 500

    @aoi_bp.route('/aoi', methods=['POST'])
    @require_auth
    def create_area_of_interest():
        """יצירת אזור עניין חדש עם הגדרות מלאות"""
        try:
            user = request.user
            data = request.get_json()
            
            # בדיקת שדות חובה
            required_fields = ['name', 'bbox_coordinates']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'שדה חובה חסר: {field}'}), 400
            
            # אימות קואורדינטות
            bbox = data['bbox_coordinates']
            is_valid, error_msg = satellite_processor.validate_bbox(bbox)
            if not is_valid:
                return jsonify({'error': f'קואורדינטות לא תקינות: {error_msg}'}), 400
            
            # יצירת AOI
            aoi = db_manager.create_aoi(
                user_id=user['id'],
                name=data['name'],
                description=data.get('description', ''),
                location_name=data.get('location_name', ''),
                bbox_coordinates=bbox,
                classification=data.get('classification', 'CONFIDENTIAL'),
                priority=data.get('priority', 'MEDIUM'),
                color_code=data.get('color_code', '#3B82F6'),
                refresh_interval=data.get('refresh_interval', 7),
                auto_refresh_enabled=data.get('auto_refresh_enabled', True),
                analysis_type=data.get('analysis_type', 'change_detection')
            )
            
            return jsonify({
                'success': True,
                'aoi': aoi,
                'message': f"AOI '{aoi['name']}' נוצר בהצלחה עם רענון כל {aoi['refresh_interval']} ימים"
            })
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            print(f"Error in create_area_of_interest: {e}")
            return jsonify({'error': f'שגיאה ביצירת AOI: {str(e)}'}), 500

    @aoi_bp.route('/aoi/<int:aoi_id>', methods=['DELETE'])
    @require_auth
    def delete_area_of_interest(aoi_id):
        """מחיקת אזור עניין"""
        try:
            user = request.user
            success, message = db_manager.delete_aoi(aoi_id, user['id'])
            
            if success:
                return jsonify({'success': True, 'message': message})
            else:
                return jsonify({'error': message}), 404
                
        except Exception as e:
            print(f"Error in delete_area_of_interest: {e}")
            return jsonify({'error': f'שגיאה במחיקת AOI: {str(e)}'}), 500

    @aoi_bp.route('/aoi/<int:aoi_id>/toggle-refresh', methods=['POST'])
    @require_auth
    def toggle_aoi_refresh(aoi_id):
        """הפעלה/כיבוי רענון אוטומטי לאזור עניין"""
        try:
            user = request.user
            data = request.get_json()
            auto_refresh_enabled = data.get('auto_refresh_enabled', True)
            
            # עדכון בבסיס הנתונים
            import sqlite3
            with db_manager.DB_LOCK:
                conn = sqlite3.connect(db_manager.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE areas_of_interest 
                    SET auto_refresh_enabled = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                ''', (auto_refresh_enabled, aoi_id, user['id']))
                
                if cursor.rowcount == 0:
                    conn.close()
                    return jsonify({'error': 'AOI לא נמצא'}), 404
                
                conn.commit()
                conn.close()
            
            return jsonify({
                'success': True,
                'message': f"רענון אוטומטי {'הופעל' if auto_refresh_enabled else 'כובה'} עבור AOI"
            })
        except Exception as e:
            print(f"Error in toggle_aoi_refresh: {e}")
            return jsonify({'error': f'שגיאה בעדכון AOI: {str(e)}'}), 500
    
    return aoi_bp