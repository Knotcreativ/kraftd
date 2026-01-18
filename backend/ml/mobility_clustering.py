"""
Mobility Solutions Model - Unsupervised Clustering on Fragmented Procurement Data

Surfaces patterns and opportunities in mobility (movement of people/goods/services)
from messy, partial, cross-source data (KraftdDocument uploads).

Models supply chain movement patterns:
- Supplier locations and distribution
- Route efficiency and lead times
- Delivery mode patterns (air, sea, land, mixed)
- Peak vs latent demand corridors
- System inefficiencies and gaps

Uses DBSCAN clustering (robust to fragmented data) + anomaly detection.
"""

import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class MobilityRoute:
    """Represents a single route from procurement data"""
    supplier_id: str
    supplier_location: str
    delivery_location: str
    transport_mode: str  # air, sea, land, mixed
    lead_time_days: int
    distance_km: Optional[float]
    frequency: int  # number of times this route occurred
    reliability_score: float  # 0-1
    last_updated: str


@dataclass
class MobilityCluster:
    """Result of clustering analysis"""
    cluster_id: int
    routes: List[MobilityRoute]
    size: int
    characteristics: Dict[str, Any]
    efficiency_score: float
    recommendation: str


class MobilityFeatureExtractor:
    """Extract mobility-relevant features from fragmented KraftdDocument data"""

    def __init__(self):
        self.logger = logger

    def extract_routes_from_documents(self, documents: List[Dict]) -> pd.DataFrame:
        """
        Extract route information from KraftdDocument list.
        
        Handles fragmented data gracefully (missing fields filled with defaults).
        
        Args:
            documents: List of KraftdDocument dictionaries
            
        Returns:
            DataFrame with columns:
            - supplier_id, supplier_name, supplier_location
            - delivery_location
            - transport_mode
            - lead_time_days
            - distance_km
            - frequency
            - reliability_score
        """
        routes = []

        for doc in documents:
            try:
                supplier = doc.get("supplier", {})
                delivery = doc.get("delivery", {})
                
                # Handle fragmented supplier location
                supplier_location = (
                    supplier.get("location")
                    or supplier.get("country")
                    or "unknown"
                )
                
                # Handle fragmented delivery location
                delivery_location = (
                    delivery.get("location")
                    or delivery.get("destination")
                    or "unknown"
                )
                
                # Lead time handling (fragmented: days vs weeks vs months)
                lead_time = self._parse_lead_time(
                    doc.get("lead_time_days")
                    or doc.get("lead_time_weeks", 0) * 7
                    or 0
                )
                
                # Transport mode (may be missing, infer from document type)
                transport_mode = self._infer_transport_mode(
                    doc.get("transport_mode"),
                    supplier_location,
                    delivery_location,
                )
                
                # Distance (optional, calculate if coordinates available)
                distance = self._calculate_distance(
                    doc.get("supplier_coordinates"),
                    doc.get("delivery_coordinates"),
                )
                
                # Frequency (count similar routes)
                frequency = doc.get("order_count", 1)
                
                # Reliability (infer from on-time delivery rate)
                reliability = self._calculate_reliability(doc)

                routes.append({
                    "supplier_id": supplier.get("id", "unknown"),
                    "supplier_name": supplier.get("name", "unknown"),
                    "supplier_location": supplier_location,
                    "delivery_location": delivery_location,
                    "transport_mode": transport_mode,
                    "lead_time_days": lead_time,
                    "distance_km": distance,
                    "frequency": frequency,
                    "reliability_score": reliability,
                    "document_id": doc.get("id"),
                })
            except Exception as e:
                self.logger.warning(f"Error extracting route from doc: {e}")
                continue

        return pd.DataFrame(routes)

    @staticmethod
    def _parse_lead_time(lead_time_value: Any) -> int:
        """Handle fragmented lead time data"""
        if isinstance(lead_time_value, int):
            return max(1, lead_time_value)
        elif isinstance(lead_time_value, str):
            try:
                return max(1, int(lead_time_value.split()[0]))
            except:
                return 14  # default
        return 14

    @staticmethod
    def _infer_transport_mode(mode: Optional[str], origin: str, dest: str) -> str:
        """Infer transport mode from available data"""
        if mode:
            return mode.lower()
        
        # Heuristic: if international, likely air or sea
        if origin != dest and origin != "unknown":
            return "air"  # default international
        return "land"

    @staticmethod
    def _calculate_distance(origin_coords: Any, dest_coords: Any) -> Optional[float]:
        """Calculate distance from coordinates if available"""
        if not origin_coords or not dest_coords:
            return None
        
        try:
            # Haversine formula (simple approximation)
            import math
            lat1, lon1 = origin_coords
            lat2, lon2 = dest_coords
            
            R = 6371  # Earth radius in km
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
                math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            return R * c
        except:
            return None

    @staticmethod
    def _calculate_reliability(doc: Dict) -> float:
        """Calculate reliability from on-time delivery rate"""
        on_time = doc.get("on_time_deliveries", 0)
        total = doc.get("total_deliveries", 1)
        
        if total == 0:
            return 0.5  # unknown default
        
        return min(1.0, on_time / total)


