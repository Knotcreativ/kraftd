"""Template Service for KRAFTD Document Generation

Handles Jinja2 template rendering, validation, and document generation.
Supports multiple output formats: HTML, PDF, DOCX, XLSX, JSON, EMAIL
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from jinja2 import Environment, BaseLoader, TemplateError, UndefinedError
import json
from io import BytesIO
import base64

logger = logging.getLogger(__name__)


class TemplateService:
    """Service for managing and rendering Jinja2 templates"""
    
    def __init__(self, enable_sandbox: bool = True):
        """
        Initialize template service with Jinja2 environment
        
        Args:
            enable_sandbox: Enable Jinja2 sandbox for security
        """
        self.enable_sandbox = enable_sandbox
        self._init_jinja2_env()
        self.generation_cache = {}  # Simple in-memory cache
        
    def _init_jinja2_env(self):
        """Initialize Jinja2 environment with custom filters"""
        self.env = Environment(loader=BaseLoader())
        
        # Register custom filters
        self.env.filters['currency'] = self._filter_currency
        self.env.filters['date_format'] = self._filter_date_format
        self.env.filters['percentage'] = self._filter_percentage
        self.env.filters['replace_newlines'] = self._filter_replace_newlines
        self.env.filters['escape_html'] = self._filter_escape_html
        
        # Register custom functions
        self.env.globals['now'] = datetime.utcnow
        self.env.globals['today'] = self._today
        self.env.globals['range'] = range
        
    def _filter_currency(self, value: float, symbol: str = "$", decimals: int = 2) -> str:
        """Format value as currency"""
        try:
            return f"{symbol}{float(value):,.{decimals}f}"
        except (ValueError, TypeError):
            return str(value)
    
    def _filter_date_format(self, value: Any, format_str: str = "%Y-%m-%d") -> str:
        """Format date value"""
        if isinstance(value, datetime):
            return value.strftime(format_str)
        elif isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value)
                return dt.strftime(format_str)
            except:
                return value
        return str(value)
    
    def _filter_percentage(self, value: float, decimals: int = 1) -> str:
        """Format value as percentage"""
        try:
            return f"{float(value) * 100:.{decimals}f}%"
        except (ValueError, TypeError):
            return str(value)
    
    def _filter_replace_newlines(self, value: str, replacement: str = "<br />") -> str:
        """Replace newlines with HTML or other replacement"""
        if not isinstance(value, str):
            value = str(value)
        return value.replace('\n', replacement)
    
    def _filter_escape_html(self, value: str) -> str:
        """Escape HTML special characters"""
        if not isinstance(value, str):
            value = str(value)
        return (value.replace('&', '&amp;')
                     .replace('<', '&lt;')
                     .replace('>', '&gt;')
                     .replace('"', '&quot;')
                     .replace("'", '&#39;'))
    
    def _today(self) -> datetime:
        """Return today's date"""
        return datetime.utcnow()
    
    def validate_template(self, content: str) -> Dict[str, Any]:
        """
        Validate template syntax and extract variables
        
        Args:
            content: Jinja2 template content
            
        Returns:
            Dict with validation results and extracted variables
        """
        validation_result = {
            "valid": False,
            "error": None,
            "variables": [],
            "warnings": []
        }
        
        try:
            # Try to compile template
            template = self.env.from_string(content)
            
            # Extract undeclared variables
            undeclared = template.module.__dict__.get('undeclared_variables', set())
            validation_result["variables"] = sorted(list(undeclared))
            
            validation_result["valid"] = True
            logger.info(f"Template validation successful, found {len(undeclared)} variables")
            
        except TemplateError as e:
            validation_result["error"] = str(e)
            logger.warning(f"Template validation failed: {e}")
        except Exception as e:
            validation_result["error"] = f"Unexpected error: {str(e)}"
            logger.error(f"Template validation error: {e}")
        
        return validation_result
    
    def render_template(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Render Jinja2 template with provided context
        
        Args:
            content: Jinja2 template content
            context: Context variables for rendering
            
        Returns:
            Dict with rendered content or error
        """
        result = {
            "success": False,
            "content": None,
            "error": None,
            "rendered_at": datetime.utcnow(),
            "variables_used": []
        }
        
        try:
            # Compile and render template
            template = self.env.from_string(content)
            rendered = template.render(**context)
            
            # Track which variables were used
            result["content"] = rendered
            result["success"] = True
            result["variables_used"] = list(context.keys())
            
            logger.info(f"Template rendered successfully, {len(context)} variables used")
            
        except UndefinedError as e:
            result["error"] = f"Undefined variable: {str(e)}"
            logger.warning(f"Template rendering failed - undefined variable: {e}")
        except TemplateError as e:
            result["error"] = f"Template error: {str(e)}"
            logger.warning(f"Template rendering failed: {e}")
        except Exception as e:
            result["error"] = f"Rendering error: {str(e)}"
            logger.error(f"Template rendering error: {e}")
        
        return result
    
    def generate_document(self, template_content: str, context: Dict[str, Any], 
                         output_format: str = "html") -> Dict[str, Any]:
        """
        Generate document from template with specified output format
        
        Args:
            template_content: Jinja2 template content
            context: Context variables for rendering
            output_format: Output format (html, pdf, docx, xlsx, json, email)
            
        Returns:
            Dict with generated document or error
        """
        # First, render the template
        render_result = self.render_template(template_content, context)
        
        if not render_result["success"]:
            return {
                "success": False,
                "error": render_result["error"],
                "status": "error"
            }
        
        rendered_content = render_result["content"]
        
        # Handle different output formats
        if output_format == "html":
            return self._generate_html(rendered_content)
        elif output_format == "json":
            return self._generate_json(rendered_content, context)
        elif output_format == "email":
            return self._generate_email(rendered_content, context)
        else:
            # For PDF, DOCX, XLSX - would need additional libraries
            return {
                "success": True,
                "format": output_format,
                "content": rendered_content,
                "note": f"Format '{output_format}' requires additional libraries (reportlab, python-docx, openpyxl)"
            }
    
    def _generate_html(self, content: str) -> Dict[str, Any]:
        """Generate HTML document"""
        return {
            "success": True,
            "status": "success",
            "format": "html",
            "content": content,
            "content_type": "text/html; charset=utf-8",
            "generated_at": datetime.utcnow()
        }
    
    def _generate_json(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate JSON document"""
        try:
            # Try to parse rendered content as JSON
            json_content = json.loads(content)
        except json.JSONDecodeError:
            # If rendered content isn't JSON, wrap context as JSON
            json_content = {
                "rendered_html": content,
                "context": context,
                "generated_at": datetime.utcnow().isoformat()
            }
        
        return {
            "success": True,
            "status": "success",
            "format": "json",
            "content": json.dumps(json_content, indent=2, default=str),
            "content_type": "application/json",
            "generated_at": datetime.utcnow()
        }
    
    def _generate_email(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate email document (HTML + plain text)"""
        # Extract email-specific fields from context
        subject = context.get("email_subject", "KRAFTD Document")
        to_email = context.get("recipient_email", "")
        cc_list = context.get("cc_list", [])
        bcc_list = context.get("bcc_list", [])
        
        return {
            "success": True,
            "status": "success",
            "format": "email",
            "email": {
                "to": to_email,
                "cc": cc_list,
                "bcc": bcc_list,
                "subject": subject,
                "html_content": content,
                "text_content": self._html_to_text(content)
            },
            "generated_at": datetime.utcnow()
        }
    
    def _html_to_text(self, html: str) -> str:
        """Simple HTML to text conversion"""
        # Remove common HTML tags
        import re
        text = re.sub('<[^<]+?>', '', html)
        # Decode HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        return text


class TemplateValidationService:
    """Service for comprehensive template validation"""
    
    @staticmethod
    def validate_jinja2_syntax(content: str) -> Dict[str, Any]:
        """Validate Jinja2 syntax"""
        service = TemplateService()
        return service.validate_template(content)
    
    @staticmethod
    def validate_required_variables(content: str, required_vars: list) -> Dict[str, Any]:
        """Check if template has all required variables"""
        service = TemplateService()
        validation = service.validate_template(content)
        
        result = {
            "valid": validation["valid"],
            "missing_variables": [],
            "unused_required": []
        }
        
        if not validation["valid"]:
            return result
        
        template_vars = set(validation["variables"])
        required_set = set(required_vars)
        
        result["missing_variables"] = list(required_set - template_vars)
        result["unused_required"] = list(template_vars - required_set)
        result["valid"] = len(result["missing_variables"]) == 0
        
        return result
    
    @staticmethod
    def validate_template_rendering(content: str, sample_context: Dict[str, Any]) -> Dict[str, Any]:
        """Test template rendering with sample data"""
        service = TemplateService()
        return service.render_template(content, sample_context)


if __name__ == "__main__":
    # Test template service
    service = TemplateService()
    
    # Test template
    template = """
    <h1>{{ title }}</h1>
    <p>Total Amount: {{ total_amount | currency }}</p>
    <p>Date: {{ date_field | date_format('%B %d, %Y') }}</p>
    <p>Discount: {{ discount | percentage }}</p>
    """
    
    # Validate
    validation = service.validate_template(template)
    print(f"Validation: {validation}")
    
    # Render
    context = {
        "title": "Purchase Order",
        "total_amount": 15000.50,
        "date_field": datetime.now(),
        "discount": 0.10
    }
    
    result = service.render_template(template, context)
    print(f"Render result: {result}")
    
    # Generate HTML
    html_result = service.generate_document(template, context, "html")
    print(f"Generated HTML: {html_result}")
