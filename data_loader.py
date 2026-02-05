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


def load_and_stage(output_path: str = "staged_loan_data.csv") -> pd.DataFrame:
    # Download latest version
    path = kagglehub.dataset_download("adarshsng/lending-club-loan-data-csv")
    print("Path to dataset files:", path)

    csv_path = _find_csv_file(path)
    df = pd.read_csv(csv_path)

    if len(df) > 10000:
        df = df.sample(n=10000, random_state=42)

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
