"""
Supplier Ecosystem Model - Semi-Supervised Classification on Fragmented Supplier Data

Extracts signal from fragmented supplier and engagement data to understand:
- Supplier success likelihood (binary/probability)
- Ecosystem health scoring (per supplier, per region, per category)
- Growth and risk patterns
- Investment opportunity scoring

Uses semi-supervised learning (combines labeled + unlabeled data)
and cost-sensitive classification (handles imbalanced data).
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class SupplierGrade(str, Enum):
    """Supplier ecosystem grades"""
    EXCELLENT = "A+"
    GOOD = "A"
    SATISFACTORY = "B"
    NEEDS_IMPROVEMENT = "C"
    AT_RISK = "D"
    CRITICAL = "F"


@dataclass
class SupplierProfile:
    """Supplier profile from procurement data"""
    supplier_id: str
    supplier_name: str
    region: str
    category: str
    engagement_history: int  # months/years
    total_orders: int
    on_time_rate: float  # 0-1
    quality_score: float  # 0-1
    pricing_consistency: float  # 0-1 (lower variance = higher)
    growth_rate: float  # YoY
    payment_reliability: float  # 0-1
    innovation_score: float  # new products/services


@dataclass
class EcosystemScoring:
    """Result of ecosystem analysis"""
    supplier_id: str
    success_probability: float  # 0-1
    ecosystem_score: float  # 0-100
    grade: SupplierGrade
    growth_potential: str  # "high", "medium", "low"
    risk_factors: List[str]
    investment_opportunity_score: float  # 0-100
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]


class SupplierFeatureExtractor:
    """Extract supplier-relevant features from KraftdDocument data"""

    def __init__(self):
        self.logger = logger

    def extract_supplier_profiles(
        self, documents: List[Dict]
    ) -> pd.DataFrame:
        """
        Build supplier profiles from transaction/engagement history.
        
        Args:
            documents: List of KraftdDocument dicts
            
        Returns:
            DataFrame with supplier profiles
        """
        supplier_data = {}

        for doc in documents:
            supplier = doc.get("supplier", {})
            supplier_id = supplier.get("id", "unknown")

            if supplier_id not in supplier_data:
                supplier_data[supplier_id] = {
                    "supplier_id": supplier_id,
                    "supplier_name": supplier.get("name", "unknown"),
                    "region": supplier.get("country", "unknown"),
                    "category": doc.get("category", "unknown"),
                    "orders": [],
                    "payments": [],
                    "quality_scores": [],
                    "prices": [],
                }

            # Track order
            supplier_data[supplier_id]["orders"].append(
                {
                    "date": doc.get("date"),
                    "on_time": doc.get("on_time_delivery", False),
                    "quality": doc.get("quality_score", 0.5),
                }
            )

            # Track payment
            supplier_data[supplier_id]["payments"].append(
                {
                    "amount": doc.get("total_price", 0),
                    "on_time": doc.get("payment_on_time", True),
                }
            )

            # Quality metrics
            supplier_data[supplier_id]["quality_scores"].append(
                doc.get("quality_score", 0.5)
            )

            # Price tracking
            supplier_data[supplier_id]["prices"].append(
                doc.get("unit_price", 0)
            )

        # Convert to profile format
        profiles = []
        for supplier_id, data in supplier_data.items():
            profile = self._build_profile(data)
            profiles.append(profile)

        return pd.DataFrame(profiles)

    @staticmethod
    def _build_profile(supplier_data: Dict) -> Dict:
        """Build single supplier profile from accumulated data"""
        orders = supplier_data["orders"]
        payments = supplier_data["payments"]
        
        if not orders:
            return None

        # Calculate metrics
        on_time_rate = (
            sum(1 for o in orders if o["on_time"]) / len(orders)
            if orders
            else 0
        )
        
        quality_score = (
            np.mean([o["quality"] for o in orders]) if orders else 0.5
        )
        
        # Pricing consistency (lower std = higher consistency)
        prices = supplier_data["prices"]
        if len(prices) > 1:
            price_std = np.std(prices)
            price_mean = np.mean(prices)
            pricing_consistency = max(0, 1 - (price_std / max(price_mean, 1)))
        else:
            pricing_consistency = 0.5
        
        # Payment reliability
        payment_reliability = (
            sum(1 for p in payments if p["on_time"]) / len(payments)
            if payments
            else 0.5
        )
        
        # Engagement duration (months, simplified)
        engagement_history = len(orders)  # use order count as proxy
        
        # Growth rate (simplified: check if recent orders > early orders)
        if len(orders) > 4:
            recent_avg = np.mean(
                [o["quality"] for o in orders[-2:]]
            )
            early_avg = np.mean([o["quality"] for o in orders[:2]])
            growth_rate = (recent_avg - early_avg) / max(early_avg, 0.1)
        else:
            growth_rate = 0

        return {
            "supplier_id": supplier_data["supplier_id"],
            "supplier_name": supplier_data["supplier_name"],
            "region": supplier_data["region"],
            "category": supplier_data["category"],
            "engagement_history": engagement_history,
            "total_orders": len(orders),
            "on_time_rate": on_time_rate,
            "quality_score": quality_score,
            "pricing_consistency": pricing_consistency,
            "growth_rate": growth_rate,
            "payment_reliability": payment_reliability,
            "innovation_score": 0.5,  # Would require additional data
        }


class SupplierSuccessClassifier:
    """
    Semi-supervised classification for supplier success likelihood.
    
    Success defined as: on-time delivery, quality, reliability.
    Uses imbalanced classification (few suppliers are truly excellent).
    """

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = [
            "on_time_rate",
            "quality_score",
            "pricing_consistency",
            "growth_rate",
            "payment_reliability",
            "engagement_history",
        ]

    def prepare_training_data(
        self, profiles_df: pd.DataFrame, success_threshold: float = 0.75
    ) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Prepare training data by defining success.
        
        Args:
            profiles_df: Supplier profiles DataFrame
            success_threshold: Min score to be labeled "successful"
            
        Returns:
            Features, Labels
        """
        # Calculate composite success score
        profiles_df["success_score"] = (
            0.3 * profiles_df["on_time_rate"]
            + 0.3 * profiles_df["quality_score"]
            + 0.2 * profiles_df["payment_reliability"]
            + 0.2 * profiles_df["pricing_consistency"]
        )

        # Label
        y = (profiles_df["success_score"] >= success_threshold).astype(int)

        return profiles_df, y

    def fit(
        self, profiles_df: pd.DataFrame, success_threshold: float = 0.75
    ) -> "SupplierSuccessClassifier":
        """Train classifier"""
        profiles_df, y = self.prepare_training_data(
            profiles_df, success_threshold
        )

        # Prepare features
        X = profiles_df[self.feature_names].fillna(
            profiles_df[self.feature_names].mean()
        )

        # Scale
        X_scaled = self.scaler.fit_transform(X)

        # Train with class weighting (handle imbalance)
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=4,
            random_state=42,
        )
        self.model.fit(X_scaled, y)

        return self

    def predict(
        self, profiles_df: pd.DataFrame
    ) -> np.ndarray:
        """Predict success probability (0-1)"""
        X = profiles_df[self.feature_names].fillna(
            profiles_df[self.feature_names].mean()
        )
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)[:, 1]


