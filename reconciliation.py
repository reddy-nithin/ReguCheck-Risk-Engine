import pandas as pd


def _build_mock_gl_totals(exposure_by_rating: pd.Series) -> dict:
    mock_gl = {}
    for idx, (rating, total) in enumerate(exposure_by_rating.items()):
        factor = 1.005 if idx % 2 == 0 else 0.995
        mock_gl[rating] = round(total * factor, 2)
    return mock_gl


def run_reconciliation(
    validated_path: str = "validated_loans.csv",
    output_path: str = "recon_report.csv",
) -> pd.DataFrame:
    df = pd.read_csv(validated_path)
    df["Exposure_Default"] = pd.to_numeric(df.get("Exposure_Default"), errors="coerce")

    exposure_by_rating = (
        df.groupby("Risk_Rating")["Exposure_Default"].sum().sort_index()
    )

    mock_gl = _build_mock_gl_totals(exposure_by_rating)

    rows = []
    for rating, source_total in exposure_by_rating.items():
        gl_total = mock_gl.get(rating, 0)
        variance = source_total - gl_total
        pct_variance = (variance / gl_total * 100) if gl_total else 0
        status = (
            "Investigation Required" if abs(pct_variance) > 1 else "Pass"
        )
        rows.append(
            {
                "Risk_Rating": rating,
                "Source_Exposure": round(source_total, 2),
                "GL_Exposure": round(gl_total, 2),
                "Variance": round(variance, 2),
                "Variance_Pct": round(pct_variance, 2),
                "Status": status,
            }
        )

    report_df = pd.DataFrame(rows)
    report_df.to_csv(output_path, index=False)
    print(f"Reconciliation report saved to {output_path}")
    return report_df


if __name__ == "__main__":
    run_reconciliation()
