#!/usr/bin/env python3
"""
STEP 6 VALIDATION SCRIPT
Document Endpoints Migration - 12 Validation Checks

This script validates that the Step 6 migration was successful.
Verifies all endpoints now use DocumentRepository with fallback support.
"""

import os
import sys
import asyncio
import importlib.util
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Constants
SCRIPT_DIR = Path(__file__).parent
MAIN_PY = SCRIPT_DIR / "main.py"

class Step6Validator:
    """Validates Step 6 implementation."""
    
    def __init__(self):
        self.checks_passed = 0
        self.checks_total = 12
        self.errors = []
    
    def check(self, check_name: str, condition: bool, error_msg: str = ""):
        """Run a validation check."""
        if condition:
            logger.info(f"✅ {check_name}")
            self.checks_passed += 1
        else:
            logger.error(f"❌ {check_name} - {error_msg}")
            self.errors.append(f"{check_name}: {error_msg}")
    
    def read_main_py(self) -> str:
        """Read main.py content."""
        try:
            with open(MAIN_PY, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read main.py: {e}")
            return ""
    
    async def validate(self):
        """Run all validation checks."""
        logger.info("="*60)
        logger.info("STEP 6 VALIDATION: Document Endpoints Migration")
        logger.info("="*60)
        
        main_content = self.read_main_py()
        if not main_content:
            logger.error("Cannot proceed - main.py not readable")
            return False
        
        # Check 1: DocumentStatus enum extended
        self.check(
            "1. DocumentStatus enum extended with workflow statuses",
            "REVIEW_PENDING" in main_content and "ESTIMATION_IN_PROGRESS" in main_content,
            "REVIEW_PENDING or ESTIMATION_IN_PROGRESS not found in imports"
        )
        
        # Check 2: Helper functions exist
        self.check(
            "2. get_document_repository() helper function exists",
            "async def get_document_repository()" in main_content,
            "get_document_repository() function not found"
        )
        
        self.check(
            "3. get_document_record() helper function exists",
            "async def get_document_record(" in main_content,
            "get_document_record() function not found"
        )
        
        self.check(
            "4. update_document_record() helper function exists", 
            "async def update_document_record(" in main_content,
            "update_document_record() function not found"
        )
        
        # Check 5-7: Core document operations migrated
        self.check(
            "5. upload endpoint uses repository pattern",
            "doc_record = await get_document_record(document_id)" not in main_content.split('async def upload_document')[1].split('async def')[0] and
            "await repo.create_document(" in main_content.split('async def upload_document')[1].split('async def')[0],
            "upload endpoint not properly migrated"
        )
        
        self.check(
            "6. convert endpoint uses get_document_record()",
            "doc_record = await get_document_record(document_id)" in main_content.split('async def convert_document')[1].split('async def')[0],
            "convert endpoint not migrated"
        )
        
        self.check(
            "7. extract endpoint uses repository helpers",
            "doc_record = await get_document_record(document_id)" in main_content.split('async def extract_intelligence')[1].split('async def')[0] and
            "await update_document_record(" in main_content.split('async def extract_intelligence')[1].split('async def')[0],
            "extract endpoint not fully migrated"
        )
        
        # Check 8-10: Read operations migrated
        self.check(
            "8. GET document details endpoint migrated",
            "doc_record = await get_document_record(document_id)" in main_content.split('async def get_document_details')[1].split('async def')[0],
            "get_document_details endpoint not migrated"
        )
        
        self.check(
            "9. GET document status endpoint migrated", 
            "doc_record = await get_document_record(document_id)" in main_content.split('async def get_document_status')[1].split('async def')[0],
            "get_document_status endpoint not migrated"
        )
        
        self.check(
            "10. GET document output endpoint migrated",
            "doc_record = await get_document_record(document_id)" in main_content.split('async def generate_output')[1].split('async def')[0],
            "generate_output endpoint not migrated"
        )
        
        # Check 11: Workflow endpoints migrated
        workflow_endpoints = ['create_inquiry', 'create_estimation', 'normalize_supplier_quotes', 'compare_quotations']
        workflow_migrated = all(
            "doc_record = await get_document_record(document_id)" in main_content.split(f'async def {endpoint}')[1].split('async def')[0]
            for endpoint in workflow_endpoints
            if f'async def {endpoint}' in main_content
        )
        
        self.check(
            "11. Workflow endpoints migrated (inquiry, estimation, normalize, comparison)",
            workflow_migrated,
            "Not all workflow endpoints properly migrated"
        )
        
        # Check 12: Fallback mechanism preserved
        fallback_preserved = (
            "documents_db[doc_id]" in main_content and  # Fallback still exists
            "return None" in main_content.split('get_document_repository')[1].split('async def')[0]  # Fallback in helper
        )
        
        self.check(
            "12. Fallback mechanism to in-memory storage preserved",
            fallback_preserved,
            "Fallback mechanism not properly preserved"
        )
        
        # Summary
        logger.info("="*60)
        logger.info("VALIDATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Checks passed: {self.checks_passed}/{self.checks_total}")
        
        if self.checks_passed == self.checks_total:
            logger.info("🎉 ALL CHECKS PASSED - STEP 6 IMPLEMENTATION SUCCESSFUL!")
            logger.info("   ✅ All 10 endpoints migrated to repository pattern")
            logger.info("   ✅ Fallback mode preserved for resilience") 
            logger.info("   ✅ DocumentStatus enum extended with workflow statuses")
            logger.info("   ✅ Helper functions implemented correctly")
            return True
        else:
            logger.error(f"❌ {self.checks_total - self.checks_passed} CHECKS FAILED")
            logger.error("ERRORS FOUND:")
            for error in self.errors:
                logger.error(f"   - {error}")
            return False

async def main():
    """Run Step 6 validation."""
    validator = Step6Validator()
    success = await validator.validate()
    
    if success:
        logger.info("="*60)
        logger.info("🚀 READY TO PROCEED TO STEP 7")
        logger.info("="*60)
        sys.exit(0)
    else:
        logger.error("="*60)
        logger.error("❌ VALIDATION FAILED - REVIEW IMPLEMENTATION")
        logger.error("="*60)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())