# auto_analysis.py - מנהל ניתוחים אוטומטיים
import os
import uuid
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

class AutoAnalysisManager:
    """מנהל ניתוחים אוטומטיים - בודק ומבצע ניתוחים לפי לוח זמנים"""
    
    def __init__(self, db_manager, satellite_processor):
        self.db_manager = db_manager
        self.satellite_processor = satellite_processor
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        
        # הגדרות ברירת מחדל
        self.check_interval_hours = 1  # בדיקה כל שעה
        self.max_analyses_per_run = 10  # מקסימום ניתוחים בכל הרצה
        
        print("🤖 מנהל ניתוחים אוטומטי אותחל")
    
    def start(self):
        """התחלת השירות האוטומטי"""
        if self.is_running:
            print("⚠️ השירות כבר פועל")
            return
        
        try:
            # הוספת משימה לבדיקה תקופתית
            self.scheduler.add_job(
                func=self.check_and_run_analyses,
                trigger=IntervalTrigger(hours=self.check_interval_hours),
                id='auto_analysis_checker',
                name='בודק ניתוחים אוטומטיים',
                replace_existing=True,
                max_instances=1  # מנע הפעלות כפולות
            )
            
            self.scheduler.start()
            self.is_running = True
            print(f"✅ שירות ניתוחים אוטומטי החל - בדיקה כל {self.check_interval_hours} שעות")
            
        except Exception as e:
            print(f"❌ שגיאה בהפעלת שירות אוטומטי: {e}")
    
    def stop(self):
        """עצירת השירות האוטומטי"""
        if not self.is_running:
            print("⚠️ השירות לא פועל")
            return
        
        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            print("✅ שירות ניתוחים אוטומטי נעצר")
        except Exception as e:
            print(f"❌ שגיאה בעצירת שירות אוטומטי: {e}")
    
    def check_and_run_analyses(self):
        """בדיקה והפעלת ניתוחים הדרושים"""
        try:
            print("🔄 בודק AOIs הזקוקים לניתוח אוטומטי...")
            
            # קבלת רשימת AOIs לניתוח
            aois_to_analyze = self.db_manager.get_aois_for_analysis()
            
            if not aois_to_analyze:
                print("📊 אין AOIs הזקוקים לניתוח כרגע")
                return
            
            print(f"🎯 נמצאו {len(aois_to_analyze)} AOIs זקוקים לניתוח")
            
            # הגבלת מספר הניתוחים
            analyses_to_run = aois_to_analyze[:self.max_analyses_per_run]
            if len(aois_to_analyze) > self.max_analyses_per_run:
                print(f"⚠️ מגביל ל-{self.max_analyses_per_run} ניתוחים בהרצה זו")
            
            # הפעלת ניתוחים
            successful_analyses = 0
            failed_analyses = 0
            
            for aoi_data in analyses_to_run:
                try:
                    success = self.run_automatic_analysis(aoi_data)
                    if success:
                        successful_analyses += 1
                    else:
                        failed_analyses += 1
                        
                except Exception as e:
                    print(f"❌ ניתוח אוטומטי נכשל עבור AOI {aoi_data['name']}: {e}")
                    failed_analyses += 1
                    continue
            
            print(f"📊 סיכום הרצה: {successful_analyses} מוצלחים, {failed_analyses} כשלונות")
                    
        except Exception as e:
            print(f"❌ שגיאה בבודק ניתוחים אוטומטי: {e}")
    
    def run_automatic_analysis(self, aoi_data):
        """הפעלת ניתוח אוטומטי עבור AOI ספציפי"""
        aoi_id = aoi_data['aoi_id']
        user_id = aoi_data['user_db_id']
        aoi_name = aoi_data['name']
        bbox = aoi_data['bbox_coordinates']
        
        print(f"🛰️ מתחיל ניתוח אוטומטי עבור: {aoi_name}")
        
        try:
            # בדיקה ושימוש בטוקנים
            success, message = self.db_manager.use_tokens(
                user_id, 
                1, 
                f"ניתוח אוטומטי: {aoi_name}"
            )
            
            if not success:
                print(f"💰 אין מספיק טוקנים עבור {aoi_name}: {message}")
                # עדכון תאריך ניתוח הבא לניסיון מאוחר יותר
                self.db_manager.update_aoi_analysis_date(aoi_id, increment_total=False)
                return False
            
            # יצירת טווחי תאריכים להשוואה
            date_ranges = self.generate_date_ranges()
            
            # הורדת תמונות
            print(f"📥 מוריד תמונה היסטורית עבור {aoi_name}")
            image1 = self.satellite_processor.download_image(
                bbox, 
                date_ranges['historical']['from'], 
                date_ranges['historical']['to']
            )
            
            if not image1:
                raise Exception("כשל בהורדת תמונה היסטורית")
            
            print(f"📥 מוריד תמונה עדכנית עבור {aoi_name}")
            image2 = self.satellite_processor.download_image(
                bbox, 
                date_ranges['recent']['from'], 
                date_ranges['recent']['to']
            )
            
            if not image2:
                raise Exception("כשל בהורדת תמונה עדכנית")
            
            # יצירת שמות קבצים
            process_id = str(uuid.uuid4())[:8]
            filenames = self.generate_filenames(user_id, process_id)
            
            # שמירת תמונות
            image1_path = os.path.join('images', filenames['image1'])
            image2_path = os.path.join('images', filenames['image2'])
            heatmap_path = os.path.join('images', filenames['heatmap'])
            
            image1.save(image1_path, 'JPEG', quality=95)
            image2.save(image2_path, 'JPEG', quality=95)
            
            # יצירת מפת חום וחישוב שינוי
            print(f"🔥 יוצר מפת חום עבור {aoi_name}")
            self.satellite_processor.create_heatmap(image1, image2, heatmap_path)
            change_percentage = self.satellite_processor.calculate_change_percentage(image1, image2)
            
            # שמירת תוצאות
            metadata = {
                'date_range_1': date_ranges['historical'],
                'date_range_2': date_ranges['recent'],
                'location_description': aoi_name,
                'processing_time': datetime.now().isoformat(),
                'analysis_type': aoi_data['analysis_type'],
                'automatic': True,
                'change_percentage': change_percentage
            }
            
            analysis_id = self.db_manager.save_analysis(
                user_id=user_id,
                process_id=process_id,
                bbox_coordinates=bbox,
                image_filenames=filenames,
                metadata=metadata,
                aoi_id=aoi_id,
                tokens_used=0,
                is_automatic=True,
                change_percentage=change_percentage
            )
            
            # עדכון תאריכי ניתוח של AOI
            self.db_manager.update_aoi_analysis_date(aoi_id, increment_total=True)
            
            # רישום פעילות
            self.db_manager.log_activity(user_id, 'automatic_analysis_completed', {
                'aoi_id': aoi_id,
                'aoi_name': aoi_name,
                'analysis_id': analysis_id,
                'change_percentage': change_percentage,
                'process_id': process_id
            }, description=f"ניתוח אוטומטי הושלם עבור {aoi_name}")
            
            print(f"✅ ניתוח אוטומטי הושלם עבור {aoi_name} - שינוי: {change_percentage:.2f}%")
            
            # בדיקת שינוי משמעותי
            if change_percentage > 10.0:
                print(f"🚨 זוהה שינוי משמעותי ב-{aoi_name}: {change_percentage:.2f}%")
                # כאן אפשר להוסיף התרעות (email, webhook, וכו')
            
            return True
            
        except Exception as e:
            print(f"❌ ניתוח אוטומטי נכשל עבור {aoi_name}: {e}")
            # עדכון תאריך לניסיון מאוחר יותר
            self.db_manager.update_aoi_analysis_date(aoi_id, increment_total=False)
            return False
    
    def generate_date_ranges(self):
        """יצירת טווחי תאריכים להשוואה"""
        end_date = datetime.now()
        
        # תאריך עדכני - 30 הימים האחרונים
        start_date_recent = end_date - timedelta(days=30)
        
        # תאריך היסטורי - לפני 60-90 ימים
        start_date_historical = end_date - timedelta(days=90)
        end_date_historical = end_date - timedelta(days=60)
        
        return {
            'historical': {
                'from': start_date_historical.strftime('%Y-%m-%d'),
                'to': end_date_historical.strftime('%Y-%m-%d')
            },
            'recent': {
                'from': start_date_recent.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d')
            }
        }
    
    def generate_filenames(self, user_id, process_id):
        """יצירת שמות קבצים ייחודיים"""
        return {
            'image1': f"auto_user_{user_id}_image1_{process_id}.jpg",
            'image2': f"auto_user_{user_id}_image2_{process_id}.jpg",
            'heatmap': f"auto_user_{user_id}_heatmap_{process_id}.png"
        }
    
    def get_status(self):
        """קבלת מצב השירות"""
        return {
            'is_running': self.is_running,
            'check_interval_hours': self.check_interval_hours,
            'max_analyses_per_run': self.max_analyses_per_run,
            'scheduler_running': self.scheduler.running if hasattr(self.scheduler, 'running') else False
        }
    
    def force_analysis_for_aoi(self, aoi_id):
        """הפעלת ניתוח מיידי עבור AOI ספציפי (לטסטים)"""
        try:
            # קבלת נתוני AOI
            aois = self.db_manager.get_aois_for_analysis()
            aoi_data = next((aoi for aoi in aois if aoi['aoi_id'] == aoi_id), None)
            
            if not aoi_data:
                return False, "AOI לא נמצא או לא זמין לניתוח"
            
            success = self.run_automatic_analysis(aoi_data)
            return success, "ניתוח הושלם" if success else "ניתוח נכשל"
            
        except Exception as e:
            return False, f"שגיאה: {e}"
    
    def cleanup_old_images(self, days_old=30):
        """ניקוי תמונות ישנות (אופציונלי)"""
        try:
            images_dir = 'images'
            if not os.path.exists(images_dir):
                return
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            deleted_count = 0
            
            for filename in os.listdir(images_dir):
                filepath = os.path.join(images_dir, filename)
                
                if os.path.isfile(filepath):
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    
                    if file_time < cutoff_date:
                        try:
                            os.remove(filepath)
                            deleted_count += 1
                        except Exception as e:
                            print(f"❌ לא ניתן למחוק {filename}: {e}")
            
            print(f"🧹 נוקו {deleted_count} תמונות ישנות")
            
        except Exception as e:
            print(f"❌ שגיאה בניקוי תמונות: {e}")
    
    def __del__(self):
        """ניקוי משאבים בסגירה"""
        if self.is_running:
            try:
                self.stop()
            except:
                pass