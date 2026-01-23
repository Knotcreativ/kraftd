#!/usr/bin/env python3
"""
KRAFTD DEPLOYMENT LAUNCH SCRIPT
===============================

This script prepares Kraftd Docs for market deployment.
Run this before executing the Azure deployment scripts.

Usage: python deploy_prep.py
"""

import os
import sys
import subprocess
import json
from pathlib import Path

class DeploymentPreparer:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        self.issues = []
        self.completed = []

    def log(self, message, level="INFO"):
        """Log a message with level"""
        print(f"[{level}] {message}")

    def check_git_status(self):
        """Check git status and ensure working directory is clean"""
        self.log("Checking git status...")

        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True, text=True
            )

            if result.returncode == 0:
                if result.stdout.strip():
                    self.issues.append("Working directory has uncommitted changes")
                    self.log("Uncommitted changes found - commit before deployment", "WARNING")
                else:
                    self.completed.append("Git working directory clean")
                    self.log("Git status clean")
            else:
                self.issues.append("Git status check failed")
        except Exception as e:
            self.issues.append(f"Git check error: {e}")

    def validate_environment(self):
        """Validate environment configuration"""
        self.log("Validating environment configuration...")

        env_file = self.project_root / ".env"
        if not env_file.exists():
            self.issues.append("Environment file (.env) missing")
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
        placeholder_vars = []

        for var in required_vars:
            if var not in env_content:
                missing_vars.append(var)
            elif f"{var}=" in env_content:
                # Check if it has placeholder values
                lines = env_content.split('\n')
                for line in lines:
                    if line.startswith(f"{var}="):
                        value = line.split('=', 1)[1].strip()
                        if "YOUR_" in value or value == "":
                            placeholder_vars.append(var)
                        break

        if missing_vars:
            self.issues.append(f"Missing environment variables: {missing_vars}")

        if placeholder_vars:
            self.issues.append(f"Environment variables with placeholder values: {placeholder_vars}")
            self.log("Update placeholder values with real Azure credentials", "WARNING")

        if not missing_vars and not placeholder_vars:
            self.completed.append("Environment configuration validated")

    def check_docker_setup(self):
        """Check Docker availability for container deployment"""
        self.log("Checking Docker setup...")

        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True, text=True
            )

            if result.returncode == 0:
                self.completed.append("Docker available for container builds")
                self.log(f"Docker version: {result.stdout.strip()}")
            else:
                self.issues.append("Docker not available or not running")
        except Exception as e:
            self.issues.append(f"Docker check failed: {e}")

    def validate_package_json(self):
        """Validate package.json configurations"""
        self.log("Validating package configurations...")

        # Backend requirements.txt
        req_file = self.backend_dir / "requirements.txt"
        if req_file.exists():
            self.completed.append("Backend requirements.txt found")
        else:
            self.issues.append("Backend requirements.txt missing")

        # Frontend package.json
        pkg_file = self.frontend_dir / "package.json"
        if pkg_file.exists():
            self.completed.append("Frontend package.json found")
        else:
            self.issues.append("Frontend package.json missing")

    def check_deployment_scripts(self):
        """Check deployment scripts exist and are executable"""
        self.log("Checking deployment scripts...")

        scripts = [
            "deploy-azure.bat",
            "deploy-azure.sh",
            "Dockerfile"
        ]

        for script in scripts:
            script_path = self.project_root / script
            if script_path.exists():
                self.completed.append(f"Deployment script found: {script}")
            else:
                self.issues.append(f"Deployment script missing: {script}")

    def generate_deployment_summary(self):
        """Generate deployment readiness summary"""
        print("\n" + "="*80)
        print("KRAFTD DEPLOYMENT PREPARATION SUMMARY")
        print("="*80)

        print(f"\nCOMPLETED CHECKS ({len(self.completed)}):")
        for item in self.completed:
            print(f"  ✓ {item}")

        if self.issues:
            print(f"\nISSUES FOUND ({len(self.issues)}):")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")

        print("\n" + "="*80)

        if not self.issues:
            print("DEPLOYMENT READY!")
            print("\nNext Steps:")
            print("1. Ensure Azure CLI is logged in: az login")
            print("2. Run deployment: ./deploy-azure.bat (Windows)")
            print("3. Monitor deployment in Azure Portal")
            print("4. Test production endpoints")
            return True
        else:
            print("DEPLOYMENT BLOCKED - Fix issues above first")
            return False

    def run_preparation(self):
        """Run all deployment preparation checks"""
        print("Preparing Kraftd for Market Deployment...")
        print("=========================================")

        checks = [
            self.check_git_status,
            self.validate_environment,
            self.check_docker_setup,
            self.validate_package_json,
            self.check_deployment_scripts
        ]

        for check in checks:
            try:
                check()
            except Exception as e:
                self.issues.append(f"Preparation check failed: {e}")

        return self.generate_deployment_summary()

if __name__ == "__main__":
    preparer = DeploymentPreparer()
    success = preparer.run_preparation()

    if success:
        print("\nLaunching deployment...")
        # Auto-launch deployment script
        if os.name == 'nt':  # Windows
            os.system("deploy-azure.bat")
        else:  # Linux/Mac
            os.system("./deploy-azure.sh")
    else:
        print("\nFix issues and re-run this script.")
        sys.exit(1)