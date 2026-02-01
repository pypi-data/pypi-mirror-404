#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理XML文件中的rsid属性脚本
用于清理Word文档XML文件中所有w:标签的rsid相关属性
"""

import os
import re
import argparse
from pathlib import Path


def clean_rsid_attributes(content):
    """
    清理XML内容中所有w:标签的rsid属性
    
    Args:
        content (str): XML文件内容
        
    Returns:
        str: 清理后的XML内容
    """
    # 定义需要清理的rsid属性模式
    rsid_patterns = [
        r'\s+w:rsidR="[^"]*"',      # w:rsidR属性
        r'\s+w:rsidRPr="[^"]*"',    # w:rsidRPr属性  
        r'\s+w:rsidRDefault="[^"]*"', # w:rsidRDefault属性
        r'\s+w:rsidP="[^"]*"',      # w:rsidP属性
    ]
    
    # 使用正则表达式匹配所有以w:开头的标签
    # 匹配格式: <w:tagname 属性...> 或 <w:tagname>
    w_tag_pattern = r'<w:([a-zA-Z][a-zA-Z0-9]*)\s+([^>]*?)>'
    
    def clean_w_tag(match):
        tag_name = match.group(1)
        attributes = match.group(2)
        
        # 移除所有rsid相关属性
        for pattern in rsid_patterns:
            attributes = re.sub(pattern, '', attributes)
        
        # 清理多余的空格
        attributes = re.sub(r'\s+', ' ', attributes).strip()
        
        if attributes:
            return f'<w:{tag_name} {attributes}>'
        else:
            return f'<w:{tag_name}>'
    
    # 处理所有w:标签
    content = re.sub(w_tag_pattern, clean_w_tag, content)
    
    # 再次处理，确保所有rsid属性都被清理
    # 使用更简单的方法：直接替换所有rsid属性
    for pattern in rsid_patterns:
        content = re.sub(pattern, '', content)
    
    return content


def process_xml_file(file_path, backup=True):
    """
    处理单个XML文件
    
    Args:
        file_path (str): XML文件路径
        backup (bool): 是否创建备份文件
        
    Returns:
        bool: 处理是否成功
    """
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # 清理rsid属性
        cleaned_content = clean_rsid_attributes(original_content)
        
        # 检查是否有变化
        if original_content == cleaned_content:
            print(f"File {file_path} has no rsid attributes to clean")
            return True
        
        # 创建备份文件
        if backup:
            backup_path = f"{file_path}.backup"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            print(f"Backup file created: {backup_path}")
        
        # 写入清理后的内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        print(f"File cleaned: {file_path}")
        return True
        
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return False


def process_directory(directory_path, backup=True, recursive=True):
    """
    处理目录下的所有XML文件
    
    Args:
        directory_path (str): 目录路径
        backup (bool): 是否创建备份文件
        recursive (bool): 是否递归处理子目录
        
    Returns:
        tuple: (成功处理的文件数, 总文件数)
    """
    directory = Path(directory_path)
    
    if not directory.exists():
        print(f"Directory does not exist: {directory_path}")
        return 0, 0
    
    if not directory.is_dir():
        print(f"Path is not a directory: {directory_path}")
        return 0, 0
    
    # 查找所有XML文件
    if recursive:
        xml_files = list(directory.rglob("*.xml"))
    else:
        xml_files = list(directory.glob("*.xml"))
    
    if not xml_files:
        print(f"No XML files found in directory {directory_path}")
        return 0, 0
    
    print(f"Found {len(xml_files)} XML files")
    
    success_count = 0
    for xml_file in xml_files:
        if process_xml_file(str(xml_file), backup):
            success_count += 1
    
    return success_count, len(xml_files)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='清理XML文件中所有w:标签的rsid属性')
    parser.add_argument('path', help='文件夹路径或XML文件路径')
    parser.add_argument('--no-backup', action='store_true', help='不创建备份文件')
    parser.add_argument('--no-recursive', action='store_true', help='不递归处理子目录')
    
    args = parser.parse_args()
    
    path = Path(args.path)
    backup = not args.no_backup
    recursive = not args.no_recursive
    
    if path.is_file():
        # 处理单个文件
        if path.suffix.lower() == '.xml':
            print(f"Processing single XML file: {path}")
            success = process_xml_file(str(path), backup)
            if success:
                print("File processing completed")
            else:
                print("File processing failed")
        else:
            print("File is not XML format")
    elif path.is_dir():
        # 处理目录
        print(f"Processing directory: {path}")
        success_count, total_count = process_directory(str(path), backup, recursive)
        print(f"Processing completed: {success_count}/{total_count} files processed successfully")
    else:
        print(f"Path does not exist: {path}")


if __name__ == "__main__":
    main()
