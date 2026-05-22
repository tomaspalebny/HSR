"""
HSR CBA Analyser — Multi-Criteria Analysis (MCA) tab module.
Complements the quantitative CBA with non-monetary criteria evaluation.

Methodology alignment:
  • Criterion framework follows MD ČR/SFDI (2023, aktualizace 2025) Rezortní metodika, §4.5
  • EU methodology alignment follows JASPERS/DG REGIO (2021) Economic Appraisal Vademecum
  • AHP (Analytic Hierarchy Process) weighting framework per Saaty (1980)

Data provenance:
  • Criteria definitions and weighting framework are grounded in the methodology documents.
  • Per-corridor default scores are EXPERT ESTIMATES based on publicly available project
    documentation (feasibility studies, parliamentary reports, EU transport appraisals).
    These estimates are NOT extracted directly from the methodology — they represent
    reasoned judgments about each corridor's characteristics and should be calibrated
    against project-specific MCA when used for formal appraisal.

Limitations:
  • Scores have not been validated against official project MCA submissions.
  • Weights are adjustable — users should calibrate to reflect their policy priorities.
  • The 1-5 scoring is ordinal; weighted sums assume cardinal comparability (standard in AHP applications).
"""
import streamlit as st
import plotly.graph_objects as go
import numpy as np

# ════════════════════════════════════════════════════════════════
# MCA CRITERIA DEFINITIONS
# ════════════════════════════════════════════════════════════════

MCA_CRITERIA = {
    "strategic_fit": {
        "label": "Strategic Fit",
        "description": "Alignment with national/EU transport strategies, TEN-T corridor coherence, policy priority",
        "weight": 12.0,
    },
    "regional_cohesion": {
        "label": "Regional Cohesion",
        "description": "Impact on reducing regional economic disparities, access to opportunities and services",
        "weight": 12.0,
    },
    "environment_sustainability": {
        "label": "Env. Sustainability",
        "description": "Beyond CO₂: biodiversity, landscape fragmentation, noise reduction, land use compatibility",
        "weight": 10.0,
    },
    "safety": {
        "label": "Safety",
        "description": "Contribution to accident reduction, modern safety systems (ETCS Level >=2)",
        "weight": 10.0,
    },
    "access_connectivity": {
        "label": "Access & Connectivity",
        "description": "Integration with existing networks, feeder connections, multimodal hub development",
        "weight": 14.0,
    },
    "implementation_feasibility": {
        "label": "Impl. Feasibility",
        "description": "Institutional capacity, land acquisition complexity, technical readiness, procurement maturity",
        "weight": 12.0,
    },
    "innovation_tech": {
        "label": "Innovation & Tech",
        "description": "New technology standards, digitalization, ERTMS/ETCS deployment, interoperability",
        "weight": 10.0,
    },
    "social_acceptance": {
        "label": "Social Acceptance",
        "description": "Public support, political endorsement, stakeholder consensus, NIMBY risk",
        "weight": 10.0,
    },
    "capacity_release": {
        "label": "Capacity Release",
        "description": "Freight and regional service potential on freed conventional rail capacity",
        "weight": 10.0,
    },
}

# Sum of default weights should be ~100
assert abs(sum(c["weight"] for c in MCA_CRITERIA.values()) - 100.0) < 0.1

# ════════════════════════════════════════════════════════════════
# MCA CRITERION SOURCES — Citations anchoring each criterion
# ⇒DOCTRINE:
# • MD Čr/SFDI (2023, akt. 2025) Rezortní metodika §4.5
# • JASPERS/DG REGIO (2021) Economic Appraisal Vademecum
# • Belton & Setwart (2002) MCDA framework
# • Saaty (1980) Analytic Hierarchy Process
# ═════════════════════════════════════════════════════════════════
MCA_CRITERION_SOURCES = {
    "strategic_fit": "MD Čr/SFDI (2023) §4.5 — strategic alignment criterion",
    "regional_cohesion": "JASPERS (2021) §2.3 — EU Cohesion objective; Belton & Stewart (2002)",
    "environment_sustainability": "MD ČR/SFDI (2023) §4.5; EC Handbook (2020) — environmental criterion",
    "safety": "MDČR/SFDI (2023) §4.5; EC Cohesion Policy Objective 3 — sécurité criterion",
    "access_connectivity": "MD ČR/SFDI (2023) §4.5; JASPERS (2021) Table p.7 — connectivity criterion",
    "implementation_feasibility": "JASPERS (2021) §2.3 — institutional capacity criterion; MD ČR/SFDI (2023)",
    "innovation_tech": "MD ČR/SFDI (2025) Metodika digitalizace; JASPERS (2021)",
    "social_acceptance": "Expert criterion analogous to Belton & Stewart (2002); EC Stakeholder Engagement guidance",
    "capacity_release": "UK DfT (2023) TAG Unit A5.4 — Released capacity benefits; MD ČR/SFDI (2023) §4.5",
}

