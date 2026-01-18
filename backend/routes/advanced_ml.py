"""
Advanced ML Predictions API - Fragmented Data Models

REST endpoints for:
1. Mobility clustering (supply chain route patterns)
2. Pricing index (fair pricing from fragmented data)
3. Supplier ecosystem scoring (success prediction + health)

All models operate on KraftdDocument procurement metadata.
"""

from fastapi import APIRouter, HTTPException, Depends, Body, Query, Header
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime
import jwt

from services.auth_service import AuthService
from ml.mobility_clustering import (
    MobilityFeatureExtractor,
    MobilityClusteringModel,
    MobilityAnomalyDetector,
)
from ml.pricing_index import (
    RobustPricingIndex,
    CompositeIndexBuilder,
)
from ml.supplier_ecosystem import (
    SupplierFeatureExtractor,
    EcosystemHealthScorer,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/ml/advanced", tags=["advanced-ml"])


# ============================================================================
# Authentication
# ============================================================================


async def verify_token(authorization: Optional[str] = Header(None)) -> dict:
    """
    Verify Bearer token from Authorization header.
    Returns user info or raises 401 Unauthorized.
    Uses the same AuthService as the main auth routes.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        scheme, token = authorization.split(" ")
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization scheme")
        
        # Use AuthService to verify token
        auth_service = AuthService()
        payload = auth_service.verify_token(token)
        return {"user_id": payload.get("sub"), "email": payload.get("email")}
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


# ============================================================================
# Request/Response Models
# ============================================================================


class MobilityAnalysisRequest(BaseModel):
    """Request for mobility/routing analysis"""
    documents: List[Dict] = Field(..., description="KraftdDocument list")
    eps: float = Field(default=0.5, description="DBSCAN clustering distance")
    min_samples: int = Field(default=3, description="Min cluster size")


class MobilityAnalysisResponse(BaseModel):
    """Mobility analysis results"""
    timestamp: str
    routes_count: int
    clusters: Dict[str, Any]
    anomalies_detected: int
    anomaly_details: List[Dict]
    recommendations: List[str]


class PricingIndexRequest(BaseModel):
    """Request for pricing index"""
    documents: List[Dict] = Field(..., description="KraftdDocument list")
    commodity_category: str = Field(..., description="Category to index")
    region: Optional[str] = Field(default=None, description="Optional region filter")
    include_trend: bool = Field(default=True, description="Include trend analysis")


class PriceIndexData(BaseModel):
    """Single price index"""
    category: str
    region: Optional[str]
    index_value: float
    fair_price_range: tuple
    trend_direction: str
    volatility: float
    anomalies: List[Dict]


class PricingIndexResponse(BaseModel):
    """Pricing index results"""
    timestamp: str
    indices: List[PriceIndexData]
    market_insights: Dict[str, str]


class SupplierEcosystemRequest(BaseModel):
    """Request for ecosystem analysis"""
    documents: List[Dict] = Field(..., description="KraftdDocument list")
    include_predictions: bool = Field(default=True, description="Include success predictions")


class SupplierScore(BaseModel):
    """Individual supplier ecosystem score"""
    supplier_id: str
    supplier_name: str
    success_probability: float
    ecosystem_score: float
    grade: str
    growth_potential: str
    investment_opportunity_score: float
    risk_factors: List[str]
    top_strength: str
    recommendation: str


class SupplierEcosystemResponse(BaseModel):
    """Ecosystem analysis results"""
    timestamp: str
    total_suppliers: int
    average_score: float
    suppliers: List[SupplierScore]
    ecosystem_summary: Dict[str, Any]


# ============================================================================
# Mobility Endpoints
# ============================================================================


@router.post("/mobility/analyze")
async def analyze_mobility(
    request: MobilityAnalysisRequest = Body(...),
    current_user: dict = Depends(verify_token),
) -> MobilityAnalysisResponse:
    """
    Analyze supply chain mobility patterns.
    
    Clusters supplier routes by efficiency, detects bottlenecks and 
    opportunities in delivery networks.
    
    **Response includes:**
    - Route clusters with efficiency scores
    - Anomalies (congestion, delays, under-served corridors)
    - Recommendations for route optimization
    """
    try:
        logger.info(f"Mobility analysis requested for {len(request.documents)} documents")
        
        # Extract routes
        extractor = MobilityFeatureExtractor()
        routes_df = extractor.extract_routes_from_documents(request.documents)
        
        if len(routes_df) == 0:
            raise HTTPException(
                status_code=400,
                detail="No valid route data extracted from documents"
            )
        
        # Cluster
        clustering = MobilityClusteringModel(
            eps=request.eps,
            min_samples=request.min_samples
        )
        clustering.fit(routes_df)
        clusters = clustering.predict_clusters(routes_df)
        
        # Detect anomalies
        anomaly_detector = MobilityAnomalyDetector()
        anomaly_detector.fit(routes_df)
        _, anomalies = anomaly_detector.predict(routes_df)
        
        # Format response
        cluster_dict = {}
        for cid, cluster in clusters.items():
            if cid != -1:  # Exclude noise points
                cluster_dict[str(cid)] = {
                    "size": cluster.size,
                    "efficiency_score": cluster.efficiency_score,
                    "recommendation": cluster.recommendation,
                    "key_corridors": cluster.characteristics.get("key_corridors", []),
                }
        
        # Generate recommendations
        recommendations = [
            cluster.recommendation
            for cluster in clusters.values()
            if cluster.cluster_id != -1
        ]
        
        return MobilityAnalysisResponse(
            timestamp=datetime.now().isoformat(),
            routes_count=len(routes_df),
            clusters=cluster_dict,
            anomalies_detected=len(anomalies),
            anomaly_details=anomalies[:10],
            recommendations=recommendations,
        )
    
    except Exception as e:
        logger.error(f"Mobility analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mobility/corridors")
async def identify_corridors(
    request: MobilityAnalysisRequest = Body(...),
    current_user: dict = Depends(verify_token),
) -> Dict:
    """
    Identify emerging and under-served mobility corridors.
    
    Analyzes route frequency and efficiency to suggest:
    - High-demand corridors (capacity planning)
    - Under-served routes (growth opportunity)
    - Inefficient corridors (optimization need)
    """
    try:
        extractor = MobilityFeatureExtractor()
        routes_df = extractor.extract_routes_from_documents(request.documents)
        
        # Find corridors by frequency
        corridor_freq = (
            routes_df["supplier_location"]
            + " → "
            + routes_df["delivery_location"]
        ).value_counts()
        
        # Categorize
        results = {
            "high_demand": corridor_freq.head(5).to_dict(),
            "underserved": corridor_freq[corridor_freq < 3].head(5).to_dict(),
            "avg_lead_time": routes_df.groupby(
                "supplier_location"
            )["lead_time_days"].mean().to_dict(),
        }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "corridors": results,
        }
    
    except Exception as e:
        logger.error(f"Corridor analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Pricing Index Endpoints
# ============================================================================


@router.post("/pricing/index")
async def calculate_pricing_index(
    request: PricingIndexRequest = Body(...),
    current_user: dict = Depends(verify_token),
) -> PricingIndexResponse:
    """
    Calculate pricing index from procurement data.
    
    Builds robust index handling:
    - Multi-currency normalization
    - Incomplete price data
    - Regional variations
    - Outlier detection
    
    **Returns:**
    - Index value (100 = baseline)
    - Fair price range
    - Trend (up/down/stable)
    - Market anomalies
    """
    try:
        logger.info(f"Pricing index requested for {request.commodity_category}")
        
        pricing_index = RobustPricingIndex()
        index_result = pricing_index.build_index(
            request.documents,
            request.commodity_category,
            request.region,
        )
        
        # Market insights
        insights = {
            "index_interpretation": (
                f"Index at {index_result.index_value:.1f} indicates "
                f"prices are {('up' if index_result.index_value > 105 else 'down' if index_result.index_value < 95 else 'stable')} "
                f"from baseline"
            ),
            "volatility_assessment": (
                "High volatility" if index_result.volatility > 0.3
                else "Moderate" if index_result.volatility > 0.15
                else "Low volatility"
            ),
            "fair_price_recommendation": (
                f"Target range: ${index_result.fair_price_range[0]:.2f} - "
                f"${index_result.fair_price_range[1]:.2f}"
            ),
        }
        
        return PricingIndexResponse(
            timestamp=datetime.now().isoformat(),
            indices=[
                PriceIndexData(
                    category=index_result.category,
                    region=index_result.region,
                    index_value=index_result.index_value,
                    fair_price_range=index_result.fair_price_range,
                    trend_direction=index_result.trend_direction,
                    volatility=index_result.volatility,
                    anomalies=index_result.anomalies[:5],
                )
            ],
            market_insights=insights,
        )
    
    except Exception as e:
        logger.error(f"Pricing index error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pricing/composite")
async def composite_pricing_index(
    request: PricingIndexRequest = Body(...),
    categories: List[str] = Query(
        ["electronics", "materials", "components"],
        description="Categories to include"
    ),
    current_user: dict = Depends(verify_token),
) -> Dict:
    """
    Build composite pricing index across multiple categories.
    
    Aggregates indices for benchmarking across product lines.
    """
    try:
        builder = CompositeIndexBuilder()
        indices = builder.build_composite_index(
            request.documents,
            categories,
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "composite_index": indices,
            "summary": {
                "average_index": sum(indices.values()) / len(indices),
                "highest": max(indices, key=indices.get),
                "lowest": min(indices, key=indices.get),
            },
        }
    
    except Exception as e:
        logger.error(f"Composite index error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Supplier Ecosystem Endpoints
# ============================================================================


@router.post("/suppliers/ecosystem")
async def analyze_supplier_ecosystem(
    request: SupplierEcosystemRequest = Body(...),
    current_user: dict = Depends(verify_token),
) -> SupplierEcosystemResponse:
    """
    Analyze supplier ecosystem health and success potential.
    
    Scores suppliers on:
    - Success probability
    - Ecosystem health (0-100)
    - Growth trajectory
    - Risk factors
    - Investment opportunity
    
    **Returns:**
    - Individual supplier scores with grades (A+ to F)
    - Strengths and weaknesses
    - Actionable recommendations
    """
    try:
        logger.info(f"Ecosystem analysis for {len(request.documents)} documents")
        
        extractor = SupplierFeatureExtractor()
        profiles_df = extractor.extract_supplier_profiles(request.documents)
        
        if len(profiles_df) == 0:
            raise HTTPException(
                status_code=400,
                detail="No valid supplier data extracted"
            )
        
        scorer = EcosystemHealthScorer()
        
        supplier_scores = []
        total_score = 0
        
        for _, profile in profiles_df.iterrows():
            scoring = scorer.score_supplier(profile)
            
            supplier_scores.append(
                SupplierScore(
                    supplier_id=scoring.supplier_id,
                    supplier_name=profile.get("supplier_name", "Unknown"),
                    success_probability=scoring.success_probability,
                    ecosystem_score=scoring.ecosystem_score,
                    grade=scoring.grade.value,
                    growth_potential=scoring.growth_potential,
                    investment_opportunity_score=scoring.investment_opportunity_score,
                    risk_factors=scoring.risk_factors,
                    top_strength=scoring.strengths[0] if scoring.strengths else "N/A",
                    recommendation=scoring.recommendations[0] if scoring.recommendations else "Monitor",
                )
            )
            
            total_score += scoring.ecosystem_score
        
        # Ecosystem summary
        grades = [s.grade for s in supplier_scores]
        summary = {
            "excellent_count": grades.count("A+"),
            "good_count": grades.count("A"),
            "satisfactory_count": grades.count("B"),
            "at_risk_count": grades.count("D") + grades.count("F"),
            "ecosystem_health": "strong" if total_score / len(supplier_scores) > 80 else "needs_improvement",
        }
        
        return SupplierEcosystemResponse(
            timestamp=datetime.now().isoformat(),
            total_suppliers=len(profiles_df),
            average_score=total_score / len(supplier_scores),
            suppliers=supplier_scores,
            ecosystem_summary=summary,
        )
    
    except Exception as e:
        logger.error(f"Ecosystem analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suppliers/investment-opportunities")
async def investment_opportunities(
    request: SupplierEcosystemRequest = Body(...),
    min_score: float = Query(70, description="Minimum investment score"),
    current_user: dict = Depends(verify_token),
) -> Dict:
    """
    Identify high-potential suppliers for investment/expansion.
    
    Filters for suppliers with:
    - High success probability
    - Strong growth trajectory
    - Acceptable risk profile
    """
    try:
        extractor = SupplierFeatureExtractor()
        profiles_df = extractor.extract_supplier_profiles(request.documents)
        
        scorer = EcosystemHealthScorer()
        
        opportunities = []
        for _, profile in profiles_df.iterrows():
            scoring = scorer.score_supplier(profile)
            
            if scoring.investment_opportunity_score >= min_score:
                opportunities.append({
                    "supplier": scoring.supplier_id,
                    "investment_score": scoring.investment_opportunity_score,
                    "success_prob": scoring.success_probability,
                    "growth": scoring.growth_potential,
                    "rationale": scoring.recommendations[0],
                })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "opportunities_found": len(opportunities),
            "investment_opportunities": sorted(
                opportunities,
                key=lambda x: x["investment_score"],
                reverse=True
            )[:10],
        }
    
    except Exception as e:
        logger.error(f"Investment opportunities error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
