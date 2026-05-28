# 飞书多维表格数据管理工具

一个基于 PyQt5 的图形界面工具，用于获取飞书（Lark）多维表格的完整数据，包括表结构、字段配置、记录内容、仪表盘、工作流、高级权限和表单配置等。

## 功能特性

- **五大功能模块**：
  - 📊 数据表：获取表结构、字段配置和记录内容
  - 📈 仪表盘：提取仪表盘配置快照
  - 🔄 工作流：获取工作流配置信息
  - 🔐 高级权限：提取角色和权限配置
  - 📝 表单：提取表单配置和字段信息

- **多种认证方式**：支持 Token、OAuth 和 Cookie 三种认证方式
- **文本对比工具**：内置文本对比功能，支持并排显示差异
- **JSON 导出**：所有获取结果可导出为 JSON 格式文件
- **现代化界面**：飞书风格的简洁美观界面设计

## 项目结构

```
table_meta_data/
├── main.py              # 程序主入口
├── icon.png             # 应用图标
├── build.bat            # 打包脚本
├── requirements.txt     # 依赖包列表
├── config/              # 配置模块
│   ├── __init__.py
│   └── settings.py      # 配置参数
├── ui/                  # 用户界面模块
│   ├── __init__.py
│   ├── styles.py        # 界面样式
│   ├── main_window.py   # 主窗口
│   ├── table_panel.py   # 数据表面板
│   ├── simple_panel.py  # 通用面板（仪表盘、工作流、表单）
│   ├── permission_panel.py  # 高级权限面板
│   ├── result_panel.py  # 结果显示面板
│   ├── text_diff_dialog.py  # 文本对比对话框
│   ├── search_logic.py  # 搜索功能逻辑
│   └── search_widget.py # 搜索组件
├── workers/             # 后台工作线程
│   ├── __init__.py
│   ├── oauth_worker.py  # OAuth 认证线程
│   ├── cookie_worker.py # Cookie 获取线程
│   └── fetch_worker.py  # 数据获取线程
├── api/                 # API 接口模块
│   ├── __init__.py
│   ├── feishu_api.py    # 开放 API 接口（数据表）
│   ├── feishu_cookie_api.py  # Cookie 方式接口
│   ├── feishu_dashboard_api.py  # 仪表盘接口
│   ├── feishu_workflow_api.py   # 工作流接口
│   ├── feishu_permission_api.py # 高级权限接口
│   └── feishu_form_api.py       # 表单接口
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
- `pyinstaller` - 打包工具

## 使用方法

### 1. 运行程序

```bash
python main.py
```

### 2. 选择功能模块

左侧导航栏选择要使用的功能模块：
- 📊 数据表
- 📈 仪表盘
- 🔄 工作流
- 🔐 高级权限
- 📝 表单

### 3. 配置认证

#### Token 方式（推荐，支持所有模块）
1. 打开飞书开放平台 API 调试台
2. 获取 User Access Token
3. 粘贴到 Token 输入框中

#### OAuth 方式
1. 在飞书开放平台创建应用
2. 配置回调地址为 `http://localhost:3000`
3. 输入 App ID 和 App Secret
4. 点击"浏览器一键授权"进行 OAuth 认证

#### Cookie 方式（用于仪表盘、工作流、表单）
- **自动获取**：点击"启动浏览器"，在打开的浏览器中登录飞书后点击"已登录"
- **手动输入**：从浏览器开发者工具中复制 Cookie 并粘贴

### 4. 获取数据

#### 数据表
1. 输入飞书多维表格链接
2. （可选）勾选是否需要获取记录内容
3. 选择认证方式（Token/OAuth/Cookie）并配置
4. 点击"获取数据"

#### 仪表盘/工作流/表单
1. 输入对应链接（表单链接格式：`https://bytedance.larkoffice.com/share/base/form/...`）
2. 使用 Cookie 方式认证
3. 点击"获取仪表盘snapshot"、"获取工作流数据"或"获取表单数据"

### 5. 文本对比功能

点击右上角的"📄 文本对比"按钮：
- 在左右两个编辑框中分别输入要对比的文本
- 点击"开始对比"查看差异
- 一致内容显示绿色背景，不一致内容显示红色背景
- 支持交换文本和清空功能
- 可导出 JSON 结果

### 6. 导出结果

获取成功后，可点击"导出 JSON"按钮将结果保存到本地。

## 常见问题

**Q: 获取失败提示权限不足？**
A: 请确保你的账号对该多维表格有访问权限，Token 或 OAuth 认证信息正确有效。

**Q: Cookie 方式提示找不到表？**
A: 请确保链接中包含 `table=tbl...` 参数，可以在浏览器中打开对应数据表后复制链接。

**Q: 数据表字段中引用了其他表的 ID？**
A: Token 和 OAuth 方式会自动将关联字段中的表 ID 和字段 ID 替换为对应的名称。

**Q: 仪表盘/工作流/高级权限提示没有设置？**
A: 这是正常现象，表示该多维表格没有配置对应的功能。

**Q: 文本对比时文字显示不全？**
A: 文本编辑框支持滚动查看所有内容，两侧内容会同步滚动。

## 打包成应用

使用提供的 `build.bat` 脚本可以将程序打包成独立的可执行文件：

```bash
build.bat
```

打包完成后，可执行文件位于 `dist/` 目录下。

## 技术栈

- **GUI 框架**: PyQt5
- **HTTP 请求**: requests
- **浏览器自动化**: Selenium
- **数据解析**: JSON, Base64, GZip
- **打包工具**: PyInstaller

## 许可证

MIT License
