import os, gettext
from fastapi import Request

DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES = ["en", "fr"]
TRANSLATION_DIR = os.path.abspath("locales")

_translation_cache = {}

def get_locale(request: Request) -> str:
    lang = request.headers.get("Accept-Language", DEFAULT_LOCALE)
    lang = lang.split(",")[0].split("-")[0].lower()
    return lang if lang in SUPPORTED_LOCALES else DEFAULT_LOCALE

def get_translator(locale: str):
    if locale in _translation_cache:
        return _translation_cache[locale].gettext

    try:
        translator = gettext.translation("messages", localedir=TRANSLATION_DIR, languages=[locale])
    except FileNotFoundError:
        translator = gettext.NullTranslations()

    _translation_cache[locale] = translator
    return translator.gettext

def get_translator_dependency(request: Request):
    locale = get_locale(request)
    _ = get_translator(locale)
    return _