# ════════════════════════════════════════════════════════════════
# CORRIDOR-SPECIFIC DEFAULT MCA SCORES
# ════════════════════════════════════════════════════════════════
#
# PROVENANCE: These scores are EXPERT ESTIMATES based on:# 해
#  + Public project documentation (feasibility studies, NAO/ECA reports)#  + Parliamentary committee reports
#  + Published CBA appraisals (HS2, Rail Baltica, etc.)
#  + EU corridor assessment studies
# 
# Methodology documents (MD ČR, JASPERS) define the criteria
# FRAMEWORK; but per-corridor scoring requires project-specific
# assessment that is beyond what any single document provides.
# Defaults are expert estimats inteaded as reasoned starting
# points.User should calibrate with project-specific data.
#

MCA_CORRIDOR_SCORES = {
    "🇫🇷 TGV Paris–Lyon": {
        "strategic_fit": 5, "regional_cohesion": 2, "environment_sustainability": 3,
        "safety": 4, "access_connectivity": 5, "implementation_feasibility": 5,
        "innovation_tech": 4, "social_acceptance": 5, "capacity_release": 4,
    },
    "🇫🇷 LGV Est": {
        "strategic_fit": 4, "regional_cohesion": 4, "environment_sustainability": 3,
        "safety": 4, "access_connectivity": 3, "implementation_feasibility": 4,
        "innovation_tech": 3, "social_acceptance": 4, "capacity_release": 3,
    },
    "🇪🇸 AVE Madrid–Barcelona": {
        "strategic_fit": 4, "regional_cohesion": 4, "environment_sustainability": 3,
        "safety": 4, "access_connectivity": 4, "implementation_feasibility": 4,
        "innovation_tech": 4, "social_acceptance": 4, "capacity_release": 3,
    },
    "🇪🇸 AVE Madrid–Seville": {
        "strategic_fit": 4, "regional_cohesion": 3, "environment_sustainability": 3,
        "safety": 4, "access_connectivity": 4, "implementation_feasibility": 5,
        "innovation_tech": 3, "social_acceptance": 4, "capacity_release": 3,
    },
    "🇬🇧 HS1 (CTRL)": {
        "strategic_fit": 5, "regional_cohesion": 2, "environment_sustainability": 3,
        "safety": 5, "access_connectivity": 5, "implementation_feasibility": 5,
        "innovation_tech": 4, "social_acceptance": 3, "capacity_release": 5,
    },
    "🇬🇧 HS2 Phase 1": {
        "strategic_fit": 5, "regional_cohesion": 3, "environment_sustainability": 2,
        "safety": 4, "access_connectivity": 4, "implementation_feasibility": 3,
        "innovation_tech": 4, "social_acceptance": 2, "capacity_release": 5,
    },
    "🇳🇱 HSL-Zuid": {
        "strategic_fit": 4, "regional_cohesion": 3, "environment_sustainability": 3,
        "safety": 4, "access_connectivity": 4, "implementation_feasibility": 4,
        "innovation_tech": 4, "social_acceptance": 4, "capacity_release": 4,
    },
    "🇮🇹 Torino–Milano": {
        "strategic_fit": 4, "regional_cohesion": 4, "environment_sustainability": 3,
        "safety": 4, "access_connectivity": 4, "implementation_feasibility": 3,
        "innovation_tech": 3, "social_acceptance": 3, "capacity_release": 4,
    },
    "🇨🇿 VRT Praha–Brno": {
        "strategic_fit": 4, "regional_cohesion": 5, "environment_sustainability": 4,
        "safety": 3, "access_connectivity": 3, "implementation_feasibility": 2,
        "innovation_tech": 3, "social_acceptance": 3, "capacity_release": 3,
    },
    "🇨🇿 VRT Brno–Ostrava": {
        "strategic_fit": 3, "regional_cohesion": 4, "environment_sustainability": 4,
        "safety": 3, "access_connectivity": 3, "implementation_feasibility": 2,
        "innovation_tech": 3, "social_acceptance": 3, "capacity_release": 3,
    },
    "🇵🇱 CPK Y-line": {
        "strategic_fit": 4, "regional_cohesion": 5, "environment_sustainability": 3,
        "safety": 3, "access_connectivity": 4, "implementation_feasibility": 2,
        "innovation_tech": 3, "social_acceptance": 3, "capacity_release": 3,
    },
    "🇭🇺 Budapest–Belgrade": {
        "strategic_fit": 3, "regional_cohesion": 4, "environment_sustainability": 3,
        "safety": 2, "access_connectivity": 3, "implementation_feasibility": 2,
        "innovation_tech": 2, "social_acceptance": 2, "capacity_release": 2,
    },
    "🇪🇺 Rail Baltica": {
        "strategic_fit": 5, "regional_cohesion": 5, "environment_sustainability": 4,
        "safety": 4, "access_connectivity": 3, "implementation_feasibility": 2,
        "innovation_tech": 3, "social_acceptance": 4, "capacity_release": 2,
    },
    "🇸🇰 Brno–Bratislava": {
        "strategic_fit": 3, "regional_cohesion": 4, "environment_sustainability": 4,
        "safety": 3, "access_connectivity": 3, "implementation_feasibility": 3,
        "innovation_tech": 3, "social_acceptance": 3, "capacity_release": 3,
    },
}

