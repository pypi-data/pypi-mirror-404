import streamlit as st
import os
import tempfile
import shutil
try:
    from git_of_theseus.analyze import analyze
    from git_of_theseus.plotly_plots import plotly_stack_plot, plotly_line_plot, plotly_survival_plot, plotly_bar_plot
except ImportError:
    from analyze import analyze
    from plotly_plots import plotly_stack_plot, plotly_line_plot, plotly_survival_plot, plotly_bar_plot

st.set_page_config(page_title="Git of Theseus Dash", layout="wide")

# GitHub Link in Sidebar
st.sidebar.markdown(
    """
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" width="30" style="margin-right: 10px;">
        <a href="https://github.com/onewesong/better-git-of-theseus" target="_blank" style="text-decoration: none; color: inherit; font-weight: bold;">
            better-git-of-theseus
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

st.title("📊 Git of Theseus - Repository Analysis")

import sys

# Sidebar Configuration
st.sidebar.header("Configuration")

with st.sidebar.expander("📖 How to use", expanded=False):
    st.markdown("""
    **Better Git of Theseus** is a tool to analyze the evolution of Git repositories.
    
    ### Plots Explained:
    - **Stack Plot**: Shows code growth over time, broken down by cohort (when code was added).
    - **Line Plot**: Shows trends across different dimensions (Author, Extension, etc.).
    - **Distribution**: Shows the **current** distribution (Who contributed most, which file types are dominant).
    - **Survival Plot**: Estimates how long a line of code typically lasts before being modified or deleted.
    
    ### Tips:
    - **Cohort Format**: `%Y` (Yearly) and `%Y-%m` (Monthly) are recommended.
    - **Mailmap**: Use a `.mailmap` file in the repo root to resolve duplicate author names.
    """)

default_repo = "."
if len(sys.argv) > 1:
    default_repo = sys.argv[1]

repo_path = default_repo
# Path display removed as per user request

# Fetch branches for the selectbox
try:
    import git
    repo = git.Repo(repo_path)
    # Get local branches
    branches = [h.name for h in repo.heads]
    
    # Try to determine the best default branch (active one, or master/main)
    try:
        current_active = repo.active_branch.name
    except:
        current_active = "master"
        
    if current_active in branches:
        branches.remove(current_active)
    
    options = [current_active] + sorted(branches)
    branch = st.sidebar.selectbox("Branch", options=options)
except Exception as e:
    # Fallback if git repo access fails
    branch = st.sidebar.text_input("Branch", value="master")

with st.sidebar.expander("Analysis Parameters"):
    cohortfm = st.text_input(
        "Cohort Format", 
        value="%Y",
        help="Python strftime format string. Common options:\n\n"
             "- `%Y`: Year (e.g., 2023)\n"
             "- `%Y-%m`: Month (e.g., 2023-01)\n"
             "- `%Y-W%W`: Week (e.g., 2023-W01)\n"
             "- `%Y-%m-%d`: Day"
    )
    interval = st.number_input(
        "Analysis Interval (seconds)", 
        value=7 * 24 * 60 * 60,
        help="The time step between data points. Default is 604800s (7 days). Larger values are faster; smaller values result in smoother curves."
    )
    st.caption(f"Current resolution: {interval / 86400:.1f} days")
    
    procs = st.number_input(
        "Parallel Processes", 
        value=2, 
        min_value=1,
        help="Number of concurrent processes. Increase to speed up analysis on multi-core CPUs, but note it increases RAM usage."
    )
    ignore = st.text_area(
        "Ignore Patterns",
        help="Glob patterns to ignore (comma separated), e.g.: 'tests/**, *.md'"
    ).split(",")
    ignore = [i.strip() for i in ignore if i.strip()]

@st.cache_data(show_spinner=False)
def run_analysis(repo_path, branch, cohortfm, interval, procs, ignore):
    return analyze(
        repo_path,
        cohortfm=cohortfm,
        interval=interval,
        ignore=ignore,
        outdir=None,
        branch=branch,
        procs=procs,
        quiet=True
    )

# State management for analysis results
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

if st.sidebar.button("🚀 Run Analysis") or (len(sys.argv) > 1 and st.session_state.analysis_results is None):
    with st.spinner("Analyzing repository... this may take a while."):
        try:
            st.session_state.analysis_results = run_analysis(
                repo_path, branch, cohortfm, interval, procs, ignore
            )
            st.success("Analysis completed!")
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            st.session_state.analysis_results = None

# Main View
if st.session_state.analysis_results:
    results = st.session_state.analysis_results
    tab1, tab2, tab3, tab4 = st.tabs(["Stack Plot", "Line Plot", "Distribution", "Survival Plot"])

    with tab1:
        st.header("Stack Plot")
        col1, col2 = st.columns([1, 3])
        with col1:
            source_map = {
                "Cohorts": "cohorts",
                "Authors": "authors",
                "Extensions": "exts",
                "Directories": "dirs",
                "Domains": "domains"
            }
            data_source_label = st.selectbox("Data Source", list(source_map.keys()), key="stack_source")
            data_key = source_map[data_source_label]
            normalize = st.checkbox("Normalize to 100%", value=False, key="stack_norm")
            max_n = st.slider("Max Series", 5, 50, 20, key="stack_max_n")
        with col2:
            project_name = os.path.basename(os.path.abspath(repo_path))
            data = results.get(data_key)
            if data:
                fig = plotly_stack_plot(data, normalize=normalize, max_n=max_n, title=project_name)
                st.plotly_chart(fig, width="stretch")
            else:
                st.warning(f"Data for {data_source_label} not found.")

    with tab2:
        st.header("Line Plot")
        col1, col2 = st.columns([1, 3])
        with col1:
            data_source_label_line = st.selectbox("Data Source", list(source_map.keys()), key="line_source")
            data_key_line = source_map[data_source_label_line]
            normalize_line = st.checkbox("Normalize to 100%", value=False, key="line_norm")
            max_n_line = st.slider("Max Series", 5, 50, 20, key="line_max_n")
        with col2:
            project_name = os.path.basename(os.path.abspath(repo_path))
            data_line = results.get(data_key_line)
            if data_line:
                fig = plotly_line_plot(data_line, normalize=normalize_line, max_n=max_n_line, title=project_name)
                st.plotly_chart(fig, width="stretch")
            else:
                st.warning(f"Data for {data_source_label_line} not found.")

    with tab3:
        st.header("Latest Distribution")
        col1, col2 = st.columns([1, 3])
        with col1:
            data_source_label_bar = st.selectbox("Data Source", list(source_map.keys()), key="bar_source")
            data_key_bar = source_map[data_source_label_bar]
            max_n_bar = st.slider("Max Series", 5, 100, 30, key="bar_max_n")
        with col2:
            project_name = os.path.basename(os.path.abspath(repo_path))
            data_bar = results.get(data_key_bar)
            if data_bar:
                fig = plotly_bar_plot(data_bar, max_n=max_n_bar, title=f"{project_name} - {data_source_label_bar}")
                st.plotly_chart(fig, width="stretch")
            else:
                st.warning(f"Data for {data_source_label_bar} not found.")

    with tab4:
        st.header("Survival Plot")
        col1, col2 = st.columns([1, 3])
        with col1:
            exp_fit = st.checkbox("Exponential Fit", value=False)
            years = st.slider("Years", 1, 20, 5)
        with col2:
            project_name = os.path.basename(os.path.abspath(repo_path))
            survival_data = results.get("survival")
            if survival_data:
                fig = plotly_survival_plot(survival_data, exp_fit=exp_fit, years=years, title=project_name)
                st.plotly_chart(fig, width="stretch")
            else:
                st.warning("Survival data not found.")

else:
    st.info("👈 Enter a repository path and click 'Run Analysis' to get started.")
