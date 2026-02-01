import pandas as pd


DATA_PATH = "data"


def load_data():
    """
    Load all traceability datasets.
    """
    suppliers = pd.read_csv(f"{DATA_PATH}/suppliers.csv")
    raw_lots = pd.read_csv(f"{DATA_PATH}/raw_lots.csv")
    production_batches = pd.read_csv(f"{DATA_PATH}/production_batches.csv")
    finished_lots = pd.read_csv(f"{DATA_PATH}/finished_lots.csv")
    shipments = pd.read_csv(f"{DATA_PATH}/shipments.csv")

    return suppliers, raw_lots, production_batches, finished_lots, shipments


def trace_back(finished_lot_id: str):
    """
    Trace back from finished lot to raw material suppliers.
    """
    suppliers, raw_lots, production_batches, finished_lots, _ = load_data()

    # Finished lot → batch
    finished = finished_lots[finished_lots["finished_lot_id"] == finished_lot_id]
    if finished.empty:
        raise ValueError(f"Finished lot {finished_lot_id} not found")

    batch_id = finished.iloc[0]["batch_id"]

    # Batch → raw lots
    batch_links = production_batches[
        production_batches["batch_id"] == batch_id
    ]

    # Raw lots → suppliers
    raw_with_supplier = batch_links.merge(
        raw_lots, on="raw_lot_id", how="left"
    ).merge(
        suppliers, on="supplier_id", how="left"
    )

    return {
        "finished_lot_id": finished_lot_id,
        "batch_id": batch_id,
        "raw_materials": raw_with_supplier[
            ["raw_lot_id", "material", "supplier_name", "quantity_used"]
        ]
    }


def trace_forward(batch_id: str):
    """
    Trace forward from batch to customers and quantities.
    """
    _, _, _, finished_lots, shipments = load_data()

    # Batch → finished lots
    finished = finished_lots[finished_lots["batch_id"] == batch_id]
    if finished.empty:
        raise ValueError(f"Batch {batch_id} not found")

    # Finished lots → shipments
    shipped = finished.merge(
        shipments, on="finished_lot_id", how="left"
    )

    impacted_customers = (
        shipped.groupby("customer", dropna=False)["quantity"]
        .sum()
        .reset_index()
    )

    total_quantity = impacted_customers["quantity"].sum()

    return {
        "batch_id": batch_id,
        "customers": impacted_customers,
        "total_quantity": total_quantity
    }
