@echo off
REM Codex kancasi -> Git Bash koprusu. URETILMIS DOSYA:
REM   python D:/TarikOS/.claude/scripts/render_codex_hooks.py --project "<proje-dizini>"
REM
REM Neden .cmd: Codex kanca komutunu KABUKTAN GECIRMEDEN calistirir; bu makinede
REM olculdu (codex-cli 0.153.0) -- "bash.exe betik.sh" bicimi dogrudan cagrildiginda
REM "Failed" verir, .cmd shim'i calisir. Is yine ayni brain-rules.sh dosyasinda:
REM Claude ve Codex tek kaynagi paylasir, iki kopya kural mantigi yok.
setlocal
set "BEYIN_BASH=C:/Program Files/Git/bin/bash.exe"
if exist "%BEYIN_BASH%" goto run
for /f "delims=" %%i in ('where bash 2^>nul') do set "BEYIN_BASH=%%i"
if exist "%BEYIN_BASH%" goto run
REM Bash yok. Sessizce 0 ile cikmak, calisan bir kancadan AYIRT EDILEMEZ:
REM ekranda 'Completed' yazar ve oturum kuralsiz kosar. Bunun yerine bagir.
echo {"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"[Beyin uyarisi] bash bulunamadi, TarikOS ev kurallari ENJEKTE EDILEMEDI. Git Bash kur ya da PATH'e ekle."}}
exit /b 0
:run
"%BEYIN_BASH%" "%~dp0brain-rules.sh"
exit /b 0
