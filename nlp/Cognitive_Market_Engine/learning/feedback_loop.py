"""
FEEDBACK LOOP — Self-learning system for the Cognitive Market Engine.

Tracks prediction accuracy per participant type, event type, and asset class.
Adjusts confidence weights over time using exponential moving averages.
Integrates with storage/database for persistence.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import json
import math


@dataclass
class PredictionRecord:
    """Record of a prediction and its outcome."""
    prediction_id: str
    timestamp: str
    event_type: str
    participant_type: str
    asset: str
    predicted_direction: str  # bullish, bearish, neutral
    predicted_magnitude: float  # 0.0 - 1.0
    confidence: float
    actual_direction: str = ""
    actual_magnitude: float = 0.0
    validated: bool = False
    accuracy_score: float = 0.0
    latency_hours: float = 0.0  # time to validate
    
    def to_dict(self) -> Dict:
        return {
            "prediction_id": self.prediction_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "participant_type": self.participant_type,
            "asset": self.asset,
            "predicted_direction": self.predicted_direction,
            "predicted_magnitude": self.predicted_magnitude,
            "confidence": self.confidence,
            "actual_direction": self.actual_direction,
            "actual_magnitude": self.actual_magnitude,
            "validated": self.validated,
            "accuracy_score": self.accuracy_score,
            "latency_hours": self.latency_hours,
        }


@dataclass
class ModelCredibility:
    """Credibility tracking for a model / participant type."""
    name: str
    total_predictions: int = 0
    correct_predictions: int = 0
    accuracy_ema: float = 0.5  # exponential moving average
    confidence_calibration: float = 0.5  # how well calibrated
    direction_accuracy: float = 0.5
    magnitude_accuracy: float = 0.5
    best_event_type: str = ""
    worst_event_type: str = ""
    weight: float = 1.0  # model weight in ensemble
    last_updated: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "total_predictions": self.total_predictions,
            "correct_predictions": self.correct_predictions,
            "accuracy_ema": round(self.accuracy_ema, 4),
            "confidence_calibration": round(self.confidence_calibration, 4),
            "direction_accuracy": round(self.direction_accuracy, 4),
            "magnitude_accuracy": round(self.magnitude_accuracy, 4),
            "best_event_type": self.best_event_type,
            "worst_event_type": self.worst_event_type,
            "weight": round(self.weight, 4),
            "last_updated": self.last_updated,
        }


class FeedbackLoop:
    """
    Self-learning feedback loop for the Cognitive Market Engine.
    
    Features:
    - Tracks prediction accuracy by participant, event type, asset
    - Adjusts model weights using exponential moving averages
    - Confidence calibration scoring
    - Performance decay for stale models
    - Persistence via database
    """
    
    EMA_ALPHA = 0.15  # Weight of new observation
    DECAY_RATE = 0.01  # Weight decay per day of inactivity
    MIN_WEIGHT = 0.1
    MAX_WEIGHT = 3.0
    
    def __init__(self, storage=None):
        """
        Args:
            storage: DatabaseManager for persistence (optional)
        """
        self.storage = storage
        
        # In-memory tracking
        self.predictions: Dict[str, PredictionRecord] = {}
        self.model_credibility: Dict[str, ModelCredibility] = {}
        self.event_type_accuracy: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.asset_accuracy: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Stats
        self.total_validated = 0
        self.total_correct = 0
        self.calibration_bins: Dict[str, List[float]] = defaultdict(list)
        
        # Initialize default participant types
        for p_type in ["institutional_strategist", "central_bank_watcher",
                       "momentum_trader", "retail_herd", "contrarian_analyst"]:
            self.model_credibility[p_type] = ModelCredibility(name=p_type)
        
        # Load from storage if available
        self._load_from_storage()
        
        print("[FEEDBACK] Learning feedback loop initialized")
    
    def record_prediction(self, prediction_id: str, event_type: str,
                          participant_type: str, asset: str,
                          predicted_direction: str,
                          predicted_magnitude: float,
                          confidence: float) -> PredictionRecord:
        """
        Record a new prediction for later validation.
        
        Args:
            prediction_id: Unique ID
            event_type: Type of event
            participant_type: Which participant model made this
            asset: Asset being predicted
            predicted_direction: bullish, bearish, neutral
            predicted_magnitude: Expected magnitude 0-1
            confidence: Confidence level 0-1
            
        Returns:
            PredictionRecord
        """
        record = PredictionRecord(
            prediction_id=prediction_id,
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            participant_type=participant_type,
            asset=asset,
            predicted_direction=predicted_direction,
            predicted_magnitude=min(1.0, max(0.0, predicted_magnitude)),
            confidence=min(1.0, max(0.0, confidence)),
        )
        
        self.predictions[prediction_id] = record
        
        # Initialize credibility if new participant type
        if participant_type not in self.model_credibility:
            self.model_credibility[participant_type] = ModelCredibility(
                name=participant_type
            )
        
        return record
    
    def validate_prediction(self, prediction_id: str,
                            actual_direction: str,
                            actual_magnitude: float) -> Optional[Dict]:
        """
        Validate a prediction against actual outcome.
        
        Args:
            prediction_id: ID of prediction to validate
            actual_direction: What actually happened
            actual_magnitude: Actual magnitude 0-1
            
        Returns:
            Validation result dict, or None if prediction not found
        """
        record = self.predictions.get(prediction_id)
        if not record:
            return None
        
        record.actual_direction = actual_direction
        record.actual_magnitude = min(1.0, max(0.0, actual_magnitude))
        record.validated = True
        
        # Compute accuracy
        direction_correct = record.predicted_direction == actual_direction
        magnitude_error = abs(record.predicted_magnitude - actual_magnitude)
        
        # Direction accuracy: 1.0 if correct, 0.0 if wrong
        # Partial credit for near-neutral ranges
        if direction_correct:
            record.accuracy_score = 1.0 - (magnitude_error * 0.3)
        elif record.predicted_direction == "neutral" or actual_direction == "neutral":
            record.accuracy_score = 0.4 - (magnitude_error * 0.2)
        else:
            record.accuracy_score = 0.0
        
        record.accuracy_score = max(0.0, min(1.0, record.accuracy_score))
        
        # Latency
        try:
            pred_time = datetime.fromisoformat(record.timestamp)
            record.latency_hours = (datetime.now() - pred_time).total_seconds() / 3600
        except Exception:
            record.latency_hours = 0
        
        # Update model credibility
        self._update_credibility(record, direction_correct, magnitude_error)
        
        # Update calibration
        bin_key = f"{int(record.confidence * 10) / 10:.1f}"
        self.calibration_bins[bin_key].append(record.accuracy_score)
        
        # Stats
        self.total_validated += 1
        if direction_correct:
            self.total_correct += 1
        
        # Persist
        self._save_to_storage(record)
        
        return {
            "prediction_id": prediction_id,
            "direction_correct": direction_correct,
            "accuracy_score": record.accuracy_score,
            "magnitude_error": round(magnitude_error, 4),
            "model_weight": self.model_credibility[record.participant_type].weight,
            "model_accuracy_ema": self.model_credibility[record.participant_type].accuracy_ema,
        }
    
    def _update_credibility(self, record: PredictionRecord,
                            direction_correct: bool,
                            magnitude_error: float):
        """Update model credibility based on validation."""
        cred = self.model_credibility.get(record.participant_type)
        if not cred:
            return
        
        cred.total_predictions += 1
        if direction_correct:
            cred.correct_predictions += 1
        
        # Exponential moving average for accuracy
        cred.accuracy_ema = (
            (1 - self.EMA_ALPHA) * cred.accuracy_ema +
            self.EMA_ALPHA * record.accuracy_score
        )
        
        # Direction accuracy
        cred.direction_accuracy = (
            (1 - self.EMA_ALPHA) * cred.direction_accuracy +
            self.EMA_ALPHA * (1.0 if direction_correct else 0.0)
        )
        
        # Magnitude accuracy
        cred.magnitude_accuracy = (
            (1 - self.EMA_ALPHA) * cred.magnitude_accuracy +
            self.EMA_ALPHA * (1.0 - magnitude_error)
        )
        
        # Confidence calibration
        # Ideal: confidence ≈ accuracy (well-calibrated)
        calibration_error = abs(record.confidence - record.accuracy_score)
        cred.confidence_calibration = (
            (1 - self.EMA_ALPHA) * cred.confidence_calibration +
            self.EMA_ALPHA * (1.0 - calibration_error)
        )
        
        # Update weight: higher accuracy → higher weight
        target_weight = 0.5 + (cred.accuracy_ema * 2.0)
        cred.weight = max(
            self.MIN_WEIGHT,
            min(self.MAX_WEIGHT, 0.9 * cred.weight + 0.1 * target_weight)
        )
        
        # Track event type accuracy
        et = record.event_type
        if et not in self.event_type_accuracy[record.participant_type]:
            self.event_type_accuracy[record.participant_type][et] = 0.5
        
        self.event_type_accuracy[record.participant_type][et] = (
            0.85 * self.event_type_accuracy[record.participant_type][et] +
            0.15 * record.accuracy_score
        )
        
        # Find best/worst event types
        et_acc = self.event_type_accuracy[record.participant_type]
        if et_acc:
            cred.best_event_type = max(et_acc, key=et_acc.get)
            cred.worst_event_type = min(et_acc, key=et_acc.get)
        
        cred.last_updated = datetime.now().isoformat()
    
    def apply_decay(self):
        """
        Apply decay to models that haven't been updated recently.
        Prevents stale models from maintaining inflated weights.
        """
        now = datetime.now()
        
        for name, cred in self.model_credibility.items():
            if not cred.last_updated:
                continue
            
            try:
                last = datetime.fromisoformat(cred.last_updated)
                days_inactive = (now - last).total_seconds() / 86400
                
                if days_inactive > 1:
                    decay = math.exp(-self.DECAY_RATE * days_inactive)
                    cred.weight = max(self.MIN_WEIGHT, cred.weight * decay)
                    cred.accuracy_ema = 0.5 + (cred.accuracy_ema - 0.5) * decay
            except Exception:
                pass
    
    def get_model_weight(self, participant_type: str) -> float:
        """Get current weight for a model."""
        cred = self.model_credibility.get(participant_type)
        return cred.weight if cred else 1.0
    
    def get_ensemble_weights(self) -> Dict[str, float]:
        """Get normalized weights for all models (for ensemble weighting)."""
        weights = {}
        total = 0
        
        for name, cred in self.model_credibility.items():
            weights[name] = cred.weight
            total += cred.weight
        
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        
        return weights
    
    def get_credibility_report(self) -> Dict:
        """Generate a full credibility report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall": {
                "total_validated": self.total_validated,
                "total_correct": self.total_correct,
                "overall_accuracy": (
                    self.total_correct / self.total_validated
                    if self.total_validated > 0 else 0
                ),
            },
            "models": {},
            "calibration": {},
            "rankings": {},
        }
        
        # Model details
        for name, cred in self.model_credibility.items():
            report["models"][name] = cred.to_dict()
        
        # Calibration analysis
        for bin_key, scores in self.calibration_bins.items():
            avg_accuracy = sum(scores) / len(scores) if scores else 0
            report["calibration"][bin_key] = {
                "count": len(scores),
                "avg_accuracy": round(avg_accuracy, 4),
                "expected": float(bin_key),
                "deviation": round(abs(avg_accuracy - float(bin_key)), 4),
            }
        
        # Rankings
        if self.model_credibility:
            ranked = sorted(
                self.model_credibility.values(),
                key=lambda c: c.accuracy_ema,
                reverse=True,
            )
            report["rankings"] = {
                "by_accuracy": [c.name for c in ranked],
                "best_model": ranked[0].name if ranked else "",
                "worst_model": ranked[-1].name if ranked else "",
            }
        
        return report
    
    def get_recommendation(self, event_type: str) -> Dict:
        """
        Get model weight recommendations for a specific event type.
        
        Returns which participant models to trust more/less for this type.
        """
        recommendations = {}
        
        for name, cred in self.model_credibility.items():
            et_acc = self.event_type_accuracy.get(name, {}).get(event_type, 0.5)
            
            trust_level = "medium"
            if et_acc > 0.7:
                trust_level = "high"
            elif et_acc < 0.3:
                trust_level = "low"
            
            recommendations[name] = {
                "weight": cred.weight,
                "event_type_accuracy": round(et_acc, 4),
                "trust_level": trust_level,
                "recommended_weight_multiplier": round(
                    0.5 + et_acc, 2
                ),
            }
        
        return recommendations
    
    def _save_to_storage(self, record: PredictionRecord):
        """Persist data to storage."""
        if not self.storage:
            return
        
        try:
            if hasattr(self.storage, "store_model_credibility"):
                cred = self.model_credibility.get(record.participant_type)
                if cred:
                    self.storage.store_model_credibility(cred.to_dict())
            
            if hasattr(self.storage, "store_validation_record"):
                self.storage.store_validation_record(record.to_dict())
        except Exception:
            pass
    
    def _load_from_storage(self):
        """Load persisted credibility data."""
        if not self.storage:
            return
        
        try:
            if hasattr(self.storage, "get_model_credibilities"):
                creds = self.storage.get_model_credibilities()
                for c in creds:
                    name = c.get("name", "")
                    if name:
                        self.model_credibility[name] = ModelCredibility(
                            name=name,
                            total_predictions=c.get("total_predictions", 0),
                            correct_predictions=c.get("correct_predictions", 0),
                            accuracy_ema=c.get("accuracy_ema", 0.5),
                            confidence_calibration=c.get("confidence_calibration", 0.5),
                            direction_accuracy=c.get("direction_accuracy", 0.5),
                            magnitude_accuracy=c.get("magnitude_accuracy", 0.5),
                            weight=c.get("weight", 1.0),
                            last_updated=c.get("last_updated", ""),
                        )
        except Exception:
            pass
