"""
ML Data Pipeline for KraftdDocument Metadata

Extracts and transforms metadata from Cosmos DB for model training:
- Risk prediction features
- Price prediction features  
- Supplier reliability features
- Document classification features
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class FeatureSet(str, Enum):
    """Available feature sets for different ML tasks"""
    RISK_PREDICTION = "risk_prediction"
    PRICE_PREDICTION = "price_prediction"
    SUPPLIER_RELIABILITY = "supplier_reliability"
    DOCUMENT_CLASSIFICATION = "document_classification"


class MetadataFeatureExtractor:
    """Extract features from KraftdDocument metadata"""
    
    def __init__(self):
        """Initialize feature extractor"""
        self.feature_columns = []
        self.categorical_features = []
        self.numerical_features = []
    
    @staticmethod
    def extract_document_features(doc: Dict) -> Dict:
        """
        Extract document-level features from KraftdDocument
        
        Args:
            doc: KraftdDocument dictionary
            
        Returns:
            Dictionary of extracted features
        """
        features = {}
        
        # Document metadata features
        metadata = doc.get("metadata", {})
        features["document_type"] = metadata.get("document_type")
        features["document_number"] = str(metadata.get("document_number", ""))[:20]
        
        # Date features
        dates = doc.get("dates", {})
        if dates.get("issue_date"):
            issue_date = datetime.fromisoformat(str(dates["issue_date"]))
            features["days_since_issue"] = (datetime.now() - issue_date).days
        
        if dates.get("submission_deadline"):
            deadline = datetime.fromisoformat(str(dates["submission_deadline"]))
            features["days_until_deadline"] = (deadline - datetime.now()).days
        
        # Party features
        parties = doc.get("parties", {})
        features["num_parties"] = len(parties)
        features["has_issuer"] = "issuer" in parties
        features["has_recipient"] = "recipient" in parties
        
        # Project context
        project = doc.get("project_context", {})
        features["has_project_code"] = bool(project.get("project_code"))
        features["has_client_name"] = bool(project.get("client_name"))
        features["discipline"] = project.get("discipline")
        
        # Line items features
        line_items = doc.get("line_items", [])
        if line_items:
            features["num_line_items"] = len(line_items)
            features["total_quantity"] = sum(
                item.get("quantity", 0) for item in line_items
            )
            features["total_value"] = sum(
                item.get("total_price", 0) for item in line_items
            )
            features["avg_unit_price"] = np.mean([
                item.get("unit_price", 0) for item in line_items if item.get("unit_price")
            ]) if line_items else 0
            features["has_deviations"] = any(
                item.get("is_alternative", False) for item in line_items
            )
        else:
            features["num_line_items"] = 0
            features["total_quantity"] = 0
            features["total_value"] = 0
            features["avg_unit_price"] = 0
            features["has_deviations"] = False
        
        return features
    
    @staticmethod
    def extract_commercial_features(doc: Dict) -> Dict:
        """
        Extract commercial terms features
        
        Args:
            doc: KraftdDocument dictionary
            
        Returns:
            Dictionary of commercial features
        """
        features = {}
        
        commercial = doc.get("commercial_terms", {})
        features["currency"] = commercial.get("currency")
        features["has_vat"] = commercial.get("tax_vat_mentioned", False)
        features["vat_rate"] = commercial.get("vat_rate", 0)
        features["incoterms"] = commercial.get("incoterms")
        features["has_performance_guarantee"] = commercial.get("performance_guarantee", False)
        features["retention_percentage"] = commercial.get("retention_percentage", 0)
        features["has_advance_payment"] = commercial.get("has_advance_payment", False)
        features["advance_payment_pct"] = commercial.get("advance_payment_percentage", 0)
        features["has_milestone_payment"] = commercial.get("milestone_based_payment", False)
        features["num_special_conditions"] = len(commercial.get("special_conditions", []))
        
        return features
    
    @staticmethod
    def extract_risk_features(doc: Dict) -> Dict:
        """
        Extract risk indicator features
        
        Args:
            doc: KraftdDocument dictionary
            
        Returns:
            Dictionary of risk features
        """
        features = {}
        
        signals = doc.get("signals", {})
        risk_ind = signals.get("risk_indicators", {})
        
        features["validity_days"] = risk_ind.get("validity_days", 0)
        features["price_confidence"] = risk_ind.get("price_confidence", "unknown")
        features["has_aggressive_discount"] = risk_ind.get("aggressive_discount", False)
        features["has_heavy_deviations"] = risk_ind.get("heavy_deviations", False)
        features["has_long_lead_time"] = risk_ind.get("long_lead_time", False)
        features["has_rare_commodity"] = risk_ind.get("rare_commodity", False)
        
        # Behavioral patterns
        patterns = signals.get("behavioral_patterns", {})
        features["supplier_on_time_rate"] = patterns.get("supplier_on_time_rate", 0)
        features["supplier_deviation_frequency"] = patterns.get("supplier_deviation_frequency", 0)
        features["item_variation_frequency"] = patterns.get("item_variation_frequency", 0)
        
        # Categorization
        categ = signals.get("categorization", {})
        features["commodity_category"] = categ.get("commodity_category")
        features["supplier_tier"] = categ.get("supplier_tier")
        features["spend_category"] = categ.get("spend_category")
        
        # Phase and criticality
        features["phase"] = signals.get("phase")
        features["criticality"] = signals.get("criticality")
        
        # Overall risk score (target variable for risk prediction)
        features["overall_risk_score"] = doc.get("overall_risk_score", 0)
        
        return features
    
    @staticmethod
    def extract_supplier_features(doc: Dict) -> Dict:
        """
        Extract supplier signal features
        
        Args:
            doc: KraftdDocument dictionary
            
        Returns:
            Dictionary of supplier features
        """
        features = {}
        
        supplier_signals = doc.get("supplier_signals", [])
        
        if supplier_signals:
            # Use first supplier (primary)
            supplier = supplier_signals[0]
            features["supplier_name"] = supplier.get("supplier_name", "unknown")
            features["supplier_risk_score"] = supplier.get("risk_score", 0)
            features["supplier_reliability_score"] = supplier.get("reliability_score", 0)
            features["supplier_deviation_count"] = supplier.get("deviation_count", 0)
            features["num_suppliers"] = len(supplier_signals)
        else:
            features["supplier_name"] = "unknown"
            features["supplier_risk_score"] = 0
            features["supplier_reliability_score"] = 0
            features["supplier_deviation_count"] = 0
            features["num_suppliers"] = 0
        
        return features
    
    @staticmethod
    def extract_quality_features(doc: Dict) -> Dict:
        """
        Extract data quality features
        
        Args:
            doc: KraftdDocument dictionary
            
        Returns:
            Dictionary of quality features
        """
        features = {}
        
        quality = doc.get("data_quality", {})
        features["completeness_percentage"] = quality.get("completeness_percentage", 0)
        features["accuracy_score"] = quality.get("accuracy_score", 0)
        features["num_warnings"] = len(quality.get("warnings", []))
        features["requires_manual_review"] = quality.get("requires_manual_review", False)
        
        extraction = doc.get("extraction_confidence", {})
        features["overall_confidence"] = extraction.get("overall_confidence", 0)
        features["num_missing_fields"] = len(extraction.get("missing_fields", []))
        
        return features
    
    def extract_all_features(self, doc: Dict) -> Dict:
        """
        Extract all features from a document
        
        Args:
            doc: KraftdDocument dictionary
            
        Returns:
            Dictionary of all extracted features
        """
        features = {}
        
        # Extract from different sections
        features.update(self.extract_document_features(doc))
        features.update(self.extract_commercial_features(doc))
        features.update(self.extract_risk_features(doc))
        features.update(self.extract_supplier_features(doc))
        features.update(self.extract_quality_features(doc))
        
        # Add document ID for tracking
        features["document_id"] = doc.get("document_id")
        features["status"] = doc.get("status")
        features["created_at"] = str(doc.get("created_at", ""))[:10]  # Date only
        
        return features


class DataPipelineProcessor:
    """Process extracted features for ML training"""
    
    def __init__(self):
        """Initialize data pipeline"""
        self.extractor = MetadataFeatureExtractor()
        self.scaler = None
        self.encoder = None
    
    def process_documents(self, documents: List[Dict]) -> pd.DataFrame:
        """
        Process list of documents into feature DataFrame
        
        Args:
            documents: List of KraftdDocument dictionaries
            
        Returns:
            Pandas DataFrame with extracted features
        """
        features_list = []
        
        for doc in documents:
            try:
                features = self.extractor.extract_all_features(doc)
                features_list.append(features)
            except Exception as e:
                logger.warning(f"Error processing document {doc.get('document_id')}: {e}")
                continue
        
        df = pd.DataFrame(features_list)
        
        # Handle missing values
        df = self._handle_missing_values(df)
        
        logger.info(f"Processed {len(df)} documents into feature matrix")
        return df
    
    @staticmethod
    def _handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values in feature matrix
        
        Args:
            df: Feature DataFrame
            
        Returns:
            DataFrame with missing values handled
        """
        # Numerical columns: fill with 0
        numerical_cols = df.select_dtypes(include=[np.number]).columns
        for col in numerical_cols:
            df[col] = df[col].fillna(0)
        
        # Categorical columns: fill with 'unknown'
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            df[col] = df[col].fillna('unknown')
        
        return df
    
    @staticmethod
    def get_feature_subset(
        df: pd.DataFrame, 
        feature_set: FeatureSet
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Get feature subset for specific ML task
        
        Args:
            df: Full feature DataFrame
            feature_set: Which features to use
            
        Returns:
            Tuple of (features DataFrame, feature column names)
        """
        if feature_set == FeatureSet.RISK_PREDICTION:
            features = [
                'document_type', 'num_line_items', 'total_value',
                'currency', 'has_vat', 'has_performance_guarantee',
                'supplier_risk_score', 'supplier_deviation_count',
                'validity_days', 'has_aggressive_discount', 'has_heavy_deviations',
                'has_long_lead_time', 'completeness_percentage', 'overall_confidence',
                'num_parties', 'num_special_conditions'
            ]
        
        elif feature_set == FeatureSet.PRICE_PREDICTION:
            features = [
                'document_type', 'num_line_items', 'total_quantity',
                'avg_unit_price', 'supplier_tier', 'commodity_category',
                'vat_rate', 'currency', 'supplier_on_time_rate',
                'completeness_percentage'
            ]
        
        elif feature_set == FeatureSet.SUPPLIER_RELIABILITY:
            features = [
                'supplier_deviation_count', 'supplier_on_time_rate',
                'supplier_risk_score', 'num_suppliers', 'days_since_issue',
                'total_value', 'num_line_items', 'completeness_percentage'
            ]
        
        elif feature_set == FeatureSet.DOCUMENT_CLASSIFICATION:
            features = [
                'num_line_items', 'total_value', 'has_deviations',
                'num_parties', 'has_performance_guarantee',
                'has_milestone_payment', 'num_special_conditions',
                'validity_days', 'completeness_percentage'
            ]
        
        else:
            features = df.columns.tolist()
        
        # Filter to available columns
        available_features = [f for f in features if f in df.columns]
        
        return df[available_features], available_features


# Example usage function
def example_data_pipeline():
    """
    Example: Load documents from Cosmos DB and process for ML
    """
    # In production, this would connect to Cosmos DB
    # For now, showing the structure
    
    processor = DataPipelineProcessor()
    
    # Mock data - in production: fetch from Cosmos DB
    sample_docs = [
        {
            "document_id": "doc-001",
            "metadata": {"document_type": "RFQ", "document_number": "RFQ-2024-001"},
            "dates": {"issue_date": "2024-01-01T00:00:00"},
            "parties": {"issuer": {}, "recipient": {}},
            "project_context": {"project_code": "P001", "discipline": "civil"},
            "line_items": [
                {"quantity": 100, "unit_price": 50, "total_price": 5000}
            ],
            "commercial_terms": {"currency": "USD", "tax_vat_mentioned": True},
            "signals": {
                "risk_indicators": {"validity_days": 30, "aggressive_discount": False},
                "behavioral_patterns": {"supplier_on_time_rate": 0.95}
            },
            "supplier_signals": [{"supplier_name": "Supplier A", "risk_score": 25}],
            "data_quality": {"completeness_percentage": 0.95},
            "extraction_confidence": {"overall_confidence": 0.92},
            "overall_risk_score": 25,
            "status": "approved"
        }
    ]
    
    # Process documents
    df = processor.process_documents(sample_docs)
    
    # Get risk prediction features
    risk_features, cols = processor.get_feature_subset(df, FeatureSet.RISK_PREDICTION)
    
    print(f"Processed {len(df)} documents")
    print(f"Features for risk prediction: {cols}")
    print(risk_features.head())
    
    return df


if __name__ == "__main__":
    example_data_pipeline()