class MobilityClusteringModel:
    """
    DBSCAN-based clustering for supply chain routes.
    
    Robust to fragmented data (doesn't require complete datasets).
    Discovers natural groupings in mobility patterns.
    """

    def __init__(self, eps: float = 0.5, min_samples: int = 3):
        """
        Args:
            eps: DBSCAN neighborhood distance (scale-dependent)
            min_samples: Minimum points to form a cluster
        """
        self.eps = eps
        self.min_samples = min_samples
        self.dbscan = None
        self.scaler = StandardScaler()
        self.feature_names = None
        self.clusters = {}
        self.anomalies = []

    def fit(self, df: pd.DataFrame) -> "MobilityClusteringModel":
        """
        Train clustering model on route data.
        
        Args:
            df: DataFrame from MobilityFeatureExtractor
            
        Returns:
            self
        """
        # Select features for clustering
        feature_cols = [
            "lead_time_days",
            "reliability_score",
            "frequency",
        ]
        
        # Add distance if available
        if "distance_km" in df.columns and df["distance_km"].notna().sum() > 0:
            feature_cols.append("distance_km")
        
        self.feature_names = feature_cols
        
        # Prepare data (handle missing values)
        X = df[feature_cols].fillna(df[feature_cols].mean())
        
        # Normalize features (DBSCAN requires normalized input)
        X_scaled = self.scaler.fit_transform(X)
        
        # Cluster
        self.dbscan = DBSCAN(eps=self.eps, min_samples=self.min_samples)
        labels = self.dbscan.fit_predict(X_scaled)
        
        # Organize results
        for label in set(labels):
            mask = labels == label
            self.clusters[label] = {
                "indices": np.where(mask)[0].tolist(),
                "size": mask.sum(),
            }
        
        return self

    def predict_clusters(
        self, df: pd.DataFrame
    ) -> Dict[int, MobilityCluster]:
        """
        Get cluster assignments with characteristics.
        
        Returns:
            Dictionary of cluster_id -> MobilityCluster
        """
        if not self.dbscan:
            raise ValueError("Model not fitted yet")
        
        results = {}
        
        for cluster_id, cluster_info in self.clusters.items():
            indices = cluster_info["indices"]
            cluster_df = df.iloc[indices]
            
            # Calculate cluster characteristics
            chars = {
                "avg_lead_time": cluster_df["lead_time_days"].mean(),
                "avg_reliability": cluster_df["reliability_score"].mean(),
                "total_frequency": cluster_df["frequency"].sum(),
                "primary_modes": cluster_df["transport_mode"].mode().tolist(),
                "key_corridors": self._identify_key_corridors(cluster_df),
            }
            
            # Efficiency score
            efficiency = self._calculate_efficiency(cluster_df)
            
            # Recommendation
            recommendation = self._generate_recommendation(chars, efficiency)
            
            routes = [
                MobilityRoute(
                    supplier_id=row["supplier_id"],
                    supplier_location=row["supplier_location"],
                    delivery_location=row["delivery_location"],
                    transport_mode=row["transport_mode"],
                    lead_time_days=int(row["lead_time_days"]),
                    distance_km=row.get("distance_km"),
                    frequency=int(row["frequency"]),
                    reliability_score=row["reliability_score"],
                    last_updated=datetime.now().isoformat(),
                )
                for _, row in cluster_df.iterrows()
            ]
            
            results[cluster_id] = MobilityCluster(
                cluster_id=cluster_id,
                routes=routes,
                size=cluster_info["size"],
                characteristics=chars,
                efficiency_score=efficiency,
                recommendation=recommendation,
            )
        
        return results

    @staticmethod
    def _identify_key_corridors(df: pd.DataFrame) -> List[str]:
        """Find most common routes in cluster"""
        corridors = (
            df["supplier_location"]
            + " → "
            + df["delivery_location"]
        )
        return corridors.value_counts().head(3).index.tolist()

    @staticmethod
    def _calculate_efficiency(df: pd.DataFrame) -> float:
        """
        Efficiency score (0-1) combining lead time and reliability.
        Higher reliability + shorter lead time = more efficient.
        """
        # Normalize metrics
        lead_time_score = 1 - (df["lead_time_days"].mean() / 90)  # 90 days as max
        lead_time_score = max(0, min(1, lead_time_score))
        
        reliability_score = df["reliability_score"].mean()
        
        # Weighted average
        return 0.4 * lead_time_score + 0.6 * reliability_score

    @staticmethod
    def _generate_recommendation(chars: Dict, efficiency: float) -> str:
        """Generate actionable recommendation for cluster"""
        if efficiency < 0.5:
            return "HIGH PRIORITY: Low efficiency routes. Consider alternative modes or consolidation."
        elif efficiency < 0.7:
            return "MEDIUM: Opportunities to improve reliability or reduce lead time."
        else:
            return "GOOD: Efficient corridor. Monitor for emerging demand patterns."