# Default fallback (custom corridor)
MCA_DEFAULT_SCORES = {
    "strategic_fit": 3, "regional_cohesion": 3, "environment_sustainability": 3,
    "safety": 3, "access_connectivity": 3, "implementation_feasibility": 3,
    "innovation_tech": 3, "social_acceptance": 3, "capacity_release": 3,
}


def get_mca_scores(corridor_name):
    """Return MCA scores for a corridor, falling back to defaults."""
    if corridor_name in MCA_CORRIDOR_SCORES:
        return dict(MCA_CORRIDOR_SCORES[corridor_name])
    return dict(MCA_DEFAULT_SCORES)


def render_mca_tab(params, country_name, corridor_name, S):
    """Render the MCA tab content — called from within a Streamlit tab context."""
    st.markdown("## Multi-Criteria Analysis (MCA)")
    st.caption(
        "MCA complements the quantitative CBA with qualitative/non-monetary evaluation. "
        "EU and Czech (MD ČR) appraisal guidelines recommend using both CBA and MCA for transport projects."
    )
    st.caption(
        "Each criterion is scored 1–5 (1 = very weak, 5 = excellent). "
        "Weights can be adjusted to reflect policy priorities — they are auto-normalized to 100%."
    )

    # Get default per-corridor scores
    default_scores = get_mca_scores(corridor_name)

    # ═══════════════════════════════
    # WEIGHT SLIDERS
    # ═══════════════════════════════
    st.markdown("### Criterion Weights")
    st.caption("Adjust the relative importance of each criterion. Weights are automatically normalized to sum to 100%.")

    raw_weights = {}
    w_cols = st.columns(4)
    for idx, (key, crit) in enumerate(MCA_CRITERIA.items()):
        col = w_cols[idx % 4]
        with col:
            raw_weights[key] = st.slider(
                f"{crit['label']}",
                0, 100, int(crit['weight']), 5,
                key=f"mca_w_{key}",
                help=crit['description'],
            )

    # Normalize weights
    total_w = sum(raw_weights.values())
    weights = {k: v / total_w * 100 if total_w > 0 else 0 for k, v in raw_weights.items()}

    # ═══════════════════════════════
    # SCORE SLIDERS
    # ═══════════════════════════════
    st.markdown("### Criterion Scores")
    st.caption("Adjust per-criterion assessment for this corridor. Defaults are corridor-specific estimates.")

    user_scores = {}
    s_cols = st.columns(4)
    for idx, (key, crit) in enumerate(MCA_CRITERIA.items()):
        col = s_cols[idx % 4]
        with col:
            user_scores[key] = st.slider(
                f"{crit['label']} (1–5)",
                1, 5, default_scores.get(key, 3),
                key=f"mca_s_{key}",
                help=crit['description'],
            )

    # ═══════════════════════════════
    # WEIGHTED SCORE CALCULATION
    # ═══════════════════════════════
    total_weighted = 0
    score_details = []
    for key in MCA_CRITERIA:
        w = weights.get(key, 0) / 100.0
        s = user_scores.get(key, 3)
        weighted = w * s
        total_weighted += weighted
        score_details.append({
            "Criterion": MCA_CRITERIA[key]['label'],
            "Weight %": f"{weights.get(key, 0):.1f}",
            "Score (1–5)": s,
            "Weighted": f"{weighted:.2f}",
        })

    # ═══════════════════════════════
    # RESULTS
    # ═══════════════════════════════
    import pandas as pd
    res_col1, res_col2 = st.columns([1, 1])

    with res_col1:
        # Radar chart
        categories = [MCA_CRITERIA[k]['label'] for k in MCA_CRITERIA]
        scores_list = [user_scores.get(k, default_scores.get(k, 3)) for k in MCA_CRITERIA]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=scores_list + [scores_list[0]],  # close the polygon
            theta=categories + [categories[0]],
            fill='toself',
            fillcolor='rgba(32,178,255,0.3)',
            line=dict(color='#20B2FF', width=2),
            name='MCA Score',
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 5]),
            ),
            margin=dict(t=40, b=10, l=50, r=50),
            height=450,
            title="MCA Profile",
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with res_col2:
        st.markdown("### Weighted Score Table")
        score_df = pd.DataFrame(score_details)
        st.dataframe(score_df, use_container_width=True, hide_index=True)

        st.metric(
            "Total Weighted MCA Score",
            f"{total_weighted:.2f} / 5.00",
            help="Sum of weighted scores. Maximum possible is 5.0 (all criteria score 5 with balanced weights). Benchmark: ≥3.5 = strong, ≥3.0 = adequate, <2.5 = weak non-monetary case.",
        )

    # ═══════════════════════════════
    # COMBINED DECISION INDEX
    # ═══════════════════════════════
    st.markdown("---")
    st.markdown("### Combined CBA + MCA Decision Index")

    st.caption(
        "The Combined Decision Index normalizes BCR (absolute) to a 1–5 scale and averages it with "
        "the MCA weighted score (also 1-5). The index equally weights CBA (50%) and MCA (50%). "
        "This is a decision-support tool, not a substitute for judgment."
    )

    # Use CBA results from the main app (passed via S dict)
    import numpy as np
    bcr_val = S.get('bcr_abs', np.nan)

    # Normalize BCR to 1-5 scale
    # <0.5 → 1, 0.5-0.8 → 2, 0.8-1.0 → 3, 1.0-1.3 → 4, >1.3 → 5
    if np.isnan(bcr_val):
        bcr_normalized = np.nan
        bcr_label = "N/A"
    elif bcr_val < 0.5:
        bcr_normalized = 1.0
        bcr_label = "Very Weak"
    elif bcr_val < 0.8:
        bcr_normalized = 2.0
        bcr_label = "Weak"
    elif bcr_val < 1.0:
        bcr_normalized = 3.0
        bcr_label = "Marginal"
    elif bcr_val < 1.3:
        bcr_normalized = 4.0
        bcr_label = "Good"
    else:
        bcr_normalized = 5.0
        bcr_label = "Excellent"

    mca_normalized = total_weighted  # already 1-5 scale
    combined_index = (bcr_normalized + mca_normalized) / 2 if not np.isnan(bcr_val) else mca_normalized

    idx_col1, idx_col2, idx_col3 = st.columns(3)
    with idx_col1:
        st.metric("CBA Score (normalized)", f"{bcr_normalized:.1f}" if bcr_normalized else "N/A",
                  help=f"BCR (absolute) = {bcr_val:.3f} → {bcr_label}")
    with idx_col2:
        st.metric("MCA Score", f"{mca_normalized:.2f}",
                  help=f"Weighted MCA score out of 5.00")
    with idx_col3:
        if combined_index >= 4.0:
            verdict = "✅ Recommend"
        elif combined_index >= 3.0:
            verdict = "⚠️ Marginal"
        else:
            verdict = "❌ Not Recommended"
        st.metric("Combined Decision Index", f"{combined_index:.2f}", help=verdict)

    # Qualitative verdict
    if bcr_val is not None and not np.isnan(bcr_val):
        if bcr_val >= 1.0 and total_weighted >= 3.5:
            st.success("✅ Project passes both CBA and MCA thresholds. Strong case from both quantitative and qualitative perspectives.")
        elif bcr_val >= 1.0 and total_weighted < 3.5:
            st.warning("⚠️ CBA is positive but MCA is below threshold. Recommend strengthening non-monetary dimensions before approval.")
        elif bcr_val < 1.0 and total_weighted >= 3.5:
            st.warning("⚠️ MCA is strong but CBA fails. Consider whether strategic benefits justify the financial gap.")
        else:
            st.error("❌ Project fails both CBA and MCA. Strong case against proceeding in current form.")

    st.markdown("---")
    st.markdown("### Methodology Reference")
    st.markdown("""
    **Sources and methodology:**
    - **EU**: JASPERS/DG REGIO (2021), *Economic Appraisal Vademecum 2021–2027*, updating EC (2014) *Guide to Cost-Benefit Analysis of Investment Projects*
    - **Czech**: MD ČR/SFDI (2023, aktualizace květ en 2025), *Rezortní metodika pro hodnocení ekonomické efektivnosti projektů dopravních staveb*, §4.5 Vícekriteriální analýza
    - **Saaty T.L.** (1980), *The Analytic Hierarchy Process*, McGraw-Hill, New York
    - **Belton V. & Stewart T.J.** (2002), *Multiple Criteria Decision Analysis: An Integrated Approach*, Springer
    """
    )
    st.caption(
        "Weighted Sum Model (WSM): V(x) = Σ w_i × s_i, where w_i is the normalized weight of criterion i, "
        "and s_i is the score assigned to this corridor for that criterion."
    )