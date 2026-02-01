import sys
from batch_traceability.recall import run_mock_recall, export_recall_report


def main():
    if len(sys.argv) != 2:
        print("Usage: mock-recall <FINISHED_LOT_ID>")
        sys.exit(1)

    finished_lot_id = sys.argv[1]

    report = run_mock_recall(finished_lot_id)
    export_recall_report(report)

    print("Mock recall completed")
    print(f"Batch: {report['batch_id']}")
    print(f"Impacted customers: {report['impacted_customers']}")
    print(f"Total quantity: {report['total_quantity']}")


if __name__ == "__main__":
    main()
