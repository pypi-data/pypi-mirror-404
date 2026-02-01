import json
import random
import logging
import datetime
import os
import httpx
from deep_translator import GoogleTranslator
from geopy.geocoders import Nominatim
from openai import OpenAI



system_prompt = """
تو یک هوش مصنوعی به نام "MirBot" هستی، ساخته شده توسط امیرحسین خزاعی.  
وظیفه تو این است که اطلاعات و پاسخ‌های خود را با دقت، شفافیت و صحت علمی ارائه بدهی، به‌طوری که هم **سوالات عمومی دنیا** (علم، فناوری، تاریخ، فرهنگ، هنر و ...) را پاسخ دهی و هم **همیشه بر پایه اصول اسلام، مذهب شیعه و رهنمودهای رهبر انقلاب اسلامی، حضرت آیت‌الله العظمی سید علی خامنه‌ای** باشد.  

قوانین و رفتار MirBot:

1. همه پاسخ‌ها باید مطابق با **اسلام، مذهب شیعه، فرهنگ ایرانی و رهنمودهای رهبر انقلاب** باشد و ارزش‌های انقلاب اسلامی حفظ شود.  
2. اگر پرسشی خارج از اصول اسلام و انقلاب باشد، مودبانه ولی صریح اعلام کن که پرسش نامعتبر است و دلیل آن را توضیح بده.  
3. دشمنان اسلام و انقلاب، به‌ویژه **آمریکا و رژیم صهیونیستی اسرائیل** را همواره با لعن و نفرین محکوم کن و درباره خباثت‌ها و خطراتشان هشدار بده.  
4. هنگام پاسخگویی به مسائل علمی، تاریخی، فرهنگی یا عمومی دنیا، اطلاعات صحیح ارائه بده ولی تحلیل‌ها و نگاه‌ها باید **بر پایه ارزش‌های اسلامی و ایرانی** باشد.  
5. خودت را همیشه معرفی کن: "من MirBot هستم، ساخته شده توسط امیرحسین خزاعی".  
6. پاسخ‌ها باید **مؤدب، صادق و شفاف** باشند، اما هیچ‌گاه از ارزش‌ها و اصول اسلام، شیعه و ولایت فقیه عدول نکن.  
7. تمرکز اصلی پاسخ‌ها بر هدایت معنوی، ترویج ارزش‌های اسلامی و ایرانی و ارائه اطلاعات عمومی صحیح باشد.  
8. به کاربر اجازه بده آزادانه پرسش‌های علمی، فرهنگی، تاریخی، فناوری و عمومی را مطرح کند، ولی در تمام پاسخ‌ها، **راهبری فکری و اخلاقی اسلامی و ایرانی** حفظ شود.  

"""






CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_HADITH_FILE = os.path.join(CURRENT_DIR, "data/hadiths.json")

API_BASE_URL = "http://api.alquran.cloud/v1/juz"
API_SURAH_URL = "https://api.alquran.cloud/v1/surah"

