import pandas as pd


def _to_numeric_rate(rate_series: pd.Series) -> pd.Series:
    if rate_series.dtype == object:
        cleaned = rate_series.astype(str).str.replace("%", "", regex=False)
        return pd.to_numeric(cleaned, errors="coerce")
    return pd.to_numeric(rate_series, errors="coerce")


def run_governance(
    staged_path: str = "staged_loan_data.csv",
    validated_path: str = "validated_loans.csv",
    exceptions_path: str = "dq_exceptions.csv",
) -> pd.DataFrame:
    df = pd.read_csv(staged_path)

    exposure = pd.to_numeric(df.get("Exposure_Default"), errors="coerce")
    interest_rate = _to_numeric_rate(df.get("Interest_Rate"))
    account_status = df.get("Account_Status")

    completeness_fail = exposure.isna()
    accuracy_fail = (interest_rate > 30) | (exposure < 0)
    validity_fail = account_status.isna()

    error_reasons = []
    for i in range(len(df)):
        reasons = []
        if completeness_fail.iat[i]:
            reasons.append("Completeness: Exposure_Default is null")
        if accuracy_fail.iat[i]:
            reasons.append("Accuracy: Interest_Rate > 30 or Exposure_Default < 0")
        if validity_fail.iat[i]:
            reasons.append("Validity: Account_Status is null")
        error_reasons.append("; ".join(reasons))

    df["Error_Reason"] = error_reasons

    bad_mask = completeness_fail | accuracy_fail | validity_fail
    bad_rows = df[bad_mask].copy()
    clean_rows = df[~bad_mask].drop(columns=["Error_Reason"]).copy()

    clean_rows.to_csv(validated_path, index=False)
    bad_rows.to_csv(exceptions_path, index=False)

    total = len(df)
    clean_count = len(clean_rows)
    quality_score = (clean_count / total * 100) if total else 0
    print(f"Quality Score: {quality_score:.2f}% ({clean_count}/{total} clean rows)")

    return clean_rows


if __name__ == "__main__":
    run_governance()
