@echo off
REM KRAFTD E2E TEST RUNNER (Windows)
REM Quick start script for running end-to-end workflow tests

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║                    KRAFTD E2E TEST RUNNER                          ║
echo ║           End-to-End Workflow and Quota Enforcement Tests          ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

REM Check if token provided
if "%1"=="" (
    echo ❌ ERROR: JWT token required
    echo.
    echo 📋 USAGE:
    echo    run_e2e_tests.bat ^<JWT_TOKEN^>
    echo.
    echo 📌 EXAMPLE:
    echo    run_e2e_tests.bat "eyJhbGciOiJIUzI1NiIs..."
    echo.
    echo 📚 For more information, see: KRAFTD_E2E_TESTING_GUIDE.md
    echo.
    exit /b 1
)

set TOKEN=%1

REM Check if server is running
echo 🔍 Checking server health...
curl -s http://localhost:8000/api/v1/health > nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Server not running on http://localhost:8000
    echo.
    echo 💡 Start the server with:
    echo    cd backend ^&^& python main.py
    echo.
    exit /b 1
)
echo ✅ Server is running
echo.

REM Check if Python is available
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python not found
    echo 💡 Install Python 3.8+ and try again
    exit /b 1
)

REM Check if requests library is available
echo 📦 Checking dependencies...
python -c "import requests" 2>nul
if errorlevel 1 (
    echo ⚠️  Missing requests library
    echo 💡 Install with: pip install requests
    exit /b 1
)
echo ✅ Dependencies OK
echo.

REM Run the test suite
echo 🚀 Running E2E test suite...
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

python KRAFTD_E2E_TEST.py %TOKEN%
set EXIT_CODE=%errorlevel%

echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if %EXIT_CODE% equ 0 (
    echo ✅ All tests passed!
    echo.
    echo 📊 Next Steps:
    echo    1. Review test output above
    echo    2. Verify Cosmos DB documents
    echo    3. Check quota counters
    echo    4. Deploy to Azure if ready
    echo.
) else (
    echo ❌ Some tests failed
    echo.
    echo 🔧 Troubleshooting:
    echo    1. Check server logs
    echo    2. Verify Cosmos DB connection
    echo    3. Review KRAFTD_E2E_TESTING_GUIDE.md for details
    echo.
)

exit /b %EXIT_CODE%
