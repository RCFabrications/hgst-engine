"""
HGST-Guard: Enterprise AI Agent Governance Middleware & REST Server.
Provides Goal Contracts, Uncertainty Ledgers, and LIFO Rollback Endpoints.
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time

from hgst.governance_engine import (
    GoalContract,
    UncertaintyLedger,
    AssumptionEntry,
    ClosedLoopGovernanceEngine,
    ExecutionAction,
    FeasibilityStatus,
    ExecutionStatus
)

app = FastAPI(
    title="HGST-Guard Enterprise Governance API",
    version="1.0.0",
    description="Deterministic Decision Gating, Uncertainty Ledger & Rollback Stack"
)

class GoalContractModel(BaseModel):
    objective: str
    owner: str
    target_metric: str
    target_value: float
    budget_ceiling: float
    deadline_seconds_from_now: float
    safety_constraints: List[str]
    privacy_constraints: List[str]
    stop_conditions: List[str]

class AssumptionModel(BaseModel):
    claim: str
    evidence_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    impact_if_invalid: str
    verification_method: str
    verified: bool = False

class FeasibilityRequest(BaseModel):
    contract: GoalContractModel
    assumptions: List[AssumptionModel]
    estimated_cost: float
    estimated_value: float

class ActionModel(BaseModel):
    action_id: str
    name: str
    blast_radius: str
    is_high_consequence: bool

class ExecutionPipelineRequest(BaseModel):
    contract: GoalContractModel
    assumptions: List[AssumptionModel]
    actions: List[ActionModel]
    human_approval_override: bool = False

@app.get("/health")
def health_check():
    return {"status": "healthy", "engine": "HGST-Sovereign-v1.0"}

@app.post("/v1/governance/assess-feasibility")
def assess_feasibility(req: FeasibilityRequest):
    gc = GoalContract(
        objective=req.contract.objective,
        owner=req.contract.owner,
        target_metric=req.contract.target_metric,
        target_value=req.contract.target_value,
        budget_ceiling=req.contract.budget_ceiling,
        deadline_epoch=time.time() + req.contract.deadline_seconds_from_now,
        safety_constraints=req.contract.safety_constraints,
        privacy_constraints=req.contract.privacy_constraints,
        stop_conditions=req.contract.stop_conditions
    )
    ledger = UncertaintyLedger()
    for a in req.assumptions:
        ledger.register(AssumptionEntry(
            claim=a.claim,
            evidence_type=a.evidence_type,
            confidence=a.confidence,
            impact_if_invalid=a.impact_if_invalid,
            verification_method=a.verification_method,
            verified=a.verified
        ))
    
    engine = ClosedLoopGovernanceEngine(gc, ledger)
    status = engine.assess_feasibility(req.estimated_cost, req.estimated_value)
    
    return {
        "status": status.value,
        "mean_confidence": ledger.mean_confidence(),
        "unverified_critical_risks": [r.claim for r in ledger.critical_unverified_risks(threshold=0.6)],
        "audit_event": engine.audit_log[-1] if engine.audit_log else None
    }

@app.post("/v1/governance/execute-pipeline")
def execute_pipeline(req: ExecutionPipelineRequest):
    gc = GoalContract(
        objective=req.contract.objective,
        owner=req.contract.owner,
        target_metric=req.contract.target_metric,
        target_value=req.contract.target_value,
        budget_ceiling=req.contract.budget_ceiling,
        deadline_epoch=time.time() + req.contract.deadline_seconds_from_now,
        safety_constraints=req.contract.safety_constraints,
        privacy_constraints=req.contract.privacy_constraints,
        stop_conditions=req.contract.stop_conditions
    )
    ledger = UncertaintyLedger()
    for a in req.assumptions:
        ledger.register(AssumptionEntry(
            claim=a.claim,
            evidence_type=a.evidence_type,
            confidence=a.confidence,
            impact_if_invalid=a.impact_if_invalid,
            verification_method=a.verification_method,
            verified=a.verified
        ))
    
    engine = ClosedLoopGovernanceEngine(gc, ledger)
    
    pipeline_actions = []
    for act in req.actions:
        pipeline_actions.append(ExecutionAction(
            action_id=act.action_id,
            name=act.name,
            forward_fn=lambda: True,
            rollback_fn=lambda: True,
            blast_radius=act.blast_radius,
            is_high_consequence=act.is_high_consequence
        ))
        
    exec_status = engine.execute_pipeline(pipeline_actions, human_approval_override=req.human_approval_override)
    
    return {
        "execution_status": exec_status.value,
        "audit_trail_events": len(engine.audit_log),
        "audit_log": engine.audit_log
    }

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
