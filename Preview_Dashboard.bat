@echo off
echo ================================================================
echo   SaaS Customer Churn & Revenue Retention Intelligence
echo   Local Dashboard Launcher
echo ================================================================
echo.
echo Launching local HTTP server on port 8080...
start http://localhost:8080
python -m http.server 8080 --directory docs
pause
