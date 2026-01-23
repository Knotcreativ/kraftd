#!/usr/bin/env python3
"""
KRAFTD MARKET READINESS CHECK & DEPLOYMENT PREP
===============================================

This script validates Kraftd Docs readiness for market deployment.
Checks infrastructure, fixes critical issues, and prepares for production.

Usage: python market_readiness.py
"""

import os
import sys
import subprocess
import json
from pathlib import Path

class MarketReadinessChecker:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        self.issues = []
        self.fixes = []

    def log(self, message, level="INFO"):
        """Log a message with level"""
        print(f"[{level}] {message}")

    def check_infrastructure_alignment(self):
        """Check if Bicep template matches deployment scripts"""
        self.log("Checking infrastructure alignment...")

        # Check Bicep file
        bicep_file = self.project_root / "infrastructure" / "main.bicep"
        if not bicep_file.exists():
            self.issues.append("Bicep template missing")
            return

        with open(bicep_file, 'r') as f:
            bicep_content = f.read()

        # Check deployment scripts
        deploy_bat = self.project_root / "deploy-azure.bat"
        deploy_sh = self.project_root / "deploy-azure.sh"

        container_apps_refs = []
        app_service_refs = []

        if deploy_bat.exists():
            with open(deploy_bat, 'r') as f:
                if "Container Apps" in f.read():
                    container_apps_refs.append("deploy-azure.bat")

        if deploy_sh.exists():
            with open(deploy_sh, 'r') as f:
                if "Container Apps" in f.read():
                    container_apps_refs.append("deploy-azure.sh")

        if "Microsoft.Web/serverfarms" in bicep_content:
            app_service_refs.append("main.bicep")

        if container_apps_refs and app_service_refs:
            self.issues.append(f"Infrastructure mismatch: {app_service_refs} uses App Service, {container_apps_refs} uses Container Apps")
            self.fixes.append("Update Bicep template to use Azure Container Apps instead of App Service")

    def check_dependencies(self):
        """Check if all required dependencies are installed"""
        self.log("Checking dependencies...")

        requirements_file = self.backend_dir / "requirements.txt"
        if not requirements_file.exists():
            self.issues.append("requirements.txt missing")
            return

        # Check if virtual environment exists
        venv_dir = self.backend_dir / ".venv"
        if not venv_dir.exists():
            self.issues.append("Virtual environment not found")
            self.fixes.append("Run: cd backend && python -m venv .venv")
            return

        # Check critical packages
        try:
            result = subprocess.run([
                str(venv_dir / "Scripts" / "python.exe"), "-c",
                "import fastapi, uvicorn, azure.cosmos, azure.ai.documentintelligence, openai"
            ], capture_output=True, text=True, cwd=self.backend_dir)

            if result.returncode != 0:
                self.issues.append(f"Critical dependencies missing: {result.stderr}")
                self.fixes.append("Run: cd backend && .venv\\Scripts\\pip install -r requirements.txt")
        except Exception as e:
            self.issues.append(f"Dependency check failed: {e}")

    def check_todo_items(self):
        """Check for critical TODO items in production code"""
        self.log("Checking TODO items...")

        critical_todos = []
        todo_files = []

        # Scan Python files for TODO
        for py_file in self.project_root.rglob("*.py"):
            if "test" in str(py_file) or "temp" in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                if "TODO:" in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if "TODO:" in line:
                            todo_files.append(str(py_file.relative_to(self.project_root)))
                            break
            except Exception as e:
                self.log(f"Error reading {py_file}: {e}", "WARNING")

        if todo_files:
            self.issues.append(f"Found TODO items in production code: {len(todo_files)} files")
            self.fixes.append("Review and implement critical TODO items before production deployment")

    def check_environment_variables(self):
        """Check if environment variables are configured"""
        self.log("Checking environment configuration...")

        env_file = self.project_root / ".env"
        if not env_file.exists():
            self.issues.append("Environment file (.env) missing")
            self.fixes.append("Create .env file with Azure credentials and API keys")
            return

        required_vars = [
            "AZURE_COSMOS_CONNECTION_STRING",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_KEY",
            "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT",
            "AZURE_DOCUMENT_INTELLIGENCE_KEY"
        ]

        with open(env_file, 'r') as f:
            env_content = f.read()

        missing_vars = []
        for var in required_vars:
            if var not in env_content or f"{var}=" not in env_content:
                missing_vars.append(var)

        if missing_vars:
            self.issues.append(f"Missing environment variables: {missing_vars}")
            self.fixes.append("Configure all required Azure service credentials in .env")

    def check_database_connection(self):
        """Test database connectivity"""
        self.log("Checking database connection...")

        test_file = self.backend_dir / "test_cosmos_connection.py"
        if not test_file.exists():
            self.issues.append("Database connection test script missing")
            return

        try:
            result = subprocess.run([
                str(self.backend_dir / ".venv" / "Scripts" / "python.exe"),
                str(test_file)
            ], capture_output=True, text=True, cwd=self.backend_dir, timeout=30)

            if result.returncode != 0:
                self.issues.append(f"Database connection test failed: {result.stderr}")
                self.fixes.append("Fix Cosmos DB connection and credentials")
            else:
                self.log("Database connection test passed")
        except subprocess.TimeoutExpired:
            self.issues.append("Database connection test timed out")
        except Exception as e:
            self.issues.append(f"Database test error: {e}")

    def run_tests(self):
        """Run test suite"""
        self.log("Running test suite...")

        try:
            result = subprocess.run([
                str(self.backend_dir / ".venv" / "Scripts" / "python.exe"),
                "-m", "pytest", "backend/tests/", "-v", "--tb=short", "-x"
            ], capture_output=True, text=True, cwd=self.project_root, timeout=300)

            if result.returncode != 0:
                # Parse test results
                output_lines = result.stdout.split('\n')
                passed = 0
                failed = 0
                for line in output_lines:
                    if "passed" in line and "failed" in line:
                        # Extract numbers from summary line
                        parts = line.split()
                        for part in parts:
                            if part.endswith("passed"):
                                passed = int(part.split()[0])
                            elif part.endswith("failed"):
                                failed = int(part.split()[0])

                if failed > 0:
                    self.issues.append(f"Test suite: {passed} passed, {failed} failed")
                    self.fixes.append("Fix failing tests before production deployment")
                else:
                    self.log(f"Test suite passed: {passed} tests")
            else:
                self.log("All tests passed")

        except subprocess.TimeoutExpired:
            self.issues.append("Test suite timed out")
        except Exception as e:
            self.issues.append(f"Test execution error: {e}")

    def generate_report(self):
        """Generate deployment readiness report"""
        print("\n" + "="*80)
        print("KRAFTD MARKET READINESS REPORT")
        print("="*80)

        if not self.issues:
            print("ALL CHECKS PASSED - READY FOR MARKET DEPLOYMENT!")
            print("\nNext Steps:")
            print("1. Run: ./deploy-azure.bat (Windows) or ./deploy-azure.sh (Linux/Mac)")
            print("2. Monitor deployment in Azure Portal")
            print("3. Test production endpoints")
            print("4. Update DNS and SSL certificates")
            return

        print(f"FOUND {len(self.issues)} ISSUES REQUIRING ATTENTION")
        print("\nISSUES:")
        for i, issue in enumerate(self.issues, 1):
            print(f"{i}. {issue}")

        print("\nRECOMMENDED FIXES:")
        for i, fix in enumerate(self.fixes, 1):
            print(f"{i}. {fix}")

        print("\nDEPLOYMENT STATUS: NOT READY")
        print("Address critical issues before proceeding to market deployment.")

    def run_all_checks(self):
        """Run all readiness checks"""
        print("Starting Kraftd Market Readiness Check...")

        checks = [
            self.check_infrastructure_alignment,
            self.check_dependencies,
            self.check_todo_items,
            self.check_environment_variables,
            self.check_database_connection,
            self.run_tests
        ]

        for check in checks:
            try:
                check()
            except Exception as e:
                self.issues.append(f"Check failed: {e}")

        self.generate_report()

if __name__ == "__main__":
    checker = MarketReadinessChecker()
    checker.run_all_checks()