import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy.exc import SQLAlchemyError

current_dir = os.path.dirname(os.path.abspath(__file__))

if os.path.exists(os.path.join(current_dir, "src")):
    src_path = os.path.join(current_dir, "src")
elif os.path.exists(os.path.join(os.path.dirname(current_dir), "src")):
    src_path = os.path.join(os.path.dirname(current_dir), "src")
else:
    src_path = os.path.join(current_dir, "src")

if src_path not in sys.path:
    sys.path.append(src_path)

try:
    from database import get_engine
except ImportError as e:
    st.error(
        f"Could not find database.py inside: `{src_path}`\n\n"
        f"Details: {e}"
    )
    st.stop()

st.set_page_config(
    page_title="Clinical Patient Segmentation Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_data(ttl=600)
def load_warehouse_data():
    try:
        engine = get_engine()
    except Exception as e:
        return None, None, f"Could not create a database connection: {e}"

    try:
        with engine.connect() as conn:
            profiles_df = pd.read_sql_table("cluster_profiles", con=conn)
    except SQLAlchemyError as e:
        return None, None, f"Could not read cluster_profiles: {e}"

    try:
        with engine.connect() as conn:
            query = """
                SELECT p.*, c.cluster_label
                FROM patients_clustered p
                LEFT JOIN cluster_profiles c ON p.cluster_id = c.cluster_id
            """
            patients_df = pd.read_sql_query(query, con=conn)
    except SQLAlchemyError as e:
        return None, None, f"Could not read patients_clustered: {e}"

    return profiles_df, patients_df, None


def safe_section(title):
    """Wraps a dashboard section so one broken chart doesn't take down the page."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except Exception as e:
                st.warning(f"'{title}' could not be displayed right now. ({e})")
        return wrapper
    return decorator


def has_columns(df, columns):
    return all(col in df.columns for col in columns)


profiles_df, patients_df, load_error = load_warehouse_data()

if load_error:
    st.error(f"⚠️ Database Connection Error: {load_error}")
    st.warning("Check that MySQL is running, `.env` values are correct, and `run_pipeline.py` has completed.")
    st.stop()

if profiles_df is None or patients_df is None or profiles_df.empty or patients_df.empty:
    st.warning("No data found in the database yet. Run `run_pipeline.py` first, then reload this page.")
    st.stop()

st.sidebar.header("🎛️ Filters")

if st.sidebar.button("🔄 Refresh data"):
    st.cache_data.clear()
    st.rerun()

filtered_patients = patients_df.copy()

if has_columns(patients_df, ["cluster_label"]):
    all_clusters = sorted(patients_df["cluster_label"].dropna().unique())
    selected_clusters = st.sidebar.multiselect("Patient segment", all_clusters, default=all_clusters)
    filtered_patients = filtered_patients[filtered_patients["cluster_label"].isin(selected_clusters)]

if has_columns(patients_df, ["gender"]):
    all_genders = sorted(patients_df["gender"].dropna().unique())
    selected_genders = st.sidebar.multiselect("Gender", all_genders, default=all_genders)
    filtered_patients = filtered_patients[filtered_patients["gender"].isin(selected_genders)]

if has_columns(patients_df, ["primary_condition"]):
    all_conditions = sorted(patients_df["primary_condition"].dropna().unique())
    selected_conditions = st.sidebar.multiselect("Primary condition", all_conditions, default=all_conditions)
    filtered_patients = filtered_patients[filtered_patients["primary_condition"].isin(selected_conditions)]

if has_columns(patients_df, ["insurance_type"]):
    all_insurance = sorted(patients_df["insurance_type"].dropna().unique())
    selected_insurance = st.sidebar.multiselect("Insurance type", all_insurance, default=all_insurance)
    filtered_patients = filtered_patients[filtered_patients["insurance_type"].isin(selected_insurance)]

if has_columns(patients_df, ["state"]):
    all_states = sorted(patients_df["state"].dropna().unique())
    selected_states = st.sidebar.multiselect("State", all_states, default=all_states)
    filtered_patients = filtered_patients[filtered_patients["state"].isin(selected_states)]

if has_columns(patients_df, ["age"]) and patients_df["age"].notna().any():
    age_min, age_max = int(patients_df["age"].min()), int(patients_df["age"].max())
    if age_min < age_max:
        selected_age = st.sidebar.slider("Age range", age_min, age_max, (age_min, age_max))
        filtered_patients = filtered_patients[filtered_patients["age"].between(*selected_age)]

if has_columns(patients_df, ["risk_score"]) and patients_df["risk_score"].notna().any():
    risk_min, risk_max = float(patients_df["risk_score"].min()), float(patients_df["risk_score"].max())
    if risk_min < risk_max:
        selected_risk = st.sidebar.slider("Risk score range", risk_min, risk_max, (risk_min, risk_max))
        filtered_patients = filtered_patients[filtered_patients["risk_score"].between(*selected_risk)]

st.title("🏥 Healthcare Patient Segmentation Dashboard")
st.caption(f"Showing {len(filtered_patients):,} of {len(patients_df):,} patients")
st.markdown("---")

kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    st.metric("Patients (filtered)", f"{len(filtered_patients):,}")

with kpi_col2:
    try:
        avg_risk = filtered_patients["risk_score"].mean()
        st.metric("Avg Risk Score", f"{avg_risk:.1f}" if pd.notna(avg_risk) else "N/A")
    except Exception:
        st.metric("Avg Risk Score", "N/A")

with kpi_col3:
    try:
        avg_billing = filtered_patients["avg_billing_amount"].mean()
        st.metric("Avg Billing", f"${avg_billing:,.0f}" if pd.notna(avg_billing) else "N/A")
    except Exception:
        st.metric("Avg Billing", "N/A")

with kpi_col4:
    try:
        active_segments = filtered_patients["cluster_id"].nunique()
        st.metric("Segments Shown", active_segments)
    except Exception:
        st.metric("Segments Shown", "N/A")

st.markdown("---")

tab_summary, tab_charts, tab_explorer = st.tabs([
    "📊 Segment Summary",
    "📈 Interactive Charts",
    "🔍 Patient Explorer"
])


with tab_summary:

    @safe_section("Segment summary table")
    def render_summary_table():
        st.subheader("Segment profiles")
        display_df = profiles_df.copy()
        format_map = {}
        for col, fmt in [
            ("avg_age", "{:.1f} yrs"), ("avg_bmi", "{:.1f}"), ("avg_risk_score", "{:.1f}"),
            ("segment_size_pct", "{:.1f}%"), ("avg_annual_visits", "{:.1f}"),
            ("avg_billing_amount", "${:,.0f}"), ("avg_days_since_last_visit", "{:.0f} days"),
        ]:
            if col in display_df.columns:
                format_map[col] = fmt
        st.dataframe(display_df.style.format(format_map), use_container_width=True, hide_index=True)

    render_summary_table()

    @safe_section("Recommendations")
    def render_recommendations():
        st.subheader("Recommendations by segment")
        for _, row in profiles_df.iterrows():
            label = row.get("cluster_label", f"Cluster {row.get('cluster_id', '?')}")
            condition = row.get("dominant_condition", "N/A")
            with st.expander(f"{label} — dominant condition: {condition}"):
                col_a, col_b = st.columns([1, 3])
                with col_a:
                    st.write(f"**Patients:** {row.get('patient_count', 'N/A')}")
                    st.write(f"**Top insurance:** {row.get('dominant_insurance_type', 'N/A')}")
                with col_b:
                    st.info(row.get("recommendation", "No recommendation available."))

    render_recommendations()


with tab_charts:

    if filtered_patients.empty:
        st.warning("No patients match the current filters.")
    else:
        chart_row1_col1, chart_row1_col2 = st.columns(2)

        with chart_row1_col1:
            @safe_section("Segment distribution")
            def render_segment_pie():
                st.markdown("**Segment distribution**")
                if has_columns(filtered_patients, ["cluster_label"]):
                    counts = filtered_patients["cluster_label"].value_counts().reset_index()
                    counts.columns = ["Segment", "Patients"]
                    fig = px.pie(counts, names="Segment", values="Patients", hole=0.4)
                    fig.update_traces(textinfo="percent+label")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("cluster_label column not available.")

            render_segment_pie()

        with chart_row1_col2:
            @safe_section("Risk vs billing")
            def render_risk_scatter():
                st.markdown("**Risk score vs. billing amount**")
                if has_columns(filtered_patients, ["risk_score", "avg_billing_amount"]):
                    fig = px.scatter(
                        filtered_patients,
                        x="risk_score",
                        y="avg_billing_amount",
                        color="cluster_label" if "cluster_label" in filtered_patients.columns else None,
                        hover_data=[c for c in ["patient_id", "age", "primary_condition"] if c in filtered_patients.columns],
                        opacity=0.6,
                    )
                    fig.update_layout(xaxis_title="Risk score", yaxis_title="Avg billing ($)")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Required columns not available.")

            render_risk_scatter()

        chart_row2_col1, chart_row2_col2 = st.columns(2)

        with chart_row2_col1:
            @safe_section("Age distribution")
            def render_age_histogram():
                st.markdown("**Age distribution by segment**")
                if has_columns(filtered_patients, ["age"]):
                    fig = px.histogram(
                        filtered_patients,
                        x="age",
                        color="cluster_label" if "cluster_label" in filtered_patients.columns else None,
                        nbins=20,
                        barmode="overlay",
                        opacity=0.7,
                    )
                    fig.update_layout(xaxis_title="Age", yaxis_title="Patients")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("age column not available.")

            render_age_histogram()

        with chart_row2_col2:
            @safe_section("Top states")
            def render_state_bar():
                st.markdown("**Top 10 states by patient count**")
                if has_columns(filtered_patients, ["state"]):
                    top_states = filtered_patients["state"].value_counts().head(10).index
                    subset = filtered_patients[filtered_patients["state"].isin(top_states)]
                    group_cols = ["state"] + (["cluster_label"] if "cluster_label" in subset.columns else [])
                    counts = subset.groupby(group_cols).size().reset_index(name="Patients")
                    fig = px.bar(
                        counts,
                        x="state",
                        y="Patients",
                        color="cluster_label" if "cluster_label" in counts.columns else None,
                        barmode="stack",
                    )
                    fig.update_layout(xaxis_title="State", yaxis_title="Patients")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("state column not available.")

            render_state_bar()


with tab_explorer:

    @safe_section("Patient explorer")
    def render_explorer():
        st.subheader("Search patients")
        search_id = st.text_input("Filter by Patient ID", "").strip()

        if search_id and "patient_id" in filtered_patients.columns:
            explorer_df = filtered_patients[
                filtered_patients["patient_id"].astype(str).str.contains(search_id, case=False, na=False)
            ]
        else:
            explorer_df = filtered_patients

        display_columns = [
            "patient_id", "cluster_label", "age", "gender", "primary_condition",
            "risk_score", "num_chronic_conditions", "annual_visits", "avg_billing_amount",
            "days_since_last_visit", "insurance_type", "state"
        ]
        available_cols = [c for c in display_columns if c in explorer_df.columns]

        st.dataframe(explorer_df[available_cols], use_container_width=True, hide_index=True)

        if len(explorer_df) == 1:
            row = explorer_df.iloc[0]
            st.markdown("### Patient detail")
            detail_col1, detail_col2, detail_col3 = st.columns(3)
            with detail_col1:
                st.write(f"**ID:** {row.get('patient_id', 'N/A')}")
                st.write(f"**Age:** {row.get('age', 'N/A')}")
                st.write(f"**Gender:** {row.get('gender', 'N/A')}")
            with detail_col2:
                st.write(f"**Segment:** {row.get('cluster_label', 'N/A')}")
                st.write(f"**Risk score:** {row.get('risk_score', 'N/A')}")
                st.write(f"**Condition:** {row.get('primary_condition', 'N/A')}")
            with detail_col3:
                st.write(f"**Insurance:** {row.get('insurance_type', 'N/A')}")
                st.write(f"**Annual visits:** {row.get('annual_visits', 'N/A')}")
                st.write(f"**Avg billing:** ${row.get('avg_billing_amount', 0):,.2f}")

        if not explorer_df.empty:
            csv_data = explorer_df[available_cols].to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Export filtered patients (CSV)",
                data=csv_data,
                file_name="segmented_patient_export.csv",
                mime="text/csv",
            )

    render_explorer()

st.markdown("---")
st.caption("Healthcare Patient Segmentation Dashboard")