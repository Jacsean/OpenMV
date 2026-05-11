import os
import json
from PySide2.QtCore import QCoreApplication, QTranslator, QObject, Signal

class TranslatorManager(QObject):
    language_changed = Signal(str)
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TranslatorManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._qt_translator = QTranslator()
        self._current_language = "zh_CN"
        self._supported_languages = {
            "zh_CN": "中文",
            "en_US": "English"
        }
        self._translations = {}
        self._translations_dir = os.path.join(os.path.dirname(__file__), "translations")
        self._load_translations()
        self._initialized = True
    
    def _load_translations(self):
        """从JSON文件加载翻译数据"""
        for lang_code in self._supported_languages.keys():
            file_path = os.path.join(self._translations_dir, f"{lang_code}.json")
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self._translations[lang_code] = json.load(f)
                except Exception as e:
                    print(f"Failed to load translation file {file_path}: {e}")
                    self._translations[lang_code] = {}
            else:
                self._translations[lang_code] = {}
    
    def set_language(self, lang_code):
        if lang_code not in self._supported_languages:
            return False
        
        QCoreApplication.removeTranslator(self._qt_translator)
        
        locale_dir = os.path.join(os.path.dirname(__file__), "locale", lang_code)
        qm_path = os.path.join(locale_dir, "app.qm")
        
        if os.path.exists(qm_path):
            self._qt_translator.load(qm_path)
            QCoreApplication.installTranslator(self._qt_translator)
        
        old_lang = self._current_language
        self._current_language = lang_code
        
        if old_lang != lang_code:
            # 重新加载翻译文件（以防文件被更新）
            self._load_translations()
            self.language_changed.emit(lang_code)
        
        return True
    
    def get_current_language(self):
        return self._current_language
    
    def get_supported_languages(self):
        return self._supported_languages
    
    def translate(self, text, context=""):
        """翻译文本（兼容旧API）"""
        if context:
            return self.get(context, text)
        return text
    
    def tr(self, text):
        """简化翻译方法（兼容旧API）"""
        return text
    
    def get(self, path, default=""):
        """
        通过路径获取翻译值
        
        Args:
            path: 翻译路径，如 "ui.main_window.title"
            default: 默认值
        
        Returns:
            翻译后的文本
        """
        try:
            parts = path.split('.')
            data = self._translations.get(self._current_language, {})
            for part in parts:
                data = data.get(part, {})
                if not data:
                    return default
            return data if data else default
        except Exception:
            return default
    
    def get_ui(self, path, default=""):
        """获取UI相关翻译"""
        return self.get(f"ui.{path}", default)
    
    def get_node(self, plugin_name, node_name, field, default=""):
        """获取节点相关翻译"""
        return self.get(f"nodes.{plugin_name}.{node_name}.{field}", default)
    
    def get_log(self, key, default=""):
        """获取日志相关翻译"""
        return self.get(f"logs.{key}", default)