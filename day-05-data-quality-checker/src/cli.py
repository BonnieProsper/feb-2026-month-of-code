import sys
from loader import load_csv
from checks.structure import check_missing_required_columns


def main() -> int:
    csv_path = sys.argv[1]

    df = load_csv(csv_path)

    result = check_missing_required_columns(
        df,
        required_columns=["id", "email"]
    )

    print(result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
