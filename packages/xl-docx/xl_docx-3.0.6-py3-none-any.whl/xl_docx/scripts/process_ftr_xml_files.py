#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
处理XML文件，只保留w:ftr标签内的内容，去除w:ftr标签本身
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

def extract_wftr_content(xml_content):
    """
    从XML内容中提取w:ftr标签内的内容，去除标签本身
    """
    # 使用正则表达式匹配w:ftr标签及其内容
    pattern = r'<w:ftr[^>]*>(.*?)</w:ftr>'
    match = re.search(pattern, xml_content, re.DOTALL)
    
    if match:
        # 返回标签内的内容，去除首尾空白
        return match.group(1).strip()
    else:
        return None

def process_xml_file(file_path):
    """
    处理单个XML文件
    """
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取w:ftr标签内的内容
        wftr_content = extract_wftr_content(content)
        
        if wftr_content:
            # 将提取的内容写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(wftr_content)
            print("Processed: " + str(file_path))
            return True
        else:
            print("No w:ftr tag found: " + str(file_path))
            return False
            
    except Exception as e:
        print("Error processing file " + str(file_path) + ": " + str(e))
        return False

def find_xml_files_with_wftr(root_dir):
    """
    递归查找包含w:ftr标签的XML文件
    """
    xml_files = []
    root_path = Path(root_dir)
    
    # 递归查找所有XML文件
    for xml_file in root_path.rglob("*.xml"):
        try:
            with open(xml_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if '<w:ftr' in content:
                    xml_files.append(xml_file)
        except Exception as e:
            print("Error reading file " + str(xml_file) + ": " + str(e))
    
    return xml_files

def main():
    """
    主函数
    """
    # 设置templates文件夹路径
    templates_dir = r"D:\git\demo\env\frontend\templates"
    
    print("Starting to process folder: " + templates_dir)
    print("=" * 50)
    
    # 查找包含w:ftr标签的XML文件
    xml_files = find_xml_files_with_wftr(templates_dir)
    
    if not xml_files:
        print("No XML files with w:ftr tags found")
        return
    
    print("Found " + str(len(xml_files)) + " XML files with w:ftr tags:")
    for file_path in xml_files:
        print("  - " + str(file_path))
    
    print("\nStarting to process files...")
    print("=" * 50)
    
    # 处理每个文件
    processed_count = 0
    for file_path in xml_files:
        if process_xml_file(file_path):
            processed_count += 1
    
    print("=" * 50)
    print("Processing completed! Successfully processed " + str(processed_count) + " files")

if __name__ == "__main__":
    main()
