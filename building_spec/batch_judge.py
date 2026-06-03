"""
批量测试逻辑模块
负责处理批量测试的核心逻辑
"""
import requests
import json
import zipfile
import xml.etree.ElementTree as ET
import csv
import os
from datetime import datetime
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import get_judge_api_key, JUDGE_API_URL


class BatchJudge:
    """批量测试类"""
    
    def __init__(self):
        self.is_running = False
    
    def _read_cases_from_csv(self, csv_path):
        """
        从 CSV 文件读取测试用例
        
        Args:
            csv_path: CSV 文件路径
        
        Returns:
            测试用例列表
        """
        cases = []
        rows = []
        
        # 尝试多种编码格式
        encodings = ['utf-8-sig', 'gbk', 'gb18030', 'utf-8', 'latin-1']
        content = None
        
        for encoding in encodings:
            try:
                with open(csv_path, 'r', encoding=encoding) as f:
                    csv_reader = csv.reader(f)
                    for row in csv_reader:
                        rows.append(row)
                content = True
                break
            except UnicodeDecodeError:
                continue
        
        if not content:
            raise Exception("无法解码 CSV 文件，请尝试转换为 UTF-8 或 GBK 编码")
        
        if not rows:
            raise Exception("未读取到数据")
        
        # 查找表头和数据
        headers = rows[0] if rows else []
        query_col = None
        base_token_col = None
        
        for idx, header in enumerate(headers):
            header_lower = str(header).lower()
            # 精确匹配query列
            if header and (header_lower == "query" or header_lower.endswith("query")):
                query_col = idx
            # 精确匹配baseToken列，优先匹配更准确的，排除snapshot相关的
            if header:
                # 优先匹配完全匹配的
                if header_lower == "basetoken" or header_lower == "base_token":
                    base_token_col = idx
                # 其次匹配以basetoken结尾且不含snapshot的
                elif (header_lower.endswith("basetoken") and "snapshot" not in header_lower):
                    if base_token_col is None:
                        base_token_col = idx
                # 最后才匹配包含但不优先的
                elif ("base_token" in header_lower or "basetoken" in header_lower):
                    if base_token_col is None and "snapshot" not in header_lower:
                        base_token_col = idx
        
        # 获取实际的表头名称列表
        actual_headers = [str(h) if h else "空" for h in headers]
        
        if query_col is None:
            raise Exception(f"未找到 query 列，请确保 CSV 文件中包含名为 'query' 的列。当前表头: {', '.join(actual_headers)}")
        if base_token_col is None:
            raise Exception(f"未找到 base_token 列，请确保 CSV 文件中包含名为 'base_token' 或 'basetoken' 的列。当前表头: {', '.join(actual_headers)}")
        
        # 读取数据行
        for i, row in enumerate(rows[1:], 1):
            if not row or len(row) <= max(query_col, base_token_col):
                continue
            query_val = row[query_col] if len(row) > query_col else None
            if query_val is None:
                continue
            base_token_val = row[base_token_col] if len(row) > base_token_col else None
            case = {
                "id": f"SpecQuery_v0.7_{i:03d}",
                "query": str(query_val or ""),
                "baseToken": str(base_token_val or "")
            }
            cases.append(case)
        
        return cases
    
    def _read_cases_from_excel(self, excel_path):
        """
        从 Excel 文件读取测试用例
        
        Args:
            excel_path: Excel 文件路径
        
        Returns:
            测试用例列表
        """
        cases = []
        
        # 打开 Excel 文件（实际是 zip）
        with zipfile.ZipFile(excel_path, 'r') as z:
            # 读取 shared strings
            shared_strings = []
            if 'xl/sharedStrings.xml' in z.namelist():
                with z.open('xl/sharedStrings.xml') as f:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                    for si in root.findall('main:si', ns):
                        t = si.find('main:t', ns)
                        if t is not None:
                            shared_strings.append(t.text)
                        else:
                            text_parts = []
                            for t in si.findall('.//main:t', ns):
                                text_parts.append(t.text if t.text else '')
                            shared_strings.append(''.join(text_parts))
            
            # 读取工作表
            sheet_file = 'xl/worksheets/sheet1.xml'
            if sheet_file not in z.namelist():
                raise Exception("未找到工作表 sheet1")
            
            with z.open(sheet_file) as f:
                tree = ET.parse(f)
                root = tree.getroot()
                ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                
                sheet_data = root.find('main:sheetData', ns)
                if sheet_data is None:
                    raise Exception("无法读取工作表数据")
                
                rows = []
                for row_elem in sheet_data.findall('main:row', ns):
                    # 先初始化足够长的数组，用None填充
                    # 从cell的r属性获取列号，比如A1、B2
                    max_col = 0
                    cells = {}
                    for cell in row_elem.findall('main:c', ns):
                        # 解析单元格位置，比如 'A1' -> 0, 'B1' -> 1
                        cell_ref = cell.get('r', '')
                        col_idx = 0
                        # 提取字母部分（列号）
                        for c in cell_ref:
                            if c.isalpha():
                                col_idx = col_idx * 26 + (ord(c.upper()) - ord('A') + 1)
                            else:
                                break
                        col_idx -= 1  # 从0开始
                        
                        cell_type = cell.get('t')
                        cell_value = cell.find('main:v', ns)
                        
                        value = None
                        if cell_value is not None:
                            if cell_type == 's':
                                idx = int(cell_value.text)
                                value = shared_strings[idx]
                            else:
                                value = cell_value.text
                        
                        cells[col_idx] = value
                        if col_idx > max_col:
                            max_col = col_idx
                    
                    # 构建完整的行数据
                    row_data = [None] * (max_col + 1)
                    for idx, val in cells.items():
                        row_data[idx] = val
                    
                    rows.append(row_data)
        
        if not rows:
            raise Exception("未读取到数据")
        
        # 查找表头和数据
        headers = rows[0] if rows else []
        query_col = None
        base_token_col = None
        
        for idx, header in enumerate(headers):
            header_lower = str(header).lower()
            # 精确匹配query列
            if header and (header_lower == "query" or header_lower.endswith("query")):
                query_col = idx
            # 精确匹配baseToken列，优先匹配更准确的，排除snapshot相关的
            if header:
                # 优先匹配完全匹配的
                if header_lower == "basetoken" or header_lower == "base_token":
                    base_token_col = idx
                # 其次匹配以basetoken结尾且不含snapshot的
                elif (header_lower.endswith("basetoken") and "snapshot" not in header_lower):
                    if base_token_col is None:
                        base_token_col = idx
                # 最后才匹配包含但不优先的
                elif ("base_token" in header_lower or "basetoken" in header_lower):
                    if base_token_col is None and "snapshot" not in header_lower:
                        base_token_col = idx
        
        # 获取实际的表头名称列表
        actual_headers = [str(h) if h else "空" for h in headers]
        
        if query_col is None:
            raise Exception(f"未找到 query 列，请确保 CSV 文件中包含名为 'query' 的列。当前表头: {', '.join(actual_headers)}")
        if base_token_col is None:
            raise Exception(f"未找到 base_token 列，请确保 CSV 文件中包含名为 'base_token' 或 'basetoken' 的列。当前表头: {', '.join(actual_headers)}")
        
        # 读取数据行
        for i, row in enumerate(rows[1:], 1):
            if not row or len(row) <= max(query_col, base_token_col):
                continue
            query_val = row[query_col] if len(row) > query_col else None
            if query_val is None:
                continue
            base_token_val = row[base_token_col] if len(row) > base_token_col else None
            case = {
                "id": f"SpecQuery_v0.7_{i:03d}",
                "query": str(query_val or ""),
                "baseToken": str(base_token_val or "")
            }
            cases.append(case)
        
        return cases
    
    def read_cases_from_file(self, file_path):
        """
        从文件读取测试用例（支持 CSV 和 Excel 格式）
        
        Args:
            file_path: 文件路径
        
        Returns:
            测试用例列表
        """
        # 首先尝试检测文件实际类型：检查是否是 ZIP 格式（Excel .xlsx）
        try:
            with open(file_path, 'rb') as f:
                # 检查文件开头是否是 ZIP 格式的魔数
                header = f.read(4)
                if header == b'PK\x03\x04':
                    # 这是 ZIP 格式，应该是 Excel 文件
                    return self._read_cases_from_excel(file_path)
        except:
            pass
        
        # 不是 ZIP 格式，尝试 CSV 解析
        try:
            return self._read_cases_from_csv(file_path)
        except Exception as csv_error:
            # CSV 解析失败，再尝试 Excel 解析（可能是 .xls 格式）
            try:
                return self._read_cases_from_excel(file_path)
            except:
                # 都失败了，抛出包含两种尝试的错误
                raise Exception(f"无法解析文件: {file_path}\n"
                              f"CSV 解析错误: {str(csv_error)}\n"
                              f"请确保文件是正确的 CSV 或 Excel 格式")
    
    def send_request(self, cases, agent="building", dimensions=None, concurrency=5, mode="spec"):
        """
        发送批量测试请求
        
        Args:
            cases: 测试用例列表
            agent: Agent 类型
            dimensions: 评估维度（仅 building agent 需要）
            concurrency: 并发数
            mode: 评估模式
        
        Returns:
            响应结果字典
        """
        if dimensions is None:
            dimensions = ["table", "permission", "workflow", "formula", "dashboard"]
        
        api_key = get_judge_api_key()
        if not api_key:
            return {
                "success": False,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "error": "未配置 JUDGE_API_KEY",
                "message": "请在 Building 机评界面中配置 JUDGE_API_KEY"
            }
        
        headers = {
            "Content-Type": "application/json",
            "x-judge-api-key": api_key
        }
        
        # 构建请求体
        if agent == "building":
            # Building agent 特殊格式（需要 dimensions 和 mode）
            data = {
                "agent": agent,
                "cases": cases,
                "options": {
                    "dimensions": dimensions,
                    "concurrency": concurrency,
                    "mode": mode
                }
            }
        else:
            # 非 building agent 格式（不需要 mode）
            data = {
                "agent": agent,
                "cases": cases,
                "options": {
                    "concurrency": concurrency
                }
            }
        
        try:
            response = requests.post(JUDGE_API_URL, headers=headers, json=data)
            
            result = {
                "success": True,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "status_code": response.status_code,
                "request_body": data,
                "response_headers": dict(response.headers),
                "response_text": response.text
            }
            
            # 尝试解析 JSON
            try:
                result["response_json"] = response.json()
            except:
                result["response_json"] = None
            
            # 提取重要标识
            result["request_id"] = response.headers.get('x-bytefaas-request-id')
            result["tt_logid"] = response.headers.get('x-tt-logid')
            result["tt_trace_id"] = response.headers.get('x-tt-trace-id')
            
            # 添加状态消息
            if response.status_code == 201:
                result["message"] = "请求成功提交（异步任务已创建）"
            elif 200 <= response.status_code < 300:
                result["message"] = "请求成功"
            else:
                result["message"] = f"请求返回状态码: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            result = {
                "success": False,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "error": str(e),
                "message": f"网络请求异常：{e}"
            }
        
        return result
