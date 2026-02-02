from setuptools import setup, find_packages

long_description = "Taha Library - Premium Edition: کتابخانه چندمنظوره فارسی با قابلیت‌های صوتی، هوش مصنوعی، گرافیکی و ابزارهای کاربردی"

setup(
    name="taha",
    version="3.0.1",
    author="Taha (NS-TAHA1515)",
    description="📦 Taha Library - Premium Edition: کتابخانه چندمنظوره فارسی با قابلیت‌های صوتی، هوش مصنوعی، گرافیکی و ابزارهای کاربردی",
    long_description=long_description,
    long_description_content_type="text/plain",
    packages=find_packages(),
    py_modules=["taha"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Natural Language :: Persian",
    ],
    keywords="taha library persian voice tts speech recognition ai turtle pygame tools premium فارسی صوتی هوش-مصنوعی کتابخانه",
    python_requires=">=3.8",
    install_requires=[
        "pygame",
        "requests",
        "pyttsx3",
        "pyperclip",
        "Pillow",
        "SpeechRecognition",
        "cryptography",
        "transformers",
        "psutil",
        "pytz",
        "PyJWT",
        "beautifulsoup4",
        "pyautogui",
        "gTTS",
    ],
    extras_require={
        "dev": ["build", "twine", "wheel"],
    },
)