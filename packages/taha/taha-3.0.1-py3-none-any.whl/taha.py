"""
بسم الله الرحمان الرحیم

اللَّهُمَّ صَلِّ عَلَى عَلِيِّ بْنِ مُوسَى الرِّضَا الْمُرْتَضَى

الْإِمَامِ التَّقِيِّ النَّقِي وَ حُجَّتِكَ عَلَى مَنْ فَوْقَ الْأَرْضِ

وَ مَنْ تَحْتَ الثَّرَى الصِّدِّيقِ الشَّهِيدِ

صَلاَةً كَثِيرَةً تَامَّةً زَاكِيَةً مُتَوَاصِلَةً مُتَوَاتِرَةً مُتَرَادِفَةً

كَأَفْضَلِ مَا صَلَّيْتَ عَلَى أَحَدٍ مِنْ أَوْلِيَائِكَ
"""

import sys
import os
import time
import random
import string
import datetime
import pytz
import jwt
from cryptography.fernet import Fernet
from functools import wraps
from pathlib import Path

print("📦 Taha Library v3.0.2 - Premium Edition")


class LicenseManager:
    """
    مدیریت لایسنس با JWT و RS256
    """

    def check_license(self):
        """
        بررسی اعتبار لایسنس
        """
        sys.modules.pop('taha', None)  # جلوگیری از cache
        try:
            with open("public_key.pem", "rb") as f:
                public_key = f.read()

            with open("buyer_license.jwt", "r", encoding="utf-8") as license_file:
                token = license_file.read().strip()

            jwt.decode(token, public_key, algorithms=["RS256"])
            return True, "لایسنس معتبر است ✅"
        except FileNotFoundError:
            return False, "فایل لایسنس یا کلید عمومی یافت نشد ❌"
        except jwt.ExpiredSignatureError:
            return False, "لایسنس منقضی شده است ⏳"
        except jwt.InvalidTokenError:
            return False, "لایسنس نامعتبر است 🔒"
        except Exception as e:
            return False, f"خطا در بررسی لایسنس: {e}"

    def premium_required(self, func):
        """
        دکوراتور برای محدود کردن دسترسی به توابع پریمیوم
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            is_valid, message = self.check_license()
            if not is_valid:
                print(f"🔒 نیاز به لایسنس پریمیوم: {message}")
                return None
            return func(*args, **kwargs)

        return wrapper


license_manager = LicenseManager()


class Audio:
    """
    کلاس مدیریت صدا (پخش، تشخیص، تبدیل متن به صوت)
    """

    def __init__(self):
        self.engine = None
        self.recognizer = None

    @license_manager.premium_required
    def speak(self, text, lang="auto", speed=1.0):
        """
        تبدیل متن به صوت با gTTS و پخش با pygame
        ذخیره در Downloads با نام یکتا
        """
        try:
            from gtts import gTTS, lang as gtts_langs
            import pygame

            if lang == "auto":
                lang = "fa" if any('\u0600' <= ch <= '\u06FF' for ch in text) else "en"

            supported_langs = gtts_langs.tts_langs()
            if lang not in supported_langs:
                fallback = "ar" if lang == "fa" else "en"
                print(f"[!] زبان '{lang}' پشتیبانی نمی‌شود. استفاده از '{fallback}'")
                lang = fallback

            downloads = Utils.get_downloads_dir()
            downloads.mkdir(parents=True, exist_ok=True)
            filename = Utils.get_unique_filename(base_name="voice", ext=".mp3", folder=downloads)

            tts = gTTS(text=text, lang=lang, slow=(speed < 1.0))
            tts.save(str(filename))

            pygame.mixer.init()
            pygame.mixer.music.load(str(filename))
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

            print(f"✅ صوت در {filename} ذخیره شد")
            return str(filename)

        except Exception as e:
            print(f"خطا در speak: {e}")
            return None

    @license_manager.premium_required
    def speech_to_text(self, timeout=10, language="fa-IR"):
        """
        تشخیص صوت به متن با Google Speech Recognition
        """
        if self.recognizer is None:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()

        try:
            with sr.Microphone() as source:
                print("🎤 در حال گوش دادن...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=15)

            try:
                text = self.recognizer.recognize_google(audio, language=language)
                print(f"📝 متن: {text}")
                return text
            except:
                if language != "en-US":
                    text = self.recognizer.recognize_google(audio, language="en-US")
                    print(f"📝 متن (انگلیسی): {text}")
                    return text
                raise

        except sr.WaitTimeoutError:
            return "⏰ زمان به پایان رسید"
        except sr.UnknownValueError:
            return "❌ صدای واضحی تشخیص داده نشد"
        except sr.RequestError as e:
            return f"❌ خطا در سرویس: {e}"
        except Exception as e:
            return f"❌ خطای ناشناخته: {e}"

    @license_manager.premium_required
    def play_mp3(self, path):
        """
        پخش فایل MP3 با pygame
        """
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
        except Exception as e:
            print(f"خطا در پخش MP3: {e}")

    def text_to_speech(self, text):
        """
        تبدیل متن به صوت آفلاین با pyttsx3 (رایگان)
        """
        if self.engine is None:
            import pyttsx3
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty('voices')
            self.engine.setProperty('voice', voices[0].id)
            self.engine.setProperty('rate', 150)

        self.engine.say(text)
        self.engine.runAndWait()


class Security:
    """
    کلاس مدیریت امنیت (رمزنگاری، تولید رمز)
    """

    @license_manager.premium_required
    def encrypt_file(self, file_path, key=None):
        """
        رمزگذاری فایل با Fernet
        """
        try:
            if key is None:
                key = Fernet.generate_key()

            cipher = Fernet(key)

            with open(file_path, 'rb') as f:
                data = f.read()

            encrypted = cipher.encrypt(data)
            encrypted_path = file_path + ".encrypted"
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted)

            print(f"✅ رمزگذاری شد: {encrypted_path}")
            print(f"🔑 کلید: {key.decode()}")
            return key.decode()

        except Exception as e:
            print(f"❌ خطا در رمزگذاری: {e}")
            return None

    @license_manager.premium_required
    def decrypt_file(self, encrypted_path, key, output_path=None):
        """
        رمزگشایی فایل
        """
        try:
            cipher = Fernet(key.encode())

            with open(encrypted_path, 'rb') as f:
                data = f.read()

            decrypted = cipher.decrypt(data)

            if output_path is None:
                output_path = encrypted_path.replace(".encrypted", ".decrypted")

            with open(output_path, 'wb') as f:
                f.write(decrypted)

            print(f"✅ رمزگشایی شد: {output_path}")
            return output_path

        except Exception as e:
            print(f"❌ خطا در رمزگشایی: {e}")
            return None

    def generate_password(self, length=12, strength="strong"):
        """
        تولید رمز عبور (رایگان)
        """
        if strength == "simple":
            chars = string.ascii_lowercase
        elif strength == "medium":
            chars = string.ascii_letters + string.digits
        else:
            chars = string.ascii_letters + string.digits + string.punctuation
        return ''.join(random.choice(chars) for _ in range(length))


class AI:
    """
    کلاس مدیریت هوش مصنوعی (چت، دستیار صوتی)
    """

    def __init__(self):
        self.audio = Audio()

    @license_manager.premium_required
    def ai_chat(self, prompt, model="gpt2", max_length=100):
        """
        چت با مدل محلی (نیاز به transformers)
        """
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM

            tokenizer = AutoTokenizer.from_pretrained(model)
            model_obj = AutoModelForCausalLM.from_pretrained(model)

            inputs = tokenizer.encode(prompt, return_tensors="pt")
            outputs = model_obj.generate(inputs, max_length=max_length, num_return_sequences=1)

            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response
        except Exception as e:
            return f"خطا در هوش مصنوعی: {e}"

    @license_manager.premium_required
    def voice_assistant(self, wake_word="تاحا"):
        """
        دستیار صوتی کامل
        """
        print(f"🎧 دستیار فعال. بگو '{wake_word}'...")

        while True:
            command = self.audio.speech_to_text(language="fa-IR")

            if command and wake_word.lower() in command.lower():
                print(f"🔔 دستور: {command}")

                if "خاموش" in command or "خداحافظ" in command:
                    self.audio.speak("خداحافظ!")
                    break
                elif "ساعت" in command:
                    current_time = datetime.datetime.now().strftime("%H:%M")
                    self.audio.speak(f"ساعت {current_time} است")
                elif "تاریخ" in command:
                    current_date = Utils.today("%Y/%m/%d")
                    self.audio.speak(f"امروز {current_date} است")
                elif "جستجو" in command:
                    query = command.replace("جستجو", "").replace(wake_word, "").strip()
                    Utils.google_search(query)
                    self.audio.speak(f"جستجو برای {query}")
                else:
                    response = self.ai_chat(command)
                    self.audio.speak(response)

        print("دستیار غیرفعال شد")


class SystemUtils:
    """
    کلاس مدیریت سیستم (بهینه‌سازی، اطلاعات)
    """

    @license_manager.premium_required
    def optimizer(self):
        """
        بهینه‌سازی سیستم (پاک تمپ و GC)
        """
        try:
            print("🔄 بهینه‌سازی...")

            if os.name == 'nt':
                os.system('del /q /f /s %temp%\\* >nul 2>&1')
                print("✅ تمپ پاک شد")

            import psutil
            ram_before = psutil.virtual_memory().percent
            print(f"🎯 RAM قبل: {ram_before}%")

            import gc
            gc.collect()

            ram_after = psutil.virtual_memory().percent
            print(f"🎯 RAM بعد: {ram_after}%")

            return True

        except Exception as e:
            print(f"❌ خطا: {e}")
            return False

    def get_summary(self):
        """
        خلاصه اطلاعات سیستم (رایگان)
        """
        try:
            import platform
            import psutil
            import socket

            return {
                "os": platform.system() + " " + platform.release(),
                "cpu": platform.processor(),
                "ram": f"{round(psutil.virtual_memory().total / (1024 ** 3))} GB",
                "python_version": platform.python_version(),
                "ip_address": socket.gethostbyname(socket.gethostname()),
                "timezone": datetime.datetime.now(pytz.timezone("Asia/Tehran")).tzname()
            }
        except Exception as e:
            return {"error": str(e)}

    def system_control(self, action):
        """
        کنترل سیستم (خاموش، ری‌استارت)
        """
        if action == "shut_down":
            os.system("shutdown /s /t 0")
        elif action == "restart":
            os.system("shutdown /r /t 1")
        elif action == "log_out":
            os.system("shutdown -l")
        elif action == "sleep":
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")


class WebUtils:
    """
    کلاس مدیریت وب (اسکرپینگ، جستجو)
    """

    @license_manager.premium_required
    def scraper(self, url, extract_images=False):
        """
        استخراج اطلاعات از وبسایت
        """
        try:
            import requests
            from bs4 import BeautifulSoup

            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            title = soup.title.string if soup.title else "بدون عنوان"
            text_content = soup.get_text()[:500] + "..."

            results = {"title": title, "content": text_content}

            if extract_images:
                images = soup.find_all('img')
                image_urls = [img.get('src') for img in images if img.get('src')]
                results["images"] = image_urls
                print(f"🖼️ تصاویر: {len(image_urls)} تا")

            return results

        except Exception as e:
            print(f"❌ خطا در اسکرپ: {e}")
            return None

    def google_search(self, text):
        """
        جستجو در گوگل (رایگان)
        """
        import webbrowser
        webbrowser.open(f"https://www.google.com/search?q={text}")


class Graphics:
    """
    کلاس مدیریت گرافیک (تصویر، turtle)
    """

    def to_gray(self, path, out="gray.png"):
        """
        تبدیل تصویر به خاکستری
        """
        from PIL import Image
        img = Image.open(path).convert("L")
        img.save(out)
        print(f"✅ ذخیره شد: {out}")

    def convert_jpg(self, new_format, new_name, image_path):
        """
        تبدیل فرمت تصویر
        """
        from PIL import Image
        img = Image.open(image_path)
        img.save(f"{new_name}.{new_format}")

    def upload_gif(self, name_or_path):
        """
        بارگذاری GIF به عنوان شکل turtle
        """
        import turtle as t
        screen = t.Screen()
        screen.register_shape(name_or_path)
        img_turtle = t.Turtle()
        img_turtle.shape(name_or_path)
        img_turtle.penup()
        img_turtle.goto(0, 0)
        return img_turtle

    # دیگر توابع turtle مثل key, click, move, randcolor و ... رو به صورت متدهای کلاس اضافه کن
    def randcolor(self):
        """
        رنگ رندوم برای turtle
        """
        import turtle as t
        t.colormode(255)
        t.color((random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))


class Camera:
    """
    کلاس مدیریت دوربین (عکس، ویدیو، تشخیص صورت)
    - جدید اضافه شده برای بهبود رتبه پروژه به اول کشور/جهان
    - استفاده از OpenCV برای قابلیت‌های پیشرفته
    - ویژگی‌ها: عکس گرفتن، ضبط ویدیو، تشخیص صورت
    """
    def __init__(self):
        try:
            import cv2
            self.cv2 = cv2
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            self.cap = None
        except ImportError:
            print("❌ OpenCV نصب نیست. pip install opencv-python")
            self.cv2 = None

    @license_manager.premium_required
    def open_camera(self, show=True):
        """
        باز کردن دوربین و نمایش ویدیو زنده
        """
        if self.cv2 is None:
            return "❌ OpenCV در دسترس نیست"

        self.cap = self.cv2.VideoCapture(0)
        if not self.cap.isOpened():
            return "❌ نمی‌توان دوربین را باز کرد"

        print("🎥 دوربین باز شد. برای خروج Q فشار دهید.")

        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            if show:
                self.cv2.imshow('Camera', frame)

            if self.cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.close_camera()
        return "✅ دوربین بسته شد"

    @license_manager.premium_required
    def take_photo(self, output="photo.jpg"):
        """
        عکس گرفتن از دوربین
        """
        if self.cv2 is None:
            return "❌ OpenCV در دسترس نیست"

        self.cap = self.cv2.VideoCapture(0)
        ret, frame = self.cap.read()
        if ret:
            self.cv2.imwrite(output, frame)
            print(f"📸 عکس ذخیره شد: {output}")
            self.close_camera()
            return output
        self.close_camera()
        return "❌ خطا در عکس گرفتن"

    @license_manager.premium_required
    def record_video(self, output="video.avi", duration=10):
        """
        ضبط ویدیو از دوربین
        """
        if self.cv2 is None:
            return "❌ OpenCV در دسترس نیست"

        self.cap = self.cv2.VideoCapture(0)
        fourcc = self.cv2.VideoWriter_fourcc(*'XVID')
        out = self.cv2.VideoWriter(output, fourcc, 20.0, (640, 480))

        start_time = time.time()
        while time.time() - start_time < duration:
            ret, frame = self.cap.read()
            if ret:
                out.write(frame)
                self.cv2.imshow('Recording', frame)
                if self.cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        out.release()
        self.close_camera()
        print(f"🎥 ویدیو ذخیره شد: {output}")
        return output

    @license_manager.premium_required
    def detect_faces(self, show=True, output="faces.jpg"):
        """
        تشخیص صورت در دوربین و ذخیره عکس
        """
        if self.cv2 is None:
            return "❌ OpenCV در دسترس نیست"

        self.cap = self.cv2.VideoCapture(0)
        ret, frame = self.cap.read()
        if not ret:
            self.close_camera()
            return "❌ خطا در خواندن فریم"

        gray = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            self.cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        if show:
            self.cv2.imshow('Faces', frame)
            self.cv2.waitKey(0)
            self.cv2.destroyAllWindows()

        self.cv2.imwrite(output, frame)
        print(f"👤 صورت‌ها تشخیص داده شد و ذخیره شد: {output} (تعداد: {len(faces)})")
        self.close_camera()
        return len(faces)

    def close_camera(self):
        """
        بستن دوربین
        """
        if self.cap:
            self.cap.release()
            self.cv2.destroyAllWindows()


class Utils:
    """
    کلاس ابزارهای عمومی (رایگان)
    """

    @staticmethod
    def today(format="%Y-%m-%d"):
        return datetime.datetime.now().strftime(format)

    @staticmethod
    def rename(old, new):
        if os.path.exists(old):
            os.rename(old, new)
            return True
        return False

    @staticmethod
    def clear_clipboard():
        import pyperclip
        pyperclip.copy("")

    @staticmethod
    def random_filename(ext=".mp3", prefix="file"):
        return f"{prefix}_{random.randint(1000, 9999)}{ext}"

    @staticmethod
    def list_files(folder="."):
        return [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]

    @staticmethod
    def to_upper(text):
        return text.upper()

    @staticmethod
    def open_web(url):
        import webbrowser
        webbrowser.open(url)

    @staticmethod
    def my_ip():
        try:
            import requests
            return requests.get("https://api.ipify.org", timeout=5).text
        except:
            return "خطای شبکه"

    @staticmethod
    def get_downloads_dir():
        return Path(os.path.expanduser("~/Downloads"))

    @staticmethod
    def get_unique_filename(base_name="voice", ext=".mp3", folder=None):
        folder = folder or Utils.get_downloads_dir()
        i = 0
        while True:
            filename = folder / f"{base_name}_{i}{ext}"
            if not filename.exists():
                return filename
            i += 1

    @staticmethod
    def count_words(text: str):
        return len(text.strip().split())

    @staticmethod
    def get_day_name(date_str: str):
        try:
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%A")
        except ValueError:
            return "فرمت اشتباه"

    @staticmethod
    def copy_text(text):
        import pyperclip
        pyperclip.copy(text)

    @staticmethod
    def save_var(filename, value):
        with open(filename, "w", encoding="utf-8") as f:
            f.write(str(value))

    @staticmethod
    def load_var(filename, default=None):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = f.read().strip()
                return data if data else default
        except FileNotFoundError:
            return default

    @staticmethod
    def ri(a, b):
        return random.randint(a, b)

    @staticmethod
    def get_file_size(path: str):
        size = os.path.getsize(path)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    @staticmethod
    def getping(url):
        start = time.time()
        try:
            import requests
            requests.get(url, timeout=5)
            return round((time.time() - start) * 1000)
        except:
            return -1

    @staticmethod
    def clock(unit):
        now = datetime.datetime.now()
        if unit == "hour":
            return now.hour
        elif unit == "minute":
            return now.minute
        elif unit == "second":
            return now.second
        elif unit == "microsecond":
            return now.microsecond
        return "واحد نامعتبر"


# =============================================================================
# لیست کلاس‌ها برای دسترسی آسان
# =============================================================================

audio = Audio()
security = Security()
ai = AI()
system_utils = SystemUtils()
web_utils = WebUtils()
graphics = Graphics()
camera = Camera()
utils = Utils()
license = license_manager

__all__ = [
    "audio", "security", "ai", "system_utils", "web_utils", "graphics", "camera", "utils", "license"
]

print(f"✅ کتابخانه Taha v3.0.2 با کلاس‌های بهینه‌شده بارگذاری شد!")