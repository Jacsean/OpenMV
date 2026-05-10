import os
from PySide2.QtCore import QCoreApplication, QTranslator, Qt, QObject, Signal

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
        self._translations = {
            "zh_CN": {},
            "en_US": {}
        }
        self._load_builtin_translations()
        self._initialized = True
    
    def _load_builtin_translations(self):
        self._translations["zh_CN"] = {
            "系统设置": "系统设置",
            "外观": "外观",
            "语言": "语言",
            "主题": "主题",
            "确定": "确定",
            "取消": "取消",
            "应用": "应用",
            "字体大小": "字体大小",
            "界面缩放": "界面缩放",
            "自动保存": "自动保存",
            "自动保存间隔": "自动保存间隔",
            "秒": "秒",
            "重置": "重置",
            "恢复默认设置": "恢复默认设置",
            "是否确定恢复所有设置为默认值？": "是否确定恢复所有设置为默认值？",
            "设置已恢复为默认值": "设置已恢复为默认值",
            "文件": "文件",
            "编辑": "编辑",
            "视图": "视图",
            "帮助": "帮助",
            "新建": "新建",
            "打开": "打开",
            "保存": "保存",
            "另存为": "另存为",
            "退出": "退出",
            "撤销": "撤销",
            "重做": "重做",
            "剪切": "剪切",
            "复制": "复制",
            "粘贴": "粘贴",
            "删除": "删除",
            "全选": "全选",
            "工具栏": "工具栏",
            "状态栏": "状态栏",
            "节点面板": "节点面板",
            "属性面板": "属性面板",
            "控制台": "控制台",
            "关于": "关于",
            "检查更新": "检查更新",
            "用户手册": "用户手册",
            "快捷键": "快捷键",
            "运行": "运行",
            "停止": "停止",
            "调试": "调试",
            "图形化视觉处理系统": "图形化视觉处理系统",
            "语言已切换到": "语言已切换到",
            "配置已保存": "配置已保存",
            "系统设置已更新": "系统设置已更新",
            "主题已变更并应用": "主题已变更并应用",
            "主题已切换为": "主题已切换为"
        }
        
        self._translations["en_US"] = {
            "系统设置": "Settings",
            "外观": "Appearance",
            "语言": "Language",
            "主题": "Theme",
            "确定": "OK",
            "取消": "Cancel",
            "应用": "Apply",
            "字体大小": "Font Size",
            "界面缩放": "UI Scale",
            "自动保存": "Auto Save",
            "自动保存间隔": "Auto Save Interval",
            "秒": "seconds",
            "重置": "Reset",
            "恢复默认设置": "Restore Defaults",
            "是否确定恢复所有设置为默认值？": "Are you sure you want to restore all settings to default?",
            "设置已恢复为默认值": "Settings have been restored to defaults",
            "文件": "File",
            "编辑": "Edit",
            "视图": "View",
            "帮助": "Help",
            "新建": "New",
            "打开": "Open",
            "保存": "Save",
            "另存为": "Save As",
            "退出": "Exit",
            "撤销": "Undo",
            "重做": "Redo",
            "剪切": "Cut",
            "复制": "Copy",
            "粘贴": "Paste",
            "删除": "Delete",
            "全选": "Select All",
            "工具栏": "Toolbar",
            "状态栏": "Status Bar",
            "节点面板": "Node Panel",
            "属性面板": "Properties Panel",
            "控制台": "Console",
            "关于": "About",
            "检查更新": "Check for Updates",
            "用户手册": "User Manual",
            "快捷键": "Shortcuts",
            "运行": "Run",
            "停止": "Stop",
            "调试": "Debug",
            "图形化视觉处理系统": "Visual Processing System",
            "语言已切换到": "Language changed to",
            "配置已保存": "Configuration saved",
            "系统设置已更新": "System settings updated",
            "主题已变更并应用": "Theme changed and applied",
            "主题已切换为": "Theme switched to"
        }
    
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
            self.language_changed.emit(lang_code)
        
        return True
    
    def get_current_language(self):
        return self._current_language
    
    def get_supported_languages(self):
        return self._supported_languages
    
    def translate(self, text, context=""):
        translations = self._translations.get(self._current_language, {})
        return translations.get(text, text)
    
    def tr(self, text):
        return self.translate(text)