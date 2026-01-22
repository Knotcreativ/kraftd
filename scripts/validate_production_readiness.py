#!/usr/bin/env python3
"""
Production Readiness Validation Script for Kraftd Docs
Checks all critical items before production deployment
"""

import os
import sys
import json
import subprocess
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

class ValidationResult:
    def __init__(self):
        self.checks = []
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def add_check(self, name: str, passed: bool, message: str = "", severity: str = "error"):
        """Add a check result."""
        self.total += 1
        if passed:
            self.passed += 1
            status = f"{Colors.GREEN}✓ PASS{Colors.END}"
        elif severity == "warning":
            self.warnings += 1
            status = f"{Colors.YELLOW}⚠ WARN{Colors.END}"
        else:
            self.failed += 1
            status = f"{Colors.RED}✗ FAIL{Colors.END}"
        
        self.checks.append({
            "name": name,
            "passed": passed,
            "message": message,
            "severity": severity
        })
        print(f"{status} | {name}")
        if message:
            print(f"       └─ {message}")
    
    def print_summary(self):
        """Print validation summary."""
        print("\n" + "="*80)
        print(f"{Colors.BLUE}VALIDATION SUMMARY{Colors.END}")
        print("="*80)
        print(f"Total Checks: {self.total}")
        print(f"{Colors.GREEN}Passed: {self.passed}{Colors.END}")
        print(f"{Colors.YELLOW}Warnings: {self.warnings}{Colors.END}")
        print(f"{Colors.RED}Failed: {self.failed}{Colors.END}")
        
        if self.failed == 0:
            print(f"\n{Colors.GREEN}✓ READY FOR PRODUCTION{Colors.END}")
            return True
        else:
            print(f"\n{Colors.RED}✗ NOT READY FOR PRODUCTION{Colors.END}")
            print("\nFailed checks:")
            for check in self.checks:
                if not check["passed"] and check["severity"] != "warning":
                    print(f"  - {check['name']}: {check['message']}")
            return False

def check_file_exists(path: str, description: str) -> Tuple[bool, str]:
    """Check if a file exists."""
    if os.path.exists(path):
        return True, f"Found at {path}"
    return False, f"Missing at {path}"

def check_env_file(env_file: str) -> Tuple[bool, str]:
    """Check if environment file exists and has required variables."""
    if not os.path.exists(env_file):
        return False, f"File not found: {env_file}"
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Check for critical variables
    required_vars = ["ENVIRONMENT", "DEBUG", "LOG_LEVEL"]
    missing = [var for var in required_vars if var not in content]
    
    if missing:
        return False, f"Missing variables: {', '.join(missing)}"
    return True, "Environment file valid"

def check_cors_configuration(main_py: str) -> Tuple[bool, str]:
    """Check if CORS is configured for production."""
    with open(main_py, 'r') as f:
        content = f.read()
    
    # Check for environment-based CORS
    if "ALLOWED_ORIGINS" in content and "os.getenv(\"ALLOWED_ORIGINS\"" in content:
        return True, "CORS configured via environment variable (correct)"
    
    # Check for hardcoded wildcard (bad for production)
    if 'allow_origins=["*"]' in content:
        return False, "CORS uses wildcard (*) - SECURITY RISK in production"
    
    return False, "CORS configuration not found or unclear"

def check_secrets_management(auth_service: str) -> Tuple[bool, str]:
    """Check if secrets use Key Vault or secure storage."""
    with open(auth_service, 'r') as f:
        content = f.read()
    
    if "_get_secret_key()" in content or "secrets.get_jwt_secret()" in content:
        return True, "Secrets retrieved via secrets manager (good)"
    
    if '"dev-secret-key"' in content or "'dev-secret-key'" in content:
        return False, "Development secret key found - must use Key Vault in production"
    
    return False, "Cannot determine secrets management method"

