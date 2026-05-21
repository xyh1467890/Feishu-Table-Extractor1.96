"""
飞书 API 工具模块
用于通过开放 API 方式获取数据表 metadata
"""

import os
import json
import requests
from urllib.parse import urlparse

# 字段类型映射（复制一份，避免循环导入）
FIELD_TYPE_MAPPING = {
    1: "文本", 2: "数字", 3: "单选", 4: "多选", 5: "日期",
    7: "复选框", 11: "人员", 13: "电话号码", 15: "超链接",
    17: "附件", 18: "单项关联", 19: "查找引用", 20: "公式",
    21: "双向关联", 22: "地理位置", 23: "群组",
    1001: "创建时间", 1002: "最后更新时间", 1003: "创建人",
    1004: "修改人", 1005: "自动编号", 3001: "按钮"
}

# ==================== 机器人方式（保留作为注释，如需使用请取消注释）====================
# APP_ID = os.getenv("FEISHU_APP_ID", "")
# APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
# _feishu_token = None
# 
# def get_access_token():
#     """获取飞书 tenant_access_token"""
#     if not APP_ID or not APP_SECRET:
#         raise RuntimeError("请先设置 FEISHU_APP_ID 和 FEISHU_APP_SECRET")
# 
#     url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
#     resp = requests.post(
#         url,
#         json={"app_id": APP_ID, "app_secret": APP_SECRET},
#         headers={"Content-Type": "application/json"},
#         timeout=20
#     )
#     data = resp.json()
# 
#     token = data.get("tenant_access_token")
#     if not token:
#         raise RuntimeError(f"获取 tenant_access_token 失败: {data}")
# 
#     return token
# 
# def get_feishu_headers_bot():
#     """获取飞书 API 请求头（使用机器人身份）"""
#     global _feishu_token
#     if _feishu_token is None:
#         _feishu_token = get_access_token()
#     return {
#         "Authorization": f"Bearer {_feishu_token}",
#         "Content-Type": "application/json"
#     }


def get_feishu_headers():
    """获取飞书 API 请求头（使用 User 身份）"""
    feishu_user_token = os.getenv("FEISHU_USER_TOKEN", "")
    if not feishu_user_token:
        raise RuntimeError("请先设置 FEISHU_USER_TOKEN 环境变量")
        
    return {
        "Authorization": f"Bearer {feishu_user_token}",
        "Content-Type": "application/json"
    }


def get_open_api_base(feishu_url):
    """根据链接域名选择开放平台 API 域名。"""
    host = urlparse(feishu_url).netloc
    if host.endswith("larkoffice.com"):
        return "https://open.larkoffice.com"
    return "https://open.feishu.cn"


def parse_app_id(feishu_url):
    """从飞书链接中解析 base_token"""
    parsed = urlparse(feishu_url)
    parts = parsed.path.strip("/").split("/")

    if len(parts) < 2 or parts[0] != "base":
        raise ValueError("不是有效的飞书多维表格链接")

    return parts[1]


def feishu_get(url, headers, params=None):
    """封装飞书 API GET 请求"""
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(f"接口请求失败: {data}")

    return data.get("data", {})


def get_all_pages(url, headers, params=None):
    """处理分页获取所有数据"""
    params = params or {}
    params = dict(params)
    params.setdefault("page_size", 100)

    items = []
    page_token = None

    while True:
        if page_token:
            params["page_token"] = page_token

        data = feishu_get(url, headers, params=params)
        items.extend(data.get("items", []))

        if not data.get("has_more"):
            break

        page_token = data.get("page_token")

    return items


def replace_formula_ids(formula_str, table_name_map, field_name_map, all_field_name_map):
    """统一替换公式中的 table id 和 field id"""
    import re
    
    # 替换 table id 为真实表名
    def replace_table_id(match):
        prefix = match.group(1)
        tbl_id = match.group(2)
        tbl_name = table_name_map.get(tbl_id, tbl_id)
        return f"{prefix}$table[{tbl_name}]"
    
    formula_str = re.sub(r'(bitable::)?\$table\[([^\]]+)\]', replace_table_id, formula_str)
    
    # 替换 field id 为真实字段名
    def replace_field_id(match):
        field_id = match.group(1)
        field_name = field_name_map.get(field_id, all_field_name_map.get(field_id, field_id))
        return f"$field[{field_name}]"
    
    formula_str = re.sub(r'\$field\[([^\]]+)\]', replace_field_id, formula_str)
    
    # 替换 column 格式的 field id
    def replace_column_id(match):
        field_id = match.group(1)
        field_name = field_name_map.get(field_id, all_field_name_map.get(field_id, field_id))
        return f"$column[{field_name}]"
    
    formula_str = re.sub(r'\$column\[([^\]]+)\]', replace_column_id, formula_str)
    
    return formula_str


