import gettext
import os
from contextvars import ContextVar
from typing import Any, Dict

from fastapi import Request

from kalorda.utils.logger import logger

# 动态获取locales目录的绝对路径
# i18n.py位于kalorda/utils/目录，locales位于kalorda/目录
LOCALES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "locales")

# 定义可用语言
AVAILABLE_LANGUAGES = ["zh_CN", "en_US"]
DEFAULT_LANGUAGE = "zh_CN"

# 创建并注册全部翻译器
translators = {}
for lang in AVAILABLE_LANGUAGES:
    translator = gettext.translation("messages", localedir=LOCALES_DIR, languages=[lang])
    translator.install()
    translators[lang] = translator

# 定义请求上下文保存当前请求的语言（请求级隔离的）
lang_var: ContextVar[str] = ContextVar("lang", default=None)


# 翻译标记
def _(message):
    return message


# 翻译运行
def t(data: Any, **kwargs):
    if data is None:
        return None
    translator = translators.get(lang_var.get())
    if not translator:
        return data

    if isinstance(data, dict):
        processed_dict: Dict[Any, Any] = {}
        for k, v in data.items():
            processed_dict[k] = t(v)
        return processed_dict
    if isinstance(data, list):
        return [t(item) for item in data]
    if isinstance(data, set):
        return {t(item) for item in data}
    if isinstance(data, tuple):
        return tuple(t(item) for item in data)
    if isinstance(data, frozenset):
        return frozenset(t(item) for item in data)
    if isinstance(data, str):
        if len(data.strip()) == 0:
            return ""
        return translator.gettext(data).format(**kwargs) if kwargs else translator.gettext(data)
    return data


def setup_i18n_middleware(app):
    """设置国际化中间件"""

    @app.middleware("http")
    async def i18n_middleware(request: Request, call_next):
        request_lang = request.headers.get("User-Language") or request.headers.get("Accept-Language")
        user_lang = request_lang.split(",")[0].replace("-", "_") if request_lang else DEFAULT_LANGUAGE
        if user_lang not in AVAILABLE_LANGUAGES:
            user_lang = DEFAULT_LANGUAGE
        lang_var.set(user_lang)
        response = await call_next(request)
        return response
