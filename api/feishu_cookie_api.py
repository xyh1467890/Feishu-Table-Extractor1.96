"""
飞书 Cookie API 工具模块
用于通过 Cookie 方式获取数据表 metadata
"""

import json
import gzip
import base64
import requests
from urllib.parse import urlparse, parse_qs

# 字段类型映射
FIELD_TYPE_MAPPING = {
    1: "文本", 2: "数字", 3: "单选", 4: "多选", 5: "日期",
    7: "复选框", 11: "人员", 13: "电话号码", 15: "超链接",
    17: "附件", 18: "单项关联", 19: "查找引用", 20: "公式",
    21: "双向关联", 22: "地理位置", 23: "群组",
    1001: "创建时间", 1002: "最后更新时间", 1003: "创建人",
    1004: "修改人", 1005: "自动编号", 3001: "按钮"
}


def extract_cookie_value(cookie, key):
    """从 Cookie 字符串中提取指定 key 的值。"""
    for item in cookie.split(";"):
        item = item.strip()
        if not item or "=" not in item:
            continue
        name, value = item.split("=", 1)
        if name.strip() == key:
            return value.strip()
    return None


def get_user_token_from_cookie(cookie):
    """从浏览器 Cookie 中提取网页侧可用的访问令牌。"""
    return extract_cookie_value(cookie, "passport_app_access_token")


def get_cookie_headers(cookie, referer=None):
    """获取 Cookie 认证方式的请求头"""
    # 清理 Cookie 字符串，去除首尾空白和非法字符
    cleaned_cookie = cookie.strip()
    # 移除可能存在的换行符和其他非法字符
    cleaned_cookie = ''.join(filter(lambda c: c not in '\r\n\t', cleaned_cookie))
    
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Content-Type": "application/json",
        "Cookie": cleaned_cookie,
        "Origin": referer.split("://")[0] + "://" + referer.split("://")[1].split("/")[0] if referer else "",
        "Referer": referer or "",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        "X-CSRF-Token": "1",
    }
    return headers


def parse_json_response(response, action_name):
    """解析内部接口响应，遇到 HTML/空响应时给出更明确的错误。"""
    text = response.text or ""
    if response.status_code != 200:
        raise ValueError(f"{action_name}失败 ({response.status_code}): {text[:300]}")
    try:
        return response.json()
    except ValueError:
        raise ValueError(
            f"{action_name}失败：接口没有返回 JSON，可能是 Cookie 失效、域名不匹配或内部接口路径不可用。"
            f"响应片段：{text[:300]}"
        )


def normalize_list(value):
    """把内部接口可能返回的 list/dict 统一转成列表。"""
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return list(value.values())
    return []


def get_nested_value(data, paths):
    """按多个候选路径从内部接口响应中提取数据。"""
    for path in paths:
        current = data
        for key in path:
            if isinstance(key, int):
                # 支持列表的数字索引
                if not isinstance(current, list) or key >= len(current):
                    current = None
                    break
                current = current[key]
            else:
                # 字典的字符串键
                if not isinstance(current, dict):
                    current = None
                    break
                current = current.get(key)
        if current:
            return current
    return None


def request_cookie_candidates(candidates, headers, action_name, extract_paths):
    """按候选内部接口逐个尝试，返回第一个可解析结果。"""
    failures = []
    for url, params in candidates:
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            status = response.status_code
            text = response.text or ""

            if status != 200:
                failures.append(f"{status} {response.url} -> {text[:120]}")
                continue

            try:
                payload = response.json()
            except ValueError:
                failures.append(f"非 JSON {response.url} -> {text[:120]}")
                continue

            if payload.get("code") not in (0, None):
                failures.append(f"code={payload.get('code')} {response.url} -> {payload.get('msg')}")
                continue

            data = payload.get("data", payload)
            value = get_nested_value(data, extract_paths)
            result = normalize_list(value)
            if result:
                return result

            failures.append(f"空数据 {response.url} -> {str(payload)[:160]}")
        except Exception as exc:
            failures.append(f"异常 {url} -> {exc}")

    raise ValueError(f"{action_name}失败：已尝试多个内部接口但都不可用。\n" + "\n".join(failures[:8]))


