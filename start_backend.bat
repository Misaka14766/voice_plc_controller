@echo off
echo =====================================
echo        启动 FastAPI 后端服务
echo        虚拟环境: Iris
echo        入口: backend.app.api:app
echo =====================================
echo.

:: 自动激活 conda 环境
call conda activate Iris

:: 启动后端
uvicorn backend.app.api:app ^
--host 0.0.0.0 ^
--port 8000 ^
--reload

pause