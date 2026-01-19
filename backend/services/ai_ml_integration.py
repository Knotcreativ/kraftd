"""
AI-ML Integration Layer - Kraft Agent & ML Models Collaboration

gpt-4o (GitHub Models) leverages ML model predictions to enhance supplier intelligence.
Creates a feedback loop: AI → ML → Enhanced Analysis → Signals
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MLInsights:
    """ML model predictions aggregated for AI use"""
    pricing_fairness_score: float  # 0-100 from pricing index
    ecosystem_health_score: float  # 0-100 from supplier ecosystem
    supply_chain_risk: float  # 0-100 from mobility clustering
    overall_risk_score: float  # 0-100 aggregated
    pricing_trend: str  # "increasing", "stable", "decreasing"
    supplier_success_probability: float  # 0-1
    anomalies_detected: List[str]
    recommendations: List[str]


class AIMLIntegration:
    """Bridge between gpt-4o and ML models"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def enrich_ai_analysis(
        self,
        ai_response: Dict[str, Any],
        ml_insights: MLInsights
    ) -> Dict[str, Any]:
        """
        Enrich gpt-4o's AI analysis with ML model predictions
        
        Args:
            ai_response: gpt-4o's analysis output
            ml_insights: ML model predictions
            
        Returns:
            Combined AI + ML enhanced analysis
        """
        
        # Add ML confidence indicators to AI insights
        enhanced = {
            **ai_response,
            "ml_confidence": self._calculate_ml_confidence(ml_insights),
            "risk_factors": self._merge_ai_ml_risks(
                ai_response.get("risk_factors", []),
                ml_insights
            ),
            "supplier_viability": self._assess_viability(
                ai_response,
                ml_insights
            ),
            "data_driven_recommendations": self._combine_recommendations(
                ai_response.get("recommendations", []),
                ml_insights.recommendations
            ),
            "ml_validation": {
                "pricing_analysis_validated": ml_insights.pricing_fairness_score > 50,
                "supplier_health_confirmed": ml_insights.ecosystem_health_score > 60,
                "supply_chain_safe": ml_insights.supply_chain_risk < 40,
                "ml_risk_score": ml_insights.overall_risk_score
            }
        }
        
        return enhanced
    
    def _calculate_ml_confidence(self, ml_insights: MLInsights) -> float:
        """Calculate confidence in ML predictions (0-100)"""
        scores = [
            ml_insights.pricing_fairness_score,
            ml_insights.ecosystem_health_score,
            100 - ml_insights.supply_chain_risk,  # Invert risk to confidence
        ]
        return sum(scores) / len(scores)
    
    def _merge_ai_ml_risks(
        self,
        ai_risks: List[str],
        ml_insights: MLInsights
    ) -> List[Dict[str, Any]]:
        """
        Merge AI-detected risks with ML-detected anomalies
        """
        merged = []
        
        # Add AI risks with ML weighting
        for risk in ai_risks:
            merged.append({
                "source": "ai_analysis",
                "risk": risk,
                "ml_confirmation": any(
                    anom.lower() in risk.lower()
                    for anom in ml_insights.anomalies_detected
                )
            })
        
        # Add pure ML anomalies
        for anomaly in ml_insights.anomalies_detected:
            if not any(anom.lower() == anomaly.lower() for anom in ai_risks):
                merged.append({
                    "source": "ml_models",
                    "risk": anomaly,
                    "ml_confirmation": True
                })
        
        return merged
    
    def _assess_viability(
        self,
        ai_response: Dict[str, Any],
        ml_insights: MLInsights
    ) -> Dict[str, Any]:
        """
        Combined AI + ML supplier viability assessment
        """
        ai_viable = ai_response.get("supplier_recommendation") in [
            "positive", "neutral", "proceed_with_caution"
        ]
        ml_viable = (
            ml_insights.ecosystem_health_score > 50 and
            ml_insights.supply_chain_risk < 50 and
            ml_insights.supplier_success_probability > 0.4
        )
        
        consensus = ai_viable and ml_viable
        
        return {
            "ai_assessment": "viable" if ai_viable else "risky",
            "ml_assessment": "viable" if ml_viable else "risky",
            "consensus": "RECOMMENDED" if consensus else "CAUTION",
            "confidence": self._calculate_ml_confidence(ml_insights),
            "reasoning": self._generate_viability_reasoning(
                ai_viable, ml_viable, ml_insights
            )
        }
    
    def _generate_viability_reasoning(
        self,
        ai_viable: bool,
        ml_viable: bool,
        ml_insights: MLInsights
    ) -> str:
        """Generate explanation for viability assessment"""
        reasons = []
        
        if ml_insights.ecosystem_health_score > 75:
            reasons.append("Strong supplier ecosystem health")
        elif ml_insights.ecosystem_health_score < 40:
            reasons.append("Weak supplier ecosystem health")
        
        if ml_insights.supply_chain_risk < 30:
            reasons.append("Low supply chain risk detected")
        elif ml_insights.supply_chain_risk > 70:
            reasons.append("High supply chain risk detected")
        
        if ml_insights.supplier_success_probability > 0.7:
            reasons.append("High success probability from historical data")
        
        if ml_insights.pricing_fairness_score > 70:
            reasons.append("Fair pricing compared to market")
        elif ml_insights.pricing_fairness_score < 40:
            reasons.append("Pricing concerns vs market baseline")
        
        return " • ".join(reasons) if reasons else "Mixed signals"
    
    def _combine_recommendations(
        self,
        ai_recommendations: List[str],
        ml_recommendations: List[str]
    ) -> List[Dict[str, Any]]:
        """Combine AI and ML recommendations"""
        combined = []
        
        # Add AI recommendations
        for rec in ai_recommendations:
            combined.append({
                "source": "ai_analysis",
                "recommendation": rec,
                "ml_backed": False
            })
        
        # Add ML recommendations with cross-validation
        for rec in ml_recommendations:
            if rec not in ai_recommendations:
                combined.append({
                    "source": "ml_models",
                    "recommendation": rec,
                    "ml_backed": True
                })
            else:
                # Mark as consensus if both suggest same thing
                for item in combined:
                    if item["recommendation"] == rec:
                        item["ml_backed"] = True
                        item["consensus"] = True
        
        return combined
    
    async def request_ml_scores(
        self,
        supplier_data: Dict[str, Any],
        procurement_metadata: Dict[str, Any]
    ) -> MLInsights:
        """
        Request ML model predictions for a supplier
        
        This is called by kraft_agent to get ML predictions
        while performing AI analysis
        """
        from ml.supplier_ecosystem import (
            SupplierFeatureExtractor,
            EcosystemHealthScorer
        )
        from ml.pricing_index import RobustPricingIndex
        from ml.mobility_clustering import MobilityAnomalyDetector
        
        try:
            # Extract features and run models in parallel
            supplier_success_prob = await self._get_supplier_success_prediction(
                supplier_data
            )
            
            ecosystem_health = await self._get_ecosystem_health(
                supplier_data
            )
            
            pricing_score = await self._get_pricing_fairness(
                procurement_metadata
            )
            
            supply_chain_risk = await self._get_supply_chain_risk(
                procurement_metadata
            )
            
            anomalies = await self._detect_anomalies(
                supplier_data, procurement_metadata
            )
            
            recommendations = await self._generate_ml_recommendations(
                supplier_success_prob,
                ecosystem_health,
                pricing_score,
                supply_chain_risk,
                anomalies
            )
            
            return MLInsights(
                pricing_fairness_score=pricing_score,
                ecosystem_health_score=ecosystem_health,
                supply_chain_risk=supply_chain_risk,
                overall_risk_score=(
                    100 - (
                        (ecosystem_health + pricing_score) / 2 -
                        supply_chain_risk / 2
                    )
                ),
                pricing_trend=self._detect_pricing_trend(procurement_metadata),
                supplier_success_probability=supplier_success_prob,
                anomalies_detected=anomalies,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Error getting ML scores: {e}")
            # Return default/safe insights on error
            return MLInsights(
                pricing_fairness_score=50,
                ecosystem_health_score=50,
                supply_chain_risk=50,
                overall_risk_score=50,
                pricing_trend="unknown",
                supplier_success_probability=0.5,
                anomalies_detected=[],
                recommendations=["Insufficient data for ML analysis"]
            )
    
    async def _get_supplier_success_prediction(
        self, supplier_data: Dict[str, Any]
    ) -> float:
        """Get supplier success probability from ecosystem model"""
        try:
            from ml.supplier_ecosystem import EcosystemHealthScorer
            scorer = EcosystemHealthScorer()
            probability = scorer.predict_success(supplier_data)
            return probability
        except:
            return 0.5
    
    async def _get_ecosystem_health(
        self, supplier_data: Dict[str, Any]
    ) -> float:
        """Get ecosystem health score from ecosystem model"""
        try:
            from ml.supplier_ecosystem import EcosystemHealthScorer
            scorer = EcosystemHealthScorer()
            health = scorer.score_ecosystem_health(supplier_data)
            return health
        except:
            return 50
    
    async def _get_pricing_fairness(
        self, procurement_metadata: Dict[str, Any]
    ) -> float:
        """Get pricing fairness score from pricing index"""
        try:
            from ml.pricing_index import RobustPricingIndex
            index = RobustPricingIndex()
            fairness = index.assess_pricing_fairness(procurement_metadata)
            return fairness
        except:
            return 50
    
    async def _get_supply_chain_risk(
        self, procurement_metadata: Dict[str, Any]
    ) -> float:
        """Get supply chain risk from mobility clustering"""
        try:
            from ml.mobility_clustering import MobilityAnomalyDetector
            detector = MobilityAnomalyDetector()
            risk = detector.assess_supply_chain_risk(procurement_metadata)
            return risk
        except:
            return 50
    
    async def _detect_anomalies(
        self, supplier_data: Dict[str, Any],
        procurement_metadata: Dict[str, Any]
    ) -> List[str]:
        """Detect anomalies across all ML models"""
        anomalies = []
        try:
            from ml.mobility_clustering import MobilityAnomalyDetector
            detector = MobilityAnomalyDetector()
            detected = detector.detect_anomalies(procurement_metadata)
            anomalies.extend(detected)
        except:
            pass
        return anomalies
    
    async def _generate_ml_recommendations(
        self,
        success_prob: float,
        health: float,
        pricing: float,
        risk: float,
        anomalies: List[str]
    ) -> List[str]:
        """Generate recommendations based on ML scores"""
        recommendations = []
        
        if success_prob < 0.4:
            recommendations.append("Low historical success rate - verify supplier track record")
        elif success_prob > 0.8:
            recommendations.append("Strong historical success pattern - good supplier choice")
        
        if health < 40:
            recommendations.append("Monitor supplier ecosystem health closely")
        
        if pricing < 40:
            recommendations.append("Pricing significantly above market - negotiate better rates")
        elif pricing > 80:
            recommendations.append("Competitive pricing detected - favorable terms")
        
        if risk > 70:
            recommendations.append("High supply chain risk - implement mitigation strategies")
        
        if anomalies:
            recommendations.append(f"Anomalies detected: {', '.join(anomalies[:2])}")
        
        return recommendations if recommendations else [
            "ML models indicate normal procurement profile"
        ]
    
    def _detect_pricing_trend(
        self, procurement_metadata: Dict[str, Any]
    ) -> str:
        """Detect pricing trend from historical data"""
        try:
            prices = procurement_metadata.get("historical_prices", [])
            if len(prices) < 2:
                return "insufficient_data"
            
            avg_recent = sum(prices[-2:]) / 2
            avg_historical = sum(prices[:-2]) / len(prices[:-2]) if len(prices) > 2 else prices[0]
            
            if avg_recent > avg_historical * 1.1:
                return "increasing"
            elif avg_recent < avg_historical * 0.9:
                return "decreasing"
            else:
                return "stable"
        except:
            return "unknown"


# Global integration instance
ai_ml_integration = AIMLIntegration()
