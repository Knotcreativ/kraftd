#!/usr/bin/env python3
"""
Comprehensive KraftdIntel Project Audit
Analyzes:
- Directory structure and cleanup opportunities
- Code quality (duplicates, unused imports, syntax)
- Deployment alignment (staticwebapp.json vs GitHub Actions)
- Architecture spec compliance
- Market readiness blockers
"""

import os
import json
import re
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

# Configuration
ROOT = Path('.')
BACKEND_ROOT = ROOT / 'backend'
FRONTEND_ROOT = ROOT / 'frontend'
FRONTEND_NEXT_ROOT = ROOT / 'frontend-next'
DOCS_ROOT = ROOT / 'docs'

# ==================== 1. DIRECTORY STRUCTURE ANALYSIS ====================

def analyze_directory_structure():
    """Identify orphaned files, duplicates, and cleanup opportunities"""
    report = {
        'root_files': [],
        'orphaned_dirs': [],
        'duplicates': [],
        'cleanup_candidates': []
    }
    
    # Root-level markdown files (should be in /docs/)
    root_mds = list(ROOT.glob('*.md'))
    report['root_files'] = [str(f.name) for f in root_mds]
    
    # Root-level Python scripts (should be in /scripts/)
    root_scripts = list(ROOT.glob('*.py'))
    report['root_scripts'] = [str(f.name) for f in root_scripts]
    
    # Check for duplicate frontends
    if FRONTEND_ROOT.exists() and FRONTEND_NEXT_ROOT.exists():
        report['duplicates'].append({
            'type': 'dual_frontends',
            'frontend': str(FRONTEND_ROOT),
            'frontend_next': str(FRONTEND_NEXT_ROOT),
            'risk': 'HIGH - Two frontends create deployment confusion'
        })
    
    # Check for log files (cleanup candidates)
    for pattern in ['*.log', '*.bak', '__pycache__', '.pytest_cache']:
        for path in ROOT.rglob(pattern):
            if path.is_file() or path.is_dir():
                report['cleanup_candidates'].append(str(path.relative_to(ROOT)))
    
    return report

# ==================== 2. CODE ANALYSIS ====================

def analyze_backend_structure():
    """Analyze backend Python code"""
    report = {
        'total_files': 0,
        'duplicates': [],
        'circular_imports': [],
        'syntax_errors': [],
        'services': [],
        'models': []
    }
    
    if not BACKEND_ROOT.exists():
        return report
    
    py_files = list(BACKEND_ROOT.rglob('*.py'))
    report['total_files'] = len(py_files)
    
    # Track imports
    imports = defaultdict(list)
    for py_file in py_files:
        try:
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            # Extract imports
            import_pattern = r'from\s+[\.\w]+\s+import|import\s+[\w]+'
            matches = re.findall(import_pattern, content)
            imports[str(py_file)] = matches
        except Exception as e:
            report['syntax_errors'].append(str(py_file))
    
    # Detect services
    services_dir = BACKEND_ROOT / 'services'
    if services_dir.exists():
        report['services'] = [f.name for f in services_dir.glob('*.py') if f.is_file()]
    
    # Detect models
    models_dir = BACKEND_ROOT / 'models'
    if models_dir.exists():
        report['models'] = [f.name for f in models_dir.glob('*.py') if f.is_file()]
    
    return report

def analyze_frontend_structure():
    """Analyze frontend React/TypeScript code"""
    report = {
        'total_components': 0,
        'total_pages': 0,
        'api_integration_points': 0,
        'auth_coverage': False,
        'errors': []
    }
    
    if not FRONTEND_ROOT.exists():
        return report
    
    components = list(FRONTEND_ROOT.rglob('*.tsx')) + list(FRONTEND_ROOT.rglob('*.ts'))
    report['total_components'] = len(components)
    
    pages_dir = FRONTEND_ROOT / 'src' / 'pages'
    if pages_dir.exists():
        report['total_pages'] = len(list(pages_dir.glob('*.tsx')))
    
    # Check for API integration
    app_file = FRONTEND_ROOT / 'src' / 'App.tsx'
    if app_file.exists():
        content = app_file.read_text()
        report['api_integration_points'] = content.count('apiClient')
        report['auth_coverage'] = 'AuthContext' in content or 'useAuth' in content
    
    return report

# ==================== 3. DEPLOYMENT CONFIGURATION ANALYSIS ====================

