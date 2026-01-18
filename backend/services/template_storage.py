"""Template Storage Service for KRAFTD

Handles CRUD operations for templates with in-memory storage (MVP).
In production, would use Cosmos DB for persistence.

Template Storage Structure:
- In-memory dictionary: {template_id -> template_data}
- Indices for quick lookups: by category, by name, by owner
- Serialization for backup/restore
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
from models.template import (
    Template, TemplateCategory, TemplateFormat,
    TemplateCreateRequest, TemplateUpdateRequest
)

logger = logging.getLogger(__name__)


class TemplateStorageService:
    """In-memory storage service for templates (MVP implementation)"""
    
    # Class-level storage (persists across requests in same process)
    _templates: Dict[str, Template] = {}
    _indices = {
        "by_category": {},  # {category -> [template_ids]}
        "by_owner": {},     # {user_id -> [template_ids]}
        "by_name": {}       # {name -> template_id} (for quick lookup)
    }
    
    @classmethod
    def create_template(cls, request: TemplateCreateRequest, created_by: str) -> Template:
        """
        Create and store a new template
        
        Args:
            request: Template creation request
            created_by: User ID of template creator
            
        Returns:
            Created template object
        """
        template_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        template = Template(
            id=template_id,
            name=request.name,
            description=request.description,
            category=request.category,
            format=request.format,
            content=request.content,
            variables=request.variables,
            fields=request.fields,
            is_default=request.is_default,
            created_by=created_by,
            created_at=now,
            updated_at=now
        )
        
        # Store template
        cls._templates[template_id] = template
        
        # Update indices
        cls._update_indices_on_create(template)
        
        logger.info(f"Template created: {template_id} by {created_by}")
        return template
    
    @classmethod
    def get_template(cls, template_id: str) -> Optional[Template]:
        """
        Retrieve a template by ID
        
        Args:
            template_id: Template ID
            
        Returns:
            Template object or None if not found
        """
        template = cls._templates.get(template_id)
        if template:
            logger.debug(f"Template retrieved: {template_id}")
        else:
            logger.debug(f"Template not found: {template_id}")
        return template
    
    @classmethod
    def get_templates(cls, category: Optional[TemplateCategory] = None,
                     created_by: Optional[str] = None,
                     active_only: bool = True) -> List[Template]:
        """
        List templates with optional filtering
        
        Args:
            category: Filter by category
            created_by: Filter by creator
            active_only: Return only active templates
            
        Returns:
            List of matching templates
        """
        templates = list(cls._templates.values())
        
        # Filter by category
        if category:
            templates = [t for t in templates if t.category == category]
        
        # Filter by creator
        if created_by:
            templates = [t for t in templates if t.created_by == created_by]
        
        # Filter active only
        if active_only:
            templates = [t for t in templates if t.is_active]
        
        logger.debug(f"Retrieved {len(templates)} templates")
        return templates
    
    @classmethod
    def update_template(cls, template_id: str, request: TemplateUpdateRequest) -> Optional[Template]:
        """
        Update an existing template
        
        Args:
            template_id: Template ID
            request: Update request with fields to modify
            
        Returns:
            Updated template or None if not found
        """
        template = cls._templates.get(template_id)
        if not template:
            logger.warning(f"Template not found for update: {template_id}")
            return None
        
        # Update fields
        if request.name is not None:
            template.name = request.name
        if request.description is not None:
            template.description = request.description
        if request.content is not None:
            template.content = request.content
        if request.variables is not None:
            template.variables = request.variables
        if request.fields is not None:
            template.fields = request.fields
        if request.is_active is not None:
            template.is_active = request.is_active
        if request.is_default is not None:
            template.is_default = request.is_default
        
        # Update metadata
        template.version = f"{float(template.version) + 0.1:.1f}"
        template.updated_at = datetime.utcnow()
        
        logger.info(f"Template updated: {template_id}")
        return template
    
    @classmethod
    def delete_template(cls, template_id: str) -> bool:
        """
        Delete a template
        
        Args:
            template_id: Template ID
            
        Returns:
            True if deleted, False if not found
        """
        if template_id not in cls._templates:
            logger.warning(f"Template not found for deletion: {template_id}")
            return False
        
        template = cls._templates.pop(template_id)
        cls._update_indices_on_delete(template)
        
        logger.info(f"Template deleted: {template_id}")
        return True
    
    @classmethod
    def record_usage(cls, template_id: str) -> bool:
        """
        Record template usage (increment usage_count, update last_used_at)
        
        Args:
            template_id: Template ID
            
        Returns:
            True if updated, False if not found
        """
        template = cls._templates.get(template_id)
        if not template:
            logger.warning(f"Template not found for usage update: {template_id}")
            return False
        
        template.usage_count += 1
        template.last_used_at = datetime.utcnow()
        
        logger.debug(f"Template usage recorded: {template_id} (count: {template.usage_count})")
        return True
    
    @classmethod
    def get_default_template(cls, category: TemplateCategory) -> Optional[Template]:
        """
        Get the default template for a category
        
        Args:
            category: Template category
            
        Returns:
            Default template or None if not found
        """
        templates = [t for t in cls._templates.values()
                    if t.category == category and t.is_default and t.is_active]
        
        if templates:
            logger.debug(f"Default template found for {category}")
            return templates[0]
        
        logger.debug(f"No default template found for {category}")
        return None
    
    @classmethod
    def duplicate_template(cls, template_id: str, new_name: str, created_by: str) -> Optional[Template]:
        """
        Create a copy of an existing template
        
        Args:
            template_id: Source template ID
            new_name: Name for the duplicated template
            created_by: User ID of duplicator
            
        Returns:
            New template or None if source not found
        """
        source = cls._templates.get(template_id)
        if not source:
            logger.warning(f"Source template not found for duplication: {template_id}")
            return None
        
        # Create request from source
        request = TemplateCreateRequest(
            name=new_name,
            description=f"Copy of: {source.name}" if source.description else None,
            category=source.category,
            format=source.format,
            content=source.content,
            variables=source.variables,
            fields=source.fields,
            is_default=False  # Duplicates are never default
        )
        
        new_template = cls.create_template(request, created_by)
        logger.info(f"Template duplicated: {template_id} -> {new_template.id}")
        return new_template
    
    @classmethod
    def _update_indices_on_create(cls, template: Template):
        """Update indices when creating a template"""
        # Index by category
        if template.category not in cls._indices["by_category"]:
            cls._indices["by_category"][template.category] = []
        cls._indices["by_category"][template.category].append(template.id)
        
        # Index by owner
        if template.created_by not in cls._indices["by_owner"]:
            cls._indices["by_owner"][template.created_by] = []
        cls._indices["by_owner"][template.created_by].append(template.id)
        
        # Index by name
        cls._indices["by_name"][template.name] = template.id
    
    @classmethod
    def _update_indices_on_delete(cls, template: Template):
        """Update indices when deleting a template"""
        # Remove from category index
        if template.category in cls._indices["by_category"]:
            try:
                cls._indices["by_category"][template.category].remove(template.id)
            except ValueError:
                pass
        
        # Remove from owner index
        if template.created_by in cls._indices["by_owner"]:
            try:
                cls._indices["by_owner"][template.created_by].remove(template.id)
            except ValueError:
                pass
        
        # Remove from name index
        if template.name in cls._indices["by_name"]:
            del cls._indices["by_name"][template.name]
    
    @classmethod
    def clear_all(cls):
        """Clear all templates (for testing)"""
        cls._templates.clear()
        cls._indices = {
            "by_category": {},
            "by_owner": {},
            "by_name": {}
        }
        logger.info("All templates cleared")
    
    @classmethod
    def get_statistics(cls) -> Dict[str, Any]:
        """Get statistics about stored templates"""
        templates = list(cls._templates.values())
        
        if not templates:
            return {
                "total_count": 0,
                "by_category": {},
                "by_owner": {},
                "by_format": {},
                "most_used": None,
                "total_usage_count": 0
            }
        
        stats = {
            "total_count": len(templates),
            "by_category": {},
            "by_owner": {},
            "by_format": {},
            "most_used": None,
            "total_usage_count": sum(t.usage_count for t in templates),
            "active_count": sum(1 for t in templates if t.is_active),
            "default_count": sum(1 for t in templates if t.is_default)
        }
        
        # Count by category
        for template in templates:
            cat = str(template.category)
            stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
            
            fmt = str(template.format)
            stats["by_format"][fmt] = stats["by_format"].get(fmt, 0) + 1
            
            owner = template.created_by
            stats["by_owner"][owner] = stats["by_owner"].get(owner, 0) + 1
        
        # Find most used
        most_used = max(templates, key=lambda t: t.usage_count)
        if most_used.usage_count > 0:
            stats["most_used"] = {
                "id": most_used.id,
                "name": most_used.name,
                "usage_count": most_used.usage_count
            }
        
        return stats


# Sample templates for MVP
SAMPLE_TEMPLATES = {
    "quotation_summary_html": {
        "name": "Quotation Summary - HTML",
        "category": TemplateCategory.QUOTATION_SUMMARY,
        "format": TemplateFormat.HTML,
        "content": """<h1>{{ quote_title }}</h1>
