import pandas as pd


def load_csv(path: str) -> pd.DataFrame:
    """
    Load a CSV file with conservative defaults.

    We avoid aggressive type coercion here to prevent
    hiding mixed-type or malformed columns.
    """
    try:
        df = pd.read_csv(
            path,
            dtype=str,
            keep_default_na=True,
            na_values=["", " ", "NA", "N/A", "null", "None"],
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to load CSV: {exc}") from exc

    return df