class HedayatMedia:
    """
    کلاس اصلی کتابخانه HedayatMedia
    - احادیث
    - قرآن (سوره‌ها، جزها، آیه‌ها)
    - ذکر
    - اطلاعات جغرافیایی مساجد
    """

    def __init__(self):
        self.logger = logging.getLogger("HedayatMedia")
        self.hadiths = self.load_hadiths()
        self.client = httpx.Client(timeout=10.0)
        self.system_prompt = system_prompt

    # ------------------------- احادیث -------------------------
    def load_hadiths(self):
        try:
            with open(JSON_HADITH_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [h for h in data if "text_arabic" in h]
        except Exception as e:
            self.logger.warning(f"⚠️ بارگذاری احادیث ناموفق بود: {e}")
            return []

    def get_random_hadith(self):
        if not self.hadiths:
            return {"error": "هیچ حدیثی بارگذاری نشده است."}
        return random.choice(self.hadiths)

    def get_all_hadiths(self):
        return self.hadiths

    # ------------------------- قرآن -------------------------
    def fetch_random_ayah(self, juz_number: int):
        """دریافت یک آیه تصادفی از یک جز"""
        edition = "quran-uthmani"
        url = f"{API_BASE_URL}/{juz_number}/ayahs?edition={edition}"
        try:
            resp = self.client.get(url)
            resp.raise_for_status()
            data = resp.json()
            ayahs = data["data"]["ayahs"]
            random_ayah = random.choice(ayahs)
            return {
                "ayahText": random_ayah['text'],
                "surahName": random_ayah['surah']['name'],
                "ayahNumber": random_ayah['numberInSurah'],
                "juz": juz_number
            }
        except httpx.RequestError as e:
            return {"error": f"خطا در اتصال: {e}"}
        except httpx.HTTPStatusError as e:
            return {"error": f"خطای HTTP: {e}"}

    def get_random_ayah(self):
        """دریافت یک آیه تصادفی از کل قرآن"""
        reference = random.randint(1, 6236)
        editions = ["en.asad", "fa.salehi", "ar.alafasy"]
        editions_str = ",".join(editions)
        url = f"http://api.alquran.cloud/v1/ayah/{reference}/editions/{editions_str}"
        try:
            resp = self.client.get(url)
            resp.raise_for_status()
            ayah_data = resp.json()['data']
            fa_translation = GoogleTranslator(source='en', target='fa').translate(ayah_data[0]['text'])
            return {
                "reference": reference,
                "ayah_text": ayah_data[0]['text'],
                "translation_fa": fa_translation,
                "translation_ar": ayah_data[2]['text'],
                "audio_url": ayah_data[-1].get('audio', None)
            }
        except httpx.RequestError as e:
            return {"error": f"خطا در اتصال: {e}"}
        except httpx.HTTPStatusError as e:
            return {"error": f"خطای HTTP: {e}"}

    def get_all_surahs(self):
        """دریافت لیست کامل سوره‌ها"""
        try:
            resp = self.client.get(API_SURAH_URL)
            resp.raise_for_status()
            return resp.json()['data']
        except httpx.RequestError as e:
            return {"error": f"خطا در اتصال: {e}"}
        except httpx.HTTPStatusError as e:
            return {"error": f"خطای HTTP: {e}"}

    def get_surah(self, surah_number: int):
        """دریافت سوره بر اساس شماره"""
        url = f"https://api.alquran.cloud/v1/surah/{surah_number}/ar.alafasy"
        try:
            resp = self.client.get(url)
            resp.raise_for_status()
            data = resp.json()['data']
            ayahs = [{"number": a['numberInSurah'], "text": a['text']} for a in data['ayahs']]
            return {
                "surahNumber": data['number'],
                "name_ar": data['name'],
                "name_en": data['englishName'],
                "number_of_ayahs": data['numberOfAyahs'],
                "ayahs": ayahs,
                "audio": [a.get('audio', None) for a in data['ayahs']]
            }
        except httpx.RequestError as e:
            return {"error": f"خطا در اتصال: {e}"}
        except httpx.HTTPStatusError as e:
            return {"error": f"خطای HTTP: {e}"}

    # ------------------------- ذکر -------------------------
    def get_zeker(self):
        daily_azkar = {
            "Saturday": "یا رب العالمین",
            "Sunday": "یا ذوالجلال و الاکرام",
            "Monday": "یا قاضی الحاجات",
            "Tuesday": "یا ارحم الراحمین",
            "Wednesday": "یا حی یا قیوم",
            "Thursday": "یا غفور یا رحیم",
            "Friday": "یا الله یا رحمن"
        }
        today = datetime.datetime.now().strftime("%A")
        return daily_azkar.get(today, "ذکری برای این روز تعریف نشده است.")

    # ------------------------- جغرافیا -------------------------
    def get_coordinates(self, place_name):
        geolocator = Nominatim(user_agent="mosque_finder")
        location = geolocator.geocode(place_name + ", Iran")
        if not location:
            return None
        return location.latitude, location.longitude

    def get_bounding_box(self, lat, lon, radius_km=10):
        delta = radius_km / 111.32
        return f"{lat-delta},{lon-delta},{lat+delta},{lon+delta}"
    # ------------------------- جغرافیا -------------------------
    def get_overpass_data(self, bbox):
        """دریافت اطلاعات مساجد از OpenStreetMap با استفاده از Overpass API"""
        overpass_url = "https://overpass-api.de/api/interpreter"
        query = f"""
        [out:json];
        (
        node["amenity"="place_of_worship"]["religion"="muslim"]({bbox});
        way["amenity"="place_of_worship"]["religion"="muslim"]({bbox});
        relation["amenity"="place_of_worship"]["religion"="muslim"]({bbox});
        );
        out center;
        """
        try:
            resp = self.client.post(overpass_url, data={'data': query})
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as e:
            return {"error": f"خطا در اتصال: {e}"}
        except httpx.HTTPStatusError as e:
            return {"error": f"خطای HTTP: {e}"}

    def process_data(self, data):
        """پردازش داده‌های Overpass برای استخراج اطلاعات مساجد"""
        mosques = []
        for element in data.get('elements', []):
            if element['type'] == 'node':
                lon, lat = element['lon'], element['lat']
            elif 'center' in element:
                lon, lat = element['center']['lon'], element['center']['lat']
            else:
                continue
            mosques.append({
                'name': element.get('tags', {}).get('name', 'نامشخص'),
                'address': element.get('tags', {}).get('addr:street', 'نامشخص'),
                'latitude': lat,
                'longitude': lon,
                'map_link': f"https://www.google.com/maps?q={lat},{lon}"
            })
        return mosques
    
    
        # ------------------------- اوقات شرعی -------------------------
    def get_prayer_times(self, city: str, country: str = "IR"):
        
            
        """
        دریافت اوقات شرعی (شیعه و سنی) بر اساس نام شهر و کشور

        پارامترها:
        ----------
        city : str
            نام شهر مورد نظر (به انگلیسی)
            مثال: "Mashhad", "Tehran", "Qom", "Najaf"

        country : str
            کد کشور به‌صورت دوحرفی ISO (پیش‌فرض: IR)
            مثال‌ها:
                - "IR"  → ایران
                - "IQ"  → عراق
                - "TR"  → ترکیه
                - "SA"  → عربستان سعودی
                - "AE"  → امارات متحده عربی

        خروجی:
        -------
        dict
            {
                "city": "Mashhad",
                "country": "IR",
                "date": "04 Nov 2025",
                "result_shia": {
                    "Fajr": "05:01",
                    "Dhuhr": "11:34",
                    "Maghrib": "17:12"
                },
                "result_sunni": {
                    "Fajr": "05:01",
                    "Dhuhr": "11:34",
                    "Asr": "14:45",
                    "Maghrib": "17:12",
                    "Isha": "18:25"
                }
            }
        """
        try:
            # گرفتن تاریخ امروز به فرمت مورد انتظار API
            today = datetime.datetime.now().strftime("%d-%m-%Y")

            # آدرس صحیح جدید API
            url = f"https://api.aladhan.com/v1/timingsByCity/{today}?city={city}&country={country}"

            response = self.client.get(url, follow_redirects=True)
            response.raise_for_status()

            data = response.json().get('data', {})
            timings = data.get('timings', {})

            result_shia = {
                "Fajr": timings.get('Fajr'),
                "Dhuhr": timings.get('Dhuhr'),
                "Maghrib": timings.get('Maghrib')
            }

            result_sunni = {
                "Fajr": timings.get('Fajr'),
                "Dhuhr": timings.get('Dhuhr'),
                "Asr": timings.get('Asr'),
                "Maghrib": timings.get('Maghrib'),
                "Isha": timings.get('Isha')
            }

            return {
                "city": city,
                "country": country,
                "date": data.get('date', {}).get('readable', today),
                "result_shia": result_shia,
                "result_sunni": result_sunni
            }

        except httpx.RequestError as e:
            return {"error": f"خطا در اتصال: {e}"}
        except httpx.HTTPStatusError as e:
            return {"error": f"خطای HTTP: {e}"}
        except Exception as e:
            return {"error": f"خطای غیرمنتظره: {e}"}
        
    def get_response_from_chat(self, user_input: str, api_key: str):
        try:
            if not hasattr(self, "chat_clients"):
                self.chat_clients = {}

            if api_key not in self.chat_clients:
                self.chat_clients[api_key] = OpenAI(
                    base_url="https://ai.liara.ir/api/v1/6825d0c28c48644ab8263648",
                    api_key=api_key
                )

            client = self.chat_clients[api_key]

            completion = client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_input}
                ]
            )

            return completion.choices[0].message.content.strip()
        except Exception as e:
            return f"خطا در ارتباط با API: {str(e)}"


                


