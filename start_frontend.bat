@echo off
echo =====================================
echo           启动前端项目
echo =====================================
echo.

:: 进入 frontend 文件夹
cd /d "%~dp0frontend"

:: 启动前端开发服务
npm run dev

pause