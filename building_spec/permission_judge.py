"""
Permission 评测逻辑模块
负责处理 Permission 场景的单条和批量测试
支持多轮对话格式
"""
import requests
import json
import csv
import os
from datetime import datetime
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import get_judge_api_key, JUDGE_API_URL


class PermissionSingleJudge:
    """Permission 单条测试类"""
    
    def __init__(self):
        self.is_running = False
    
    def send_request(self, queries, source_base_token, base_tokens=None, 
                     agent="permission", concurrency=5):
        """
        发送 Permission 单条测试请求
        
        Args:
            queries: 查询列表（支持多轮），例如 ["第一轮", "第二轮"]
            source_base_token: 源 Base Token
            base_tokens: 目标 Base Token 列表（多轮），如果不传则和 queries 长度一致
            agent: Agent 类型
            concurrency: 并发数
        
        Returns:
            响应结果字典
        """
        api_key = get_judge_api_key()
        if not api_key:
            return {
                "success": False,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "error": "未配置 JUDGE_API_KEY",
                "message": "请在 Building 机评界面中配置 JUDGE_API_KEY"
            }
        
        # 如果没有提供 base_tokens，创建一个空列表
        if base_tokens is None:
            base_tokens = [""] * len(queries)
        
        # 确保 base_tokens 的长度和 queries 一致
        if len(base_tokens) < len(queries):
            base_tokens.extend([""] * (len(queries) - len(base_tokens)))
        elif len(base_tokens) > len(queries):
            base_tokens = base_tokens[:len(queries)]
        
        headers = {
            "Content-Type": "application/json",
            "x-judge-api-key": api_key
        }
        
        # 构建请求体 - Permission 特殊格式（支持多轮对话，不需要 mode）
        data = {
            "agent": agent,
            "cases": [{
                "id": "permission_multi_turn_001",
                "query": queries,
                "sourceBaseToken": source_base_token,
                "baseToken": base_tokens,
                "options": {
                    "concurrency": concurrency
                }
            }]
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
                "message": f"网络请求异常: {e}"
            }
        
        return result


