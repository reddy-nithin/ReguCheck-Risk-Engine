import kagglehub
import pandas as pd
import os


def _find_csv_file(folder_path: str) -> str:
    csv_files = []
    for root, _, files in os.walk(folder_path):
        for file_name in files:
            if file_name.lower().endswith(".csv"):
                full_path = os.path.join(root, file_name)
                size = os.path.getsize(full_path)
                csv_files.append((size, full_path))
    if not csv_files:
        raise FileNotFoundError("No CSV files found in the downloaded dataset.")
    csv_files.sort(reverse=True)
    return csv_files[0][1]


def _select_usecols(csv_path: str) -> list[str] | None:
    desired_cols = [
        "loan_amnt",
        "int_rate",
        "grade",
        "loan_status",
        "term",
        "installment",
        "funded_amnt",
        "funded_amnt_inv",
        "sub_grade",
        "emp_title",
        "id",
        "member_id",
    ]
    try:
        header = pd.read_csv(csv_path, nrows=0)
    except Exception:
        return None
    available = [col for col in desired_cols if col in header.columns]
    return available or None


def _read_and_sample_csv(
    csv_path: str, sample_size: int = 10000, random_state: int = 42
) -> pd.DataFrame:
    usecols = _select_usecols(csv_path)
    chunks = pd.read_csv(
        csv_path, chunksize=50000, usecols=usecols, low_memory=False
    )
    sampled_chunks = []
    total_rows = 0

    for chunk in chunks:
        total_rows += len(chunk)
        if total_rows <= sample_size:
            sampled_chunks.append(chunk)
            continue

        keep_frac = sample_size / total_rows
        sampled_chunks.append(
            chunk.sample(frac=keep_frac, random_state=random_state)
        )
        combined = pd.concat(sampled_chunks, ignore_index=True)
        if len(combined) > sample_size:
            combined = combined.sample(n=sample_size, random_state=random_state)
        sampled_chunks = [combined]

    if not sampled_chunks:
        return pd.DataFrame()

    return pd.concat(sampled_chunks, ignore_index=True)


def load_and_stage(output_path: str = "staged_loan_data.csv") -> pd.DataFrame:
    # Download latest version
    path = kagglehub.dataset_download("adarshsng/lending-club-loan-data-csv")
    print("Path to dataset files:", path)

    csv_path = _find_csv_file(path)
    df = _read_and_sample_csv(csv_path, sample_size=10000, random_state=42)

    df = df.rename(
        columns={
            "loan_amnt": "Exposure_Default",
            "int_rate": "Interest_Rate",
            "grade": "Risk_Rating",
            "loan_status": "Account_Status",
        }
    )

    df.to_csv(output_path, index=False)
    print(f"Staged data saved to {output_path} with {len(df)} rows.")
    return df


if __name__ == "__main__":
    load_and_stage()