class MobilityAnomalyDetector:
    """Detect anomalies in mobility patterns (congestion, bottlenecks, inefficiencies)"""

    def __init__(self, contamination: float = 0.1):
        """
        Args:
            contamination: Expected proportion of anomalies
        """
        self.iso_forest = IsolationForest(contamination=contamination)
        self.feature_names = None

    def fit(self, df: pd.DataFrame) -> "MobilityAnomalyDetector":
        """Train anomaly detector"""
        feature_cols = [
            "lead_time_days",
            "reliability_score",
            "distance_km",
        ]
        
        X = df[feature_cols].dropna()
        self.feature_names = feature_cols
        
        self.iso_forest.fit(X)
        return self

    def predict(self, df: pd.DataFrame) -> Tuple[np.ndarray, List[Dict]]:
        """
        Detect anomalies.
        
        Returns:
            - predictions: -1 for anomaly, 1 for normal
            - anomalies: List of anomalous route details
        """
        X = df[self.feature_names].dropna()
        predictions = self.iso_forest.predict(X)
        
        anomalies = []
        for idx, pred in enumerate(predictions):
            if pred == -1:
                anomalies.append({
                    "route": df.iloc[idx]["supplier_location"]
                    + " → "
                    + df.iloc[idx]["delivery_location"],
                    "lead_time": df.iloc[idx]["lead_time_days"],
                    "reliability": df.iloc[idx]["reliability_score"],
                    "anomaly_type": self._classify_anomaly(df.iloc[idx]),
                })
        
        return predictions, anomalies

    @staticmethod
    def _classify_anomaly(row: pd.Series) -> str:
        """Classify type of anomaly"""
        if row["lead_time_days"] > 60:
            return "excessive_lead_time"
        elif row["reliability_score"] < 0.6:
            return "low_reliability"
        else:
            return "unusual_pattern"


# Example usage function
def example_mobility_analysis(sample_documents: List[Dict]) -> Dict:
    """
    Complete example: Load documents → extract routes → cluster → analyze
    """
    # Extract routes
    extractor = MobilityFeatureExtractor()
    routes_df = extractor.extract_routes_from_documents(sample_documents)
    
    # Cluster
    clustering = MobilityClusteringModel(eps=0.5, min_samples=2)
    clustering.fit(routes_df)
    clusters = clustering.predict_clusters(routes_df)
    
    # Detect anomalies
    anomaly_detector = MobilityAnomalyDetector()
    anomaly_detector.fit(routes_df)
    _, anomalies = anomaly_detector.predict(routes_df)
    
    return {
        "routes_count": len(routes_df),
        "clusters": {
            cid: {
                "size": c.size,
                "efficiency": c.efficiency_score,
                "recommendation": c.recommendation,
            }
            for cid, c in clusters.items()
        },
        "anomalies_detected": len(anomalies),
        "anomaly_examples": anomalies[:3],
    }
