import time
import pandas as pd
from batch_traceability.traceability import trace_back, trace_forward

def run_mock_recall(finished_lot_id: str):
    """
    Run a complete mock recall starting from a finished lot.
    """

    start_time = time.time()

    # Trace back
    back_result = trace_back(finished_lot_id)
    batch_id = back_result["batch_id"]

    # Trace forward
    forward_result = trace_forward(batch_id)

    end_time = time.time()

    # KPI calculations
    recall_time_seconds = round(end_time - start_time, 3)
    impacted_customers = len(forward_result["customers"])
    total_quantity = forward_result["total_quantity"]

    recall_report = {
        "finished_lot_id": finished_lot_id,
        "batch_id": batch_id,
        "recall_time_seconds": recall_time_seconds,
        "impacted_customers": impacted_customers,
        "total_quantity": total_quantity,
        "raw_materials": back_result["raw_materials"],
        "customer_impact": forward_result["customers"]
    }

    return recall_report


def export_recall_report(recall_report: dict):
    """
    Export recall results to CSV files.
    """

    summary = pd.DataFrame([{
        "finished_lot_id": recall_report["finished_lot_id"],
        "batch_id": recall_report["batch_id"],
        "recall_time_seconds": recall_report["recall_time_seconds"],
        "impacted_customers": recall_report["impacted_customers"],
        "total_quantity": recall_report["total_quantity"]
    }])

    raw_materials = recall_report["raw_materials"]
    customer_impact = recall_report["customer_impact"]

    summary.to_csv("output/recall_summary.csv", index=False)
    raw_materials.to_csv("output/recall_raw_materials.csv", index=False)
    customer_impact.to_csv("output/recall_customers.csv", index=False)
