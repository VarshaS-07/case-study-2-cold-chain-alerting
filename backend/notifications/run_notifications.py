
import argparse

from backend.notifications.manager import (
    prepare_notifications,
    process_notifications,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send real emails through SMTP",
    )
    parser.add_argument(
        "--confirm-historical-send",
        action="store_true",
        help="Explicitly permit sending alerts from historical data",
    )

    args = parser.parse_args()

    if args.send and not args.confirm_historical_send:
        parser.error(
            "Historical replay emails require "
            "--confirm-historical-send"
        )

    created = prepare_notifications()
    results = process_notifications(send=args.send)

    print(f"New notification records: {created}")
    print(f"Notifications processed: {len(results)}")

    for result in results:
        print(
            result["truck_id"],
            result["status"],
            result["recipient"],
        )


if __name__ == "__main__":
    main()