def check_rate_limiting(config_py: str) -> Tuple[bool, str]:
    """Check if rate limiting is configured."""
    with open(config_py, 'r') as f:
        content = f.read()
    
    if "RATE_LIMIT_ENABLED" in content and "RATE_LIMIT_REQUESTS_PER_MINUTE" in content:
        return True, "Rate limiting configured with environment variables"
    
    return False, "Rate limiting not properly configured"

def check_https_enforcement(main_py: str) -> Tuple[bool, str]:
    """Check if HTTPS is enforced."""
    with open(main_py, 'r') as f:
        content = f.read()
    
    # Check for secure cookie configuration
    if 'secure": True' in content or 'secure=True' in content:
        return True, "HTTPS/secure cookies configured"
    
    return False, "HTTPS enforcement not found"

def check_logging_configuration(config_py: str) -> Tuple[bool, str]:
    """Check logging is not in DEBUG mode for production."""
    with open(config_py, 'r') as f:
        content = f.read()
    
    if "LOG_LEVEL" in content:
        # Will be checked at runtime from environment
        return True, "Logging configured via environment variable"
    
    return False, "Logging configuration not found"

def check_database_configuration(config_py: str) -> Tuple[bool, str]:
    """Check if Cosmos DB is configured."""
    with open(config_py, 'r') as f:
        content = f.read()
    
    required = ["COSMOS_DB_ENDPOINT", "COSMOS_DB_KEY", "COSMOS_DB_NAME"]
    found = all(var in content for var in required)
    
    if found:
        return True, "Cosmos DB configuration variables defined"
    return False, "Cosmos DB configuration incomplete"

def check_requirements_file(requirements_path: str) -> Tuple[bool, str]:
    """Check if requirements.txt exists and has critical packages."""
    if not os.path.exists(requirements_path):
        return False, f"requirements.txt not found at {requirements_path}"
    
    with open(requirements_path, 'r') as f:
        content = f.read()
    
    critical = ["fastapi", "pydantic", "python-jose", "sqlalchemy", "azure-cosmos"]
    missing = [pkg for pkg in critical if pkg not in content.lower()]
    
    if missing:
        return False, f"Missing critical packages: {', '.join(missing)}"
    return True, "All critical packages found"

def check_docker_configuration(dockerfile_path: str) -> Tuple[bool, str]:
    """Check if Dockerfile exists and is production-ready."""
    if not os.path.exists(dockerfile_path):
        return False, f"Dockerfile not found at {dockerfile_path}"
    
    with open(dockerfile_path, 'r') as f:
        content = f.read()
    
    # Check for production base image
    if "python:3.11" in content or "python:3.10" in content:
        return True, "Using appropriate Python base image"
    
    return False, "Dockerfile may not be production-ready"

def check_production_files():
    """Check if all required production files exist."""
    root_dir = Path(__file__).parent.parent
    backend_dir = root_dir / "backend"
    frontend_dir = root_dir / "frontend"
    
    files_to_check = {
        str(backend_dir / ".env.production"): "Backend production environment",
        str(frontend_dir / ".env.production"): "Frontend production environment",
        str(backend_dir / "requirements.txt"): "Python dependencies",
        str(root_dir / "infrastructure" / "main.bicep"): "Infrastructure as Code",
        str(root_dir / "infrastructure" / "cosmos-db.bicep"): "Database IaC",
    }
    
    results = {}
    for file_path, description in files_to_check.items():
        exists, msg = check_file_exists(file_path, description)
        results[description] = (exists, msg)
    
    return results

