@echo off

REM 删除JGSL\__pycache__目录下的所有文件
if exist "JGSL\__pycache__" (
    for /f "delims=" %%i in ('dir /b "JGSL\__pycache__" ^| findstr /v "\.gitkeep"') do (
        del /f /q "JGSL\__pycache__\%%i"
    )
)

REM 删除Logs目录下的所有文件
if exist "Logs" (
    for /f "delims=" %%i in ('dir /b "Logs" ^| findstr /v "\.gitkeep"') do (
        del /f /q "Logs\%%i"
    )
)

echo 清理完成！
pause