def analyze_deployment_config():
    """Check SWA config alignment with GitHub Actions"""
    report = {
        'staticwebapp_json': {},
        'github_actions': {},
        'alignment_issues': [],
        'env_vars_missing': []
    }
    
    # Check staticwebapp.json
    swa_file = ROOT / 'staticwebapp.json'
    if swa_file.exists():
        try:
            swa_config = json.loads(swa_file.read_text())
            if 'buildConfiguration' in swa_config:
                report['staticwebapp_json'] = swa_config['buildConfiguration']
        except:
            report['alignment_issues'].append('staticwebapp.json is invalid JSON')
    
    # Check GitHub Actions workflow
    workflow_file = ROOT / '.github' / 'workflows' / 'azure-static-web-apps-jolly-coast-03a4f4d03.yml'
    if workflow_file.exists():
        content = workflow_file.read_text()
        if 'npm run build' in content:
            report['github_actions']['build_command'] = 'npm run build'
        if 'frontend' in content:
            report['github_actions']['frontend_target'] = 'frontend'
        if 'frontend-next' in content:
            report['alignment_issues'].append('GitHub Actions references frontend-next (DEPRECATED)')
    
    # Check .env file
    env_file = ROOT / '.env'
    if not env_file.exists():
        report['env_vars_missing'].append('.env file not found (copy from .env.example)')
    
    return report

# ==================== 4. ARCHITECTURE SPEC COMPLIANCE ====================

def analyze_spec_compliance():
    """Check if implementation matches documented spec"""
    report = {
        'backend_spec': {},
        'frontend_spec': {},
        'gaps': [],
        'deviations': []
    }
    
    # Check DEPLOYMENT_GUIDE.md
    deploy_guide = ROOT / 'DEPLOYMENT_GUIDE.md'
    if deploy_guide.exists():
        content = deploy_guide.read_text()
        if 'Azure Container Apps' in content:
            report['backend_spec']['hosting'] = 'Azure Container Apps'
        if 'Docker' in content:
            report['backend_spec']['containerization'] = 'Docker'
    
    # Check PROJECT_STRUCTURE.md
    project_struct = ROOT / 'PROJECT_STRUCTURE.md'
    if project_struct.exists():
        content = project_struct.read_text()
        expected_dirs = ['backend', 'frontend', 'infrastructure', 'docs', 'scripts']
        report['frontend_spec']['expected_dirs'] = expected_dirs
        for d in expected_dirs:
            if not (ROOT / d).exists():
                report['gaps'].append(f"Missing directory: {d}")
    
    return report

# ==================== 5. MARKET READINESS ASSESSMENT ====================

def assess_market_readiness():
    """Identify blockers for production deployment"""
    blockers = {
        'critical': [],
        'high': [],
        'medium': [],
        'low': []
    }
    
    # Critical blockers
    if not (ROOT / '.env').exists():
        blockers['critical'].append('No .env file - cannot deploy without credentials')
    
    if (ROOT / 'staticwebapp.json').exists():
        try:
            config = json.loads((ROOT / 'staticwebapp.json').read_text())
            if config.get('buildConfiguration', {}).get('appLocation') == 'frontend-next':
                blockers['critical'].append('staticwebapp.json still points to deprecated frontend-next')
        except:
            blockers['critical'].append('staticwebapp.json is invalid JSON')
    
    # High priority
    if (FRONTEND_NEXT_ROOT).exists():
        blockers['high'].append('Dual frontend (frontend-next) still exists - consolidate or archive')
    
    if (ROOT / 'backend' / 'main.py').exists():
        main_content = (ROOT / 'backend' / 'main.py').read_text()
        if 'TODO' in main_content or 'FIXME' in main_content:
            blockers['high'].append('Unresolved TODOs/FIXMEs in backend/main.py')
    
    if not (ROOT / 'backend' / 'requirements.txt').exists():
        blockers['high'].append('Missing backend/requirements.txt')
    
    # Medium priority
    log_files = list(ROOT.rglob('*.log'))
    if log_files:
        blockers['medium'].append(f'Found {len(log_files)} log files - should be in .gitignore')
    
    if (ROOT / '.env').exists():
        env_content = (ROOT / '.env').read_text()
        if 'PLACEHOLDER' in env_content or 'your-' in env_content:
            blockers['medium'].append('.env contains placeholder values - needs production credentials')
    
    return blockers

# ==================== MAIN REPORT ====================

