@echo off
REM Script de limpeza do Gemini Code

echo Limpando arquivos temporários e cache...

REM Remove cache Python
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "gemini_code\__pycache__" rmdir /s /q "gemini_code\__pycache__"
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

REM Remove cache pytest
if exist ".pytest_cache" rmdir /s /q ".pytest_cache"

REM Remove arquivos temporários
del /s /q *.tmp 2>nul
del /s /q *.bak 2>nul
del /s /q *~ 2>nul
del /s /q *.swp 2>nul

REM Remove logs antigos (mais de 7 dias)
if exist "logs" (
    forfiles /p logs /s /m *.log /d -7 /c "cmd /c del @path" 2>nul
)

REM Remove cache do Gemini Code
if exist ".gemini_code\cache" rmdir /s /q ".gemini_code\cache"

echo Limpeza concluída!
pause