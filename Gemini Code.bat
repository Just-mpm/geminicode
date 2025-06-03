@echo off
setlocal enabledelayedexpansion
title GEMINI CODE - Iniciador

echo.
echo ===============================================
echo   GEMINI CODE - INICIADOR DO SISTEMA
echo ===============================================
echo.

echo [VERIFICANDO PYTHON...]
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo.
    echo SOLUCAO:
    echo 1. Baixe Python em: https://python.org/downloads/
    echo 2. Marque "Add Python to PATH" na instalacao
    echo 3. Reinicie o computador
    echo 4. Execute este arquivo novamente
    echo.
    start https://python.org/downloads/
    pause
    exit
)

python --version
echo Python encontrado com sucesso!
echo.

echo [VERIFICANDO DEPENDENCIAS...]
python -c "import google.generativeai" >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias essenciais...
    python -m pip install --user google-generativeai pandas sqlalchemy aiofiles python-dotenv click rich
    if errorlevel 1 (
        echo ERRO na instalacao de dependencias!
        pause
        exit
    )
    echo Dependencias instaladas!
) else (
    echo Dependencias OK!
)
echo.

echo [VERIFICANDO API KEY...]
if exist .env (
    findstr "GEMINI_API_KEY" .env >nul 2>&1
    if not errorlevel 1 (
        echo API Key configurada no arquivo .env
    ) else (
        echo Arquivo .env existe mas sem API Key
        goto config_api
    )
) else (
    if "%GEMINI_API_KEY%"=="" (
        echo API Key nao configurada
        goto config_api
    ) else (
        echo API Key encontrada em variavel de ambiente
    )
)
goto iniciar

:config_api
echo.
echo CONFIGURACAO DA API KEY
echo =======================
echo.
echo Para usar o Gemini Code completo, voce precisa de uma API Key GRATUITA:
echo.
echo Como obter:
echo 1. Acesse: https://makersuite.google.com/app/apikey
echo 2. Faca login com conta Google
echo 3. Clique "Create API Key"
echo 4. Copie a chave
echo.

set /p abrir=Abrir pagina para obter API Key? (s/N): 
if /i "!abrir!"=="s" (
    start https://makersuite.google.com/app/apikey
    echo Aguarde obter a API Key...
    timeout /t 5 >nul
)

echo.
set /p api_key=Cole sua API Key (ou Enter para modo demo): 

if not "!api_key!"=="" (
    echo GEMINI_API_KEY=!api_key! > .env
    echo API Key salva com sucesso!
) else (
    echo Modo demonstracao ativado
)

:iniciar
echo.
echo [INICIANDO GEMINI CODE...]
echo ===========================
echo.
echo Sistema pronto para usar!
echo.
echo Comandos de exemplo:
echo - "Crie um projeto Python"
echo - "Analise a seguranca do codigo"
echo - "Gere um relatorio"
echo - "sair" para encerrar
echo.

python main.py
set resultado=%errorlevel%

echo.
echo ===========================
if !resultado! EQU 0 (
    echo Gemini Code executado com sucesso!
) else (
    echo Erro na execucao - codigo: !resultado!
    echo.
    echo Possiveis solucoes:
    echo - Verifique se Python esta instalado
    echo - Verifique se as dependencias foram instaladas
    echo - Verifique se a API Key esta correta
)

echo.
echo O que fazer agora?
echo [1] Executar novamente
echo [2] Reinstalar dependencias
echo [3] Sair
echo.

set /p escolha=Digite sua opcao (1-3): 

if "!escolha!"=="1" goto iniciar
if "!escolha!"=="2" goto reinstalar
if "!escolha!"=="3" goto sair

echo Opcao invalida
timeout /t 2 >nul
goto iniciar

:reinstalar
echo.
echo REINSTALANDO DEPENDENCIAS...
echo ============================
echo.

echo Atualizando pip...
python -m pip install --upgrade pip --user

echo.
echo Instalando pacotes essenciais...
python -m pip install --user google-generativeai pandas sqlalchemy aiofiles python-dotenv click rich pyyaml

echo.
echo Instalando pacotes de analise...
python -m pip install --user matplotlib seaborn numpy scipy scikit-learn

echo.
echo Instalando pacotes de seguranca...
python -m pip install --user safety cryptography

echo.
echo Reinstalacao concluida!
echo.

python -c "
try:
    import google.generativeai, pandas
    print('Teste OK - Dependencias funcionando!')
except Exception as e:
    print(f'Problema: {e}')
"

echo.
pause
goto iniciar

:sair
echo.
echo SAINDO...
echo.
echo Obrigado por usar o Gemini Code!
echo Para usar novamente, execute este arquivo
echo.
timeout /t 3 >nul
exit