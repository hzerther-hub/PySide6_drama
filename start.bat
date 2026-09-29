@echo off
rem 易好短剧 · PySide6 版 启动脚本
cd /d "%~dp0"
py -3.13 -m app.main 2>nul || python -m app.main
