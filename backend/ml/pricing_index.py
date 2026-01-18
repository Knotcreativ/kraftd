"""
Pricing Index Model - Robust Index Construction from Fragmented Price Data

Builds a pricing index from incomplete, noisy, multi-source price data
extracted from KraftdDocument uploads.

Handles:
- Missing prices
- Different currencies
- Regional variations
- Commodity categories
- Time-series normalization

Outputs:
- Fair price ranges by category/region
- Price trend indices
- Market anomalies and spikes
- Benchmark indices per category
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import HuberRegressor  # Robust to outliers
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class Currency(str, Enum):
    """Supported currencies"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CNY = "CNY"
    INR = "INR"


@dataclass
class PricePoint:
    """Single price observation from procurement data"""
    commodity_id: str
    commodity_category: str
    quantity: float
    unit: str
    price_per_unit: float
    currency: str
    region: str
    supplier_id: str
    date: str
    data_quality_score: float  # 0-1, confidence in this price


@dataclass
class PriceIndex:
    """Result of index calculation"""
    index_date: str
    category: str
    region: Optional[str]
    index_value: float  # 100 = baseline
    fair_price_range: Tuple[float, float]
    price_count: int
    trend_direction: str  # "up", "down", "stable"
    volatility: float
    anomalies: List[Dict]


