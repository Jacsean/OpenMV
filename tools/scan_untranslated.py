#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动扫描未国际化的中文文本工具

功能：
1. 扫描项目中所有Python文件
2. 识别硬编码的中文文本字符串
3. 生成翻译文件模板
4. 检测已国际化但缺少翻译的文本
"""

import os
import re
import json
from pathlib import Path

def scan_chinese_strings(file_path):
    """扫描文件中的中文文本"""
    chinese_pattern = re.compile(r'["\']([\u4e00-\u9fa5]+(?:[\u4e00-\u9fa5\s，。！？、；：]+)*)[\'"]')
    results = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                matches = chinese_pattern.findall(line)
                for match in matches:
                    # 过滤掉非常短的文本（可能是注释中的单个汉字）
                    if len(match.strip()) >= 2:
                        # 检查是否已经是翻译调用
                        if 'get_ui(' not in line and 'tr(' not in line and 'translate(' not in line:
                            results.append({
                                'file': file_path,
                                'line': line_num,
                                'text': match.strip(),
                                'context': line.strip()
                            })
    except Exception as e:
        print(f"Error scanning {file_path}: {e}")
    
    return results

def scan_all_files(base_dir):
    """扫描所有Python文件"""
    all_results = []
    for root, dirs, files in os.walk(base_dir):
        # 跳过隐藏目录和第三方库
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', '.git']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                results = scan_chinese_strings(file_path)
                all_results.extend(results)
    
    return all_results

def load_existing_translations(translations_dir):
    """加载现有的翻译文件"""
    translations = {}
    
    for lang_file in os.listdir(translations_dir):
        if lang_file.endswith('.json'):
            lang_code = lang_file.replace('.json', '')
            file_path = os.path.join(translations_dir, lang_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    translations[lang_code] = json.load(f)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
    
    return translations

def find_missing_translations(scanned_texts, translations):
    """查找缺失的翻译"""
    missing = {}
    
    for lang_code, trans_data in translations.items():
        missing[lang_code] = []
        
        for item in scanned_texts:
            text = item['text']
            # 检查文本是否已在翻译中
            found = False
            
            # 搜索所有嵌套的翻译键
            def search_dict(d):
                nonlocal found
                if isinstance(d, dict):
                    for k, v in d.items():
                        if v == text:
                            found = True
                            return
                        search_dict(v)
                elif isinstance(d, list):
                    for item in d:
                        search_dict(item)
            
            search_dict(trans_data)
            
            if not found:
                missing[lang_code].append(item)
    
    return missing

def generate_report(scanned_texts, missing_translations, output_dir):
    """生成扫描报告"""
    report = {
        'summary': {
            'total_scanned': len(scanned_texts),
            'missing_translations': {
                lang: len(items) for lang, items in missing_translations.items()
            }
        },
        'scanned_texts': scanned_texts,
        'missing_translations': missing_translations
    }
    
    # 保存JSON报告
    report_path = os.path.join(output_dir, 'untranslated_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 生成可读的报告
    report_text = []
    report_text.append("=" * 70)
    report_text.append("          未国际化文本扫描报告")
    report_text.append("=" * 70)
    report_text.append(f"\n扫描文件数量: {len(set(item['file'] for item in scanned_texts))}")
    report_text.append(f"发现中文文本: {len(scanned_texts)}")
    
    for lang, items in missing_translations.items():
        report_text.append(f"\n{lang} 缺失翻译: {len(items)}")
    
    report_text.append("\n" + "=" * 70)
    report_text.append("          缺失翻译详情")
    report_text.append("=" * 70)
    
    for lang, items in missing_translations.items():
        if items:
            report_text.append(f"\n【{lang}】")
            for item in items[:20]:  # 只显示前20条
                report_text.append(f"  - {item['file']}:{item['line']}")
                report_text.append(f"    原文: {item['text']}")
                report_text.append(f"    上下文: {item['context'][:80]}...")
                report_text.append("")
            if len(items) > 20:
                report_text.append(f"    ... 还有 {len(items) - 20} 条")
    
    report_path_txt = os.path.join(output_dir, 'untranslated_report.txt')
    with open(report_path_txt, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_text))
    
    print(f"报告已保存到: {report_path}")
    print(f"可读报告已保存到: {report_path_txt}")
    
    return report

def main():
    print("=" * 70)
    print("          自动扫描未国际化文本工具")
    print("=" * 70)
    
    # 设置路径
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src" / "python"
    translations_dir = src_dir / "language" / "translations"
    output_dir = project_root / "tools" / "output"
    
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n扫描目录: {src_dir}")
    print(f"翻译文件目录: {translations_dir}")
    print(f"输出目录: {output_dir}")
    
    # 扫描所有中文文本
    print("\n正在扫描代码中的中文文本...")
    scanned_texts = scan_all_files(src_dir)
    print(f"发现 {len(scanned_texts)} 个中文文本")
    
    # 加载现有翻译
    print("\n正在加载现有翻译文件...")
    translations = load_existing_translations(translations_dir)
    print(f"已加载 {len(translations)} 个语言文件")
    
    # 查找缺失的翻译
    print("\n正在对比查找缺失翻译...")
    missing_translations = find_missing_translations(scanned_texts, translations)
    
    # 生成报告
    print("\n正在生成报告...")
    report = generate_report(scanned_texts, missing_translations, output_dir)
    
    print("\n" + "=" * 70)
    print("扫描完成！")
    print("=" * 70)
    print(f"\n总扫描中文文本: {report['summary']['total_scanned']}")
    for lang, count in report['summary']['missing_translations'].items():
        print(f"{lang} 缺失翻译: {count}")

if __name__ == '__main__':
    main()