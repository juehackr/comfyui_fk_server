@echo off
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo NO Node.js 
) else (
    node -v
    echo Node.js OK
    npm install
)
pause