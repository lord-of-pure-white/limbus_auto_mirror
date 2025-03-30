@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 脚本正在启动，大约需要5~30s，请等待...
start "" pythonw.exe main.py
timeout /t 5 >nul