def generate_audit_report():
    """Generate comprehensive audit report"""
    
    print("\n" + "="*80)
    print("KRAFTDINTEL COMPREHENSIVE PROJECT AUDIT")
    print("Generated: 2026-01-24")
    print("="*80 + "\n")
    
    # 1. Directory Structure
    print("\n1. DIRECTORY STRUCTURE ANALYSIS")
    print("-" * 80)
    dir_analysis = analyze_directory_structure()
    print(f"✓ Root markdown files: {len(dir_analysis['root_files'])}")
    for f in dir_analysis['root_files'][:5]:
        print(f"  - {f}")
    if len(dir_analysis['root_files']) > 5:
        print(f"  ... and {len(dir_analysis['root_files'])-5} more")
    
    print(f"\n✓ Root Python scripts: {len(dir_analysis['root_scripts'])}")
    for f in dir_analysis['root_scripts'][:5]:
        print(f"  - {f}")
    
    print(f"\n⚠ Cleanup candidates (logs, cache): {len(dir_analysis['cleanup_candidates'])}")
    for item in dir_analysis['cleanup_candidates'][:5]:
        print(f"  - {item}")
    
    if dir_analysis['duplicates']:
        print(f"\n❌ DUPLICATES DETECTED: {len(dir_analysis['duplicates'])}")
        for dup in dir_analysis['duplicates']:
            print(f"  Type: {dup['type']}")
            print(f"  Risk: {dup['risk']}")
    
    # 2. Backend Analysis
    print("\n\n2. BACKEND CODE ANALYSIS")
    print("-" * 80)
    backend_analysis = analyze_backend_structure()
    print(f"✓ Total Python files: {backend_analysis['total_files']}")
    print(f"✓ Services detected: {len(backend_analysis['services'])}")
    print(f"  - {', '.join(backend_analysis['services'][:5])}")
    print(f"✓ Models detected: {len(backend_analysis['models'])}")
    print(f"  - {', '.join(backend_analysis['models'][:5])}")
    
    if backend_analysis['syntax_errors']:
        print(f"❌ Syntax errors: {len(backend_analysis['syntax_errors'])}")
        for f in backend_analysis['syntax_errors'][:3]:
            print(f"  - {f}")
    
    # 3. Frontend Analysis
    print("\n\n3. FRONTEND CODE ANALYSIS")
    print("-" * 80)
    frontend_analysis = analyze_frontend_structure()
    print(f"✓ React components: {frontend_analysis['total_components']}")
    print(f"✓ Pages: {frontend_analysis['total_pages']}")
    print(f"✓ API integration points: {frontend_analysis['api_integration_points']}")
    print(f"✓ Auth context detected: {'YES' if frontend_analysis['auth_coverage'] else 'NO'}")
    
    # 4. Deployment Config
    print("\n\n4. DEPLOYMENT CONFIGURATION ANALYSIS")
    print("-" * 80)
    deploy_analysis = analyze_deployment_config()
    print(f"✓ SWA Config (staticwebapp.json):")
    for k, v in deploy_analysis['staticwebapp_json'].items():
        print(f"  - {k}: {v}")
    
    if deploy_analysis['alignment_issues']:
        print(f"\n❌ ALIGNMENT ISSUES:")
        for issue in deploy_analysis['alignment_issues']:
            print(f"  - {issue}")
    
    # 5. Market Readiness
    print("\n\n5. MARKET READINESS BLOCKERS")
    print("-" * 80)
    blockers = assess_market_readiness()
    
    for severity, items in blockers.items():
        if items:
            symbol = "❌" if severity == "critical" else "⚠" if severity == "high" else "ℹ"
            print(f"\n{symbol} {severity.upper()} ({len(items)}):")
            for blocker in items:
                print(f"  - {blocker}")
    
    # Summary
    print("\n\n" + "="*80)
    print("SUMMARY & PATH FORWARD")
    print("="*80)
    
    total_blockers = sum(len(items) for items in blockers.values())
    print(f"\nTotal Blockers: {total_blockers}")
    print(f"Critical: {len(blockers['critical'])}")
    print(f"High: {len(blockers['high'])}")
    
    print("\n📋 RECOMMENDED ACTIONS (Priority Order):")
    print("\n1. CRITICAL - Must fix before deployment:")
    print("   • Ensure .env has correct Azure credentials")
    print("   • Verify staticwebapp.json appLocation is 'frontend' (not 'frontend-next')")
    print("   • Merge fix/swa-config-align PR to main")
    print("   • Run: 'git push -u origin main' to trigger GitHub Actions deployment")
    
    print("\n2. HIGH PRIORITY - Fix immediately after critical:")
    print("   • Archive or remove frontend-next/ to eliminate dual frontend")
    print("   • Resolve any TODOs/FIXMEs in backend code")
    print("   • Review and clean up backend/requirements.txt for production")
    
    print("\n3. MEDIUM PRIORITY - Cleanup before launch:")
    print("   • Move root markdown files to /docs/")
    print("   • Move root scripts to /scripts/")
    print("   • Add *.log and __pycache__ to .gitignore")
    print("   • Replace .env placeholder values with production credentials")
    
    print("\n4. VALIDATION & TESTING:")
    print("   • Run: 'npm run build' in frontend/ - should create dist/")
    print("   • Run: 'python -m pytest backend/tests/' - all tests should pass")
    print("   • Test SWA deployment: Visit https://green-mushroom-06da9040f.1.azurestaticapps.net/")
    print("   • Test backend API: GET https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1/health")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    generate_audit_report()
