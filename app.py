import streamlit as st

from src.parsers import parse_file
from src.preprocessor import clean_text
from src.embeddings import compute_similarity
from src.skills import load_taxonomy, extract_skills, analyze_gap
from src.ui_components import (
    render_score_card,
    render_radar_chart,
    render_category_breakdown,
    render_skills_tags,
)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AI Resume Screener",
    page_icon=":page_facing_up:",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    .block-container { max-width: 1100px; }
    h1 { text-align: center; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 8px 8px 0 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("AI Resume Screener")
st.caption(
    "Upload a resume and paste a job description to get an instant match score "
    "and a detailed skills gap analysis."
)
st.divider()

# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------

col_resume, col_job = st.columns(2, gap="large")

with col_resume:
    st.subheader("Resume")
    uploaded_file = st.file_uploader(
        "Upload your resume",
        type=["pdf", "docx", "txt"],
        help="Supported formats: PDF, DOCX, TXT",
    )

with col_job:
    st.subheader("Job Description")
    job_description = st.text_area(
        "Paste the job description here",
        height=250,
        placeholder="e.g. We are looking for a Senior Python Developer with experience in ...",
    )

# ---------------------------------------------------------------------------
# Analyze button
# ---------------------------------------------------------------------------

analyze = st.button("Analyze Match", type="primary", use_container_width=True)

if analyze:
    # -- Validate inputs ---------------------------------------------------
    if not uploaded_file:
        st.error("Please upload a resume file.")
        st.stop()
    if not job_description or not job_description.strip():
        st.error("Please enter a job description.")
        st.stop()

    # -- Parse resume ------------------------------------------------------
    with st.spinner("Parsing resume..."):
        try:
            resume_text = parse_file(uploaded_file)
        except ValueError as exc:
            st.error(str(exc))
            st.stop()
        except Exception:
            st.error("Failed to parse the uploaded file. Please check the format and try again.")
            st.stop()

    # -- Preprocess --------------------------------------------------------
    resume_clean = clean_text(resume_text)
    job_clean = clean_text(job_description)

    # -- Semantic similarity -----------------------------------------------
    with st.spinner("Computing semantic similarity..."):
        similarity_score = compute_similarity(resume_clean, job_clean)

    # -- Skills extraction & gap analysis ----------------------------------
    with st.spinner("Extracting skills and analyzing gaps..."):
        taxonomy = load_taxonomy()
        resume_skills = extract_skills(resume_clean, taxonomy)
        job_skills = extract_skills(job_clean, taxonomy)
        gap = analyze_gap(resume_skills, job_skills)

    # -- Compute combined score --------------------------------------------
    skills_score = gap["overall"]["score"]
    combined_score = round(similarity_score * 0.6 + skills_score * 0.4, 1)

    # ======================================================================
    # Results
    # ======================================================================
    st.divider()
    st.header("Results")

    # -- Top-level scores --------------------------------------------------
    score_cols = st.columns(3)
    with score_cols[0]:
        render_score_card("Overall Match", combined_score)
    with score_cols[1]:
        render_score_card("Semantic Similarity", similarity_score)
    with score_cols[2]:
        render_score_card("Skills Match", skills_score)

    st.divider()

    # -- Radar chart + summary side by side --------------------------------
    chart_col, summary_col = st.columns([3, 2], gap="large")

    with chart_col:
        st.subheader("Category Scores")
        cat_scores = {
            cat: data["score"]
            for cat, data in gap["categories"].items()
            if data["score"] is not None and data["job_count"] > 0
        }
        if cat_scores:
            render_radar_chart(cat_scores)
        else:
            st.info("No category scores to display.")

    with summary_col:
        st.subheader("Quick Summary")
        overall = gap["overall"]
        st.metric("Skills Matched", f"{overall['matched']} / {overall['job_required']}")
        st.metric("Skills Missing", overall["missing"])
        st.metric("Extra Skills", overall["extra"])

        if overall["missing"] == 0 and overall["job_required"] > 0:
            st.success("The resume covers all required skills!")
        elif overall["job_required"] > 0:
            pct = round(overall["matched"] / overall["job_required"] * 100, 1)
            if pct >= 70:
                st.success(f"Strong skill match at {pct}%.")
            elif pct >= 40:
                st.warning(f"Partial skill match at {pct}%. Consider addressing the gaps.")
            else:
                st.error(f"Weak skill match at {pct}%. Significant gaps exist.")

    st.divider()

    # -- Detailed category breakdown ---------------------------------------
    st.subheader("Skills Gap Analysis by Category")
    render_category_breakdown(gap)

    # -- All skills flat view (collapsed by default) -----------------------
    with st.expander("View all extracted skills"):
        all_matched = []
        all_missing = []
        all_extra = []
        for cat_data in gap["categories"].values():
            all_matched.extend(cat_data["matched"])
            all_missing.extend(cat_data["missing"])
            all_extra.extend(cat_data["extra"])
        render_skills_tags(sorted(all_matched), sorted(all_missing), sorted(all_extra))
