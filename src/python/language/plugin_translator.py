import os
import json

class PluginTranslator:
    def __init__(self):
        self._translations = {}
        self._current_language = "zh_CN"
    
    def set_language(self, lang_code):
        self._current_language = lang_code
    
    def load_plugin_translations(self, plugin_path):
        lang_dir = os.path.join(plugin_path, "language")
        if not os.path.exists(lang_dir):
            return {}
        
        lang_file = os.path.join(lang_dir, f"{self._current_language}.json")
        if os.path.exists(lang_file):
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        en_file = os.path.join(lang_dir, "en_US.json")
        if os.path.exists(en_file):
            try:
                with open(en_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return {}
    
    def translate_plugin_info(self, plugin_info):
        translations = self.load_plugin_translations(plugin_info.get("path", ""))
        
        if translations:
            plugin_trans = translations.get("plugin", {})
            if plugin_trans.get("name"):
                plugin_info["name"] = plugin_trans["name"]
            if plugin_trans.get("description"):
                plugin_info["description"] = plugin_trans["description"]
        
        return plugin_info
    
    def translate_node_info(self, node_info, plugin_path):
        translations = self.load_plugin_translations(plugin_path)
        
        if translations:
            nodes_trans = translations.get("nodes", {})
            node_name = node_info.get("name", "")
            if node_name in nodes_trans:
                node_trans = nodes_trans[node_name]
                if node_trans.get("display_name"):
                    node_info["display_name"] = node_trans["display_name"]
                if node_trans.get("category"):
                    node_info["category"] = node_trans["category"]
                if node_trans.get("description"):
                    node_info["description"] = node_trans["description"]
        
        return node_info
    
    def translate_category(self, category_name, plugin_path):
        translations = self.load_plugin_translations(plugin_path)
        
        if translations:
            categories_trans = translations.get("categories", {})
            if category_name in categories_trans:
                return categories_trans[category_name]
        
        return category_name