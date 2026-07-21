@echo off
rem Instala os scripts de menu no DaVinci Resolve (pasta Utility do usuario).
rem So os NN_*.py sao scripts de menu; transcrever_palavras.py fica no cofre.
setlocal
set "DESTINO=%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility"
set "ORIGEM=%~dp0"

if not exist "%DESTINO%" mkdir "%DESTINO%"

for %%F in ("%ORIGEM%[0-9][0-9]_*.py") do (
    copy /Y "%%F" "%DESTINO%\" >nul
    echo instalado: %%~nxF
)

echo.
echo Pronto. No Resolve: menu Workspace ^> Scripts.
echo (Se o Resolve ja estava aberto, feche e reabra pra listar.)
pause