def process_single_table(table, base_token, headers, fetch_records, all_tables_info=None, table_name_map=None, all_field_name_map=None, api_base="https://open.feishu.cn"):
    """处理单个表的信息获取"""
    table_id = table.get("table_id")
    table_name = table.get("table_name") or table.get("name")

    # 获取字段
    fields_url = f"{api_base}/open-apis/bitable/v1/apps/{base_token}/tables/{table_id}/fields"
    fields = get_all_pages(fields_url, headers)

    # 获取字段映射（用于解析记录数据和替换 field id）
    field_name_map = {}
    fields_list = []
    # 先构建 field id 到 field name 的映射
    for field in fields:
        field_id = field.get("field_id")
        field_name = field.get("field_name")
        if field_id and field_name:
            field_name_map[field_id] = field_name

    # 如果没有传入 table_name_map，则自己构建
    if table_name_map is None:
        table_name_map = {}
        if all_tables_info:
            for tbl in all_tables_info:
                tbl_id = tbl.get("table_id")
                tbl_name = tbl.get("table_name")
                if tbl_id and tbl_name:
                    table_name_map[tbl_id] = tbl_name

    # 如果没有传入 all_field_name_map，则自己构建
    if all_field_name_map is None:
        all_field_name_map = {}

    for field in fields:
        field_type_code = field.get("field_type") or field.get("type")
        field_id = field.get("field_id")
        field_name = field.get("field_name")
        
        field_info = {
            "field_id": field_id,
            "field_name": field_name,
            "field_type_code": field_type_code,
            "field_type_name": FIELD_TYPE_MAPPING.get(field_type_code, f"未知类型({field_type_code})"),
            "is_primary": field.get("is_primary", False)
        }
        # 如果是单选或多选类型，添加选项名称
        if field_type_code in [3, 4]:
            property_data = field.get("property", {})
            if property_data and "options" in property_data:
                options = []
                for opt in property_data["options"]:
                    options.append(opt.get("name"))
                field_info["options"] = options
                field_info["property"] = property_data
        # 如果是关联字段（单项关联、查找引用、双向关联），添加配置
        if field_type_code in [18, 19, 21]:
            property_data = field.get("property", {})
            if property_data:
                # 复制一份用于修改
                modified_property = dict(property_data)
                
                # 处理 table id 替换为真实表名
                if "table_id" in modified_property:
                    tbl_id = modified_property["table_id"]
                    modified_property["table_id"] = table_name_map.get(tbl_id, tbl_id)
                
                # 隐藏 target_table 和 target_field 字段（包括 filter_info 里面的）
                if "target_table" in modified_property:
                    del modified_property["target_table"]
                if "target_field" in modified_property:
                    del modified_property["target_field"]
                
                # 处理条件中的 field id 替换为 field name，以及 target_table
                if "filter_info" in modified_property:
                    # 递归处理字段 id 替换和其他清理
                    def process_filter_conditions(obj):
                        if isinstance(obj, dict):
                            if "field_id" in obj:
                                f_id = obj["field_id"]
                                # 优先用当前表的映射，其次用所有表的映射
                                if f_id in field_name_map:
                                    obj["field_id"] = field_name_map[f_id]
                                elif f_id in all_field_name_map:
                                    obj["field_id"] = all_field_name_map[f_id]
                            # 删除 target_table 和 target_field
                            if "target_table" in obj:
                                del obj["target_table"]
                            if "target_field" in obj:
                                del obj["target_field"]
                            for key, value in obj.items():
                                process_filter_conditions(value)
                        elif isinstance(obj, list):
                            for item in obj:
                                process_filter_conditions(item)
                    
                    process_filter_conditions(modified_property["filter_info"])
                
                # 处理关联字段中的 formula 字段
                if "formula" in modified_property and modified_property["formula"]:
                    formula_str = modified_property["formula"]
                    formula_str = replace_formula_ids(formula_str, table_name_map, field_name_map, all_field_name_map)
                    modified_property["formula"] = formula_str
                
                field_info["property"] = modified_property
        # 如果是公式类型，添加公式配置
        if field_type_code == 20:
            property_data = field.get("property", {})
            if property_data:
                # 复制一份用于修改
                modified_property = dict(property_data)
                
                # 处理公式表达式中的 table id 和 field id
                if "formula_expression" in modified_property:
                    formula = modified_property["formula_expression"]
                    formula = replace_formula_ids(formula, table_name_map, field_name_map, all_field_name_map)
                    modified_property["formula_expression"] = formula
                
                # 如果有 formula 字段，也需要处理一下
                if "formula" in modified_property and modified_property["formula"]:
                    formula_str = modified_property["formula"]
                    formula_str = replace_formula_ids(formula_str, table_name_map, field_name_map, all_field_name_map)
                    modified_property["formula"] = formula_str
                
                field_info["formula_expression"] = modified_property.get("formula_expression")
                field_info["formula_result_type"] = modified_property.get("formula_result_type")
                field_info["formula"] = modified_property.get("formula")
                field_info["property"] = modified_property
        fields_list.append(field_info)

    # 获取记录（如果需要）
    records_data = []
    if fetch_records:
        records_url = f"{api_base}/open-apis/bitable/v1/apps/{base_token}/tables/{table_id}/records"
        records = get_all_pages(records_url, headers)
        # 解析记录数据，将字段ID转换为字段名
        for record in records:
            record_fields = record.get("fields", {})
            parsed_record = {}
            for field_id, value in record_fields.items():
                field_name = field_name_map.get(field_id, field_id)
                parsed_record[field_name] = value
            records_data.append(parsed_record)

    # 不获取views信息
    view_count = 0

    table_info = {
        "table_id": table_id,
        "table_name": table_name,
        "view_count": view_count,
        "fields": fields_list
    }
    
    # 如果获取了记录，添加到结果中
    if fetch_records:
        table_info["records"] = records_data

    return table_info


