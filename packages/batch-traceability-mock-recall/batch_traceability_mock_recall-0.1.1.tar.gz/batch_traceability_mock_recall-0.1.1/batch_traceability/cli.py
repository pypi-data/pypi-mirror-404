import argparse
from batch_traceability.recall import run_mock_recall


def main():
    parser = argparse.ArgumentParser(
        description="Mock recall simulation (one step back / one step forward)"
    )

    parser.add_argument(
        "finished_lot_id",
        help="Finished product lot ID to recall (e.g. FG-LOT-001)"
    )

    args = parser.parse_args()

    report = run_mock_recall(args.finished_lot_id)

    print("\n=== MOCK RECALL REPORT ===")
    print(f"Finished lot: {args.finished_lot_id}")
    print(f"Suppliers involved: {report['suppliers']}")
    print(f"Customers impacted: {report['customers']}")
    print(f"Total quantity recalled: {report['total_quantity']}")
