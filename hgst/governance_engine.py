from __future__ import annotations
import dataclasses
from enum import Enum
import time
from typing import Any, Callable, Dict, List, Optional

class FeasibilityStatus(Enum):
    FEASIBLE = "feasible"
    RESEARCH_NEEDED = "research_needed"
    INFEASIBLE = "infeasible"

class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclasses.dataclass
class GoalContract:
    objective: str
    owner: str
    target_metric: str
    target_value: float
    budget_ceiling: float
    deadline_epoch: float
    safety_constraints: List[str]
    privacy_constraints: List[str]
    stop_conditions: List[str]

    def validate_preconditions(self) -> bool:
        if not self.objective or not self.owner:
            return False
        if self.budget_ceiling <= 0 or self.deadline_epoch <= time.time():
            return False
        return len(self.safety_constraints) > 0 and len(self.stop_conditions) > 0

@dataclasses.dataclass
class AssumptionEntry:
    claim: str
    evidence_type: str
    confidence: float
    impact_if_invalid: str
    verification_method: str
    verified: bool = False

class UncertaintyLedger:
    def __init__(self) -> None:
        self.assumptions: List[AssumptionEntry] = []

    def register(self, entry: AssumptionEntry) -> None:
        self.assumptions.append(entry)

    def mean_confidence(self) -> float:
        if not self.assumptions:
            return 1.0
        return sum(a.confidence for a in self.assumptions) / len(self.assumptions)

    def critical_unverified_risks(self, threshold: float = 0.7) -> List[AssumptionEntry]:
        return [a for a in self.assumptions if not a.verified and a.confidence < threshold]

@dataclasses.dataclass
class ExecutionAction:
    action_id: str
    name: str
    forward_fn: Callable[[], bool]
    rollback_fn: Callable[[], bool]
    blast_radius: str
    is_high_consequence: bool

class ClosedLoopGovernanceEngine:
    def __init__(self, contract: GoalContract, ledger: UncertaintyLedger) -> None:
        self.contract = contract
        self.ledger = ledger
        self.audit_log: List[Dict[str, Any]] = []
        self.executed_stack: List[ExecutionAction] = []

    def log(self, event: str, payload: Dict[str, Any]) -> None:
        entry = {
            "timestamp": time.time(),
            "event": event,
            "payload": payload
        }
        self.audit_log.append(entry)

    def assess_feasibility(self, estimated_cost: float, estimated_value: float) -> FeasibilityStatus:
        if not self.contract.validate_preconditions():
            self.log("FEASIBILITY_REJECTED", {"reason": "Contract precondition validation failure"})
            return FeasibilityStatus.INFEASIBLE

        unverified = self.ledger.critical_unverified_risks(threshold=0.6)
        if len(unverified) > 0:
            self.log("FEASIBILITY_STAGED", {"unverified_risks": [u.claim for u in unverified]})
            return FeasibilityStatus.RESEARCH_NEEDED

        if estimated_cost > self.contract.budget_ceiling:
            self.log("FEASIBILITY_REJECTED", {"reason": "Budget ceiling exceeded"})
            return FeasibilityStatus.INFEASIBLE

        self.log("FEASIBILITY_APPROVED", {"estimated_value": estimated_value, "cost": estimated_cost})
        return FeasibilityStatus.FEASIBLE

    def execute_pipeline(self, pipeline: List[ExecutionAction], human_approval_override: bool = False) -> ExecutionStatus:
        for action in pipeline:
            if action.is_high_consequence and not human_approval_override:
                self.log("GATE_DENIED", {
                    "action_id": action.action_id,
                    "reason": "High-consequence action requires explicit human approval"
                })
                self.rollback_all()
                return ExecutionStatus.FAILED

            self.log("ACTION_ATTEMPT", {"action_id": action.action_id, "blast_radius": action.blast_radius})
            try:
                success = action.forward_fn()
                if success:
                    self.executed_stack.append(action)
                    self.log("ACTION_SUCCESS", {"action_id": action.action_id})
                else:
                    self.log("ACTION_FAILURE", {"action_id": action.action_id})
                    self.rollback_all()
                    return ExecutionStatus.FAILED
            except Exception as exc:
                self.log("ACTION_EXCEPTION", {"action_id": action.action_id, "error": str(exc)})
                self.rollback_all()
                return ExecutionStatus.FAILED

        return ExecutionStatus.COMPLETED

    def rollback_all(self) -> None:
        self.log("ROLLBACK_INITIATED", {"stack_depth": len(self.executed_stack)})
        while self.executed_stack:
            action = self.executed_stack.pop()
            try:
                rb_success = action.rollback_fn()
                self.log("ROLLBACK_STEP", {"action_id": action.action_id, "success": rb_success})
            except Exception as exc:
                self.log("ROLLBACK_ERROR", {"action_id": action.action_id, "error": str(exc)})
