"""ML prediction service for rate calculations."""

import logging
from typing import Dict, Any
from pathlib import Path
import joblib
import pandas as pd

from ..schemas.rates import RateRequest

logger = logging.getLogger(__name__)


class MLPredictionService:
    """Service for loading and using trained ML models for rate prediction."""

    def __init__(self, model_path: str = "./ml_models/rate_predictor_v1.0.pkl"):
        """Initialize ML prediction service.

        Args:
            model_path: Path to trained model file
        """
        self.model_path = Path(model_path)
        self.model = None
        self.feature_engineer = None
        self.loaded = False

        # Try to load model on initialization
        try:
            self.load_model()
        except Exception as e:
            logger.warning(f"Could not load ML model on initialization: {e}")

    def load_model(self):
        """Load trained model from disk."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}")

        # Load model artifacts
        model_dict = joblib.load(self.model_path)

        # Extract components
        self.model = model_dict
        self.loaded = True

        logger.info(f"ML model loaded successfully from {self.model_path}")
        logger.info(
            f"Model version: {model_dict.get('metadata', {}).get('version', 'unknown')}"
        )

        # Try to load feature engineer if available
        feature_path = self.model_path.parent / "feature_engineer.pkl"
        if feature_path.exists():
            try:
                self.feature_engineer = joblib.load(feature_path)
                logger.info("Feature engineer loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load feature engineer: {e}")

    def is_available(self) -> bool:
        """Check if ML service is available.

        Returns:
            True if model is loaded and ready
        """
        return self.loaded and self.model is not None

    def prepare_features(self, request: RateRequest) -> pd.DataFrame:
        """Convert RateRequest to model features.

        Args:
            request: Rate calculation request

        Returns:
            DataFrame with engineered features
        """
        # Create base DataFrame from request
        df = pd.DataFrame(
            [
                {
                    "project_type": request.project_type,
                    "complexity": request.project_complexity,
                    "experience_years": request.experience_years,
                    "skills_count": request.skills_count,
                    "client_region": request.client_region,
                    "urgency": request.urgency,
                }
            ]
        )

        # If feature engineer is available, use it
        if self.feature_engineer:
            try:
                features = self.feature_engineer.transform(df)
                return features
            except Exception as e:
                logger.error(f"Error in feature engineering: {e}")
                # Fall back to manual feature engineering

        # Manual feature engineering (fallback)
        features = self._manual_feature_engineering(df)

        return features

    def _manual_feature_engineering(self, df: pd.DataFrame) -> pd.DataFrame:
        """Manual feature engineering as fallback.

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with features
        """
        features = pd.DataFrame()

        # One-hot encode project type
        project_types = [
            "web_development",
            "mobile_development",
            "design",
            "writing",
            "marketing",
            "consulting",
            "data_analysis",
            "other",
        ]
        for pt in project_types:
            features[f"project_type_{pt}"] = (df["project_type"] == pt).astype(int)

        # One-hot encode complexity
        complexity_levels = ["simple", "moderate", "complex", "enterprise"]
        for complexity in complexity_levels:
            features[f"complexity_{complexity}"] = (
                df["complexity"] == complexity
            ).astype(int)

        # Numeric features
        features["experience_years"] = df["experience_years"]
        features["skills_count"] = df["skills_count"]

        # One-hot encode client region
        regions = ["egypt", "mena", "europe", "usa", "global"]
        for region in regions:
            features[f"client_region_{region}"] = (
                df["client_region"] == region
            ).astype(int)

        # Urgency
        features["urgency_rush"] = (df["urgency"] == "rush").astype(int)

        # Derived features
        features["experience_skill_interaction"] = (
            features["experience_years"] * features["skills_count"]
        )
        features["is_senior"] = (features["experience_years"] >= 8).astype(int)
        features["is_international_client"] = (
            (features["client_region_usa"] == 1)
            | (features["client_region_europe"] == 1)
        ).astype(int)

        # Complexity score
        complexity_scores = {"simple": 1, "moderate": 2, "complex": 3, "enterprise": 4}
        features["complexity_score"] = df["complexity"].map(complexity_scores).fillna(2)

        return features

    def predict_rate(self, request: RateRequest) -> Dict[str, Any]:
        """Predict rate using ML model.

        Args:
            request: Rate calculation request

        Returns:
            Dictionary with rate predictions and metadata
        """
        if not self.is_available():
            raise RuntimeError("ML model is not loaded")

        try:
            # Prepare features
            features = self.prepare_features(request)

            # Get prediction using ensemble
            competitive_rate = self._predict_with_ensemble(features)

            # Calculate rate tiers (same as rule-based approach)
            minimum_rate = round(competitive_rate * 0.8)
            premium_rate = round(competitive_rate * 1.3)

            # Calculate confidence score
            confidence = self._calculate_confidence(features)

            return {
                "minimum_rate": float(minimum_rate),
                "competitive_rate": float(round(competitive_rate)),
                "premium_rate": float(premium_rate),
                "currency": "EGP",
                "method": "ml_prediction",
                "confidence_score": float(confidence),
                "model_version": self.model.get("metadata", {}).get("version", "1.0"),
            }

        except Exception as e:
            logger.error(f"Error during ML prediction: {e}")
            raise

    def _predict_with_ensemble(self, features: pd.DataFrame) -> float:
        """Make prediction using ensemble model.

        Args:
            features: Engineered features

        Returns:
            Predicted competitive rate
        """
        # Extract model components
        xgb_model = self.model["xgb_model"]
        lgbm_model = self.model["lgbm_model"]
        scaler = self.model["scaler"]
        xgb_weight = self.model.get("xgb_weight", 0.6)
        lgbm_weight = self.model.get("lgbm_weight", 0.4)
        feature_names = self.model["feature_names"]

        # Ensure features are in correct order
        features = features[feature_names]

        # Scale features
        features_scaled = scaler.transform(features)

        # Get predictions from both models
        xgb_pred = xgb_model.predict(features_scaled)[0]
        lgbm_pred = lgbm_model.predict(features_scaled)[0]

        # Weighted ensemble
        ensemble_pred = (xgb_weight * xgb_pred) + (lgbm_weight * lgbm_pred)

        # Ensure rate is within reasonable bounds
        ensemble_pred = max(30, min(5000, ensemble_pred))

        return ensemble_pred

    def _calculate_confidence(self, features: pd.DataFrame) -> float:
        """Calculate confidence score for prediction.

        Args:
            features: Engineered features

        Returns:
            Confidence score (0-1)
        """
        try:
            # Get predictions from both models
            xgb_model = self.model["xgb_model"]
            lgbm_model = self.model["lgbm_model"]
            scaler = self.model["scaler"]
            feature_names = self.model["feature_names"]

            features = features[feature_names]
            features_scaled = scaler.transform(features)

            xgb_pred = xgb_model.predict(features_scaled)[0]
            lgbm_pred = lgbm_model.predict(features_scaled)[0]

            # Confidence based on model agreement
            avg_pred = (xgb_pred + lgbm_pred) / 2
            relative_diff = abs(xgb_pred - lgbm_pred) / avg_pred

            # High agreement = high confidence
            confidence = 1.0 - min(relative_diff, 1.0)

            # Clamp to reasonable range
            confidence = max(0.5, min(1.0, confidence))

            return confidence

        except Exception as e:
            logger.warning(f"Could not calculate confidence: {e}")
            return 0.75  # Default confidence

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded model.

        Returns:
            Dictionary with model metadata
        """
        if not self.is_available():
            return {"status": "not_loaded"}

        metadata = self.model.get("metadata", {})

        return {
            "status": "loaded",
            "version": metadata.get("version", "unknown"),
            "trained_at": metadata.get("trained_at", "unknown"),
            "training_samples": metadata.get("training_samples", 0),
            "xgb_weight": self.model.get("xgb_weight", 0.6),
            "lgbm_weight": self.model.get("lgbm_weight", 0.4),
        }
