import pandas as pd
import plotly.express as px
import streamlit as st


def _to_numeric_rate(rate_series: pd.Series) -> pd.Series:
    if rate_series is None:
        return pd.Series(dtype=float)
    if rate_series.dtype == object:
        cleaned = rate_series.astype(str).str.replace("%", "", regex=False)
        return pd.to_numeric(cleaned, errors="coerce")
    return pd.to_numeric(rate_series, errors="coerce")


def _load_csv(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        return pd.DataFrame()


st.set_page_config(page_title="ReguCheck", layout="wide")
st.title("ReguCheck: Regulatory Risk Reporting System")
with st.expander("How to read this dashboard (plain-English guide)"):
    st.markdown(
        "- **Portfolio tab**: A quick read on portfolio size and pricing.\n"
        "  - **Total Exposure**: Sum of all loan balances (`Exposure_Default`).\n"
        "  - **Weighted Avg Rate**: Average interest rate, weighted by loan size.\n"
        "  - **Bar chart (Exposure by Risk Rating)**:\n"
        "    - **X-axis**: Risk ratings from **A (lowest risk)** to **G (highest "
        "risk)** — common credit grades used by lenders.\n"
        "    - **Y-axis**: Total exposure in dollars for each rating.\n"
        "    - **How to read it**: A taller bar means more of the portfolio sits "
        "in that risk grade.\n"
        "- **Data Quality tab**: Shows which records failed validation rules.\n"
        "  - **Data Failure Rate**: Percent of records that failed a rule.\n"
        "  - **Table columns**: Raw loan fields plus **Error_Reason**, which says "
        "whether a record failed completeness (missing), accuracy (out of range), "
        "or validity (missing status).\n"
        "- **Reconciliation tab**: Compares loan totals to a mock General Ledger "
        "(GL) used by Finance.\n"
        "  - **Source Exposure**: Total from the validated loan data.\n"
        "  - **GL Exposure**: Finance's recorded total for the same risk rating.\n"
        "  - **Variance** and **Variance_Pct**: Difference between Source and GL.\n"
        "  - **Status**: **Pass** if variance is within 1%; **Investigation "
        "Required** if above 1%."
    )

tab_portfolio, tab_quality, tab_recon = st.tabs(
    ["Portfolio", "Data Quality", "Reconciliation"]
)

with tab_portfolio:
    staged_df = _load_csv("staged_loan_data.csv")
    if staged_df.empty:
        st.info("No staged data found. Run `data_loader.py` first.")
    else:
        st.caption(
            "Interpretation: Higher exposure in a rating bucket means more "
            "portfolio concentration in that risk grade."
        )
        exposure = pd.to_numeric(
            staged_df.get("Exposure_Default"), errors="coerce"
        )
        rates = _to_numeric_rate(staged_df.get("Interest_Rate"))
        total_exposure = exposure.sum(skipna=True)
        weighted_avg_rate = (
            (exposure * rates).sum(skipna=True) / exposure.sum(skipna=True)
            if exposure.sum(skipna=True) else 0
        )

        col1, col2 = st.columns(2)
        col1.metric("Total Exposure", f"{total_exposure:,.2f}")
        col2.metric("Weighted Avg Rate", f"{weighted_avg_rate:.2f}%")

        exposure_by_rating = (
            staged_df.assign(Exposure_Default=exposure)
            .groupby("Risk_Rating")["Exposure_Default"]
            .sum()
            .reset_index()
        )

        fig = px.bar(
            exposure_by_rating,
            x="Risk_Rating",
            y="Exposure_Default",
            title="Exposure by Risk Rating",
        )
        st.plotly_chart(fig, use_container_width=True)

with tab_quality:
    dq_df = _load_csv("dq_exceptions.csv")
    validated_df = _load_csv("validated_loans.csv")

    total_rows = len(dq_df) + len(validated_df)
    failure_rate = (len(dq_df) / total_rows * 100) if total_rows else 0

    st.metric("Data Failure Rate", f"{failure_rate:.2f}%")
    if dq_df.empty:
        st.info("No data quality exceptions found. Run `governance_engine.py`.")
    else:
        st.caption(
            "Interpretation: Review Error_Reason to see which rule each row failed."
        )
        st.dataframe(dq_df, use_container_width=True)

with tab_recon:
    recon_df = _load_csv("recon_report.csv")
    if recon_df.empty:
        st.info("No reconciliation report found. Run `reconciliation.py`.")
    else:
        st.caption(
            "Interpretation: Red status indicates variance above the 1% threshold."
        )
        def highlight_investigation(val: str) -> str:
            return "color: red" if val == "Investigation Required" else ""

        styled = recon_df.style.applymap(
            highlight_investigation, subset=["Status"]
        )
        st.dataframe(styled, use_container_width=True)
