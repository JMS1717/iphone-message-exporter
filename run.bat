@echo off
setlocal

:menu
cls
echo Select an option:
echo 1. Extract all messages
echo 2. Extract only sent messages
echo 3. Exit

set /p choice="Enter your choice: "

if "%choice%"=="1" goto extract_all
if "%choice%"=="2" goto extract_sent
if "%choice%"=="3" goto exit

echo Invalid choice.
pause
goto menu

:extract_all
set /p backup_path="Enter the path to your iPhone backup directory: "
python extract_sms.py "%backup_path%"
pause
goto menu

:extract_sent
set /p backup_path="Enter the path to your iPhone backup directory: "
python extract_sent_texts.py "%backup_path%"
pause
goto menu

:exit
endlocal
