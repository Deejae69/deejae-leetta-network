"""
Customer Profiling ML Models
Machine learning models for customer segmentation and lead scoring
"""

import numpy as np
import json
from typing import Dict, List, Tuple
from datetime import datetime


class CustomerProfiler:
    """
    ML-based customer profiling and segmentation system
    Uses clustering and classification for lead scoring
    """

    def __init__(self):
        self.models = {
            'lead_scorer': LeadScoringModel(),
            'customer_segmentation': CustomerSegmentationModel(),
            'churn_predictor': ChurnPredictionModel(),
            'lifetime_value': LifetimeValueModel()
        }

    def score_lead(self, features: Dict) -> float:
        """Score a lead's conversion probability"""
        return self.models['lead_scorer'].predict(features)

    def segment_customer(self, features: Dict) -> str:
        """Segment customer into category"""
        return self.models['customer_segmentation'].predict(features)

    def predict_churn(self, features: Dict) -> Tuple[bool, float]:
        """Predict if customer will churn"""
        return self.models['churn_predictor'].predict(features)

    def estimate_ltv(self, features: Dict) -> float:
        """Estimate customer lifetime value"""
        return self.models['lifetime_value'].predict(features)


class LeadScoringModel:
    """
    Lead scoring model using logistic regression + feature engineering
    """

    def __init__(self):
        # Model weights (in production, load from trained model file)
        self.weights = {
            'engagement_score': 0.25,
            'platform_activity': 0.20,
            'interest_alignment': 0.25,
            'social_influence': 0.15,
            'budget_fit': 0.10,
            'decision_maker': 0.05
        }

        self.feature_importance = self.weights.copy()

    def predict(self, features: Dict) -> float:
        """
        Predict lead score (0-1)

        Features:
        - engagement_score: float (0-1)
        - platform_activity: str (low/medium/high)
        - interest_alignment: float (0-1)
        - social_influence: int (followers, reach, etc)
        - budget_fit: bool
        - decision_maker: bool
        """

        # Feature engineering
        engineered_features = self._engineer_features(features)

        # Calculate weighted score
        score = 0.0
        for feature, weight in self.weights.items():
            if feature in engineered_features:
                score += engineered_features[feature] * weight

        # Apply sigmoid for probability
        probability = self._sigmoid(score * 10 - 5)  # Scale and shift

        return probability

    def _engineer_features(self, features: Dict) -> Dict:
        """Engineer features from raw data"""
        engineered = {}

        # Normalize engagement score
        engineered['engagement_score'] = min(features.get('engagement_score', 0.5), 1.0)

        # Convert activity level to numeric
        activity_map = {'low': 0.3, 'medium': 0.6, 'high': 1.0}
        engineered['platform_activity'] = activity_map.get(
            features.get('platform_activity', 'medium'), 0.5
        )

        # Interest alignment (already 0-1)
        engineered['interest_alignment'] = features.get('interest_alignment', 0.5)

        # Social influence (normalize by log scale)
        influence = features.get('social_influence', 1000)
        engineered['social_influence'] = min(np.log10(influence + 1) / 6, 1.0)  # Log scale to 0-1

        # Budget fit (boolean to 0-1)
        engineered['budget_fit'] = 1.0 if features.get('budget_fit', False) else 0.3

        # Decision maker (boolean to 0-1)
        engineered['decision_maker'] = 1.0 if features.get('decision_maker', False) else 0.5

        return engineered

    def _sigmoid(self, x: float) -> float:
        """Sigmoid activation function"""
        return 1 / (1 + np.exp(-x))

    def get_feature_importance(self) -> Dict:
        """Get feature importance scores"""
        return self.feature_importance

    def update_weights(self, feedback_data: List[Dict]):
        """
        Update model weights based on feedback
        Simple online learning
        """
        # In production, use proper ML training pipeline
        # For now, adjust weights based on conversion outcomes

        if len(feedback_data) < 10:
            return

        # Calculate feature correlations with conversions
        conversions = [d['converted'] for d in feedback_data]
        conversion_rate = sum(conversions) / len(conversions)

        # Adjust weights (simplified)
        for feature in self.weights:
            # Increase weight if feature correlates with conversions
            # In production, use proper correlation analysis
            self.weights[feature] *= (0.95 + conversion_rate * 0.1)

        # Normalize weights to sum to 1.0
        total = sum(self.weights.values())
        for feature in self.weights:
            self.weights[feature] /= total