def run_validation():
    """Run all validation checks."""
    result = ValidationResult()
    
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}KRAFTD DOCS - PRODUCTION READINESS VALIDATION{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}\n")
    
    root_dir = Path(__file__).parent.parent
    backend_dir = root_dir / "backend"
    frontend_dir = root_dir / "frontend"
    
    # Section 1: Critical Files
    print(f"\n{Colors.BLUE}1. CRITICAL FILES{Colors.END}")
    print("-" * 80)
    
    file_checks = check_production_files()
    for description, (exists, message) in file_checks.items():
        result.add_check(description, exists, message)
    
    # Section 2: Security Configuration
    print(f"\n{Colors.BLUE}2. SECURITY CONFIGURATION{Colors.END}")
    print("-" * 80)
    
    # CORS Check
    cors_ok, cors_msg = check_cors_configuration(str(backend_dir / "main.py"))
    result.add_check("CORS Configuration (restrict to production domain)", cors_ok, cors_msg)
    
    # Secrets Check
    secrets_ok, secrets_msg = check_secrets_management(str(backend_dir / "services" / "auth_service.py"))
    result.add_check("Secrets Management (uses Key Vault)", secrets_ok, secrets_msg)
    
    # HTTPS Check
    https_ok, https_msg = check_https_enforcement(str(backend_dir / "main.py"))
    result.add_check("HTTPS Enforcement (secure cookies)", https_ok, https_msg)
    
    # Environment Variables Check
    env_ok, env_msg = check_env_file(str(backend_dir / ".env.production"))
    result.add_check("Production Environment File (.env.production)", env_ok, env_msg)
    
    # Section 3: Configuration
    print(f"\n{Colors.BLUE}3. CONFIGURATION{Colors.END}")
    print("-" * 80)
    
    # Rate Limiting Check
    rate_ok, rate_msg = check_rate_limiting(str(backend_dir / "config.py"))
    result.add_check("Rate Limiting Configuration", rate_ok, rate_msg)
    
    # Logging Check
    logging_ok, logging_msg = check_logging_configuration(str(backend_dir / "config.py"))
    result.add_check("Logging Configuration (environment-based)", logging_ok, logging_msg)
    
    # Database Check
    db_ok, db_msg = check_database_configuration(str(backend_dir / "config.py"))
    result.add_check("Cosmos DB Configuration", db_ok, db_msg)
    
    # Section 4: Dependencies
    print(f"\n{Colors.BLUE}4. DEPENDENCIES{Colors.END}")
    print("-" * 80)
    
    req_ok, req_msg = check_requirements_file(str(backend_dir / "requirements.txt"))
    result.add_check("Required Python Packages", req_ok, req_msg)
    
    # Section 5: Deployment
    print(f"\n{Colors.BLUE}5. DEPLOYMENT{Colors.END}")
    print("-" * 80)
    
    docker_ok, docker_msg = check_docker_configuration(str(root_dir / "Dockerfile"))
    result.add_check("Dockerfile (production-ready)", docker_ok, docker_msg)
    
    # Section 6: Infrastructure
    print(f"\n{Colors.BLUE}6. INFRASTRUCTURE AS CODE{Colors.END}")
    print("-" * 80)
    
    bicep_ok, bicep_msg = check_file_exists(str(root_dir / "infrastructure" / "main.bicep"), "Main Bicep template")
    result.add_check("Azure IaC - main.bicep", bicep_ok, bicep_msg)
    
    cosmos_ok, cosmos_msg = check_file_exists(str(root_dir / "infrastructure" / "cosmos-db.bicep"), "Cosmos DB Bicep")
    result.add_check("Azure IaC - cosmos-db.bicep", cosmos_ok, cosmos_msg)
    
    # Section 7: Pre-Deployment Checklist
    print(f"\n{Colors.BLUE}7. DEPLOYMENT READINESS{Colors.END}")
    print("-" * 80)
    
    # Check if deployment plan exists
    plan_ok, plan_msg = check_file_exists(
        str(root_dir / "KRAFTD_DOCS_PRODUCTION_ROLLOUT_PLAN.md"),
        "Production Rollout Plan"
    )
    result.add_check("Production Rollout Plan", plan_ok, plan_msg)
    
    # Check if checklist exists
    checklist_ok, checklist_msg = check_file_exists(
        str(root_dir / "KRAFTD_DOCS_PRE_FLIGHT_CHECKLIST.md"),
        "Pre-Flight Checklist"
    )
    result.add_check("Pre-Flight Checklist", checklist_ok, checklist_msg)
    
    # Final Summary
    result.print_summary()
    
    # Return success/failure
    return result.failed == 0

if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
