
"""
飞书表单 API 工具模块
用于通过 Cookie 方式获取表单配置信息
"""

import json
import requests


def extract_form_info(form_url, cookie):
    """
    从飞书表单页面提取 Snapshot 信息
    
    Args:
        form_url: 飞书表单链接
        cookie: 完整的飞书 Cookie 字符串
    
    Returns:
        解析后的表单数据字典
    """
    headers = {
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    # 请求页面
    response = requests.get(form_url, headers=headers, timeout=30)
    response.raise_for_status()
    
    html_content = response.text
    
    # 找到 Snapshot 位置
    snapshot_key = '"Snapshot":'
    idx = html_content.find(snapshot_key)
    if idx == -1:
        raise ValueError("未能找到 Snapshot 字段")
    
    # 从该位置开始查找
    start_idx = idx + len(snapshot_key)
    
    # 找到开始引号的位置
    start_quote = html_content.find('"', start_idx)
    if start_quote == -1:
        raise ValueError("Snapshot 格式不对")
    
    # 寻找匹配的结束引号
    end_quote = start_quote + 1
    while end_quote < len(html_content):
        if html_content[end_quote] == '"' and html_content[end_quote - 1] != '\\':
            break
        end_quote += 1
    
    # 提取 JSON 字符串
    json_str = html_content[start_quote + 1: end_quote]
    
    try:
        # 先尝试直接解析
        snapshot_data = json.loads(json_str)
    except:
        # 处理转义
        # 步骤1：替换 \\" 为 "
        fixed = json_str.replace('\\"', '"')
        # 步骤2：再解析
        snapshot_data = json.loads(fixed)
    
    return {
        "type": "form",
        "url": form_url,
        "snapshot": snapshot_data
    }

