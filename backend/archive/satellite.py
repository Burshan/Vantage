# satellite.py - מעבד תמונות לוויין
import requests
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO
import os

class SatelliteProcessor:
    """מחלקה לעיבוד תמונות לוויין מ-Sentinel Hub"""
    
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.base_url = "https://services.sentinel-hub.com"
        
        # וודא שתיקיית images קיימת
        os.makedirs('images', exist_ok=True)
        
    def get_access_token(self):
        """קבלת access token מ-Sentinel Hub"""
        token_url = f"{self.base_url}/oauth/token"
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = requests.post(token_url, data=data, timeout=30)
            if response.status_code == 200:
                self.access_token = response.json()['access_token']
                print("✅ התחברות מוצלחת ל-Sentinel Hub")
                return True
            else:
                print(f"❌ כשל בקבלת access token: {response.status_code}")
                print(f"תשובה: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ שגיאת רשת בהתחברות ל-Sentinel Hub: {e}")
            return False
    
    def download_image(self, bbox, date_from, date_to, width=1024, height=1024):
        """הורדת תמונת לוויין מ-Sentinel Hub"""
        if not self.access_token:
            if not self.get_access_token():
                return None
                
        evalscript = """
        //VERSION=3
        function setup() {
            return {
                input: [{
                    bands: ["B02", "B03", "B04"]
                }],
                output: {
                    bands: 3,
                    sampleType: "AUTO"
                }
            };
        }

        function evaluatePixel(sample) {
            return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02];
        }
        """

        payload = {
            "input": {
                "bounds": {
                    "bbox": bbox,
                    "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
                },
                "data": [{
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {
                            "from": f"{date_from}T00:00:00Z",
                            "to": f"{date_to}T23:59:59Z"
                        },
                        "maxCloudCoverage": 20
                    }
                }]
            },
            "output": {
                "width": width,
                "height": height,
                "responses": [{
                    "identifier": "default",
                    "format": {
                        "type": "image/jpeg"
                    }
                }]
            },
            "evalscript": evalscript
        }
        
        url = f"{self.base_url}/api/v1/process"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                print(f"✅ הורדת תמונה מוצלחת עבור {date_from} עד {date_to}")
                return image
            else:
                print(f"❌ שגיאה בהורדת תמונה: {response.status_code}")
                print(f"תשובה: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ שגיאת רשת בהורדת תמונה: {e}")
            return None
        except Exception as e:
            print(f"❌ שגיאה כללית בהורדת תמונה: {e}")
            return None
    
    def create_heatmap(self, image1, image2, filename):
        """יצירת מפת חום של שינויים בין שתי תמונות"""
        try:
            img1_array = np.array(image1)
            img2_array = np.array(image2)
            
            if img1_array.shape != img2_array.shape:
                print("❌ התמונות בגדלים שונים, לא ניתן ליצור מפת חום")
                return None
            
            # חישוב הפרש
            diff = np.abs(img1_array.astype(float) - img2_array.astype(float))
            
            # המרה לגוונים אפורים אם צריך
            if len(diff.shape) == 3:
                diff_gray = np.mean(diff, axis=2)
            else:
                diff_gray = diff
            
            # יצירת התמונה
            fig, ax = plt.subplots(1, 1, figsize=(12, 12), dpi=150)
            
            # הדגשת שינויים משמעותיים
            threshold = np.percentile(diff_gray, 75)
            enhanced_diff = np.where(diff_gray > threshold, diff_gray, 0)
            
            # יצירת מפת החום
            im = ax.imshow(enhanced_diff, cmap='hot', interpolation='bilinear')
            
            # הוספת כותרת
            ax.set_title('מפת שינויים - Change Detection Heatmap', 
                        fontsize=18, fontweight='bold', pad=20)
            ax.axis('off')
            
            # הוספת סרגל צבעים
            cbar = plt.colorbar(im, ax=ax, shrink=0.8, aspect=20)
            cbar.set_label('עוצמת השינוי - Change Intensity', 
                          rotation=270, labelpad=20, fontsize=12)
            
            # שמירה
            plt.tight_layout()
            plt.savefig(filename, dpi=200, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close()
            
            print(f"✅ נוצרה מפת חום: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ שגיאה ביצירת מפת חום: {e}")
            return None
    
    def calculate_change_percentage(self, image1, image2):
        """חישוב אחוז השינוי בין שתי תמונות"""
        try:
            img1_array = np.array(image1)
            img2_array = np.array(image2)
            
            if img1_array.shape != img2_array.shape:
                print("❌ התמונות בגדלים שונים")
                return 0.0
            
            # חישוב הפרש
            diff = np.abs(img1_array.astype(float) - img2_array.astype(float))
            
            # המרה לגוונים אפורים אם צריך
            if len(diff.shape) == 3:
                diff_gray = np.mean(diff, axis=2)
            else:
                diff_gray = diff
            
            # חישוב אחוז הפיקסלים שהשתנו באופן משמעותי
            threshold = 30  # סף לשינוי משמעותי
            changed_pixels = np.sum(diff_gray > threshold)
            total_pixels = diff_gray.size
            
            change_percentage = (changed_pixels / total_pixels) * 100
            return round(change_percentage, 2)
            
        except Exception as e:
            print(f"❌ שגיאה בחישוב אחוז שינוי: {e}")
            return 0.0
    
    def save_image(self, image, filename, quality=95):
        """שמירת תמונה לדיסק"""
        try:
            filepath = os.path.join('images', filename)
            image.save(filepath, 'JPEG', quality=quality)
            print(f"✅ תמונה נשמרה: {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ שגיאה בשמירת תמונה: {e}")
            return None
    
    def validate_bbox(self, bbox):
        """בדיקת תקינות קואורדינטות"""
        if not isinstance(bbox, list) or len(bbox) != 4:
            return False, "bbox צריך להיות רשימה של 4 מספרים"
        
        try:
            lat_min, lon_min, lat_max, lon_max = bbox
            
            # בדיקת טווחים
            if not (-90 <= lat_min <= 90) or not (-90 <= lat_max <= 90):
                return False, "קו רוחב צריך להיות בין -90 ל-90"
            
            if not (-180 <= lon_min <= 180) or not (-180 <= lon_max <= 180):
                return False, "קו אורך צריך להיות בין -180 ל-180"
            
            # בדיקה שמינימום קטן ממקסימום
            if lat_min >= lat_max:
                return False, "קו רוחב מינימלי צריך להיות קטן ממקסימלי"
            
            if lon_min >= lon_max:
                return False, "קו אורך מינימלי צריך להיות קטן ממקסימלי"
            
            return True, "קואורדינטות תקינות"
            
        except (ValueError, TypeError):
            return False, "קואורדינטות צריכות להיות מספרים"
    
    def get_image_info(self, image):
        """קבלת מידע על תמונה"""
        try:
            return {
                'size': image.size,
                'mode': image.mode,
                'format': image.format,
                'width': image.width,
                'height': image.height
            }
        except Exception as e:
            print(f"❌ שגיאה בקבלת מידע תמונה: {e}")
            return None