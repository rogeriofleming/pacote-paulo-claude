@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ============================================================
echo   KIT DE EDICAO DE VIDEO - instalador (Windows)
echo   Baixa e configura tudo que as skills precisam pra rodar.
echo ============================================================
echo.

REM --- 1. Python ---
python --version >nul 2>&1
if errorlevel 1 (
  echo [ERRO] Python 3.10+ nao encontrado.
  echo        Instale em https://www.python.org/downloads/ ^(marque "Add to PATH"^)
  echo        e rode este INSTALAR.bat de novo.
  pause
  exit /b 1
)
echo [ok] Python encontrado.

REM --- 2. uv e ffmpeg: instala o que faltar (via winget) ---
set NEED_RESTART=0

where uv >nul 2>&1
if errorlevel 1 (
  echo [..] uv nao encontrado. Instalando com winget...
  winget install --id astral-sh.uv -e --accept-package-agreements --accept-source-agreements
  set NEED_RESTART=1
) else (
  echo [ok] uv encontrado.
)

where ffmpeg >nul 2>&1
if errorlevel 1 (
  echo [..] ffmpeg nao encontrado. Instalando o build do gyan.dev com winget...
  echo      ^(esse build especifico passa pelo Smart App Control - ver WINDOWS_SETUP.md 4^)
  winget install --id Gyan.FFmpeg -e --accept-package-agreements --accept-source-agreements
  set NEED_RESTART=1
) else (
  echo [ok] ffmpeg encontrado.
)

if "%NEED_RESTART%"=="1" (
  echo.
  echo ============================================================
  echo   Instalei uv e/ou ffmpeg. FECHE esta janela e rode o
  echo   INSTALAR.bat DE NOVO - o Windows so enxerga os programas
  echo   novos num terminal novo. A 2a rodada termina a instalacao.
  echo ============================================================
  pause
  exit /b 0
)

REM --- 3. dependencias Python (faster-whisper etc.) ---
echo.
echo [..] Instalando as dependencias Python ^(faster-whisper, etc^)...
uv sync --all-extras
if errorlevel 1 (
  echo [ERRO] Falhou o "uv sync". Veja a mensagem acima.
  pause
  exit /b 1
)
echo [ok] Dependencias instaladas.

REM --- 4. Baixar o modelo Whisper e testar a transcricao ---
echo.
echo [..] Baixando o modelo Whisper "medium" ^(~1,5 GB, so na 1a vez^) e testando...
ffmpeg -f lavfi -i anullsrc=r=16000:cl=mono -t 1 -y "%TEMP%\kit_teste_audio.wav" >nul 2>&1
uv run python scripts_resolve\transcrever_palavras.py "%TEMP%\kit_teste_audio.wav"
if errorlevel 1 (
  echo [AVISO] A transcricao de teste falhou. Se o erro citar DLL / Smart App
  echo         Control, a solucao ja esta em WINDOWS_SETUP.md secao 4.
) else (
  echo [ok] Transcricao funcionando ^(modelo baixado^).
)
del "%TEMP%\kit_teste_audio.wav" >nul 2>&1

REM --- 5. Testar o pipeline de video (prova ffmpeg + scripts) ---
echo.
echo [..] Testando o pipeline de video ^(reframe 9:16^)...
uv run python scripts_resolve\40_reframe_vertical.py --autoteste
if errorlevel 1 (
  echo [AVISO] O autoteste de video falhou - confira o ffmpeg.
) else (
  echo [ok] Pipeline de video funcionando.
)

echo.
echo ============================================================
echo   PRONTO. As skills de edicao ja podem rodar.
echo   Opcional: rode scripts_resolve\instalar_scripts.bat para
echo   ter os cortes DENTRO do DaVinci Resolve ^(menu Workspace^).
echo   Leia kit-edicao-video\COMO_USAR.md para usar as skills.
echo ============================================================
echo.
pause
