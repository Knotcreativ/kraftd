from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from enum import Enum

# ===== Enums =====
class DocumentType(str, Enum):
    RFQ = "RFQ"
    BOQ = "BOQ"
    QUOTATION = "Quotation"
    PO = "PO"
    CONTRACT = "Contract"
    ADDENDUM = "Addendum"
    INVOICE = "Invoice"

class UserIntent(str, Enum):
    SELL = "sell"
    BUY = "buy"
    ESTIMATE = "estimate"
    CONSULT = "consult"
    INQUIRE = "inquire"

class Currency(str, Enum):
    SAR = "SAR"
    USD = "USD"
    AED = "AED"
    EUR = "EUR"
    GBP = "GBP"
    INR = "INR"

class UnitOfMeasure(str, Enum):
    METER = "m"
    SQUARE_METER = "m2"
    CUBIC_METER = "m3"
    KILOGRAM = "kg"
    TON = "ton"
    LITER = "liter"
    PIECE = "piece"
    SET = "set"
    LOT = "lot"
    HOUR = "hour"
    DAY = "day"
    EACH = "each"

class RiskLevel(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"

class Incoterms(str, Enum):
    FOB = "FOB"
    CIF = "CIF"
    DAP = "DAP"
    DDP = "DDP"
    EX_WORKS = "Ex Works"

class Discipline(str, Enum):
    CIVIL = "civil"
    MECHANICAL = "mechanical"
    ELECTRICAL = "electrical"
    INSTRUMENTATION = "instrumentation"
    HVAC = "HVAC"
    PLUMBING = "plumbing"
    MIXED = "mixed"

class PaymentBasis(str, Enum):
    LUMP_SUM = "lump_sum"
    UNIT_RATE = "unit_rate"
    COST_PLUS = "cost_plus"
    MILESTONE_BASED = "milestone_based"
    HYBRID = "hybrid"

class Phase(str, Enum):
    TENDER = "tender"
    EXECUTION = "execution"
    VARIATION = "variation"
    CLOSE_OUT = "close_out"
    FRAMEWORK = "framework"
    STANDING_ORDER = "standing_order"

class Criticality(str, Enum):
    CRITICAL_PATH = "critical_path"
    ON_PATH = "on_path"
    BUFFER = "buffer"
    NON_CRITICAL = "non_critical"

class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    EXTRACTED = "extracted"
    REVIEW_PENDING = "review_pending"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class ExtractionMethod(str, Enum):
    DIRECT_PARSE = "direct_parse"
    OCR = "ocr"
    AI_EXTRACTION = "ai_extraction"
    HYBRID = "hybrid"

# ===== Basic Models =====
class Address(BaseModel):
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

class Contact(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    department: Optional[str] = None

class Label(BaseModel):
    key: str  # "commodity", "urgency", "supplier_tier", "risk_level"
    value: str
    confidence: Optional[float] = None
    auto_assigned: bool = True

class AuditLog(BaseModel):
    timestamp: datetime
    action: str  # "created", "extracted", "reviewed", "approved", "modified"
    user: Optional[str] = None
    details: Optional[str] = None

class ReviewState(BaseModel):
    is_reviewed: bool = False
    is_normalized: bool = False
    reviewer_notes: Optional[str] = None
    review_date: Optional[datetime] = None
    reviewer: Optional[str] = None

class ProcessingMetadata(BaseModel):
    extraction_method: ExtractionMethod
    ocr_confidence: Optional[float] = None
    processing_duration_ms: int
    processor_version: str = "1.0.0"
    source_file_hash: Optional[str] = None
    source_file_size_bytes: int

class DataQuality(BaseModel):
    completeness_percentage: float
    accuracy_score: float
    warnings: Optional[List[str]] = None
    requires_manual_review: bool = False

class Party(BaseModel):
    name: str
    legal_entity: Optional[str] = None
    trn_vat_number: Optional[str] = None
    contact_person: Optional[Contact] = None
    registered_address: Optional[Address] = None
    project_address: Optional[Address] = None
    billing_address: Optional[Address] = None
    bank_account: Optional[str] = None

# ===== Line Item Model =====
class LineItem(BaseModel):
    line_number: int
    item_code: Optional[str] = None
    drawing_reference: Optional[str] = None
    wbs_code: Optional[str] = None
    description: str
    technical_spec: Optional[str] = None
    model_brand: Optional[str] = None
    
    quantity: float
    unit_of_measure: UnitOfMeasure
    min_quantity: Optional[float] = None
    max_quantity: Optional[float] = None
    
    unit_price: float
    total_price: float
    currency: Currency
    discount_percentage: Optional[float] = None
    discount_amount: Optional[float] = None
    
    delivery_time: Optional[str] = None
    delivery_location: Optional[str] = None
    packaging_notes: Optional[str] = None
    
    status_flags: Optional[List[str]] = None
    notes: Optional[str] = None
    
    is_alternative: bool = False
    parent_item_id: Optional[str] = None
    data_quality: Optional[str] = None  # "high" | "medium" | "low"
    requires_clarification: bool = False
    normalization_notes: Optional[str] = None

# ===== Metadata Models =====
class DocumentMetadata(BaseModel):
    document_type: DocumentType
    document_number: str
    revision_number: Optional[str] = None
    issue_date: Optional[date] = None
    page_count: Optional[int] = None
    pages_present: Optional[str] = None
    user_intent: Optional[UserIntent] = None

class ProjectContext(BaseModel):
    project_name: Optional[str] = None
    project_code: Optional[str] = None
    client_name: Optional[str] = None
    end_user: Optional[str] = None
    location: Optional[str] = None
    discipline: Optional[Discipline] = None
    package: Optional[str] = None

class Dates(BaseModel):
    issue_date: Optional[date] = None
    submission_deadline: Optional[date] = None
    validity_date: Optional[date] = None
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    delivery_date: Optional[date] = None

class CommercialTerms(BaseModel):
    currency: Optional[Currency] = None
    tax_vat_mentioned: Optional[bool] = None
    vat_rate: Optional[float] = None
    incoterms: Optional[Incoterms] = None
    payment_terms: Optional[str] = None
    performance_guarantee: Optional[bool] = None
    retention_percentage: Optional[float] = None
    warranty_period: Optional[str] = None
    
    has_advance_payment: bool = False
    advance_payment_percentage: Optional[float] = None
    milestone_based_payment: bool = False
    payment_currency_different_from_doc: bool = False
    special_conditions: Optional[List[str]] = None

class DocumentRelationship(BaseModel):
    related_document_id: str
    relationship_type: str  # "rfq_for", "quotation_for", "po_for", "variation_of"
    relationship_direction: str  # "parent" | "child" | "sibling"

class SupplierSignal(BaseModel):
    supplier_id: Optional[str] = None
    supplier_name: str
    risk_score: float  # 0-100, higher = more risky
    reliability_score: Optional[float] = None
    deviation_count: int = 0
    notes: Optional[List[str]] = None

# ===== RFQ-Specific Models =====
class RFQScope(BaseModel):
    packages_included: Optional[List[str]] = None
    packages_excluded: Optional[List[str]] = None
    work_type: Optional[str] = None

class SubmissionInstructions(BaseModel):
    submission_method: Optional[str] = None
    submission_address: Optional[str] = None
    required_documents: Optional[List[str]] = None
    number_of_copies: Optional[int] = None
    required_formats: Optional[List[str]] = None

class EvaluationCriteria(BaseModel):
    technical_score_weight: Optional[float] = None
    commercial_score_weight: Optional[float] = None
    mandatory_compliance_points: Optional[List[str]] = None
    prequalification_requirements: Optional[List[str]] = None
    scoring_method: Optional[str] = None

class RFQConditions(BaseModel):
    liquidated_damages: Optional[float] = None
    performance_penalties: Optional[List[str]] = None
    mandatory_guarantees: Optional[List[str]] = None
    retention_percentage: Optional[float] = None
    bond_requirement: Optional[bool] = None
    insurance_requirement: Optional[str] = None

class RFQData(BaseModel):
    scope: Optional[RFQScope] = None
    submission_instructions: Optional[SubmissionInstructions] = None
    evaluation_criteria: Optional[EvaluationCriteria] = None
    conditions: Optional[RFQConditions] = None

# ===== Quotation-Specific Models =====
class Deviation(BaseModel):
    item_line: Optional[int] = None
    deviation_type: str
    deviation_description: str
    impact: Optional[RiskLevel] = None
    reason: Optional[str] = None

class QuotationData(BaseModel):
    quotation_number: Optional[str] = None
    quotation_date: Optional[date] = None
    linked_rfq_number: Optional[str] = None
    offer_validity: Optional[date] = None
    delivery_terms: Optional[str] = None
    payment_terms: Optional[str] = None
    discount_structure: Optional[List[str]] = None
    overall_discount: Optional[float] = None
    
    deviations_from_rfq: Optional[List[Deviation]] = None
    exclusions: Optional[List[str]] = None
    clarifications: Optional[List[str]] = None
    warranty_terms: Optional[str] = None
    after_sales_support: Optional[str] = None
    
    total_quoted_value: Optional[float] = None
    vat_amount: Optional[float] = None
    final_amount: Optional[float] = None

# ===== PO-Specific Models =====
class SplitDelivery(BaseModel):
    delivery_number: int
    delivery_date: Optional[date] = None
    items: Optional[List[int]] = None
    location: Optional[str] = None
    quantity_portion: Optional[float] = None

class PriceVariance(BaseModel):
    line: int
    quoted_price: float
    po_price: float
    variance: float

class PaymentMilestone(BaseModel):
    milestone: int
    description: str
    payment_percentage: float
    trigger_condition: Optional[str] = None

class POData(BaseModel):
    po_number: str
    po_date: Optional[date] = None
    linked_rfq_number: Optional[str] = None
    linked_quotation_number: Optional[str] = None
    
    split_deliveries: Optional[List[SplitDelivery]] = None
    po_value: Optional[float] = None
    agreed_prices_vs_quoted: Optional[List[PriceVariance]] = None
    payment_milestones: Optional[List[PaymentMilestone]] = None
    
    liquidated_damages: Optional[float] = None
    performance_guarantee: Optional[bool] = None
    retention_percentage: Optional[float] = None
    termination_clause: Optional[str] = None
    change_order_procedure: Optional[str] = None

# ===== Contract-Specific Models =====
class ContractMilestone(BaseModel):
    milestone_number: int
    description: str
    condition: str
    payment_percentage: float
    due_date: Optional[date] = None

class ContractData(BaseModel):
    contract_number: Optional[str] = None
    contract_type: Optional[str] = None
    effective_date: Optional[date] = None
    duration: Optional[str] = None
    
    scope_summary: Optional[str] = None
    deliverables: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    disciplines: Optional[List[Discipline]] = None
    
    payment_basis: Optional[PaymentBasis] = None
    milestones: Optional[List[ContractMilestone]] = None
    total_contract_value: Optional[float] = None
    
    indemnity_clause: Optional[bool] = None
    liability_cap: Optional[float] = None
    force_majeure: Optional[bool] = None
    insurance_required: Optional[str] = None
    dispute_resolution: Optional[str] = None
    termination_conditions: Optional[List[str]] = None
    change_management: Optional[bool] = None

# ===== Signals Models =====
class Categorization(BaseModel):
    commodity_category: Optional[str] = None
    subcategory: Optional[str] = None
    supplier_tier: Optional[str] = None
    spend_category: Optional[str] = None

class RiskIndicators(BaseModel):
    validity_days: Optional[int] = None
    price_confidence: Optional[str] = None
    aggressive_discount: Optional[bool] = None
    heavy_deviations: Optional[bool] = None
    long_lead_time: Optional[bool] = None
    rare_commodity: Optional[bool] = None

class BehavioralPatterns(BaseModel):
    supplier_on_time_rate: Optional[float] = None
    supplier_deviation_frequency: Optional[int] = None
    supplier_price_consistency: Optional[str] = None
    supplier_payment_term_variance: Optional[bool] = None
    supplier_warranty_reliability: Optional[str] = None
    item_variation_frequency: Optional[int] = None
    item_availability_risk: Optional[str] = None

class Signals(BaseModel):
    categorization: Optional[Categorization] = None
    risk_indicators: Optional[RiskIndicators] = None
    behavioral_patterns: Optional[BehavioralPatterns] = None
    phase: Optional[Phase] = None
    criticality: Optional[Criticality] = None

# ===== Extraction Confidence Model =====
class FieldConfidence(BaseModel):
    parties: Optional[float] = None
    line_items: Optional[float] = None
    dates: Optional[float] = None
    commercial_terms: Optional[float] = None
    project_context: Optional[float] = None
    document_specific: Optional[float] = None

class ExtractionConfidence(BaseModel):
    overall_confidence: float
    field_confidence: Optional[FieldConfidence] = None
    missing_fields: Optional[List[str]] = None
    flags: Optional[List[str]] = None

# ===== Main Document Model =====
class KraftdDocument(BaseModel):
    document_id: str
    metadata: DocumentMetadata
    parties: Dict[str, Party]  # "issuer", "recipient"
    project_context: Optional[ProjectContext] = None
    dates: Optional[Dates] = None
    commercial_terms: Optional[CommercialTerms] = None
    line_items: Optional[List[LineItem]] = None
    
    document_specific: Dict[str, Optional[Any]] = {
        "rfq_data": None,
        "quotation_data": None,
        "po_data": None,
        "contract_data": None
    }
    
    signals: Optional[Signals] = None
    extraction_confidence: Optional[ExtractionConfidence] = None
    
    # ===== Lifecycle & Status =====
    status: DocumentStatus = DocumentStatus.UPLOADED
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    last_modified_by: Optional[str] = None
    
    # ===== Processing & Quality =====
    processing_metadata: Optional[ProcessingMetadata] = None
    data_quality: Optional[DataQuality] = None
    review_state: Optional[ReviewState] = None
    
    # ===== Document Relationships & Signals =====
    related_documents: Optional[List[DocumentRelationship]] = None
    parent_document_id: Optional[str] = None
    supplier_signals: Optional[List[SupplierSignal]] = None
    overall_risk_score: float = 0.0
    
    # ===== Labels & Audit =====
    labels: Optional[List[Label]] = None
    audit_log: Optional[List[AuditLog]] = None
    
    class Config:
        use_enum_values = True
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