def parse_bitable_url_for_cookie(feishu_url):
    """从飞书链接中解析 host、base_id、table_id（用于 Cookie 方式）"""
    parsed = urlparse(feishu_url)
    host = parsed.netloc
    
    path_parts = parsed.path.strip("/").split("/")
    base_id = path_parts[-1] if path_parts else None
    
    query = parse_qs(parsed.query)
    if not query and parsed.fragment:
        # 部分分享链接会把 table 参数放在 hash 后面。
        fragment_query = parsed.fragment.split("?", 1)[-1]
        query = parse_qs(fragment_query)
    table_id = query.get("table", [None])[0]
    
    if not host or not base_id:
        raise ValueError("不是有效的飞书多维表格链接")
    
    return host, base_id, table_id


def get_tables_via_cookie(cookie, base_id, host, table_id=None):
    """通过 Cookie 方式获取表信息 - 使用 tablesv3 接口"""
    referer = f"https://{host}/base/{base_id}"
    headers = get_cookie_headers(cookie, referer)
    
    # 1. 先请求 block_info 获取表名映射（优先使用 block_info 获取真实表名）
    table_name_map = {}
    try:
        print(f"\n📋 先请求 block_info 获取表名...")
        block_info_url = f"https://{host}/space/api/bitable/{base_id}/block_info"
        bi_response = requests.get(block_info_url, headers=headers, timeout=30)
        if bi_response.status_code == 200:
            bi_data = bi_response.json()
            if bi_data.get('code') == 0:
                blocks = bi_data.get('data', {}).get('blocks', {})
                print(f"   block_info 返回 {len(blocks)} 个块")
                # 建立表 ID 到名字的映射
                for block_id, block_info in blocks.items():
                    if block_id.startswith('tbl') and isinstance(block_info, dict):
                        for name_key in ['name', 'title', 'displayName']:
                            if name_key in block_info and block_info[name_key]:
                                table_name_map[block_id] = block_info[name_key]
                                print(f"   找到表 {block_id} 的名字: {block_info[name_key]}")
                                break
    except Exception as e:
        print(f"   block_info 请求失败: {e}")
    
    # 2. 用 tablesv3 请求表数据
    url = f"https://{host}/space/api/bitable/{base_id}/tablesv3/"
    
    try:
        # 允许不带 table_id，会尝试获取所有表
        if not table_id:
            print(f"   没有指定 table_id，将尝试获取所有表")
        
        print(f"\n🔍 正在请求 tablesv3，目标表: {table_id}")
        
        # POST 请求，带上正确的 JSON body
        if table_id:
            body = {
                "tableIDList": [table_id],
                "tablePartitionFlagList": [0],
                "tablePartitionForNoRankFlagList": [],
                "encodingProtocol": {
                    "compression": 1,
                    "serialization": 0
                }
            }
        else:
            # 没有 table_id，尝试用空列表获取所有表
            body = {
                "tableIDList": [],
                "tablePartitionFlagList": [],
                "tablePartitionForNoRankFlagList": [],
                "encodingProtocol": {
                    "compression": 1,
                    "serialization": 0
                }
            }
        
        response = requests.post(url, json=body, headers=headers)
        print(f"   响应状态: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   响应内容: {response.text[:500]}")
            raise ValueError(f"tablesv3 请求失败: {response.status_code}")
        
        resp_json = response.json()
        print(f"   响应 code: {resp_json.get('code')}")
        
        if resp_json.get("code") != 0:
            raise ValueError(f"tablesv3 返回错误: {resp_json.get('msg')}")
        
        data = resp_json.get("data", {})
        print(f"   data 键数: {len(data) if data else 0}")
        
        tables = []
        
        # 遍历所有表
        for tbl_id, encoded in data.items():
            # 解码这个表的数据
            print(f"   表 {tbl_id} 解码中...")
            
            decoded = base64.b64decode(encoded)
            decompressed = gzip.decompress(decoded)
            table_data = json.loads(decompressed.decode('utf-8'))
            
            # 优先从 block_info 映射中获取表名（这是真实表名）
            tbl_name = tbl_id
            if tbl_id in table_name_map:
                tbl_name = table_name_map[tbl_id]
                print(f"   从 block_info 映射中找到表名: {tbl_name}")
            else:
                # 如果没找到，再从 meta 中获取（可能是视图名）
                meta = table_data.get("meta", {})
                tbl_name = meta.get("name", "") or "未命名表"
            
            tables.append({
                "table_id": tbl_id,
                "table_name": tbl_name
            })
        
        print(f"   总共找到 {len(tables)} 个表")
        
        if tables:
            return tables
        else:
            # 如果没找到，至少返回一个占位表
            return [{
                "table_id": table_id,
                "table_name": table_name_map.get(table_id, "当前数据表")
            }]
    
    except Exception as e:
        print(f"tablesv3 获取表失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 失败，尝试旧方式
    if not table_id:
        raise ValueError("Cookie 方式需要从链接中解析到 table 参数")
    
    block_info_url = f"https://{host}/space/api/bitable/{base_id}/block_info"
    
    params = {"table": table_id}
        
    response = requests.get(block_info_url, params=params, headers=headers, timeout=30)
    payload = parse_json_response(response, "获取表信息")
    
    if payload.get("code") != 0:
        raise ValueError(f"API 返回错误: code={payload.get('code')}, msg={payload.get('msg')}")
    
    blocks = payload.get("data", {}).get("blocks", {})
    block = blocks.get(table_id, {}) if isinstance(blocks, dict) else {}
    table_name = block.get("name") or block.get("text") or "当前数据表"

    return [{
        "table_id": table_id,
        "table_name": table_name
    }]


def get_fields_via_tablesv3(cookie, base_id, table_id, host):
    """通过 tablesv3 接口获取表字段 - 这是最可靠的方式！"""
    print(f"\n📝 get_fields_via_tablesv3 开始：table_id={table_id}")
    referer = f"https://{host}/base/{base_id}"
    headers = get_cookie_headers(cookie, referer)
    url = f"https://{host}/space/api/bitable/{base_id}/tablesv3/"
    
    try:
        # POST 请求，带上正确的 JSON body
        body = {
            "tableIDList": [table_id],  # 传目标表 ID
            "tablePartitionFlagList": [0],
            "tablePartitionForNoRankFlagList": [],
            "encodingProtocol": {
                "compression": 1,
                "serialization": 0
            }
        }
        
        print(f"📤 POST {url}")
        response = requests.post(url, json=body, headers=headers)
        print(f"📥 响应: {response.status_code}")
        
        if response.status_code != 200:
            raise ValueError(f"tablesv3 请求失败: {response.status_code}")
        
        resp_json = response.json()
        if resp_json.get("code") != 0:
            raise ValueError(f"tablesv3 返回错误: {resp_json.get('msg')}")
        
        data = resp_json.get("data", {})
        print(f"   Data 表数: {len(data)}")
        
        # 遍历所有表，找到目标表
        for tbl_id, encoded in data.items():
            print(f"   检查表: {tbl_id} (目标是: {table_id})")
            
            if tbl_id == table_id or not table_id:
                print(f"   ✅ 找到目标表，正在解码...")
                
                # 解码这个表的数据
                decoded = base64.b64decode(encoded)
                decompressed = gzip.decompress(decoded)
                table_data = json.loads(decompressed.decode('utf-8'))
                
                # 提取字段信息
                field_map = table_data.get("fieldMap", {})
                fields_list = []
                
                print(f"   ✅ fieldMap 大小: {len(field_map)}")
                
                for field_id, field_info in field_map.items():
                    # 构建完整的字段
                    field_dict = {
                        "id": field_id,
                        "name": field_info.get("name", ""),
                        "type": field_info.get("type"),
                        "isPrimary": field_info.get("isPrimary", False),
                        "property": field_info.get("property", {}),
                        "fieldUIType": field_info.get("fieldUIType", ""),
                    }
                    
                    # 如果 property 里有 options，也加上
                    property_data = field_info.get("property", {})
                    if "options" in property_data:
                        field_dict["options"] = property_data["options"]
                    
                    fields_list.append(field_dict)
                
                print(f"   ✅ 成功返回 {len(fields_list)} 个字段！")
                return fields_list
    
    except Exception as e:
        print(f"❌ tablesv3 方式失败: {e}")
        import traceback
        traceback.print_exc()
    
    raise ValueError("tablesv3 方式未找到字段数据")


def get_fields_via_cookie(cookie, base_id, table_id, host):
    """通过 Cookie 方式获取表字段 - 优先使用 tablesv3"""
    try:
        return get_fields_via_tablesv3(cookie, base_id, table_id, host)
    except:
        pass
    
    # tablesv3 失败，尝试其他方式
    referer = f"https://{host}/base/{base_id}"
    headers = get_cookie_headers(cookie, referer)
    candidates = [
        (f"https://{host}/space/api/v1/bitable/{base_id}/clientvars", {"tableID": table_id, "needBase": "true", "recordLimit": 200}),
        (f"https://{host}/space/api/meta/", {"token": base_id, "type": 8, "need_extra_fields": 1, "need_extra_fields": 3}),
        (f"https://{host}/space/api/bitable/{base_id}/table/{table_id}/field", None),
        (f"https://{host}/space/api/bitable/{base_id}/table/{table_id}/fields", None),
        (f"https://{host}/space/api/bitable/{base_id}/tables/{table_id}/fields", None),
        (f"https://{host}/space/api/bitable/{base_id}/fields", {"table": table_id}),
        (f"https://{host}/space/api/bitable/{base_id}/field", {"table": table_id}),
        (f"https://{host}/space/api/bitable/{base_id}/meta", {"table": table_id}),
        (f"https://{host}/space/api/bitable/{base_id}/schema", {"table": table_id}),
    ]
    return request_cookie_candidates(
        candidates,
        headers,
        "获取字段",
        [
            ("fields",),
            ("fieldList",),
            ("items",),
            ("fieldMap",),
            ("tables", 0, "fields"),
            ("tables", "fields"),
            ("table", "fields"),
            ("table", "fieldMap"),
            ("meta", "fields"),
            ("schema", "fields"),
            ("data", "fields"),
            ("data", "fieldMap"),
        ],
    )


def get_records_via_cookie(cookie, base_id, table_id, host):
    """通过 Cookie 方式获取记录"""
    referer = f"https://{host}/base/{base_id}"
    headers = get_cookie_headers(cookie, referer)
    candidates = [
        (f"https://{host}/space/api/meta/", {"token": base_id, "type": 8, "need_extra_fields": 1, "need_extra_fields": 3}),
        (f"https://{host}/space/api/bitable/{base_id}/table/{table_id}/record", None),
        (f"https://{host}/space/api/bitable/{base_id}/table/{table_id}/records", None),
        (f"https://{host}/space/api/bitable/{base_id}/tables/{table_id}/records", None),
        (f"https://{host}/space/api/bitable/{base_id}/records", {"table": table_id}),
        (f"https://{host}/space/api/bitable/{base_id}/record", {"table": table_id}),
    ]
    return request_cookie_candidates(
        candidates,
        headers,
        "获取记录",
        [
            ("records",),
            ("items",),
            ("recordMap",),
            ("tables", 0, "records"),
            ("tables", "records"),
            ("table", "records"),
            ("data", "records"),
        ],
    )


def process_single_table_via_cookie(cookie, table, base_id, host, fetch_records):
    """通过 Cookie 方式处理单个表"""
    table_id = table.get("table_id")
    table_name = table.get("table_name")
    if not table_id:
        raise ValueError("未解析到有效的数据表 table_id，请检查链接中是否包含 table=tbl... 参数")
    
    # 获取字段
    fields = get_fields_via_cookie(cookie, base_id, table_id, host)
    
    fields_list = []
    field_name_map = {}
    
    for field in fields:
        field_id = field.get("id") or field.get("fieldId") or field.get("field_id")
        field_name = field.get("name") or field.get("fieldName") or field.get("field_name")
        field_type = field.get("type") or field.get("fieldType") or field.get("field_type")
        if field_id and field_name:
            field_name_map[field_id] = field_name
        
        # 转换字段类型
        field_type_code = None
        if isinstance(field_type, int):
            field_type_code = field_type
        elif isinstance(field_type, str):
            # 尝试将字符串类型转换为数字
            type_mapping = {
                "text": 1, "number": 2, "singleSelect": 3, "multiSelect": 4, 
                "date": 5, "checkbox": 7, "person": 11, "phone": 13, 
                "url": 15, "attachment": 17, "singleLink": 18, 
                "lookup": 19, "formula": 20, "duplexLink": 21,
                "location": 22, "groupChat": 23
            }
            field_type_code = type_mapping.get(field_type)
        
        field_info = {
            "field_id": field_id,
            "field_name": field_name,
            "field_type_code": field_type_code,
            "field_type_name": FIELD_TYPE_MAPPING.get(field_type_code, f"未知类型({field_type})"),
            "is_primary": field.get("isPrimary", False)
        }
        
        # 添加选项信息
        if "options" in field:
            options = []
            for opt in field["options"]:
                if isinstance(opt, dict):
                    options.append(opt.get("name", ""))
                else:
                    options.append(str(opt))
            field_info["options"] = options
        
        fields_list.append(field_info)
    
    # 获取记录
    records_data = []
    if fetch_records:
        try:
            records = get_records_via_cookie(cookie, base_id, table_id, host)
            for record in records:
                record_fields = record.get("fields", {})
                parsed_record = {}
                for field_id, value in record_fields.items():
                    field_name = field_name_map.get(field_id, field_id)
                    parsed_record[field_name] = value
                records_data.append(parsed_record)
        except Exception as e:
            print(f"获取表 {table_name} 记录失败: {e}")
    
    table_info = {
        "table_id": table_id,
        "table_name": table_name,
        "view_count": 0,
        "fields": fields_list
    }
    
    if fetch_records:
        table_info["records"] = records_data
    
    return table_info


def extract_bitable_info_via_cookie(feishu_url, cookie, fetch_records=True):
    """
    通过 Cookie 方式从飞书多维表格链接提取数据表 metadata
    
    Args:
        feishu_url: 飞书多维表格链接
        cookie: 飞书 Cookie
        fetch_records: 是否获取数据表记录内容
        
    Returns:
        包含 base_token 和 tables 信息的字典
    """
    # 延迟导入以避免循环依赖
    import importlib
    feishu_api = importlib.import_module('api.feishu_api')
    extract_bitable_info = feishu_api.extract_bitable_info
    get_open_api_base = feishu_api.get_open_api_base
    parse_app_id = feishu_api.parse_app_id
    
    open_api_error = None
    cookie_user_token = get_user_token_from_cookie(cookie)
    if cookie_user_token:
        headers = {
            "Authorization": f"Bearer {cookie_user_token}",
            "Content-Type": "application/json"
        }
        try:
            return extract_bitable_info(
                feishu_url,
                headers=headers,
                fetch_records=fetch_records,
                api_base=get_open_api_base(feishu_url)
            )
        except Exception as exc:
            open_api_error = str(exc)

    host, base_id, table_id = parse_bitable_url_for_cookie(feishu_url)
    referer = f"https://{host}/base/{base_id}"
    headers = get_cookie_headers(cookie, referer)
    
    if not table_id:
        raise ValueError("未解析到有效的数据表 table_id，请检查链接中是否包含 table=tbl... 参数")
    
    try:
        print("\n" + "=" * 80)
        print("🚀 Cookie 方式 - 获取当前表")
        print("=" * 80)
        
        # 1. 先请求 block_info 获取表名映射
        print(f"\n📋 先请求 block_info 获取表名...")
        table_name_map = {}
        try:
            block_info_url = f"https://{host}/space/api/bitable/{base_id}/block_info"
            bi_response = requests.get(block_info_url, headers=headers, timeout=30)
            if bi_response.status_code == 200:
                bi_data = bi_response.json()
                if bi_data.get('code') == 0:
                    blocks = bi_data.get('data', {}).get('blocks', {})
                    print(f"   block_info 返回 {len(blocks)} 个块")
                    # 建立表 ID 到名字的映射
                    for block_id, block_info in blocks.items():
                        if block_id.startswith('tbl') and isinstance(block_info, dict):
                            # 尝试从 block_info 中找名字
                            for name_key in ['name', 'title', 'displayName']:
                                if name_key in block_info and block_info[name_key]:
                                    table_name_map[block_id] = block_info[name_key]
                                    print(f"   找到表 {block_id} 的名字: {block_info[name_key]}")
                                    break
        except Exception as e:
            print(f"   block_info 请求失败: {e}")
        
        # 2. 用 tablesv3 请求当前表数据
        tablesv3_url = f"https://{host}/space/api/bitable/{base_id}/tablesv3/"
        body = {
            "tableIDList": [table_id],
            "tablePartitionFlagList": [0],
            "tablePartitionForNoRankFlagList": [],
            "encodingProtocol": {"compression": 1, "serialization": 0}
        }
        
        print(f"\n📋 请求 tablesv3 接口...")
        response = requests.post(tablesv3_url, json=body, headers=headers, timeout=30)
        
        if response.status_code != 200:
            raise ValueError(f"tablesv3 请求失败: {response.status_code}")
        
        data = response.json()
        
        if data.get('code') != 0:
            raise ValueError(f"tablesv3 返回错误: {data.get('msg')}")
        
        tv3_data = data.get('data', {})
        print(f"   tablesv3 返回 {len(tv3_data)} 个表的数据")
        
        if table_id not in tv3_data:
            raise ValueError(f"未在响应中找到表 {table_id}")
        
        # 解析单个表
        encoded = tv3_data[table_id]
        decoded = base64.b64decode(encoded)
        decompressed = gzip.decompress(decoded)
        table_data = json.loads(decompressed.decode('utf-8'))
        
        print(f"\n📦 解析表 {table_id}...")
        print(f"   table_data 完整 keys: {list(table_data.keys())}")
        
        # 提取表名 - 尝试多个位置
        meta = table_data.get('meta', {})
        print(f"   meta 完整 keys: {list(meta.keys())}")
        print(f"   meta 完整内容: {meta}")
        
        # 也检查一下其他可能包含表名的字段
        if 'viewMap' in table_data:
            print(f"   viewMap 内容: {table_data['viewMap']}")
        if 'views' in table_data:
            print(f"   views 内容: {table_data['views']}")
        if 'exInfo' in table_data:
            print(f"   exInfo 内容: {table_data['exInfo']}")
        
        tbl_name = table_id
        # 1. 先从 block_info 的映射中查找（这应该是正确的中文表名）
        if table_id in table_name_map:
            tbl_name = table_name_map[table_id]
            print(f"   从 block_info 映射中找到中文表名: {tbl_name}")
        
        # 2. 如果没找到，再尝试从其他位置找
        if tbl_name == table_id:
            for name_key in ['name', 'title', 'displayName', 'tableName']:
                if name_key in meta and meta.get(name_key):
                    tbl_name = meta[name_key]
                    print(f"   从 meta.{name_key} 找到表名: {tbl_name}")
                    break
        
        # 3. 如果还没找到，尝试 table_data 的其他位置
        if tbl_name == table_id:
            for top_key in ['name', 'title', 'displayName', 'tableName']:
                if top_key in table_data and table_data.get(top_key):
                    tbl_name = table_data[top_key]
                    print(f"   从 table_data.{top_key} 找到表名: {tbl_name}")
                    break
        
        # 提取字段
        field_map = table_data.get('fieldMap', {})
        fields_list = []
        
        for field_id, field_info in field_map.items():
            f_name = field_info.get('name', field_id)
            f_type = field_info.get('type')
            f_is_primary = field_info.get('isPrimary', False)
            
            f_type_code = f_type if isinstance(f_type, int) else None
            f_type_name = FIELD_TYPE_MAPPING.get(f_type_code, "未知类型")
            
            field_obj = {
                "field_id": field_id,
                "field_name": f_name,
                "field_type_code": f_type_code,
                "field_type_name": f_type_name,
                "is_primary": f_is_primary
            }
            
            # 如果有 options 就加上
            property_data = field_info.get('property', {})
            if property_data:
                field_obj["property"] = property_data
                if "options" in property_data:
                    field_obj["options"] = []
                    for opt in property_data["options"]:
                        if isinstance(opt, dict):
                            field_obj["options"].append(opt.get("name", ""))
            
            fields_list.append(field_obj)
        
        print(f"   表名: {tbl_name}")
        print(f"   字段数: {len(fields_list)}")
        
        # 组装结果
        tables_info = [{
            "table_id": table_id,
            "table_name": tbl_name,
            "view_count": 0,
            "fields": fields_list
        }]
        
        print("\n✅ 成功解析当前表！")
        
        return {
            "base_token": base_id,
            "host": host,
            "tables": tables_info
        }
        
    except Exception as e:
        message = f"Cookie 方式获取失败: {str(e)}"
        if cookie_user_token:
            message += f"\n尝试开放 API 也失败: {open_api_error}"
        raise ValueError(message)
