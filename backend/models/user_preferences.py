"""
User profile and preferences models for FastAPI
Handles user profile data and user preferences
"""

from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, validator


class Theme(str, Enum):
    """User theme preference"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class NotificationFrequency(str, Enum):
    """Email notification frequency"""
    REALTIME = "realtime"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    NEVER = "never"


class Language(str, Enum):
    """User language preference"""
    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    PT = "pt"
    ZH = "zh"


class DashboardLayout(str, Enum):
    """Dashboard layout preference"""
    GRID = "grid"
    LIST = "list"
    COMPACT = "compact"


class ProfileUpdate(BaseModel):
    """Model for updating user profile"""
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    bio: Optional[str] = Field(None, max_length=500)
    company: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=255)
    
    @validator("phone")
    def validate_phone(cls, v):
        """Validate phone number contains only digits and common separators"""
        if v and not all(c.isdigit() or c in "-+() " for c in v):
            raise ValueError("Phone number contains invalid characters")
        return v
    
    class Config:
        example = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1-555-0123",
            "bio": "Supply chain analyst",
            "company": "TechCorp",
            "job_title": "Senior Analyst",
            "location": "San Francisco, CA",
            "website": "https://example.com"
        }


class Preferences(BaseModel):
    """Model for user preferences"""
    
    theme: Theme = Field(default=Theme.LIGHT)
    language: Language = Field(default=Language.EN)
    dashboard_layout: DashboardLayout = Field(default=DashboardLayout.GRID)
    
    # Notification preferences
    email_notifications_enabled: bool = Field(default=True)
    notification_frequency: NotificationFrequency = Field(default=NotificationFrequency.DAILY)
    
    # Alert preferences
    price_alerts_enabled: bool = Field(default=True)
    anomaly_alerts_enabled: bool = Field(default=True)
    supplier_alerts_enabled: bool = Field(default=True)
    trend_alerts_enabled: bool = Field(default=True)
    
    # Feature preferences
    enable_advanced_ml: bool = Field(default=True)
    enable_predictive_analytics: bool = Field(default=True)
    enable_recommendations: bool = Field(default=True)
    
    # Privacy preferences
    share_usage_data: bool = Field(default=False)
    allow_marketing_emails: bool = Field(default=False)
    
    # Additional settings
    default_currency: str = Field(default="USD", min_length=3, max_length=3)
    timezone: str = Field(default="UTC", max_length=50)
    rows_per_page: int = Field(default=25, ge=5, le=100)
    
    class Config:
        example = {
            "theme": "dark",
            "language": "en",
            "dashboard_layout": "grid",
            "email_notifications_enabled": True,
            "notification_frequency": "daily",
            "price_alerts_enabled": True,
            "anomaly_alerts_enabled": True,
            "supplier_alerts_enabled": True,
            "trend_alerts_enabled": True,
            "enable_advanced_ml": True,
            "enable_predictive_analytics": True,
            "enable_recommendations": True,
            "share_usage_data": False,
            "allow_marketing_emails": False,
            "default_currency": "USD",
            "timezone": "America/New_York",
            "rows_per_page": 25
        }


class UserProfile(BaseModel):
    """Model for user profile response"""
    
    email: str = Field(..., description="User email")
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    
    created_at: datetime = Field(description="Profile creation timestamp")
    updated_at: datetime = Field(description="Profile last update timestamp")
    
    class Config:
        example = {
            "email": "user@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1-555-0123",
            "bio": "Supply chain analyst",
            "company": "TechCorp",
            "job_title": "Senior Analyst",
            "location": "San Francisco, CA",
            "website": "https://example.com",
            "created_at": "2025-01-15T10:30:00Z",
            "updated_at": "2025-01-18T14:45:00Z"
        }


class UserPreferencesResponse(BaseModel):
    """Model for user preferences response"""
    
    email: str = Field(..., description="User email")
    preferences: Preferences = Field(..., description="User preferences")
    updated_at: datetime = Field(description="Preferences last update timestamp")
    
    class Config:
        example = {
            "email": "user@example.com",
            "preferences": {
                "theme": "dark",
                "language": "en",
                "dashboard_layout": "grid",
                "email_notifications_enabled": True,
                "notification_frequency": "daily"
            },
            "updated_at": "2025-01-18T14:45:00Z"
        }