def extract_bitable_info(feishu_url, headers=None, fetch_records=True, api_base=None):
    """
    从飞书多维表格链接提取数据表 metadata
    
    Args:
        feishu_url: 飞书多维表格链接
        headers: 可选的请求头，如果不传则自动获取
        fetch_records: 是否获取数据表记录内容，默认为 True
        
    Returns:
        包含 base_token 和 tables 信息的字典
    """
    if headers is None:
        headers = get_feishu_headers()
        
    base_token = parse_app_id(feishu_url)
    api_base = api_base or get_open_api_base(feishu_url)

    tables_url = f"{api_base}/open-apis/bitable/v1/apps/{base_token}/tables"
    tables = get_all_pages(tables_url, headers)
    
    # 先获取所有表的基本信息（用于公式字段的 table id 替换）
    all_tables_info = []
    # 同时构建 table id 到 table name 的映射
    table_name_map = {}
    for table in tables:
        tbl_id = table.get("table_id")
        tbl_name = table.get("table_name") or table.get("name")
        all_tables_info.append({
            "table_id": tbl_id,
            "table_name": tbl_name
        })
        if tbl_id and tbl_name:
            table_name_map[tbl_id] = tbl_name
    
    # 获取所有表的所有字段信息（用于跨表字段引用）
    all_field_name_map = {}
    for table in tables:
        tbl_id = table.get("table_id")
        if tbl_id:
            try:
                tbl_fields_url = f"{api_base}/open-apis/bitable/v1/apps/{base_token}/tables/{tbl_id}/fields"
                tbl_fields = get_all_pages(tbl_fields_url, headers)
                for fld in tbl_fields:
                    fld_id = fld.get("field_id")
                    fld_name = fld.get("field_name")
                    if fld_id and fld_name:
                        all_field_name_map[fld_id] = fld_name
            except Exception as e:
                print(f"获取表 {tbl_id} 的字段信息时出错: {e}")
                pass  # 如果某个表获取失败，跳过

    # 使用并发处理每个表
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    tables_info = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        # 提交所有表的处理任务
        futures = {executor.submit(process_single_table, table, base_token, headers, fetch_records, all_tables_info, table_name_map, all_field_name_map, api_base): table for table in tables}
        
        # 收集结果
        for future in as_completed(futures):
            try:
                table_info = future.result()
                tables_info.append(table_info)
            except Exception as e:
                print(f"处理表时出错: {e}")

    # 按原顺序排序结果
    # 创建一个table_id到原索引的映射
    id_to_index = {table.get("table_id"): i for i, table in enumerate(tables)}
    # 排序
    tables_info.sort(key=lambda x: id_to_index.get(x.get("table_id"), len(tables)))

    return {
        "base_token": base_token,
        "tables": tables_info
    }


def parse_bitable_url(feishu_url):
    """
    解析单个飞书链接，返回数据表 metadata 的 JSON 字符串
    
    Args:
        feishu_url: 飞书多维表格链接
        
    Returns:
        JSON 字符串，包含数据表 metadata
    """
    try:
        table_info = extract_bitable_info(feishu_url)
        return json.dumps(table_info, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"解析失败: {str(e)}"}, ensure_ascii=False)
