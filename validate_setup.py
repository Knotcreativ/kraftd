"""
Quick validation that all Kraftd MVP components are working together:
- FastAPI Backend
- Document Extraction (Local + Azure)
- AI Agent Framework
- Integration between all components
"""

import subprocess
import sys
import os
import json
from pathlib import Path


def check_python_version():
    """Verify Python 3.13+"""
    version = sys.version_info
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    if version < (3, 10):
        print("⚠ Warning: Python 3.10+ recommended")
    return True


def check_venv():
    """Verify virtual environment is active"""
    in_venv = sys.prefix != sys.base_prefix
    if in_venv:
        print(f"✓ Virtual environment active: {sys.prefix}")
    else:
        print("⚠ Not in virtual environment")
    return in_venv


def check_backend_packages():
    """Check backend dependencies"""
    required = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "pdfplumber",
        "python-docx",
        "openpyxl",
        "pandas",
        "azure-ai-documentintelligence",
        "azure-storage-blob",
    ]
    
    missing = []
    for pkg in required:
        try:
            __import__(pkg.replace("-", "_"))
            print(f"  ✓ {pkg}")
        except ImportError:
            print(f"  ✗ {pkg} (missing)")
            missing.append(pkg)
    
    return len(missing) == 0, missing


def check_agent_packages():
    """Check agent framework dependencies"""
    required = [
        "agent_framework",
        "azure.ai.projects",
        "httpx",
    ]
    
    missing = []
    for pkg in required:
        try:
            __import__(pkg.replace("-", "_"))
            print(f"  ✓ {pkg}")
        except ImportError:
            print(f"  ✗ {pkg} (missing - run: pip install --pre agent-framework-azure-ai)")
            missing.append(pkg)
    
    return len(missing) == 0, missing


def check_azure_credentials():
    """Check Azure credentials are configured"""
    di_endpoint = os.environ.get("DOCUMENTINTELLIGENCE_ENDPOINT")
    di_key = os.environ.get("DOCUMENTINTELLIGENCE_API_KEY")
    foundry_endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT")
    foundry_model = os.environ.get("FOUNDRY_MODEL_DEPLOYMENT")
    
    print("\n  Document Intelligence:")
    if di_endpoint and di_key:
        print(f"    ✓ Configured: {di_endpoint[:50]}...")
    else:
        print("    ⚠ Not configured (local extraction will work as fallback)")
    
    print("\n  Microsoft Foundry (for Agent):")
    if foundry_endpoint and foundry_model:
        print(f"    ✓ Configured: {foundry_endpoint[:50]}...")
        print(f"    ✓ Model: {foundry_model}")
    else:
        print("    ⚠ Not configured (agent won't work without this)")
    
    return bool(foundry_endpoint and foundry_model)


def check_file_structure():
    """Verify expected file structure"""
    files_to_check = [
        "backend/main.py",
        "backend/document_processing/__init__.py",
        "backend/document_processing/extractor.py",
        "backend/document_processing/schemas.py",
        "backend/document_processing/azure_service.py",
        "backend/agent/__init__.py",
        "backend/agent/kraft_agent.py",
    ]
    
    all_exist = True
    for file_path in files_to_check:
        if Path(file_path).exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} (missing)")
            all_exist = False
    
    return all_exist


def check_backend_api():
    """Check if FastAPI backend is running"""
    try:
        import httpx
        with httpx.Client() as client:
            response = client.get("http://127.0.0.1:8000/", timeout=2)
            if response.status_code == 200:
                data = response.json()
                print(f"  ✓ Backend running: {data.get('version', 'unknown version')}")
                print(f"    Endpoints: {len(data.get('endpoints', {}))} available")
                return True
            else:
                print(f"  ✗ Backend returned {response.status_code}")
                return False
    except Exception as e:
        print(f"  ⚠ Backend not running (start with: uvicorn main:app --port 8000)")
        return False


def check_agent_framework():
    """Verify Agent Framework can initialize"""
    try:
        from backend.agent import KraftdAIAgent
        print("  ✓ Agent module imports successfully")
        
        # Check if credentials are available
        foundry_endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT")
        if not foundry_endpoint:
            print("  ⚠ FOUNDRY_PROJECT_ENDPOINT not set (agent won't initialize)")
            return False
        else:
            print("  ✓ Foundry credentials available")
            return True
            
    except Exception as e:
        print(f"  ✗ Agent import failed: {str(e)}")
        return False


def check_document_extraction():
    """Test document extraction capabilities"""
    try:
        from backend.document_processing import DocumentExtractor
        print("  ✓ Local extractor available")
        
        try:
            from backend.document_processing import is_azure_configured, get_azure_service
            if is_azure_configured():
                print("  ✓ Azure Document Intelligence configured")
                return True
            else:
                print("  ⚠ Azure Document Intelligence not configured (local extraction available)")
                return True
        except Exception as e:
            print(f"  ⚠ Azure Document Intelligence check failed: {e}")
            return True
            
    except Exception as e:
        print(f"  ✗ Document processing import failed: {str(e)}")
        return False


def main():
    """Run all validation checks"""
    print("=" * 70)
    print("KRAFTD MVP - SYSTEM VALIDATION")
    print("=" * 70)
    
    results = {}
    
    # Section 1: Python & Environment
    print("\n[1] Python Environment")
    print("-" * 70)
    results["python"] = check_python_version()
    results["venv"] = check_venv()
    
    # Section 2: Backend Dependencies
    print("\n[2] Backend Dependencies")
    print("-" * 70)
    backend_ok, missing_backend = check_backend_packages()
    results["backend_packages"] = backend_ok
    
    # Section 3: Agent Dependencies
    print("\n[3] Agent Framework Dependencies")
    print("-" * 70)
    agent_ok, missing_agent = check_agent_packages()
    results["agent_packages"] = agent_ok
    
    # Section 4: Azure Credentials
    print("\n[4] Azure Credentials")
    print("-" * 70)
    results["azure"] = check_azure_credentials()
    
    # Section 5: File Structure
    print("\n[5] File Structure")
    print("-" * 70)
    results["files"] = check_file_structure()
    
    # Section 6: Backend API
    print("\n[6] Backend API")
    print("-" * 70)
    results["backend_api"] = check_backend_api()
    
    # Section 7: Agent Framework
    print("\n[7] Agent Framework")
    print("-" * 70)
    results["agent_framework"] = check_agent_framework()
    
    # Section 8: Document Extraction
    print("\n[8] Document Extraction")
    print("-" * 70)
    results["extraction"] = check_document_extraction()
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    for check, result in results.items():
        status = "✓" if result else "✗"
        print(f"  {status} {check.replace('_', ' ').title()}")
    
    # Recommendations
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    
    if not results["backend_api"]:
        print("\n1. Start the FastAPI backend:")
        print("   cd backend")
        print("   .venv\\Scripts\\uvicorn main:app --port 8000")
    
    if missing_agent:
        print("\n2. Install missing agent dependencies:")
        print("   pip install agent-framework-azure-ai --pre")
        print("   pip install azure-ai-projects httpx")
    
    if not results["azure"]:
        print("\n3. Configure Azure credentials:")
        print("   See AZURE_SETUP.md for Document Intelligence")
        print("   See AGENT_SETUP.md for Microsoft Foundry")
    
    if results["agent_packages"] and results["azure"]:
        print("\n4. Start the AI Agent:")
        print("   python backend/agent/kraft_agent.py")
    
    print("\n" + "=" * 70)
    
    return passed == total


if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    success = main()
    sys.exit(0 if success else 1)
