"""Pytest configuration for KraftdIntel tests"""
import sys
from pathlib import Path

# Add backend directory to Python path so imports work
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))
