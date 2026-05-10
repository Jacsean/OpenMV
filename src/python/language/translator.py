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
            "主题": "Theme",
            "确定": "确定",
            "取消": "取消",
            "应用": "应用",
            "字体": "字体",
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
            "主题已切换为": "主题已切换为",
            "设置": "设置",
            "新建工程": "新建工程",
            "打开工程": "打开工程",
            "保存工程": "保存工程",
            "工作流": "工作流",
            "添加工作流": "添加工作流",
            "关闭当前工作流": "关闭当前工作流",
            "重命名": "重命名",
            "执行": "执行",
            "运行当前工作流": "运行当前工作流",
            "运行所有工作流": "运行所有工作流",
            "清空当前工作流": "清空当前工作流",
            "插件": "插件",
            "节点编辑器": "节点编辑器",
            "安装插件": "安装插件",
            "管理插件": "管理插件",
            "刷新插件": "刷新插件",
            "系统设置": "系统设置",
            "跟随系统": "跟随系统",
            "亮色": "亮色",
            "暗色": "暗色",
            "自定义": "自定义",
            "自定义颜色": "自定义颜色",
            "主题色": "主题色",
            "强调色": "强调色",
            "背景色": "背景色",
            "表面色": "表面色",
            "文字色": "文字色",
            "边框色": "边框色",
            "成功色": "成功色",
            "警告色": "警告色",
            "错误色": "错误色",
            "信息色": "信息色",
            "窗口大小": "窗口大小",
            "宽度": "宽度",
            "高度": "高度",
            "像素": "像素",
            "启动选项": "启动选项",
            "启动时最大化窗口": "启动时最大化窗口",
            "项目默认设置": "项目默认设置",
            "默认工作流名称": "默认工作流名称",
            "节点设置": "节点设置",
            "自动连接节点": "自动连接节点",
            "显示节点描述": "显示节点描述",
            "节点宽度": "节点宽度",
            "节点间距": "节点间距",
            "执行设置": "执行设置",
            "执行超时时间": "执行超时时间",
            "主工具栏": "主工具栏",
            "适应": "适应",
            "适应所有节点": "适应所有节点",
            "浏览...": "浏览...",
            "成功": "成功",
            "提示": "提示",
            "配置已保存！": "配置已保存！",
            "保存配置失败": "保存配置失败",
            "功能": "功能",
            "提示：快捷键配置将在下一次启动时生效": "提示：快捷键配置将在下一次启动时生效",
            "预览文本示例": "预览文本示例",
            "测试字体显示效果": "测试字体显示效果",
            "窗口": "窗口",
            "项目": "项目",
            "最近工程": "最近工程",
            "节点说明": "节点说明",
            "未选择节点": "未选择节点"
        }
        
        self._translations["en_US"] = {
            "系统设置": "Settings",
            "外观": "Appearance",
            "语言": "Language",
            "主题": "Theme",
            "确定": "OK",
            "取消": "Cancel",
            "应用": "Apply",
            "字体": "Font",
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
            "主题已切换为": "Theme switched to",
            "设置": "Settings",
            "新建工程": "New Project",
            "打开工程": "Open Project",
            "保存工程": "Save Project",
            "工作流": "Workflow",
            "添加工作流": "Add Workflow",
            "关闭当前工作流": "Close Current Workflow",
            "重命名": "Rename",
            "执行": "Execute",
            "运行当前工作流": "Run Current Workflow",
            "运行所有工作流": "Run All Workflows",
            "清空当前工作流": "Clear Current Workflow",
            "插件": "Plugins",
            "节点编辑器": "Node Editor",
            "安装插件": "Install Plugin",
            "管理插件": "Manage Plugins",
            "刷新插件": "Refresh Plugins",
            "系统设置": "System Settings",
            "跟随系统": "System",
            "亮色": "Light",
            "暗色": "Dark",
            "自定义": "Custom",
            "自定义颜色": "Custom Colors",
            "主题色": "Primary",
            "强调色": "Accent",
            "背景色": "Background",
            "表面色": "Surface",
            "文字色": "Text",
            "边框色": "Border",
            "成功色": "Success",
            "警告色": "Warning",
            "错误色": "Error",
            "信息色": "Info",
            "窗口大小": "Window Size",
            "宽度": "Width",
            "高度": "Height",
            "像素": "px",
            "启动选项": "Startup Options",
            "启动时最大化窗口": "Maximize window on startup",
            "项目默认设置": "Project Defaults",
            "默认工作流名称": "Default workflow name",
            "节点设置": "Node Settings",
            "自动连接节点": "Auto-connect nodes",
            "显示节点描述": "Show node descriptions",
            "节点宽度": "Node width",
            "节点间距": "Node spacing",
            "执行设置": "Execution Settings",
            "执行超时时间": "Execution timeout",
            "主工具栏": "Main Toolbar",
            "适应": "Fit",
            "适应所有节点": "Fit all nodes",
            "浏览...": "Browse...",
            "成功": "Success",
            "提示": "Info",
            "配置已保存！": "Configuration saved!",
            "保存配置失败": "Failed to save configuration",
            "功能": "Action",
            "提示：快捷键配置将在下一次启动时生效": "Note: Shortcut settings will take effect on next restart",
            "预览文本示例": "Preview Text Example",
            "测试字体显示效果": "Test font display effect",
            "窗口": "Window",
            "项目": "Project",
            "最近工程": "Recent Projects",
            "节点说明": "Node Info",
            "未选择节点": "No Node Selected"
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