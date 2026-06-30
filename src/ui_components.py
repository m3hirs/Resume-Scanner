import streamlit as st
import plotly.graph_objects as go


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------

def _score_color(score: float) -> str:
    if score >= 70:
        return "#28a745"
    if score >= 40:
        return "#ffc107"
    return "#dc3545"


# ---------------------------------------------------------------------------
# Overall score card
# ---------------------------------------------------------------------------

def render_score_card(label: str, score: float):
    """Render a large metric card with a colored progress bar."""
    color = _score_color(score)
    st.markdown(
        f"""
        <div style="text-align:center;padding:1rem 0;">
            <p style="font-size:1rem;margin:0;color:#888;">{label}</p>
            <p style="font-size:3rem;font-weight:700;margin:0;color:{color};">{score}%</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(min(score / 100.0, 1.0))


# ---------------------------------------------------------------------------
# Skills tags
# ---------------------------------------------------------------------------

_TAG_STYLES = {
    "matched": "background:#d4edda;color:#155724;",
    "missing": "background:#f8d7da;color:#721c24;",
    "extra": "background:#cce5ff;color:#004085;",
}


def _render_tag(skill: str, kind: str) -> str:
    style = _TAG_STYLES.get(kind, "")
    return (
        f'<span style="{style}display:inline-block;padding:4px 10px;'
        f'margin:3px;border-radius:12px;font-size:0.85rem;">{skill}</span>'
    )


def render_skills_tags(matched: list[str], missing: list[str], extra: list[str]):
    """Display color-coded skill tags: green=matched, red=missing, blue=extra."""
    if matched:
        st.markdown("**Matched Skills**")
        st.markdown(" ".join(_render_tag(s, "matched") for s in matched), unsafe_allow_html=True)
    if missing:
        st.markdown("**Missing Skills** (in job, not in resume)")
        st.markdown(" ".join(_render_tag(s, "missing") for s in missing), unsafe_allow_html=True)
    if extra:
        st.markdown("**Extra Skills** (in resume, not in job)")
        st.markdown(" ".join(_render_tag(s, "extra") for s in extra), unsafe_allow_html=True)
    if not matched and not missing and not extra:
        st.info("No skills detected in this category.")


# ---------------------------------------------------------------------------
# Radar chart
# ---------------------------------------------------------------------------

def render_radar_chart(category_scores: dict[str, float]):
    """Render a Plotly radar chart of per-category match scores."""
    categories = list(category_scores.keys())
    scores = list(category_scores.values())

    if not categories:
        st.info("Not enough data for a radar chart.")
        return

    # Close the polygon
    categories_closed = categories + [categories[0]]
    scores_closed = scores + [scores[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(99, 110, 250, 0.25)",
        line=dict(color="#636efa", width=2),
        name="Match %",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], ticksuffix="%"),
        ),
        showlegend=False,
        margin=dict(l=60, r=60, t=40, b=40),
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Category breakdown
# ---------------------------------------------------------------------------

def render_category_breakdown(analysis: dict):
    """Render tabbed breakdown of each skill category."""
    categories = analysis["categories"]
    if not categories:
        st.info("No skill categories to display.")
        return

    tabs = st.tabs(list(categories.keys()))
    for tab, (cat_name, cat_data) in zip(tabs, categories.items()):
        with tab:
            score = cat_data["score"]
            job_count = cat_data["job_count"]
            if score is not None and job_count > 0:
                col1, col2 = st.columns([1, 3])
                with col1:
                    color = _score_color(score)
                    st.markdown(
                        f'<p style="font-size:2rem;font-weight:700;color:{color};margin:0;">{score}%</p>'
                        f'<p style="color:#888;margin:0;">{len(cat_data["matched"])}/{job_count} skills</p>',
                        unsafe_allow_html=True,
                    )
                with col2:
                    st.progress(min(score / 100.0, 1.0))
            elif job_count == 0:
                st.caption("Job description has no requirements in this category.")
            render_skills_tags(cat_data["matched"], cat_data["missing"], cat_data["extra"])