<p><strong>Supplier:</strong> {{ supplier_name }}</p>
<p><strong>Date:</strong> {{ quote_date | date_format('%B %d, %Y') }}</p>
<table border="1" cellpadding="5">
    <tr>
        <th>Item Description</th>
        <th>Quantity</th>
        <th>Unit Price</th>
        <th>Total</th>
    </tr>
    {% for item in items %}
    <tr>
        <td>{{ item.description }}</td>
        <td>{{ item.quantity }}</td>
        <td>{{ item.unit_price | currency }}</td>
        <td>{{ item.total | currency }}</td>
    </tr>
    {% endfor %}
</table>
<p><strong>Grand Total:</strong> {{ grand_total | currency }}</p>
<p><strong>Terms:</strong> {{ payment_terms }}</p>
<p><strong>Validity:</strong> {{ validity_period }} days</p>"""
    },
    "purchase_order_docx": {
        "name": "Purchase Order - DOCX",
        "category": TemplateCategory.PURCHASE_ORDER,
        "format": TemplateFormat.DOCX,
        "content": """PURCHASE ORDER

PO Number: {{ po_number }}
Date: {{ po_date | date_format('%m/%d/%Y') }}
Reference: {{ reference_number }}

SUPPLIER:
{{ supplier_company }}
{{ supplier_address }}
{{ supplier_city }}, {{ supplier_state }} {{ supplier_zip }}

