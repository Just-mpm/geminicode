@echo off
REM ===============================================
REM  Gemini Code - Inicializador Completo
REM ===============================================

echo.
echo =========================================
echo    GEMINI CODE v1.0.0-supreme
echo    Assistente IA Superior
echo =========================================
echo.

REM Verifica se Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python não encontrado!
    echo Por favor instale Python 3.8 ou superior
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Verifica se a API key está configurada
if "%GEMINI_API_KEY%"=="" (
    echo [!] API Key do Gemini não configurada
    echo.
    echo Para configurar:
    echo 1. Obtenha sua chave em: https://makersuite.google.com/app/apikey
    echo 2. Execute: setx GEMINI_API_KEY "sua-chave-aqui"
    echo.
    set /p "temp_key=Digite sua API Key agora (ou pressione Enter para continuar sem): "
    if not "!temp_key!"=="" (
        set GEMINI_API_KEY=!temp_key!
    )
)

REM Navega para o diretório do projeto
cd /d "%~dp0"

REM Verifica se as dependências estão instaladas
echo [*] Verificando dependências...
python -c "import google.generativeai" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Instalando dependências necessárias...
    pip install -r requirements.txt
)

REM Menu de opções
:menu
echo.
echo Escolha uma opção:
echo.
echo   [1] Iniciar REPL Interativo (Recomendado)
echo   [2] Iniciar Interface Principal
echo   [3] Executar Teste de Sistema
echo   [4] Verificar Saúde do Sistema
echo   [5] Atualizar Dependências
echo   [6] Configurar API Key
echo   [7] Limpar Cache e Logs
echo   [8] Sair
echo.
set /p choice="Digite sua escolha (1-8): "

if "%choice%"=="1" goto start_repl
if "%choice%"=="2" goto start_main
if "%choice%"=="3" goto run_tests
if "%choice%"=="4" goto health_check
if "%choice%"=="5" goto update_deps
if "%choice%"=="6" goto config_api
if "%choice%"=="7" goto clean_cache
if "%choice%"=="8" goto end

echo [!] Opção inválida!
goto menu

:start_repl
echo.
echo [*] Iniciando REPL Interativo...
echo.
echo ========================================
echo   Comandos disponíveis:
echo   /help    - Mostra ajuda
echo   /cost    - Verifica custos
echo   /doctor  - Diagnóstico do sistema
echo   /memory  - Status da memória
echo   Ctrl+D   - Sair
echo ========================================
echo.
python gemini_repl_launcher.py
goto menu

:start_main
echo.
echo [*] Iniciando Interface Principal...
python main.py
goto menu

:run_tests
echo.
echo [*] Executando Teste de Sistema...
python tests/test_system_functionality.py
echo.
pause
goto menu

:health_check
echo.
echo [*] Verificando Saúde do Sistema...
python -c "import asyncio; from gemini_code.core.master_system import GeminiCodeMasterSystem; asyncio.run(GeminiCodeMasterSystem('.').comprehensive_health_check())"
pause
goto menu

:update_deps
echo.
echo [*] Atualizando dependências...
pip install --upgrade -r requirements.txt
echo [*] Dependências atualizadas!
pause
goto menu

:config_api
echo.
echo [*] Configuração da API Key do Gemini
echo.
echo Obtenha sua chave em: https://makersuite.google.com/app/apikey
echo.
set /p "new_key=Digite sua API Key: "
if not "%new_key%"=="" (
    setx GEMINI_API_KEY "%new_key%"
    set GEMINI_API_KEY=%new_key%
    echo [*] API Key configurada com sucesso!
    echo [!] Pode ser necessário reiniciar o terminal para aplicar
) else (
    echo [!] Nenhuma chave fornecida
)
pause
goto menu

:clean_cache
echo.
echo [*] Limpando cache e logs...
if exist ".gemini_code\cache" rmdir /s /q ".gemini_code\cache"
if exist "logs" (
    echo [?] Deseja limpar os logs também? (S/N)
    set /p "clean_logs="
    if /i "%clean_logs%"=="S" (
        del /q "logs\*.log" 2>nul
        echo [*] Logs limpos!
    )
)
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist ".pytest_cache" rmdir /s /q ".pytest_cache"
echo [*] Cache limpo com sucesso!
pause
goto menu

:end
echo.
echo Obrigado por usar o Gemini Code!
echo.
timeout /t 2 >nul
exit /b 0