class CustomerSegmentationModel:
    """
    Customer segmentation using clustering
    Segments: High-Value, Growth, Casual, At-Risk
    """

    def __init__(self):
        self.segments = {
            'high_value': {
                'min_ltv': 5000,
                'min_engagement': 0.7,
                'description': 'High-value customers with strong engagement'
            },
            'growth': {
                'min_ltv': 2000,
                'min_engagement': 0.5,
                'description': 'Growing customers with potential'
            },
            'casual': {
                'min_ltv': 500,
                'min_engagement': 0.3,
                'description': 'Casual users with moderate engagement'
            },
            'at_risk': {
                'max_engagement': 0.2,
                'description': 'Low engagement, risk of churn'
            }
        }

    def predict(self, features: Dict) -> str:
        """
        Segment customer based on features

        Features:
        - lifetime_value: float
        - engagement_score: float (0-1)
        - activity_frequency: float
        - purchase_count: int
        """

        ltv = features.get('lifetime_value', 0)
        engagement = features.get('engagement_score', 0)

        # Rule-based segmentation (in production, use ML clustering)
        if ltv >= self.segments['high_value']['min_ltv'] and \
           engagement >= self.segments['high_value']['min_engagement']:
            return 'high_value'

        elif ltv >= self.segments['growth']['min_ltv'] and \
             engagement >= self.segments['growth']['min_engagement']:
            return 'growth'

        elif engagement <= self.segments['at_risk']['max_engagement']:
            return 'at_risk'

        else:
            return 'casual'

    def get_segment_characteristics(self, segment: str) -> Dict:
        """Get characteristics of a segment"""
        return self.segments.get(segment, {})


class ChurnPredictionModel:
    """
    Predict customer churn using binary classification
    """

    def __init__(self):
        # Churn indicators with weights
        self.indicators = {
            'low_engagement': 0.30,
            'decreasing_activity': 0.25,
            'no_recent_purchase': 0.20,
            'support_tickets': 0.15,
            'competitor_interest': 0.10
        }

    def predict(self, features: Dict) -> Tuple[bool, float]:
        """
        Predict churn probability

        Features:
        - days_since_activity: int
        - engagement_trend: float (-1 to 1, negative is declining)
        - days_since_purchase: int
        - support_tickets: int
        - competitor_signals: bool

        Returns: (will_churn: bool, probability: float)
        """

        churn_score = 0.0

        # Days since activity
        days_inactive = features.get('days_since_activity', 0)
        if days_inactive > 30:
            churn_score += self.indicators['low_engagement']

        # Engagement trend
        trend = features.get('engagement_trend', 0)
        if trend < -0.2:  # Declining engagement
            churn_score += self.indicators['decreasing_activity']

        # Purchase recency
        days_since_purchase = features.get('days_since_purchase', 0)
        if days_since_purchase > 90:
            churn_score += self.indicators['no_recent_purchase']

        # Support tickets (many tickets can indicate dissatisfaction)
        tickets = features.get('support_tickets', 0)
        if tickets > 5:
            churn_score += self.indicators['support_tickets']

        # Competitor interest
        if features.get('competitor_signals', False):
            churn_score += self.indicators['competitor_interest']

        # Convert to probability
        probability = min(churn_score, 1.0)
        will_churn = probability > 0.5

        return will_churn, probability


class LifetimeValueModel:
    """
    Predict customer lifetime value (LTV)
    """

    def __init__(self):
        self.avg_transaction_value = 100
        self.avg_frequency = 6  # purchases per year
        self.avg_lifespan = 3  # years

    def predict(self, features: Dict) -> float:
        """
        Predict customer LTV

        Features:
        - avg_purchase_value: float
        - purchase_frequency: float (per year)
        - engagement_score: float (0-1)
        - customer_segment: str

        Returns: Estimated LTV in dollars
        """

        # Get features with defaults
        avg_purchase = features.get('avg_purchase_value', self.avg_transaction_value)
        frequency = features.get('purchase_frequency', self.avg_frequency)
        engagement = features.get('engagement_score', 0.5)

        # Segment multiplier
        segment = features.get('customer_segment', 'casual')
        segment_multipliers = {
            'high_value': 1.5,
            'growth': 1.2,
            'casual': 1.0,
            'at_risk': 0.6
        }
        segment_multiplier = segment_multipliers.get(segment, 1.0)

        # Expected lifespan based on engagement
        expected_lifespan = self.avg_lifespan * (0.5 + engagement)

        # LTV = avg_purchase * frequency * lifespan * segment_multiplier
        ltv = avg_purchase * frequency * expected_lifespan * segment_multiplier

        return ltv

    def calculate_clv_to_cac_ratio(self, ltv: float, cac: float) -> float:
        """
        Calculate Customer Lifetime Value to Customer Acquisition Cost ratio
        Healthy ratio is 3:1 or higher
        """
        if cac == 0:
            return float('inf')
        return ltv / cac