class PermissionBatchJudge:
    """Permission 批量测试类"""
    
    def __init__(self):
        self.is_running = False
    
    def _read_cases_from_csv(self, csv_path):
        """
        从 CSV 文件读取 Permission 测试用例
        
        CSV 格式要求:
            - query: 查询内容（多轮用换行分隔）
            - sourceBaseToken: 源 Base Token
            - baseToken: 目标 Base Token（多轮用换行分隔）
        
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
        source_base_token_col = None
        base_token_col = None
        
        for idx, header in enumerate(headers):
            header_lower = str(header).lower()
            if header and "query" in header_lower:
                query_col = idx
            if header and ("sourcebasetoken" in header_lower or "source_base_token" in header_lower):
                source_base_token_col = idx
            if header and ("basetoken" in header_lower or "base_token" in header_lower):
                base_token_col = idx
        
        # 获取实际的表头名称列表
        actual_headers = [str(h) if h else "空" for h in headers]
        
        if query_col is None:
            raise Exception(f"未找到 query 列，请确保 CSV 文件中包含名为 'query' 的列。当前表头: {', '.join(actual_headers)}")
        if source_base_token_col is None:
            raise Exception(f"未找到 sourceBaseToken 列，请确保 CSV 文件中包含名为 'sourceBaseToken' 或 'source_base_token' 的列。当前表头: {', '.join(actual_headers)}")
        
        # 读取数据行
        for i, row in enumerate(rows[1:], 1):
            if not row or len(row) <= max(query_col, source_base_token_col):
                continue
            
            # 获取查询内容（支持多轮，用换行分隔）
            query_str = row[query_col] if len(row) > query_col else ""
            queries = [q.strip() for q in query_str.split('\n') if q.strip()]
            
            if not queries:
                continue
            
            # 获取 sourceBaseToken
            source_base_token = str(row[source_base_token_col] or "") if len(row) > source_base_token_col else ""
            
            # 获取 baseToken（支持多轮，用换行分隔）
            base_tokens = []
            if base_token_col is not None and len(row) > base_token_col:
                base_token_str = str(row[base_token_col] or "")
                base_tokens = [b.strip() for b in base_token_str.split('\n')]
            
            # 确保 base_tokens 和 queries 长度一致
            while len(base_tokens) < len(queries):
                base_tokens.append("")
            if len(base_tokens) > len(queries):
                base_tokens = base_tokens[:len(queries)]
            
            case = {
                "id": f"permission_test_{i:03d}",
                "query": queries,
                "sourceBaseToken": source_base_token,
                "baseToken": base_tokens
            }
            cases.append(case)
        
        return cases
    
    def _read_cases_from_excel(self, excel_path):
        """
        从 Excel 文件读取 Permission 测试用例
        
        Args:
            excel_path: Excel 文件路径
        
        Returns:
            测试用例列表
        """
        import zipfile
        import xml.etree.ElementTree as ET
        
        cases = []
        
        # 打开 Excel 文件（实际是 ZIP）
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
                    row_data = []
                    for cell in row_elem.findall('main:c', ns):
                        cell_type = cell.get('t')
                        cell_value = cell.find('main:v', ns)
                        
                        value = None
                        if cell_value is not None:
                            if cell_type == 's':
                                idx = int(cell_value.text)
                                value = shared_strings[idx]
                            else:
                                value = cell_value.text
                        row_data.append(value)
                    rows.append(row_data)
        
        if not rows:
            raise Exception("未读取到数据")
        
        # 查找表头和数据
        headers = rows[0] if rows else []
        query_col = None
        source_base_token_col = None
        base_token_col = None
        
        for idx, header in enumerate(headers):
            header_lower = str(header).lower() if header else ""
            if header and "query" in header_lower:
                query_col = idx
            if header and ("sourcebasetoken" in header_lower or "source_base_token" in header_lower):
                source_base_token_col = idx
            if header and ("basetoken" in header_lower or "base_token" in header_lower):
                base_token_col = idx
        
        # 获取实际的表头名称列表
        actual_headers = [str(h) if h else "空" for h in headers]
        
        if query_col is None:
            raise Exception(f"未找到 query 列，请确保 Excel 文件中包含名为 'query' 的列。当前表头: {', '.join(actual_headers)}")
        if source_base_token_col is None:
            raise Exception(f"未找到 sourceBaseToken 列，请确保 Excel 文件中包含名为 'sourceBaseToken' 或 'source_base_token' 的列。当前表头: {', '.join(actual_headers)}")
        
        # 读取数据行
        for i, row in enumerate(rows[1:], 1):
            if not row or len(row) <= max(query_col, source_base_token_col):
                continue
            
            # 获取查询内容（支持多轮，用换行分隔）
            query_str = str(row[query_col] or "") if len(row) > query_col else ""
            queries = [q.strip() for q in query_str.split('\n') if q.strip()]
            
            if not queries:
                continue
            
            # 获取 sourceBaseToken
            source_base_token = str(row[source_base_token_col] or "") if len(row) > source_base_token_col else ""
            
            # 获取 baseToken（支持多轮，用换行分隔）
            base_tokens = []
            if base_token_col is not None and len(row) > base_token_col:
                base_token_str = str(row[base_token_col] or "")
                base_tokens = [b.strip() for b in base_token_str.split('\n')]
            
            # 确保 base_tokens 和 queries 长度一致
            while len(base_tokens) < len(queries):
                base_tokens.append("")
            if len(base_tokens) > len(queries):
                base_tokens = base_tokens[:len(queries)]
            
            case = {
                "id": f"permission_test_{i:03d}",
                "query": queries,
                "sourceBaseToken": source_base_token,
                "baseToken": base_tokens
            }
            cases.append(case)
        
        return cases
    
    def read_cases_from_file(self, file_path):
        """
        从文件读取 Permission 测试用例（支持 CSV 和 Excel 格式）
        
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
                raise Exception(f"无法解析文件：{file_path}\n"
                              f"CSV 解析错误：{str(csv_error)}\n"
                              f"请确保文件是正确的 CSV 或 Excel 格式")
    
    def send_request(self, cases, agent="permission", concurrency=5):
        """
        发送 Permission 批量测试请求
        
        Args:
            cases: 测试用例列表
            agent: Agent 类型
            concurrency: 并发数
        
        Returns:
            响应结果字典
        """
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
        
        # 构建请求体 - Permission 特殊格式（支持多轮对话，不需要 mode）
        # 给每个 case 加上 options
        cases_with_options = []
        for case in cases:
            case_copy = case.copy()
            case_copy["options"] = {
                "concurrency": concurrency
            }
            cases_with_options.append(case_copy)
        
        data = {
            "agent": agent,
            "cases": cases_with_options
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
                result["message"] = f"请求返回状态码：{response.status_code}"
                
        except requests.exceptions.RequestException as e:
            result = {
                "success": False,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "error": str(e),
                "message": f"网络请求异常：{e}"
            }
        
        return result
