from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.app.database import get_db
from backend.app.models.schema import ExperimentResult, FailureTestCase
from scripts.run_experiment import run_complete_experiment_suite
from scripts.run_leakage_tests import run_synthetic_leakage_tests

router = APIRouter(prefix="/api/experiments", tags=["Experiments & Baseline Metrics"])

@router.get("/results")
def get_experiment_results(db: Session = Depends(get_db)):
    """Returns baseline vs proposed metrics and failure edge cases test report."""
    results = db.query(ExperimentResult).all()

    if not results:
        # Trigger fresh run if table is empty
        run_complete_experiment_suite()
        results = db.query(ExperimentResult).all()

    test_cases = db.query(FailureTestCase).all()

    return {
        "metrics": [
            {
                "id": r.id,
                "metric_name": r.metric_name,
                "baseline_value": r.baseline_value,
                "target_value": r.target_value,
                "proposed_value": r.proposed_value,
                "unit": r.unit,
                "status": r.status
            } for r in results
        ],
        "failure_test_cases": [
            {
                "test_id": tc.test_id,
                "scenario": tc.scenario,
                "expected_result": tc.expected_result,
                "actual_result": tc.actual_result,
                "failure_reason": tc.failure_reason,
                "corrective_action": tc.corrective_action,
                "status": tc.status
            } for tc in test_cases
        ]
    }

@router.post("/run-suite")
def trigger_experiment_suite(db: Session = Depends(get_db)):
    """Triggers complete execution of experiment suite and synthetic leakage tests."""
    payload = run_complete_experiment_suite()
    return {
        "success": True,
        "message": "Experiment suite completed successfully.",
        "payload": payload
    }

@router.post("/run-leakage-test")
def trigger_leakage_tests(db: Session = Depends(get_db)):
    """Runs automated synthetic leakage test."""
    res = run_synthetic_leakage_tests()
    return res
