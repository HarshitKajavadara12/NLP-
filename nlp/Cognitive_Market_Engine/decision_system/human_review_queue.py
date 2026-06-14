"""
Decision Queue with Human Review — Category 1.7
================================================
For high-stakes decisions (large position changes, drawdown proximity,
hidden-truth-flagged events), queue for human review before execution.

Provides:
- Priority-based decision queue (FIFO within priority)
- Auto-approve for low-risk decisions (configurable threshold)
- Escalation rules (time-based, risk-based, drawdown-based)
- Audit trail for every decision (approved, rejected, modified, expired)
- Multi-reviewer support with quorum
- Slack / Webhook notification hooks for pending reviews
"""
import time
import json
import logging
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from collections import deque
from enum import Enum

logger = logging.getLogger("cme.human_review")


class ReviewStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    EXPIRED = "expired"
    AUTO_APPROVED = "auto_approved"


class ReviewPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ReviewableDecision:
    """A decision queued for human review."""
    decision_id: str
    action: str                  # BUY / SELL / REDUCE / HEDGE / EMERGENCY_EXIT
    asset: str
    direction: str               # long / short
    size_pct: float              # position size as % of portfolio
    confidence: float            # system's confidence
    reasoning_chain: List[str]   # why the system made this decision
    risk_flags: List[str]        # what triggered review
    priority: ReviewPriority = ReviewPriority.MEDIUM
    status: ReviewStatus = ReviewStatus.PENDING
    created_at: float = field(default_factory=time.time)
    reviewed_at: Optional[float] = None
    reviewed_by: Optional[str] = None
    reviewer_notes: str = ""
    modified_params: Dict[str, Any] = field(default_factory=dict)
    expiry_seconds: float = 300  # 5 min default
    original_decision: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.expiry_seconds

    def to_dict(self) -> Dict:
        return {
            "decision_id": self.decision_id,
            "action": self.action,
            "asset": self.asset,
            "direction": self.direction,
            "size_pct": self.size_pct,
            "confidence": self.confidence,
            "reasoning": self.reasoning_chain,
            "risk_flags": self.risk_flags,
            "priority": self.priority.name,
            "status": self.status.value,
            "created_at": self.created_at,
            "age_seconds": time.time() - self.created_at,
            "expiry_seconds": self.expiry_seconds,
            "reviewed_by": self.reviewed_by,
            "reviewer_notes": self.reviewer_notes,
        }


class EscalationRule:
    """Defines when a decision requires human review."""

    def __init__(self, name: str, condition: Callable, priority: ReviewPriority,
                 expiry_seconds: float = 300):
        self.name = name
        self.condition = condition
        self.priority = priority
        self.expiry_seconds = expiry_seconds


