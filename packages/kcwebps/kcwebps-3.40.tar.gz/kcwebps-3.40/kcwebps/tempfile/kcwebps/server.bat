@echo off
if "%1" == "h" goto begin
mshta vbscript:createobject("wscript.shell").run("%~nx0 h",0)(window.close)&&exit
:begin
timeout /t 1 /nobreak
kcwebps server
timeout /t 3 /nobreak