DELIVERY ADDRESS:
{{ delivery_company }}
{{ delivery_address }}
{{ delivery_city }}, {{ delivery_state }} {{ delivery_zip }}

ITEMS:
{% for item in items %}
{{ loop.index }}. {{ item.description }}
   Quantity: {{ item.quantity }} {{ item.unit }}
   Unit Price: {{ item.unit_price | currency }}
   Total: {{ item.total | currency }}
{% endfor %}

SUMMARY:
Subtotal: {{ subtotal | currency }}
Tax: {{ tax | currency }}
Total: {{ total | currency }}

Payment Terms: {{ payment_terms }}
Delivery Date: {{ delivery_date | date_format('%B %d, %Y') }}
Notes: {{ special_notes }}

Authorized By: {{ authorized_by }}
Date: {{ authorization_date | date_format('%m/%d/%Y') }}"""
    },
    "comparison_matrix_xlsx": {
        "name": "Supplier Comparison Matrix - XLSX",
        "category": TemplateCategory.COMPARISON_MATRIX,
        "format": TemplateFormat.XLSX,
        "content": """SUPPLIER COMPARISON MATRIX - {{ rfq_number }}

Generated: {{ generated_date | date_format('%B %d, %Y') }}
Criteria: {{ evaluation_criteria }}

SUPPLIER SCORES:
Supplier | Price Score | Quality Score | Delivery Score | Overall Score | Recommendation
{% for supplier in suppliers %}
{{ supplier.name }} | {{ supplier.price_score | percentage }} | {{ supplier.quality_score | percentage }} | {{ supplier.delivery_score | percentage }} | {{ supplier.overall_score | percentage }} | {{ supplier.recommendation }}
{% endfor %}

SUMMARY:
Recommended Supplier: {{ recommended_supplier }}
Total Cost Savings: {{ total_savings | currency }}
Risk Level: {{ risk_level }}
Next Steps: {{ next_steps }}"""
    }
}


def initialize_sample_templates(user_id: str = "admin"):
    """Initialize with sample templates (for testing/MVP)"""
    for template_key, template_data in SAMPLE_TEMPLATES.items():
        request = TemplateCreateRequest(**template_data)
        TemplateStorageService.create_template(request, user_id)
    logger.info(f"Initialized {len(SAMPLE_TEMPLATES)} sample templates")