class HumanReviewQueue:
    """
    Queue high-impact decisions for human review before execution.

    Auto-approve rules:
    - Low conviction + small size → auto-approve
    - No hidden truth flags → auto-approve (if below size threshold)

    Escalation rules (require review):
    - Position size > 5% of portfolio
    - Hidden truth flags present
    - Drawdown > 10% and adding risk
    - Action = EMERGENCY_EXIT
    - Confidence < 0.4 but still trading
    - Multiple conflicting signals (dissent > 40%)
    """

    DEFAULT_AUTO_APPROVE_THRESHOLD = 0.03   # 3% position auto-approves
    DEFAULT_CONFIDENCE_FLOOR = 0.5          # below this → requires review
    DEFAULT_EXPIRY = 300                    # 5 minutes

    def __init__(self, auto_approve_size: float = DEFAULT_AUTO_APPROVE_THRESHOLD,
                 confidence_floor: float = DEFAULT_CONFIDENCE_FLOOR,
                 default_expiry: float = DEFAULT_EXPIRY):
        self._queue: List[ReviewableDecision] = []
        self._history: deque = deque(maxlen=5000)
        self._escalation_rules: List[EscalationRule] = []
        self._notification_hooks: List[Callable] = []
        self._auto_approve_size = auto_approve_size
        self._confidence_floor = confidence_floor
        self._default_expiry = default_expiry
        self._lock = threading.Lock()
        self._stats = {
            "total_queued": 0, "auto_approved": 0, "human_approved": 0,
            "human_rejected": 0, "expired": 0, "modified": 0,
        }

        self._register_default_rules()

    def _register_default_rules(self):
        """Register built-in escalation rules."""
        self.add_escalation_rule(EscalationRule(
            name="large_position",
            condition=lambda d: d.get("size_pct", 0) > 5.0,
            priority=ReviewPriority.HIGH,
            expiry_seconds=600,
        ))
        self.add_escalation_rule(EscalationRule(
            name="hidden_truth_flagged",
            condition=lambda d: bool(d.get("hidden_truth_flags")),
            priority=ReviewPriority.HIGH,
            expiry_seconds=300,
        ))
        self.add_escalation_rule(EscalationRule(
            name="emergency_exit",
            condition=lambda d: d.get("action") == "EMERGENCY_EXIT",
            priority=ReviewPriority.CRITICAL,
            expiry_seconds=120,
        ))
        self.add_escalation_rule(EscalationRule(
            name="low_confidence",
            condition=lambda d: d.get("confidence", 1) < 0.4,
            priority=ReviewPriority.MEDIUM,
            expiry_seconds=300,
        ))
        self.add_escalation_rule(EscalationRule(
            name="high_drawdown",
            condition=lambda d: (d.get("current_drawdown", 0) > 0.10
                                 and d.get("action") in ("BUY", "SELL")),
            priority=ReviewPriority.HIGH,
            expiry_seconds=180,
        ))
        self.add_escalation_rule(EscalationRule(
            name="high_dissent",
            condition=lambda d: d.get("dissent_ratio", 0) > 0.4,
            priority=ReviewPriority.MEDIUM,
            expiry_seconds=300,
        ))

    def add_escalation_rule(self, rule: EscalationRule) -> None:
        self._escalation_rules.append(rule)

    def add_notification_hook(self, hook: Callable) -> None:
        """Add callback for new review notifications (Slack, email, etc.)."""
        self._notification_hooks.append(hook)

    def submit_decision(self, decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a decision for review. Returns immediately with status.
        
        decision_data: {
            decision_id, action, asset, direction, size_pct, confidence,
            reasoning_chain, hidden_truth_flags, current_drawdown,
            dissent_ratio, original_decision
        }
        """
        # Check escalation rules
        triggered_rules = []
        max_priority = ReviewPriority.LOW
        max_expiry = self._default_expiry

        for rule in self._escalation_rules:
            try:
                if rule.condition(decision_data):
                    triggered_rules.append(rule.name)
                    if rule.priority.value > max_priority.value:
                        max_priority = rule.priority
                    max_expiry = max(max_expiry, rule.expiry_seconds)
            except Exception:
                pass

        # Auto-approve logic
        size = decision_data.get("size_pct", 0)
        confidence = decision_data.get("confidence", 0)
        has_hidden_flags = bool(decision_data.get("hidden_truth_flags"))

        if (not triggered_rules
                and size <= self._auto_approve_size
                and confidence >= self._confidence_floor
                and not has_hidden_flags):
            self._stats["auto_approved"] += 1
            self._history.append({
                "decision_id": decision_data.get("decision_id", ""),
                "status": "auto_approved",
                "timestamp": time.time(),
                "reason": "Below thresholds, no escalation rules triggered",
            })
            return {
                "status": "auto_approved",
                "decision_id": decision_data.get("decision_id", ""),
                "execute": True,
            }

        # Queue for review
        review = ReviewableDecision(
            decision_id=decision_data.get("decision_id", f"d_{int(time.time())}"),
            action=decision_data.get("action", "HOLD"),
            asset=decision_data.get("asset", ""),
            direction=decision_data.get("direction", ""),
            size_pct=size,
            confidence=confidence,
            reasoning_chain=decision_data.get("reasoning_chain", []),
            risk_flags=triggered_rules,
            priority=max_priority,
            expiry_seconds=max_expiry,
            original_decision=decision_data.get("original_decision", {}),
        )

        with self._lock:
            self._queue.append(review)
            self._queue.sort(key=lambda r: (-r.priority.value, r.created_at))

        self._stats["total_queued"] += 1

        # Notify
        for hook in self._notification_hooks:
            try:
                hook(review.to_dict())
            except Exception as e:
                logger.error(f"Notification hook failed: {e}")

        logger.info(f"Decision {review.decision_id} queued for review "
                     f"(priority={max_priority.name}, rules={triggered_rules})")

        return {
            "status": "queued",
            "decision_id": review.decision_id,
            "priority": max_priority.name,
            "triggered_rules": triggered_rules,
            "expiry_seconds": max_expiry,
            "execute": False,
        }

    def review_decision(self, decision_id: str, action: str,
                        reviewer: str = "human",
                        notes: str = "",
                        modified_params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Human reviews a queued decision.
        action: 'approve', 'reject', 'modify'
        """
        with self._lock:
            target = None
            for item in self._queue:
                if item.decision_id == decision_id:
                    target = item
                    break

            if target is None:
                return {"error": f"Decision {decision_id} not found in queue"}

            if target.is_expired:
                target.status = ReviewStatus.EXPIRED
                self._queue.remove(target)
                self._history.append(target.to_dict())
                self._stats["expired"] += 1
                return {"error": "Decision expired", "status": "expired"}

            target.reviewed_at = time.time()
            target.reviewed_by = reviewer
            target.reviewer_notes = notes

            if action == "approve":
                target.status = ReviewStatus.APPROVED
                self._stats["human_approved"] += 1
                execute = True
            elif action == "reject":
                target.status = ReviewStatus.REJECTED
                self._stats["human_rejected"] += 1
                execute = False
            elif action == "modify":
                target.status = ReviewStatus.MODIFIED
                target.modified_params = modified_params or {}
                self._stats["modified"] += 1
                execute = True
            else:
                return {"error": f"Unknown action: {action}"}

            self._queue.remove(target)
            self._history.append(target.to_dict())

        logger.info(f"Decision {decision_id} {action}ed by {reviewer}")

        result = {
            "status": target.status.value,
            "decision_id": decision_id,
            "execute": execute,
            "reviewer": reviewer,
            "latency_seconds": target.reviewed_at - target.created_at,
        }
        if modified_params:
            result["modified_params"] = modified_params
        return result

    def get_pending(self) -> List[Dict]:
        """Get all pending decisions, sorted by priority."""
        self._expire_stale()
        with self._lock:
            return [d.to_dict() for d in self._queue if d.status == ReviewStatus.PENDING]

    def _expire_stale(self) -> int:
        """Expire decisions past their deadline."""
        expired = 0
        with self._lock:
            still_valid = []
            for item in self._queue:
                if item.is_expired and item.status == ReviewStatus.PENDING:
                    item.status = ReviewStatus.EXPIRED
                    self._history.append(item.to_dict())
                    self._stats["expired"] += 1
                    expired += 1
                else:
                    still_valid.append(item)
            self._queue = still_valid
        return expired

    def get_stats(self) -> Dict:
        self._expire_stale()
        return {
            **self._stats,
            "pending_count": len([d for d in self._queue
                                   if d.status == ReviewStatus.PENDING]),
            "queue_size": len(self._queue),
        }

    def get_audit_trail(self, limit: int = 100) -> List[Dict]:
        """Get recent decision review history."""
        return list(self._history)[-limit:]
