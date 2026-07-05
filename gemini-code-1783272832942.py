import pandas as pd

# Let's inspect the unique departments in the 'Unit Head' file to make sure our script captures them accurately.
df_unit_head = pd.read_csv("Srikara Hospitals Dashboard.xlsx - Unit Head.csv")
print("Columns:", df_unit_head.columns.tolist())
print("Unique Departments raw:", df_unit_head['Department'].dropna().unique().tolist())

# Now let's write out a highly robust, clean, complete Streamlit app code to a file called `app.py`.
streamlit_code = """import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Srikara Hospitals - Unit Head Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a professional look
st.markdown(\"\"\"
    <style>
    .main-title { font-size: 2.2rem; color: #1e3a8a; font-weight: 700; margin-bottom: 5px; }
    .sub-title { font-size: 1.1rem; color: #4b5563; margin-bottom: 25px; }
    .section-header { font-size: 1.5rem; color: #1e3a8a; font-weight: 600; border-left: 5px solid #3b82f6; padding-left: 10px; margin-vertical: 20px; }
    .card-title { font-size: 1.1rem; font-weight: bold; color: #1f2937; margin-bottom: 10px; }
    </style>
\"\"\", unsafe_html=True)

# -----------------------------------------------------------------------------
# 2. DATA LOADING & PREPROCESSING
# -----------------------------------------------------------------------------
@st.cache_data(ttl=600)  # Cache data for 10 minutes
def load_dashboard_data():
    try:
        # Connect to live Google Sheet connection using Streamlit GSheets Connection
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Pull from the "Unit Head" worksheet
        df = conn.read(worksheet="Unit Head", ttl="10m")
    except Exception as e:
        st.sidebar.warning(f"Live Google Sheet connection not configured or failed. Using uploaded CSV structure.")
        # Fallback reading the structural format matching the 'Unit Head' file provided
        try:
            df = pd.read_csv("Srikara Hospitals Dashboard.xlsx - Unit Head.csv")
        except Exception:
            # Complete standalone programmatic fallback template in case file isn't present in directory
            fallback_data = {
                "Department": ["OP", "OP", "OP", "OP", "OP", "IP", "IP", "IP", "IP", "IP", "Billing", "Billing", "ER", "Radiology"],
                "Particulars": ["Total OP Footfall", "New Patients", "Follow-up Patients", "OP → Diagnostics Conversion %", "OP → Admission Conversion %", 
                                "Total IP Census", "Bed Occupancy %", "Admissions Today", "Discharges Today", "IP Revenue Today (₹)", 
                                "Pending Bills", "Total Revenue Billed (₹)", "ER Footfall Today", "Total Scans Done"],
                "Today": [70.0, 56.99, 81.6, 35.0, 5.0, 73.11, 65.0, 11.85, 11.25, 474075.0, 9.28, 740818.0, 25.0, 58.0],
                "MTD": [151.15, 57.16, 91.9, 38.0, 6.0, 83.82, 67.0, 12.56, 11.56, 478892.0, 10.0, 795051.0, 680.0, 980.0],
                "Target": [150.0, 60.0, 90.0, 40.0, 8.0, 80.0, 80.0, 12.0, 12.0, 500000.0, 10.0, 800000.0, 600.0, 900.0],
                "Last Month": [132.57, 51.78, 83.65, 41.0, 7.0, 71.46, 79.0, 10.72, 11.68, 463407.58, 9.01, 694476.93, 620.0, 850.0],
                "Projection": [162.64, 60.24, 97.4, 45.0, 9.0, 83.16, 87.0, 12.34, 12.46, 513904.08, 10.99, 873494.91, 710.0, 1020.0]
            }
            df = pd.DataFrame(fallback_data)
            
    # Rigorous Clean up
    df = df.dropna(subset=['Department', 'Particulars'])
    df['Department'] = df['Department'].astype(str).str.strip()
    df['Particulars'] = df['Particulars'].astype(str).str.strip()
    
    # Filter out empty spacer rows if any
    df = df[df['Department'] != '']
    
    # Convert numerical columns robustly
    numeric_cols = ['Today', 'MTD', 'Target', 'Last Month', 'Projection']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    return df

df_clean = load_dashboard_data()

# Extract list of departments safely
available_depts = [d for d in df_clean['Department'].unique() if d and d.lower() != 'nan']

# -----------------------------------------------------------------------------
# 3. SIDEBAR NAVIGATION
# -----------------------------------------------------------------------------
st.sidebar.image("https://img.icons8.com/color/96/hospital-buildings.png", width=80)
st.sidebar.title("Srikara Unit Analytics")
st.sidebar.markdown("---")

# Navigation options
nav_selection = st.sidebar.radio(
    "Select Dashboard Layer:",
    ["🌐 Cluster Dashboard (Overview)"] + [f"📊 {dept} Department" for dept in available_depts]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **GSheets Sync Info:** Data pulls directly via live connectivity parameters. Cache refreshes automatically.")

# -----------------------------------------------------------------------------
# 4. HELPER UTILITIES FOR VISUALIZATION
# -----------------------------------------------------------------------------
def format_metric_value(val, particulars):
    """Formats numeric elements neatly as currencies, percentages, or normal counts."""
    is_pct = "%" in particulars or "occupancy" in particulars.lower() or "conversion" in particulars.lower()
    is_curr = "₹" in particulars or "revenue" in particulars.lower() or "collection" in particulars.lower() or "billed" in particulars.lower()
    
    if is_pct:
        # If value is a small fraction (e.g. 0.82 for 82%), scale up appropriately if layout specifies
        if val <= 1.0 and val > 0:
            return f"{val * 100:.1f}%"
        return f"{val:.1f}%"
    elif is_curr:
        if val >= 100000:
            return f"₹ {val/100000:.2f} L"
        return f"₹ {val:,.2f}"
    else:
        return f"{val:,.1f}".rstrip('0').rstrip('.')

# -----------------------------------------------------------------------------
# 5. VIEW CONTROLLER
# -----------------------------------------------------------------------------

# --- A. MASTER CLUSTER DASHBOARD ---
if "Cluster Dashboard" in nav_selection:
    st.markdown('<div class="main-title">🌐 Srikara Hospitals - Executive Cluster Dashboard</div>', unsafe_html=True)
    st.markdown('<div class="sub-title">Multi-department operational summary matrix and aggregate metrics performance tracker.</div>', unsafe_html=True)
    
    # Dynamic KPI Cards at top of cluster overview
    st.markdown('<div class="section-header">🔑 Cross-Departmental Highlights (MTD)</div>', unsafe_html=True)
    kpi_cols = st.columns(min(len(available_depts), 5))
    
    for idx, dept in enumerate(available_depts[:5]):
        dept_subset = df_clean[df_clean['Department'] == dept]
        if not dept_subset.empty:
            # Grab the primary/first representative metric row for the department highlight card
            primary_row = dept_subset.iloc[0]
            val_str = format_metric_value(primary_row['MTD'], primary_row['Particulars'])
            tar_str = format_metric_value(primary_row['Target'], primary_row['Particulars'])
            
            with kpi_cols[idx]:
                st.metric(
                    label=f"{dept}: {primary_row['Particulars']}",
                    value=val_str,
                    delta=f"Target: {tar_str}",
                    delta_color="normal"
                )
                
    st.markdown("---")
    
    # Comparative Cross-Department Group Chart
    st.markdown('<div class="section-header">📊 Cross-Department Comparison Chart</div>', unsafe_html=True)
    metric_view = st.selectbox("Choose Performance Timeline Aspect to Compare Across Units:", ['Today', 'MTD', 'Target', 'Projection', 'Last Month'])
    
    # Filter to look at macro volumes (e.g. Total counts, Revenue, footprints) to avoid cluttered scale mismatch
    macro_df = df_clean[df_clean['Particulars'].str.contains("Total|Footfall|Census|Revenue|Billed|Scans", case=False, na=False)]
    
    if not macro_df.empty:
        fig_cluster = px.bar(
            macro_df,
            x="Department",
            y=metric_view,
            color="Particulars",
            barmode="group",
            title=f"Cross-Department Analysis Summary View: {metric_view}",
            labels={metric_view: "Value Summary Metrics"},
            template="plotly_white",
            height=500
        )
        st.plotly_chart(fig_cluster, use_container_width=True)
    
    # Comprehensive Master Sheet view
    st.markdown('<div class="section-header">📂 Aggregated Master Sheet Data</div>', unsafe_html=True)
    with st.expander("Click to view full tabular dataset"):
        st.dataframe(df_clean, use_container_width=True)

# --- B. INDIVIDUAL DEPARTMENT SUB-DASHBOARDS ---
else:
    # Filter exact active unit department name
    selected_dept = nav_selection.replace("📊 ", "").replace(" Department", "").strip()
    
    st.markdown(f'<div class="main-title">📊 {selected_dept} Department Operations Performance</div>', unsafe_html=True)
    st.markdown(f'<div class="sub-title">Detailed tracking dashboard metrics for operational segment: <b>{selected_dept}</b></div>', unsafe_html=True)
    
    df_dept = df_clean[df_clean['Department'] == selected_dept]
    
    if df_dept.empty:
        st.error(f"No records discovered for department: {selected_dept}")
    else:
        # Layout metrics in clear grids
        st.markdown('<div class="section-header">📋 Metric Highlights & Key Performance Targets</div>', unsafe_html=True)
        
        # Display each row metric as a clear grid row
        for idx, row in df_dept.iterrows():
            with st.expander(f"🔍 Metric Focus: {row['Particulars']}", expanded=True):
                col1, col2, col3, col4, col5 = st.columns(5)
                
                col1.metric("Today", format_metric_value(row['Today'], row['Particulars']))
                
                # Performance calculations
                mtd_val = row['MTD']
                target_val = row['Target']
                delta_num = mtd_val - target_val
                
                # Check formatting delta direction
                is_inverse = "pending" in row['Particulars'].lower() or "downtime" in row['Particulars'].lower() or "repeat" in row['Particulars'].lower()
                d_color = "inverse" if is_inverse else "normal"
                
                delta_lbl = f"{delta_num:+.1f}" if delta_num != 0 else "On Target"
                
                col2.metric("MTD Performance", format_metric_value(mtd_val, row['Particulars']), delta=f"{delta_lbl} vs Target", delta_color=d_color)
                col3.metric("Target Set", format_metric_value(target_val, row['Particulars']))
                col4.metric("Last Month", format_metric_value(row['Last Month'], row['Particulars']))
                col5.metric("End-Month Projection", format_metric_value(row['Projection'], row['Particulars']))
                
        # Timeline Bar Graph breakdown
        st.markdown(f'<div class="section-header">📈 Performance Matrix Trajectory - {selected_dept}</div>', unsafe_html=True)
        
        # Reshape data to fit beautiful comparison bars
        melted_dept = df_dept.melt(
            id_vars=['Particulars'],
            value_vars=['Last Month', 'Today', 'MTD', 'Target', 'Projection'],
            var_name='Timeline Timeline/Metric',
            value_name='Value'
        )
        
        fig_dept = px.bar(
            melted_dept,
            x='Particulars',
            y='Value',
            color='Timeline Timeline/Metric',
            barmode='group',
            title=f"Comparative Structural Metrics View for {selected_dept}",
            template="plotly_white",
            height=500
        )
        fig_dept.update_layout(xaxis_tickangle=-15)
        st.plotly_chart(fig_dept, use_container_width=True)
"""

with open("app.py", "w", encoding="utf-8") as f:
    f.write(streamlit_code)
print("File successfully unified into app.py")