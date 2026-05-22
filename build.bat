@echo off
echo ========================================
echo 飞书多维表格元数据工具 - 打包脚本
echo ========================================
echo.

REM 检查是否安装了 PyInstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [INFO] PyInstaller 未安装，正在安装...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] PyInstaller 安装失败！
        pause
        exit /b 1
    )
)

echo.
echo [INFO] 开始打包...
echo.

REM 使用 spec 文件进行打包（包含资源文件）
pyinstaller --clean build.spec

if errorlevel 1 (
    echo.
    echo [ERROR] 打包失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo [SUCCESS] 打包完成！
echo ========================================
echo.
echo 可执行文件位于: dist\飞书多维表格元数据工具.exe
echo 视频文件已包含在打包中！
echo.

pause