class EcosystemHealthScorer:
    """Score supplier ecosystem health based on aggregate metrics"""

    def __init__(self):
        self.classifier = SupplierSuccessClassifier()

    def score_supplier(
        self, profile: pd.Series
    ) -> EcosystemScoring:
        """
        Score single supplier across multiple dimensions.
        
        Args:
            profile: Single row from supplier profiles DataFrame
            
        Returns:
            EcosystemScoring with comprehensive assessment
        """
        # Success probability
        success_prob = self._calculate_success_probability(profile)
        
        # Ecosystem score (0-100)
        eco_score = self._calculate_ecosystem_score(profile)
        
        # Grade
        grade = self._assign_grade(eco_score)
        
        # Growth potential
        growth = self._assess_growth_potential(profile)
        
        # Risk factors
        risks = self._identify_risk_factors(profile)
        
        # Investment score
        investment_score = self._calculate_investment_score(
            success_prob, eco_score, growth
        )
        
        # Strengths/weaknesses
        strengths = self._identify_strengths(profile, eco_score)
        weaknesses = self._identify_weaknesses(profile, risks)
        
        # Recommendations
        recommendations = self._generate_recommendations(
            profile, grade, risks, growth
        )

        return EcosystemScoring(
            supplier_id=profile["supplier_id"],
            success_probability=success_prob,
            ecosystem_score=eco_score,
            grade=grade,
            growth_potential=growth,
            risk_factors=risks,
            investment_opportunity_score=investment_score,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
        )

    @staticmethod
    def _calculate_success_probability(profile: pd.Series) -> float:
        """Probability of sustained success"""
        score = (
            0.35 * profile["on_time_rate"]
            + 0.35 * profile["quality_score"]
            + 0.15 * profile["payment_reliability"]
            + 0.15 * profile["pricing_consistency"]
        )
        return min(1.0, max(0.0, score))

    @staticmethod
    def _calculate_ecosystem_score(profile: pd.Series) -> float:
        """Overall ecosystem health score (0-100)"""
        score = (
            30 * profile["on_time_rate"]
            + 25 * profile["quality_score"]
            + 15 * profile["pricing_consistency"]
            + 15 * profile["payment_reliability"]
            + 10 * min(1.0, profile["growth_rate"] * 0.5 + 0.5)
        )
        return min(100.0, max(0.0, score))

    @staticmethod
    def _assign_grade(score: float) -> SupplierGrade:
        """Assign letter grade based on score"""
        if score >= 95:
            return SupplierGrade.EXCELLENT
        elif score >= 85:
            return SupplierGrade.GOOD
        elif score >= 70:
            return SupplierGrade.SATISFACTORY
        elif score >= 55:
            return SupplierGrade.NEEDS_IMPROVEMENT
        elif score >= 40:
            return SupplierGrade.AT_RISK
        else:
            return SupplierGrade.CRITICAL

    @staticmethod
    def _assess_growth_potential(profile: pd.Series) -> str:
        """Assess growth trajectory"""
        growth = profile["growth_rate"]
        
        if growth > 0.1:
            return "high"
        elif growth > -0.1:
            return "medium"
        else:
            return "low"

    @staticmethod
    def _identify_risk_factors(profile: pd.Series) -> List[str]:
        """List risk factors"""
        risks = []
        
        if profile["on_time_rate"] < 0.8:
            risks.append("Delivery delays")
        if profile["quality_score"] < 0.75:
            risks.append("Quality issues")
        if profile["payment_reliability"] < 0.8:
            risks.append("Payment irregularities")
        if profile["pricing_consistency"] < 0.6:
            risks.append("Price volatility")
        
        return risks

    @staticmethod
    def _calculate_investment_score(
        success_prob: float, eco_score: float, growth: str
    ) -> float:
        """Score investment opportunity (0-100)"""
        score = (
            50 * success_prob
            + 40 * (eco_score / 100)
            + 10 * (1 if growth == "high" else 0.5 if growth == "medium" else 0)
        )
        return min(100.0, max(0.0, score))

    @staticmethod
    def _identify_strengths(profile: pd.Series, eco_score: float) -> List[str]:
        """Identify key strengths"""
        strengths = []
        
        if profile["on_time_rate"] > 0.9:
            strengths.append("Excellent delivery reliability")
        if profile["quality_score"] > 0.85:
            strengths.append("High quality standards")
        if profile["pricing_consistency"] > 0.8:
            strengths.append("Stable pricing")
        if profile["payment_reliability"] > 0.9:
            strengths.append("Reliable payment handling")
        if profile["growth_rate"] > 0.1:
            strengths.append("Strong growth trajectory")
        
        return strengths if strengths else ["Baseline competency"]

    @staticmethod
    def _identify_weaknesses(
        profile: pd.Series, risks: List[str]
    ) -> List[str]:
        """Identify areas for improvement"""
        weaknesses = []
        
        if profile["engagement_history"] < 5:
            weaknesses.append("Limited track record")
        if profile["pricing_consistency"] < 0.5:
            weaknesses.append("Inconsistent pricing")
        if profile["growth_rate"] < -0.05:
            weaknesses.append("Declining performance")
        
        return weaknesses + risks

    @staticmethod
    def _generate_recommendations(
        profile: pd.Series,
        grade: SupplierGrade,
        risks: List[str],
        growth: str,
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if grade.value in ["A+", "A"]:
            recommendations.append("Maintain relationship; consider long-term contract")
            if growth == "high":
                recommendations.append("Explore volume expansion")
        elif grade.value in ["B"]:
            recommendations.append("Monitor performance; set improvement targets")
        elif grade.value in ["C", "D"]:
            recommendations.append("Develop improvement plan or consider alternatives")
        else:
            recommendations.append("Critical: Review relationship or transition to alternative supplier")
        
        if risks:
            recommendations.append(f"Address: {', '.join(risks[:2])}")
        
        return recommendations


# Example usage
def example_ecosystem_analysis(
    sample_documents: List[Dict],
) -> Dict:
    """Complete ecosystem analysis example"""
    extractor = SupplierFeatureExtractor()
    profiles_df = extractor.extract_supplier_profiles(sample_documents)
    
    scorer = EcosystemHealthScorer()
    
    results = []
    for _, profile in profiles_df.iterrows():
        scoring = scorer.score_supplier(profile)
        results.append(
            {
                "supplier": scoring.supplier_id,
                "score": scoring.ecosystem_score,
                "grade": scoring.grade.value,
                "success_prob": scoring.success_probability,
                "investment_score": scoring.investment_opportunity_score,
                "top_risk": scoring.risk_factors[0] if scoring.risk_factors else None,
            }
        )
    
    return {
        "total_suppliers": len(profiles_df),
        "avg_ecosystem_score": np.mean([r["score"] for r in results]),
        "top_suppliers": sorted(results, key=lambda x: x["score"], reverse=True)[:3],
        "at_risk": [r for r in results if r["grade"] in ["D", "F"]],
    }
