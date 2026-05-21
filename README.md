# 飞书多维表格元数据获取工具

一个基于 PyQt5 的图形界面工具，用于获取飞书（Lark）多维表格的元数据信息，包括表结构、字段配置、记录内容等。

## 功能特性

- **多种认证方式**：支持 Token、OAuth 和 Cookie 三种认证方式
- **完整元数据获取**：获取表名、字段名、字段类型、选项配置等完整信息
- **记录内容导出**：可选择是否同时获取数据表记录内容
- **多种字段类型**：支持文本、数字、单选、多选、日期、人员、公式等所有字段类型
- **JSON 导出**：获取结果可导出为 JSON 格式文件
- **美观界面**：基于 Element Plus 风格的现代化界面设计

## 项目结构

```
table_meta_data/
├── main.py              # 程序主入口
├── config/              # 配置模块
│   ├── __init__.py
│   └── settings.py      # 配置参数
├── ui/                  # 用户界面模块
│   ├── __init__.py
│   ├── styles.py        # 界面样式
│   └── main_window.py   # 主窗口
├── workers/             # 后台工作线程
│   ├── __init__.py
│   ├── oauth_worker.py  # OAuth 认证线程
│   ├── cookie_worker.py # Cookie 获取线程
│   └── fetch_worker.py  # 数据获取线程
├── api/                 # API 接口模块
│   ├── __init__.py
│   ├── feishu_api.py    # 开放 API 接口
│   └── feishu_cookie_api.py  # Cookie 方式接口
└── requirements.txt     # 依赖包列表
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 依赖说明

- `requests` - HTTP 请求库，用于 API 调用
- `PyQt5` - 图形界面框架
- `selenium` - 浏览器自动化工具（Cookie 方式自动获取时需要）
- `webdriver-manager` - 自动管理浏览器驱动

## 使用方法

### 1. 运行程序

```bash
python main.py
```

### 2. 选择认证方式

#### Token 方式（推荐）
1. 打开飞书开放平台 API 调试台
2. 获取 User Access Token
3. 粘贴到 Token 输入框中

#### OAuth 方式
1. 在飞书开放平台创建应用
2. 配置回调地址为 `http://localhost:3000`
3. 输入 App ID 和 App Secret
4. 点击"浏览器一键授权"进行 OAuth 认证

#### Cookie 方式（不推荐）
- **注意**：Cookie 方式仅支持获取当前数据表，不支持批量获取
- **方法一（自动）**：点击"启动浏览器"，在打开的浏览器中登录飞书后点击"已登录"
- **方法二（手动）**：从浏览器开发者工具中复制 Cookie 并粘贴

### 3. 配置目标

1. 输入飞书多维表格链接
2. 勾选是否需要获取记录内容
3. 点击"获取数据"按钮

### 4. 导出结果

获取成功后，可点击"导出 JSON"按钮将结果保存到本地。

## 使用说明

### 链接格式

支持的飞书多维表格链接格式：
```
https://xxx.feishu.cn/base/xxxxxx
https://xxx.feishu.cn/base/xxxxxx?table=tblxxxxxx
```

### Cookie 方式限制

- 仅支持获取当前打开的数据表
- 需要链接中包含 `table=tbl...` 参数
- 不支持获取记录内容
- 建议使用 Token 或 OAuth 方式获得更好体验

## 输出格式

```json
{
  "base_token": "xxxxx",
  "tables": [
    {
      "table_id": "tblxxxxx",
      "table_name": "表名",
      "view_count": 0,
      "fields": [
        {
          "field_id": "fldxxxxx",
          "field_name": "字段名",
          "field_type_code": 1,
          "field_type_name": "文本",
          "is_primary": false,
          "options": ["选项1", "选项2"],
          "property": {}
        }
      ],
      "records": [
        {
          "字段名": "字段值"
        }
      ]
    }
  ]
}
```

## 字段类型映射

| 类型代码 | 类型名称 |
|---------|---------|
| 1 | 文本 |
| 2 | 数字 |
| 3 | 单选 |
| 4 | 多选 |
| 5 | 日期 |
| 7 | 复选框 |
| 11 | 人员 |
| 13 | 电话号码 |
| 15 | 超链接 |
| 17 | 附件 |
| 18 | 单项关联 |
| 19 | 查找引用 |
| 20 | 公式 |
| 21 | 双向关联 |
| 22 | 地理位置 |
| 23 | 群组 |
| 1001 | 创建时间 |
| 1002 | 最后更新时间 |
| 1003 | 创建人 |
| 1004 | 修改人 |
| 1005 | 自动编号 |
| 3001 | 按钮 |

## 常见问题

**Q: 获取失败提示权限不足？**
A: 请确保你的账号对该多维表格有访问权限，Token 或 OAuth 认证信息正确有效。

**Q: Cookie 方式提示找不到表？**
A: 请确保链接中包含 `table=tbl...` 参数，可以在浏览器中打开对应数据表后复制链接。

**Q: 字段中引用了其他表的 ID？**
A: Token 和 OAuth 方式会自动将关联字段中的表 ID 和字段 ID 替换为对应的名称。

## 技术栈

- **GUI 框架**: PyQt5
- **HTTP 请求**: requests
- **浏览器自动化**: Selenium
- **数据解析**: JSON, Base64, GZip

## 许可证

MIT License

---

需要帮助请联系作者：[飞书](https://www.larkoffice.com/invitation/page/add_contact/?token=6e2ma113-ab71-48a6-a684-2c8bb2e38e32)