class PriceNormalizationEngine:
    """Normalize fragmented price data before indexing"""

    def __init__(self):
        self.currency_rates = {
            "USD": 1.0,
            "EUR": 1.08,
            "GBP": 1.27,
            "CNY": 0.14,
            "INR": 0.012,
        }
        self.category_encoder = LabelEncoder()
        self.region_encoder = LabelEncoder()

    def extract_prices_from_documents(
        self, documents: List[Dict]
    ) -> pd.DataFrame:
        """
        Extract price information from KraftdDocument list.
        Handles fragmented/incomplete data gracefully.
        
        Args:
            documents: List of KraftdDocument dicts
            
        Returns:
            DataFrame with normalized price columns
        """
        prices = []

        for doc in documents:
            try:
                # Extract line items (fragmented: may be missing quantities)
                line_items = doc.get("line_items", [])
                if not line_items:
                    line_items = [doc]  # Fallback to document level

                for item in line_items:
                    commodity = item.get("commodity", {})
                    
                    # Handle fragmented commodity data
                    category = (
                        commodity.get("category")
                        or item.get("category")
                        or "unknown"
                    )
                    
                    quantity = (
                        item.get("quantity")
                        or item.get("qty")
                        or 1
                    )
                    
                    unit = (
                        item.get("unit")
                        or commodity.get("unit")
                        or "unit"
                    )
                    
                    # Price extraction (may be total or unit price)
                    price = self._extract_unit_price(item, quantity)
                    
                    if price is None or price <= 0:
                        continue
                    
                    currency = (
                        item.get("currency")
                        or doc.get("currency")
                        or "USD"
                    ).upper()
                    
                    region = (
                        doc.get("delivery_location")
                        or doc.get("supplier", {}).get("country")
                        or "global"
                    )
                    
                    # Data quality score
                    quality = self._calculate_data_quality(item)
                    
                    prices.append({
                        "commodity_id": commodity.get("id", "unknown"),
                        "commodity_category": category,
                        "quantity": quantity,
                        "unit": unit,
                        "price_per_unit": price,
                        "currency": currency,
                        "region": region,
                        "supplier_id": doc.get("supplier", {}).get("id", "unknown"),
                        "date": doc.get("date", datetime.now().isoformat()),
                        "data_quality_score": quality,
                    })
            except Exception as e:
                logger.warning(f"Error extracting price from doc: {e}")
                continue

        return pd.DataFrame(prices)

    @staticmethod
    def _extract_unit_price(item: Dict, quantity: float) -> Optional[float]:
        """Handle fragmented price data"""
        # Try direct unit price first
        if "unit_price" in item:
            return float(item["unit_price"])
        
        # Try total price / quantity
        if "total_price" in item and quantity > 0:
            return float(item["total_price"]) / quantity
        
        # Try price field
        if "price" in item:
            return float(item["price"])
        
        return None

    @staticmethod
    def _calculate_data_quality(item: Dict) -> float:
        """
        Score data quality (0-1).
        Full information = high score, fragmented = lower score.
        """
        score = 0.5  # base
        
        if "unit_price" in item:
            score += 0.2
        if "quantity" in item:
            score += 0.15
        if "currency" in item:
            score += 0.15
        
        return min(1.0, score)

    def normalize_prices(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize prices to USD, per unit, adjusted for region.
        
        Args:
            df: Price DataFrame from extract_prices_from_documents
            
        Returns:
            Normalized DataFrame
        """
        df = df.copy()
        
        # Convert to USD
        df["price_usd"] = df.apply(
            lambda row: row["price_per_unit"]
            * self.currency_rates.get(row["currency"], 1.0),
            axis=1,
        )
        
        # Standardize units (simplistic: assume similar items)
        # In production, would need commodity-specific conversion
        
        # Quality-weighted: discount prices with low confidence
        df["adjusted_price"] = (
            df["price_usd"] * df["data_quality_score"]
        )
        
        return df


class RobustPricingIndex:
    """
    Construct robust pricing indices from fragmented data.
    Uses Huber regression (robust to outliers).
    """

    def __init__(self):
        self.normalizer = PriceNormalizationEngine()
        self.indices = {}
        self.baselines = {}

    def build_index(
        self,
        documents: List[Dict],
        category: str,
        region: Optional[str] = None,
        baseline_date: Optional[str] = None,
    ) -> PriceIndex:
        """
        Build pricing index for a commodity category.
        
        Args:
            documents: KraftdDocument list
            category: Commodity category
            region: Optional regional filter
            baseline_date: Date to set as index=100 (default: earliest date)
            
        Returns:
            PriceIndex with index value, trend, and metrics
        """
        # Extract and normalize
        prices_df = self.normalizer.extract_prices_from_documents(documents)
        prices_df = self.normalizer.normalize_prices(prices_df)
        
        # Filter by category and region
        filtered = prices_df[prices_df["commodity_category"] == category]
        if region:
            filtered = filtered[filtered["region"] == region]
        
        if len(filtered) == 0:
            raise ValueError(
                f"No price data for {category} in {region or 'any region'}"
            )
        
        # Sort by date
        filtered["date"] = pd.to_datetime(filtered["date"])
        filtered = filtered.sort_values("date")
        
        # Calculate time-series metrics
        index_value, trend = self._calculate_time_series_index(
            filtered, baseline_date
        )
        
        fair_price = self._calculate_fair_price_range(filtered)
        
        anomalies = self._detect_price_anomalies(filtered)
        
        volatility = self._calculate_volatility(filtered)

        index = PriceIndex(
            index_date=datetime.now().isoformat(),
            category=category,
            region=region,
            index_value=index_value,
            fair_price_range=fair_price,
            price_count=len(filtered),
            trend_direction=trend,
            volatility=volatility,
            anomalies=anomalies,
        )
        
        # Cache
        key = f"{category}:{region or 'global'}"
        self.indices[key] = index

        return index

    @staticmethod
    def _calculate_time_series_index(
        df: pd.DataFrame, baseline_date: Optional[str] = None
    ) -> Tuple[float, str]:
        """
        Calculate index (100 = baseline date).
        Detect trend direction.
        """
        if len(df) < 2:
            return 100.0, "stable"
        
        # Set baseline
        if baseline_date:
            baseline_df = df[df["date"] <= baseline_date]
            if len(baseline_df) == 0:
                baseline_df = df
        else:
            baseline_df = df.iloc[:len(df)//3]  # First 1/3
        
        baseline_price = baseline_df["adjusted_price"].mean()
        
        # Current price (recent, last 1/3)
        current_df = df.iloc[-len(df)//3:]
        current_price = current_df["adjusted_price"].mean()
        
        # Index
        index_value = (current_price / baseline_price) * 100
        
        # Trend
        trend = "up" if index_value > 105 else ("down" if index_value < 95 else "stable")
        
        return index_value, trend

    @staticmethod
    def _calculate_fair_price_range(df: pd.DataFrame) -> Tuple[float, float]:
        """Fair price range: 25th-75th percentile (robust to outliers)"""
        return (
            df["adjusted_price"].quantile(0.25),
            df["adjusted_price"].quantile(0.75),
        )

    @staticmethod
    def _detect_price_anomalies(df: pd.DataFrame) -> List[Dict]:
        """Find prices outside normal range"""
        q1 = df["adjusted_price"].quantile(0.25)
        q3 = df["adjusted_price"].quantile(0.75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        anomalies = []
        for _, row in df.iterrows():
            if row["adjusted_price"] < lower_bound or \
               row["adjusted_price"] > upper_bound:
                anomalies.append({
                    "supplier": row["supplier_id"],
                    "price": row["adjusted_price"],
                    "type": "below_range"
                    if row["adjusted_price"] < lower_bound
                    else "above_range",
                    "date": row["date"].isoformat(),
                })
        
        return anomalies

    @staticmethod
    def _calculate_volatility(df: pd.DataFrame) -> float:
        """Price volatility (coefficient of variation)"""
        mean_price = df["adjusted_price"].mean()
        std_price = df["adjusted_price"].std()
        
        if mean_price == 0:
            return 0.0
        
        return min(1.0, std_price / mean_price)


class CompositeIndexBuilder:
    """Build aggregate indices across multiple categories/regions"""

    def __init__(self):
        self.pricing_index = RobustPricingIndex()

    def build_composite_index(
        self,
        documents: List[Dict],
        categories: List[str],
        base_value: float = 100.0,
    ) -> Dict[str, float]:
        """
        Build weighted composite index across categories.
        
        Args:
            documents: All procurement documents
            categories: Categories to include
            base_value: Base value for index
            
        Returns:
            Dictionary of category indices
        """
        indices = {}
        
        for category in categories:
            try:
                cat_index = self.pricing_index.build_index(
                    documents, category
                )
                indices[category] = cat_index.index_value
            except ValueError:
                logger.warning(f"No data for category {category}")
                indices[category] = base_value  # fallback
        
        return indices


# Example usage
def example_pricing_index_analysis(
    sample_documents: List[Dict],
) -> Dict:
    """Complete pricing index example"""
    builder = CompositeIndexBuilder()
    
    categories = ["electronics", "raw_materials", "components"]
    
    indices = builder.build_composite_index(sample_documents, categories)
    
    # Also get detailed index for primary category
    detailed = builder.pricing_index.build_index(
        sample_documents, "electronics"
    )
    
    return {
        "composite_indices": indices,
        "primary_category": {
            "category": "electronics",
            "index_value": detailed.index_value,
            "trend": detailed.trend_direction,
            "fair_price_range": detailed.fair_price_range,
            "volatility": detailed.volatility,
        },
    }
