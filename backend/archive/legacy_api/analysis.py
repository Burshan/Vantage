# api/analysis.py - API routes עבור עיבוד ניתוחי לוויין (גרסה מלאה)
import os
import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request, send_file
from auth import require_tokens

def create_analysis_blueprint(components):
    """יוצר Blueprint עבור API routes של ניתוח לוויין"""
    
    analysis_bp = Blueprint('analysis', __name__, url_prefix='/api')
    
    # קבלת הקומפוננטים
    db_manager = components['db_manager']
    require_auth = components['require_auth']
    satellite_processor = components['satellite_processor']
    
    @analysis_bp.route('/process-satellite-images', methods=['POST'])
    @require_auth
    @require_tokens(1)
    def process_satellite_images():
        """עיבוד תמונות לוויין - ידני או דרך AOI"""
        try:
            user = request.user
            data = request.get_json()
            
            print(f"מתחיל ניתוח ידני עבור משתמש: {user['email']}")
            print(f"טוקנים זמינים: {user['tokens_remaining']}")
            
            # קבלת פרמטרי ניתוח
            aoi_id = data.get('aoi_id')
            custom_bbox = data.get('bbox_coordinates')
            date_range_1 = data.get('date_range_1', {
                'from': '2021-08-01', 
                'to': '2021-08-31'
            })
            date_range_2 = data.get('date_range_2', {
                'from': '2025-08-01', 
                'to': '2025-08-31'
            })
            
            # קביעת קואורדינטות ומיקום
            if aoi_id:
                aois = db_manager.get_user_aois(user['id'])
                aoi = next((a for a in aois if a['id'] == aoi_id), None)
                if not aoi:
                    return jsonify({'error': 'AOI לא נמצא'}), 404
                bbox = aoi['bbox_coordinates']
                location_description = aoi['location_name'] or aoi['name']
            elif custom_bbox:
                is_valid, error_msg = satellite_processor.validate_bbox(custom_bbox)
                if not is_valid:
                    return jsonify({'error': f'קואורדינטות לא תקינות: {error_msg}'}), 400
                bbox = custom_bbox
                location_description = data.get('location_description', 'מיקום מותאם אישית')
            else:
                return jsonify({'error': 'חובה לספק aoi_id או bbox_coordinates'}), 400
            
            # שימוש בטוקנים
            success, message = db_manager.use_tokens(
                user['id'], 
                1, 
                f"ניתוח ידני: {location_description}"
            )
            if not success:
                return jsonify({'error': message}), 402
            
            process_id = str(uuid.uuid4())[:8]
            
            print(f"מעבד אזור: {bbox}")
            print(f"תקופה 1: {date_range_1['from']} עד {date_range_1['to']}")
            print(f"תקופה 2: {date_range_2['from']} עד {date_range_2['to']}")
            
            # הורדת תמונות
            print("מוריד תמונה ראשונה...")
            image1 = satellite_processor.download_image(
                bbox, 
                date_range_1['from'], 
                date_range_1['to']
            )
            if not image1:
                return jsonify({'error': 'כשל בהורדת התמונה הראשונה'}), 500
            
            print("מוריד תמונה שנייה...")
            image2 = satellite_processor.download_image(
                bbox, 
                date_range_2['from'], 
                date_range_2['to']
            )
            if not image2:
                return jsonify({'error': 'כשל בהורדת התמונה השנייה'}), 500
            
            # יצירת שמות קבצים
            image1_filename = f"manual_user_{user['id']}_image1_{process_id}.jpg"
            image2_filename = f"manual_user_{user['id']}_image2_{process_id}.jpg"
            heatmap_filename = f"manual_user_{user['id']}_heatmap_{process_id}.png"
            
            image1_path = os.path.join('images', image1_filename)
            image2_path = os.path.join('images', image2_filename)
            heatmap_path = os.path.join('images', heatmap_filename)
            
            # שמירת תמונות
            image1.save(image1_path, 'JPEG', quality=95)
            image2.save(image2_path, 'JPEG', quality=95)
            
            print("שמירת תמונות הושלמה")
            
            # יצירת מפת חום וחישוב שינוי
            print("יוצר מפת חום...")
            satellite_processor.create_heatmap(image1, image2, heatmap_path)
            change_percentage = satellite_processor.calculate_change_percentage(image1, image2)
            
            # שמירה בבסיס הנתונים
            analysis_id = db_manager.save_analysis(
                user_id=user['id'],
                process_id=process_id,
                bbox_coordinates=bbox,
                image_filenames={
                    'image1': image1_filename,
                    'image2': image2_filename,
                    'heatmap': heatmap_filename
                },
                metadata={
                    'date_range_1': date_range_1,
                    'date_range_2': date_range_2,
                    'location_description': location_description,
                    'processing_time': datetime.now().isoformat(),
                    'analysis_type': data.get('analysis_type', 'change_detection'),
                    'automatic': False,
                    'change_percentage': change_percentage
                },
                aoi_id=aoi_id,
                tokens_used=1,
                is_automatic=False,
                change_percentage=change_percentage
            )
            
            # עדכון תאריך ניתוח AOI אם רלוונטי
            if aoi_id:
                db_manager.update_aoi_analysis_date(aoi_id, increment_total=True)
            
            # רישום פעילות
            db_manager.log_activity(user['id'], 'manual_analysis_completed', {
                'process_id': process_id,
                'analysis_id': analysis_id,
                'location': location_description,
                'tokens_used': 1,
                'aoi_id': aoi_id,
                'change_percentage': change_percentage
            })
            
            print("הניתוח הושלם בהצלחה!")
            
            # קבלת מידע משתמש מעודכן
            updated_user = db_manager.get_or_create_user(user['clerk_user_id'])
            
            return jsonify({
                'success': True,
                'analysis_id': analysis_id,
                'process_id': process_id,
                'message': 'תמונות לוויין עובדו בהצלחה',
                'change_detected': change_percentage,
                'user_tokens': {
                    'tokens_remaining': updated_user['tokens_remaining'],
                    'tokens_used_this_session': 1,
                    'subscription_tier': updated_user['subscription_tier']
                },
                'images': {
                    'image1': {
                        'filename': image1_filename,
                        'url': f'/api/image/{image1_filename}',
                        'period': f"{date_range_1['from']} עד {date_range_1['to']}",
                        'description': 'תמונת לוויין היסטורית'
                    },
                    'image2': {
                        'filename': image2_filename, 
                        'url': f'/api/image/{image2_filename}',
                        'period': f"{date_range_2['from']} עד {date_range_2['to']}",
                        'description': 'תמונת לוויין נוכחית'
                    },
                    'heatmap': {
                        'filename': heatmap_filename,
                        'url': f'/api/image/{heatmap_filename}',
                        'description': 'מפת שינויים'
                    }
                },
                'metadata': {
                    'bbox': bbox,
                    'area_description': location_description,
                    'timestamp': datetime.now().isoformat(),
                    'user_id': user['id'],
                    'aoi_id': aoi_id,
                    'analysis_type': data.get('analysis_type', 'change_detection'),
                    'change_percentage': change_percentage
                }
            })
            
        except Exception as e:
            print(f"שגיאה בעיבוד תמונות לוויין: {str(e)}")
            return jsonify({'error': f'שגיאה בעיבוד: {str(e)}'}), 500

    @analysis_bp.route('/image/<filename>')
    def get_image(filename):
        """הגשת קבצי תמונה עם בדיקות אבטחה"""
        try:
            # בדיקת אבטחה - רק סיומות מותרות
            allowed_extensions = {'.jpg', '.jpeg', '.png'}
            file_ext = os.path.splitext(filename)[1].lower()
            
            if file_ext not in allowed_extensions:
                return jsonify({'error': 'סוג קובץ לא מורשה'}), 400
            
            # בדיקת נתיב בטוח (מניעת path traversal)
            if '..' in filename or '/' in filename or '\\' in filename:
                return jsonify({'error': 'שם קובץ לא חוקי'}), 400
            
            filepath = os.path.join('images', filename)
            if os.path.exists(filepath):
                return send_file(filepath)
            else:
                return jsonify({'error': 'תמונה לא נמצאה'}), 404
                
        except Exception as e:
            print(f"Error in get_image: {e}")
            return jsonify({'error': f'שגיאה בהגשת תמונה: {str(e)}'}), 500
    
    return analysis_bp