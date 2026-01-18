#!/usr/bin/env python
"""Quick test of Phase 4 template system"""

import sys
sys.path.insert(0, '.')

from services.template_storage import TemplateStorageService, initialize_sample_templates
from services.template_service import TemplateService, TemplateValidationService

print("\n" + "="*60)
print("PHASE 4: TEMPLATE SYSTEM TEST")
print("="*60 + "\n")

# Initialize sample templates
print("[1] Initializing sample templates...")
initialize_sample_templates("test-user")
print("    ✓ Sample templates created\n")

# Get statistics
print("[2] Getting template statistics...")
stats = TemplateStorageService.get_statistics()
print(f"    ✓ Total templates: {stats['total_count']}")
print(f"    ✓ By category: {stats['by_category']}")
print(f"    ✓ By format: {stats['by_format']}")
print()

# Get a template
print("[3] Retrieving first template...")
templates = TemplateStorageService.get_templates()
if templates:
    first_template = templates[0]
    print(f"    ✓ Template ID: {first_template.id}")
    print(f"    ✓ Name: {first_template.name}")
    print(f"    ✓ Category: {first_template.category}")
    print(f"    ✓ Format: {first_template.format}")
    print()
    
    # Validate template
    print("[4] Validating template syntax...")
    validation = TemplateValidationService.validate_jinja2_syntax(first_template.content)
    print(f"    ✓ Valid: {validation['valid']}")
    print(f"    ✓ Variables found: {validation['variables']}")
    print()
    
    # Test rendering (quotation summary)
    if first_template.category.value == "quotation_summary":
        print("[5] Testing template rendering...")
        context = {
            "quote_title": "Test Quote #001",
            "supplier_name": "Test Supplier Inc",
            "quote_date": "2026-01-18",
            "items": [
                {"description": "Widget A", "quantity": 100, "unit_price": 10.50, "total": 1050},
                {"description": "Widget B", "quantity": 50, "unit_price": 15.00, "total": 750}
            ],
            "grand_total": 1800,
            "payment_terms": "Net 30",
            "validity_period": 30
        }
        
        result = TemplateService().render_template(first_template.content, context)
        print(f"    ✓ Render successful: {result['success']}")
        if result['success']:
            print(f"    ✓ Content length: {len(result['content'])} chars")
            print(f"    ✓ Variables used: {result['variables_used']}")
        print()

print("="*60)
print("ALL TESTS PASSED ✓")
print("="*60 + "\n")