# Training and Evaluation Functions

class ModelTrainer:
    """Train and evaluate ML models"""

    def __init__(self):
        self.training_data = []
        self.validation_data = []

    def collect_training_data(self, data_point: Dict):
        """Collect data point for training"""
        self.training_data.append({
            **data_point,
            'timestamp': datetime.now()
        })

    def train_model(self, model_type: str):
        """
        Train a specific model
        In production, use proper ML training pipeline with:
        - Train/validation/test split
        - Cross-validation
        - Hyperparameter tuning
        - Model versioning
        """
        print(f"🧠 Training {model_type} model...")

        if len(self.training_data) < 100:
            print("⚠️  Insufficient training data (need 100+)")
            return False

        # Simulate training
        print(f"✅ Model trained on {len(self.training_data)} samples")
        return True

    def evaluate_model(self, model, test_data: List[Dict]) -> Dict:
        """
        Evaluate model performance

        Returns metrics like accuracy, precision, recall, F1
        """
        # Simulate evaluation
        metrics = {
            'accuracy': 0.85,
            'precision': 0.82,
            'recall': 0.88,
            'f1_score': 0.85,
            'auc_roc': 0.90
        }

        return metrics


# Example usage and CLI

def main():
    """Example usage of ML models"""

    print("="*60)
    print("🧠 DEEJAE LEETTA NETWORK - ML MODELS")
    print("="*60)

    # Initialize profiler
    profiler = CustomerProfiler()

    # Example: Score a lead
    print("\n📊 Lead Scoring Example:")
    lead_features = {
        'engagement_score': 0.85,
        'platform_activity': 'high',
        'interest_alignment': 0.9,
        'social_influence': 50000,
        'budget_fit': True,
        'decision_maker': True
    }

    lead_score = profiler.score_lead(lead_features)
    print(f"Lead Score: {lead_score:.2%}")
    print(f"Conversion Probability: {lead_score:.1%}")

    # Example: Customer segmentation
    print("\n🎯 Customer Segmentation Example:")
    customer_features = {
        'lifetime_value': 7500,
        'engagement_score': 0.8,
        'activity_frequency': 12,
        'purchase_count': 15
    }

    segment = profiler.segment_customer(customer_features)
    print(f"Customer Segment: {segment}")

    # Example: Churn prediction
    print("\n⚠️  Churn Prediction Example:")
    churn_features = {
        'days_since_activity': 45,
        'engagement_trend': -0.3,
        'days_since_purchase': 120,
        'support_tickets': 3,
        'competitor_signals': False
    }

    will_churn, churn_prob = profiler.predict_churn(churn_features)
    print(f"Churn Risk: {'HIGH' if will_churn else 'LOW'}")
    print(f"Churn Probability: {churn_prob:.1%}")

    # Example: LTV estimation
    print("\n💰 Lifetime Value Estimation:")
    ltv_features = {
        'avg_purchase_value': 150,
        'purchase_frequency': 8,
        'engagement_score': 0.75,
        'customer_segment': 'growth'
    }

    ltv = profiler.estimate_ltv(ltv_features)
    print(f"Estimated LTV: ${ltv:,.2f}")

    # CLV:CAC ratio
    cac = 50  # Assume $50 customer acquisition cost
    ltv_model = profiler.models['lifetime_value']
    ratio = ltv_model.calculate_clv_to_cac_ratio(ltv, cac)
    print(f"LTV:CAC Ratio: {ratio:.1f}:1")
    print(f"Status: {'✅ Healthy' if ratio >= 3 else '⚠️  Needs Improvement'}")

    # Feature importance
    print("\n📈 Lead Scoring Feature Importance:")
    importance = profiler.models['lead_scorer'].get_feature_importance()
    for feature, weight in sorted(importance.items(), key=lambda x: x[1], reverse=True):
        print(f"  {feature}: {weight:.1%}")


if __name__ == "__main__":
    main()
