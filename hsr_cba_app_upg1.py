"""
HSR Social CBA Sensitivity Analyser — Professional Edition
==========================================================

Model scope:
  Social cost–benefit analysis (CBA) of high-speed rail (HSR) projects,
  comparing a proposed HSR investment against an explicit counterfactual
  (conventional rail upgrade). The model is strictly incremental.

Analytical features:
    • Deterministic base-case CBA (NPV, BCR, IRR, nominal & discounted payback)
  • Incremental and absolute perspectives
  • Reference Class Forecasting (Flyvbjerg et al.)
  • One-way sensitivity (tornado) for any parameter
  • User-configurable Monte Carlo simulation
  • Threshold (break-even) analysis
  • Corridor comparison across presets
  • Downloadable audit trail of annual cash flows

Data requirements:
  All inputs are user-supplied via the sidebar. Built-in corridor presets
  and country socio-economic profiles provide defensible starting values
  sourced from published appraisals (HS2 BCR, SNCF reports, EU Handbook
  on External Costs, UIC cost benchmarks). Users should override defaults
  with project-specific data.

Main limitations:
  • Single-point demand forecast (no endogenous mode-choice model).
  • Simplified linear construction spend profile.
  • No distributional (equity) analysis.
  • No real-options or phasing analysis.
  • Counterfactual is static (no dynamic feedback).
  • Externalities use average unit costs, not marginal damage functions.
  • No agglomeration micro-modelling (WEBs are a fixed % of time benefits).

Companion to: "When is HSR Worthwhile? Lessons from Western Europe and
Implications for Central and Eastern Europe" (Nash, Jandová, Paleta,
Król, 2026).
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import io, textwrap, datetime

st.set_page_config(page_title="HSR CBA Analyser", layout="wide", page_icon="🚄")


def is_defined_metric(value):
    return value is not None and not pd.isna(value)


def format_bcr(value, digits=3):
    return f"{value:.{digits}f}" if is_defined_metric(value) else "N/A"

# ════════════════════════════════════════════════════════════════
# LABELS & UNITS (centralised for future i18n)
# ════════════════════════════════════════════════════════════════
PARAM_META = {
    # key: (label, unit, short_help, role)
    # role: cost | benefit | externality | weighting | appraisal
    "line_length_km":   ("Line length",          "km",       "Total route length of the new HSR alignment.", "cost"),
    "pct_tunnel":       ("Tunnel share",         "%",        "Share of route in tunnel — drives construction cost.", "cost"),
    "pct_viaduct":      ("Viaduct share",        "%",        "Share of route on elevated structures.", "cost"),
    "access_egress_hsr":("Access/egress HSR",    "min",      "Average time to reach HSR station (door to platform).", "benefit"),
    "access_egress_conv":("Access/egress conv.", "min",      "Average time to reach conventional station.", "benefit"),
    "cost_at_grade":    ("At-grade cost",        "€m/km",    "Unit cost of surface-level track construction. Typical: 10–55 €m/km.", "cost"),
    "cost_tunnel":      ("Tunnel cost",          "€m/km",    "Unit cost of tunnelled sections. Typical: 40–200 €m/km.", "cost"),
    "cost_viaduct":     ("Viaduct cost",         "€m/km",    "Unit cost of elevated sections. Typical: 25–100 €m/km.", "cost"),
    "cost_signalling":  ("Signalling cost",      "€m/km",    "ERTMS/ETCS and signalling equipment per route-km.", "cost"),
    "cost_land":        ("Land acquisition",     "€m/km",    "Average land purchase cost per route-km.", "cost"),
    "cost_stations":    ("Stations total",       "€m",       "Total station construction/upgrade cost.", "cost"),
    "cost_rolling":     ("Rolling stock",        "€m",       "Cost of new train fleet. Zero if operator-supplied.", "cost"),
    "cost_overrun":     ("Cost overrun uplift",  "%",        "Percentage uplift applied to base CAPEX to account for optimism bias.", "cost"),
    "constr_years":     ("Construction period",  "yr",       "Years from ground-breaking to service start.", "cost"),
    "counterfactual_capex":("Upgrade CAPEX",     "€m",       "Total capital cost of the counterfactual rail upgrade.", "cost"),
    "counterfactual_opex_yr":("Upgrade OPEX/yr", "€m",       "Annual operating cost of the counterfactual.", "cost"),
    "opex_infra_maint": ("Infra maintenance",    "€m/km/yr", "Annual infrastructure maintenance per route-km. Typical: 0.03–0.12.", "cost"),
    "opex_energy":      ("Energy cost",          "€/train-km","Traction energy cost per train-kilometre.", "cost"),
    "opex_staff":       ("Staff cost",           "€/train-km","On-board and operational staff cost per train-km.", "cost"),
    "opex_rs_maint":    ("RS maintenance",       "€/train-km","Rolling stock maintenance per train-km.", "cost"),
    "opex_overhead":    ("Overhead",             "€m/yr",    "Annual fixed overhead (admin, insurance, etc.).", "cost"),
    "trains_day":       ("Trains per day",       "",         "Total daily service frequency (both directions).", "cost"),
    "op_days":          ("Operating days/yr",    "",         "Revenue-service days per year.", "cost"),
    "annual_pax":       ("Annual passengers",    "million",  "Base-year annual ridership. Applied to all demand.", "benefit"),
    "demand_growth":    ("Demand growth",        "%/yr",     "Compound annual growth in ridership.", "benefit"),
    "pax_biz":          ("Business share",       "%",        "Share of passengers travelling for business. Higher VOT.", "weighting"),
    "pax_com":          ("Commuter share",       "%",        "Share of passengers commuting. Medium VOT.", "weighting"),
    "modal_shift_air":  ("Shifted from air",     "%",        "Share of HSR passengers previously using air. Externality benefits apply.", "externality"),
    "modal_shift_car":  ("Shifted from car",     "%",        "Share previously using car. Accident and congestion benefits apply.", "externality"),
    "generated_share":  ("Generated demand",     "%",        "Induced (new) trips. Rule-of-half applied to time benefits.", "benefit"),
    "avg_fare":         ("Average fare",         "€/pax",    "Mean ticket price in base year.", "benefit"),
    "fare_growth":      ("Real fare growth",     "%/yr",     "Above-inflation annual fare increase.", "benefit"),
    "current_time":     ("Current journey time", "min",      "End-to-end journey time today (excluding access/egress).", "benefit"),
    "upgrade_time":     ("Upgrade counterfact.", "min",      "Journey time after conventional upgrade.", "benefit"),
    "hsr_time":         ("HSR journey time",     "min",      "Journey time on the new HSR line.", "benefit"),
    "vot_biz":          ("VOT business",         "€/hr",     "Value of in-vehicle time for business travellers.", "benefit"),
    "vot_com":          ("VOT commuter",         "€/hr",     "Value of time for commuters.", "benefit"),
    "vot_lei":          ("VOT leisure",          "€/hr",     "Value of time for leisure travellers.", "benefit"),
    "vot_growth":       ("VOT real growth",      "%/yr",     "Annual real growth in value of time (linked to GDP/capita growth).", "benefit"),
    "co2_price":        ("CO₂ price",            "€/tonne",  "Shadow price of CO₂ for monetising emission savings.", "externality"),
    "co2_per_mpax":     ("CO₂ saved",            "t/m shifted pax","Tonnes of CO₂ avoided per million passengers shifted from air.", "externality"),
    "accident_ben":     ("Accident benefit",     "€m/m car pax","Avoided accident cost per million passengers shifted from car.", "externality"),
    "congestion":       ("Congestion relief",    "€m/yr",    "Base-year annual road congestion benefit associated with the base-year shift from car; scaled over time with shifted car passengers.", "externality"),
    "webs_pct":         ("WEBs",                 "% of time","Wider Economic Benefits as a share of user time savings.", "externality"),
    "discount":         ("Discount rate",        "%",        "Social discount rate for present-value calculation. EU guide: 3–5%.", "appraisal"),
    "appraisal_yrs":    ("Appraisal period",     "yr",       "Operating years over which benefits and costs are evaluated.", "appraisal"),
    "residual_pct":     ("Residual value",       "% CAPEX",  "Share of CAPEX treated as residual value at appraisal end.", "appraisal"),
}

ROLE_COLOURS = {
    "cost": "🔴", "benefit": "🟢", "externality": "🌍", "weighting": "⚖️", "appraisal": "📊",
}

# ════════════════════════════════════════════════════════════════
# COUNTRY SOCIO-ECONOMIC PROFILES
# ════════════════════════════════════════════════════════════════
COUNTRY_PRESETS = {
    "— No profile —": {},
    "🇫🇷 France": dict(
        vot_biz=50.0, vot_com=22.0, vot_lei=12.0, vot_growth=1.0,
        discount=4.0, appraisal_yrs=40, co2_price=90.0,
        co2_per_mpax=18000, accident_ben=0.4, congestion=25.0,
        webs_pct=15, cost_overrun=10, residual_pct=30,
    ),
    "🇪🇸 Spain": dict(
        vot_biz=38.0, vot_com=16.0, vot_lei=9.0, vot_growth=1.2,
        discount=4.0, appraisal_yrs=40, co2_price=80.0,
        co2_per_mpax=20000, accident_ben=0.3, congestion=8.0,
        webs_pct=12, cost_overrun=5, residual_pct=30,
    ),
    "🇬🇧 United Kingdom": dict(
        vot_biz=60.0, vot_com=28.0, vot_lei=14.0, vot_growth=1.0,
        discount=3.5, appraisal_yrs=40, co2_price=100.0,
        co2_per_mpax=12000, accident_ben=0.5, congestion=40.0,
        webs_pct=20, cost_overrun=25, residual_pct=25,
    ),
    "🇳🇱 Netherlands": dict(
        vot_biz=55.0, vot_com=24.0, vot_lei=13.0, vot_growth=1.0,
        discount=4.0, appraisal_yrs=40, co2_price=100.0,
        co2_per_mpax=10000, accident_ben=0.3, congestion=15.0,
        webs_pct=15, cost_overrun=15, residual_pct=30,
    ),
    "🇮🇹 Italy": dict(
        vot_biz=45.0, vot_com=20.0, vot_lei=11.0, vot_growth=1.0,
        discount=4.0, appraisal_yrs=40, co2_price=80.0,
        co2_per_mpax=14000, accident_ben=0.4, congestion=20.0,
        webs_pct=15, cost_overrun=20, residual_pct=30,
    ),
    "🇨🇿 Czech Republic": dict(
        vot_biz=28.0, vot_com=12.0, vot_lei=7.0, vot_growth=2.0,
        discount=4.0, appraisal_yrs=40, co2_price=80.0,
        co2_per_mpax=15000, accident_ben=0.5, congestion=15.0,
        webs_pct=15, cost_overrun=10, residual_pct=30,
    ),
    "🇵🇱 Poland": dict(
        vot_biz=25.0, vot_com=10.0, vot_lei=6.0, vot_growth=2.0,
        discount=4.0, appraisal_yrs=40, co2_price=80.0,
        co2_per_mpax=18000, accident_ben=0.4, congestion=10.0,
        webs_pct=15, cost_overrun=10, residual_pct=30,
    ),
    "🇪🇺 Generic EU": dict(
        vot_biz=40.0, vot_com=18.0, vot_lei=10.0, vot_growth=1.2,
        discount=4.0, appraisal_yrs=40, co2_price=80.0,
        co2_per_mpax=15000, accident_ben=0.4, congestion=15.0,
        webs_pct=15, cost_overrun=15, residual_pct=30,
    ),
    "🌐 OECD High-income": dict(
        vot_biz=50.0, vot_com=22.0, vot_lei=12.0, vot_growth=1.0,
        discount=3.5, appraisal_yrs=40, co2_price=100.0,
        co2_per_mpax=15000, accident_ben=0.4, congestion=20.0,
        webs_pct=18, cost_overrun=20, residual_pct=30,
    ),
    "🌍 Emerging Economy": dict(
        vot_biz=18.0, vot_com=7.0, vot_lei=4.0, vot_growth=3.0,
        discount=5.0, appraisal_yrs=40, co2_price=50.0,
        co2_per_mpax=20000, accident_ben=0.3, congestion=5.0,
        webs_pct=10, cost_overrun=30, residual_pct=25,
    ),
}

# ════════════════════════════════════════════════════════════════
# CORRIDOR PRESETS
# ════════════════════════════════════════════════════════════════
CORRIDOR_PRESETS = {
    "— Custom —": {},
    "🇫🇷 TGV Paris–Lyon": dict(line_length_km=409,pct_tunnel=2,pct_viaduct=3,cost_at_grade=16.0,cost_tunnel=60.0,cost_viaduct=40.0,cost_signalling=1.2,cost_land=0.8,cost_stations=300.0,cost_rolling=800.0,cost_overrun=0,constr_years=6,opex_infra_maint=0.060,opex_energy=9.0,opex_staff=8.0,opex_rs_maint=6.0,opex_overhead=50.0,trains_day=150,op_days=360,annual_pax=52.0,demand_growth=0.5,pax_biz=35,pax_com=25,avg_fare=50.0,fare_growth=0.3,current_time=240,upgrade_time=180,hsr_time=120,vot_biz=50.0,vot_com=22.0,vot_lei=12.0,vot_growth=1.0,co2_price=80.0,co2_per_mpax=18000,modal_shift_air=30,modal_shift_car=15,generated_share=10,accident_ben=0.4,congestion=25.0,webs_pct=15,discount=4.0,appraisal_yrs=40,residual_pct=30,counterfactual_capex=2000.0,counterfactual_opex_yr=80.0,access_egress_hsr=15,access_egress_conv=10),
    "🇫🇷 LGV Est": dict(line_length_km=300,pct_tunnel=5,pct_viaduct=4,cost_at_grade=22.0,cost_tunnel=75.0,cost_viaduct=45.0,cost_signalling=1.5,cost_land=1.2,cost_stations=350.0,cost_rolling=500.0,cost_overrun=10,constr_years=8,opex_infra_maint=0.060,opex_energy=9.0,opex_staff=8.0,opex_rs_maint=6.0,opex_overhead=40.0,trains_day=50,op_days=355,annual_pax=14.0,demand_growth=1.0,pax_biz=30,pax_com=20,avg_fare=55.0,fare_growth=0.3,current_time=280,upgrade_time=200,hsr_time=140,vot_biz=50.0,vot_com=22.0,vot_lei=12.0,vot_growth=1.0,co2_price=80.0,co2_per_mpax=15000,modal_shift_air=20,modal_shift_car=10,generated_share=12,accident_ben=0.4,congestion=10.0,webs_pct=12,discount=4.0,appraisal_yrs=40,residual_pct=30,counterfactual_capex=1500.0,counterfactual_opex_yr=60.0,access_egress_hsr=12,access_egress_conv=8),
    "🇪🇸 AVE Madrid–Barcelona": dict(line_length_km=621,pct_tunnel=8,pct_viaduct=10,cost_at_grade=10.0,cost_tunnel=55.0,cost_viaduct=30.0,cost_signalling=1.2,cost_land=0.6,cost_stations=400.0,cost_rolling=700.0,cost_overrun=0,constr_years=10,opex_infra_maint=0.050,opex_energy=7.0,opex_staff=5.0,opex_rs_maint=4.5,opex_overhead=40.0,trains_day=45,op_days=360,annual_pax=5.0,demand_growth=1.5,pax_biz=25,pax_com=15,avg_fare=55.0,fare_growth=0.3,current_time=360,upgrade_time=280,hsr_time=155,vot_biz=38.0,vot_com=16.0,vot_lei=9.0,vot_growth=1.2,co2_price=80.0,co2_per_mpax=20000,modal_shift_air=35,modal_shift_car=8,generated_share=10,accident_ben=0.3,congestion=8.0,webs_pct=12,discount=4.0,appraisal_yrs=40,residual_pct=30,counterfactual_capex=2500.0,counterfactual_opex_yr=90.0,access_egress_hsr=20,access_egress_conv=12),
    "🇪🇸 AVE Madrid–Seville": dict(line_length_km=471,pct_tunnel=4,pct_viaduct=6,cost_at_grade=8.0,cost_tunnel=50.0,cost_viaduct=28.0,cost_signalling=1.0,cost_land=0.5,cost_stations=250.0,cost_rolling=400.0,cost_overrun=0,constr_years=6,opex_infra_maint=0.050,opex_energy=7.0,opex_staff=5.0,opex_rs_maint=4.5,opex_overhead=30.0,trains_day=35,op_days=360,annual_pax=7.0,demand_growth=1.0,pax_biz=25,pax_com=15,avg_fare=45.0,fare_growth=0.3,current_time=330,upgrade_time=240,hsr_time=140,vot_biz=35.0,vot_com=14.0,vot_lei=8.0,vot_growth=1.2,co2_price=80.0,co2_per_mpax=18000,modal_shift_air=25,modal_shift_car=10,generated_share=8,accident_ben=0.3,congestion=5.0,webs_pct=10,discount=4.0,appraisal_yrs=40,residual_pct=30,counterfactual_capex=1800.0,counterfactual_opex_yr=70.0,access_egress_hsr=18,access_egress_conv=10),
    "🇬🇧 HS1 (CTRL)": dict(line_length_km=108,pct_tunnel=37,pct_viaduct=5,cost_at_grade=35.0,cost_tunnel=100.0,cost_viaduct=60.0,cost_signalling=2.5,cost_land=5.0,cost_stations=800.0,cost_rolling=0.0,cost_overrun=0,constr_years=7,opex_infra_maint=0.080,opex_energy=12.0,opex_staff=10.0,opex_rs_maint=7.0,opex_overhead=40.0,trains_day=55,op_days=360,annual_pax=26.0,demand_growth=1.5,pax_biz=40,pax_com=25,avg_fare=65.0,fare_growth=0.3,current_time=120,upgrade_time=90,hsr_time=55,vot_biz=60.0,vot_com=28.0,vot_lei=14.0,vot_growth=1.0,co2_price=80.0,co2_per_mpax=12000,modal_shift_air=30,modal_shift_car=5,generated_share=10,accident_ben=0.5,congestion=30.0,webs_pct=18,discount=3.5,appraisal_yrs=40,residual_pct=25,counterfactual_capex=1200.0,counterfactual_opex_yr=50.0,access_egress_hsr=10,access_egress_conv=8),
    "🇬🇧 HS2 Phase 1": dict(line_length_km=225,pct_tunnel=25,pct_viaduct=12,cost_at_grade=55.0,cost_tunnel=180.0,cost_viaduct=90.0,cost_signalling=3.0,cost_land=6.0,cost_stations=2500.0,cost_rolling=2500.0,cost_overrun=25,constr_years=14,opex_infra_maint=0.100,opex_energy=12.0,opex_staff=10.0,opex_rs_maint=7.0,opex_overhead=60.0,trains_day=48,op_days=360,annual_pax=18.0,demand_growth=1.0,pax_biz=35,pax_com=30,avg_fare=55.0,fare_growth=0.3,current_time=130,upgrade_time=90,hsr_time=49,vot_biz=60.0,vot_com=28.0,vot_lei=14.0,vot_growth=1.0,co2_price=80.0,co2_per_mpax=12000,modal_shift_air=15,modal_shift_car=10,generated_share=12,accident_ben=0.5,congestion=40.0,webs_pct=20,discount=3.5,appraisal_yrs=40,residual_pct=25,counterfactual_capex=3000.0,counterfactual_opex_yr=100.0,access_egress_hsr=15,access_egress_conv=10),
    "🇳🇱 HSL-Zuid": dict(line_length_km=125,pct_tunnel=12,pct_viaduct=8,cost_at_grade=35.0,cost_tunnel=100.0,cost_viaduct=60.0,cost_signalling=2.5,cost_land=4.0,cost_stations=500.0,cost_rolling=500.0,cost_overrun=75,constr_years=8,opex_infra_maint=0.070,opex_energy=10.0,opex_staff=9.0,opex_rs_maint=6.0,opex_overhead=35.0,trains_day=30,op_days=360,annual_pax=8.0,demand_growth=1.5,pax_biz=35,pax_com=20,avg_fare=40.0,fare_growth=0.3,current_time=90,upgrade_time=70,hsr_time=42,vot_biz=55.0,vot_com=24.0,vot_lei=13.0,vot_growth=1.0,co2_price=80.0,co2_per_mpax=10000,modal_shift_air=15,modal_shift_car=5,generated_share=10,accident_ben=0.3,congestion=15.0,webs_pct=15,discount=4.0,appraisal_yrs=40,residual_pct=30,counterfactual_capex=800.0,counterfactual_opex_yr=40.0,access_egress_hsr=12,access_egress_conv=8),
    "🇮🇹 Torino–Milano": dict(line_length_km=125,pct_tunnel=15,pct_viaduct=12,cost_at_grade=30.0,cost_tunnel=90.0,cost_viaduct=55.0,cost_signalling=2.0,cost_land=3.0,cost_stations=600.0,cost_rolling=400.0,cost_overrun=50,constr_years=10,opex_infra_maint=0.070,opex_energy=9.0,opex_staff=7.0,opex_rs_maint=5.5,opex_overhead=35.0,trains_day=70,op_days=355,annual_pax=15.0,demand_growth=1.0,pax_biz=35,pax_com=25,avg_fare=35.0,fare_growth=0.3,current_time=105,upgrade_time=80,hsr_time=45,vot_biz=45.0,vot_com=20.0,vot_lei=11.0,vot_growth=1.0,co2_price=80.0,co2_per_mpax=12000,modal_shift_air=10,modal_shift_car=20,generated_share=8,accident_ben=0.4,congestion=20.0,webs_pct=15,discount=4.0,appraisal_yrs=40,residual_pct=30,counterfactual_capex=1000.0,counterfactual_opex_yr=45.0,access_egress_hsr=15,access_egress_conv=10),
    "🇨🇿 VRT Praha–Brno": dict(line_length_km=230,pct_tunnel=10,pct_viaduct=8,cost_at_grade=18.0,cost_tunnel=80.0,cost_viaduct=45.0,cost_signalling=1.5,cost_land=1.0,cost_stations=400.0,cost_rolling=600.0,cost_overrun=0,constr_years=8,opex_infra_maint=0.060,opex_energy=8.0,opex_staff=6.0,opex_rs_maint=5.0,opex_overhead=30.0,trains_day=60,op_days=350,annual_pax=9.0,demand_growth=1.5,pax_biz=25,pax_com=30,avg_fare=25.0,fare_growth=0.5,current_time=150,upgrade_time=100,hsr_time=60,vot_biz=28.0,vot_com=12.0,vot_lei=7.0,vot_growth=2.0,co2_price=80.0,co2_per_mpax=15000,modal_shift_air=10,modal_shift_car=20,generated_share=15,accident_ben=0.5,congestion=15.0,webs_pct=15,discount=4.0,appraisal_yrs=40,residual_pct=30,counterfactual_capex=1500.0,counterfactual_opex_yr=55.0,access_egress_hsr=12,access_egress_conv=8),
    "🇨🇿 VRT Brno–Ostrava": dict(line_length_km=160,pct_tunnel=12,pct_viaduct=6,cost_at_grade=18.0,cost_tunnel=80.0,cost_viaduct=45.0,cost_signalling=1.5,cost_land=1.0,cost_stations=300.0,cost_rolling=400.0,cost_overrun=0,constr_years=7,opex_infra_maint=0.060,opex_energy=8.0,opex_staff=6.0,opex_rs_maint=5.0,opex_overhead=25.0,trains_day=45,op_days=350,annual_pax=6.0,demand_growth=1.5,pax_biz=22,pax_com=35,avg_fare=20.0,fare_growth=0.5,current_time=100,upgrade_time=75,hsr_time=45,vot_biz=28.0,vot_com=12.0,vot_lei=7.0,vot_growth=2.0,co2_price=80.0,co2_per_mpax=12000,modal_shift_air=5,modal_shift_car=20,generated_share=15,accident_ben=0.5,congestion=10.0,webs_pct=12,discount=4.0,appraisal_yrs=40,residual_pct=30,counterfactual_capex=1000.0,counterfactual_opex_yr=40.0,access_egress_hsr=10,access_egress_conv=6),
    "🇵🇱 CPK Y-line": dict(line_length_km=450,pct_tunnel=5,pct_viaduct=6,cost_at_grade=16.0,cost_tunnel=70.0,cost_viaduct=40.0,cost_signalling=1.5,cost_land=0.8,cost_stations=500.0,cost_rolling=800.0,cost_overrun=0,constr_years=10,opex_infra_maint=0.055,opex_energy=7.0,opex_staff=5.0,opex_rs_maint=4.5,opex_overhead=40.0,trains_day=60,op_days=350,annual_pax=12.0,demand_growth=1.5,pax_biz=25,pax_com=25,avg_fare=30.0,fare_growth=0.5,current_time=270,upgrade_time=190,hsr_time=110,vot_biz=25.0,vot_com=10.0,vot_lei=6.0,vot_growth=2.0,co2_price=80.0,co2_per_mpax=18000,modal_shift_air=15,modal_shift_car=15,generated_share=12,accident_ben=0.4,congestion=10.0,webs_pct=15,discount=4.0,appraisal_yrs=40,residual_pct=30,counterfactual_capex=3000.0,counterfactual_opex_yr=100.0,access_egress_hsr=15,access_egress_conv=10),
    "🇭🇺 Budapest–Belgrade": dict(line_length_km=350,pct_tunnel=3,pct_viaduct=8,cost_at_grade=14.0,cost_tunnel=60.0,cost_viaduct=35.0,cost_signalling=1.2,cost_land=0.5,cost_stations=300.0,cost_rolling=400.0,cost_overrun=40,constr_years=8,opex_infra_maint=0.050,opex_energy=6.0,opex_staff=4.0,opex_rs_maint=4.0,opex_overhead=20.0,trains_day=25,op_days=350,annual_pax=3.0,demand_growth=2.0,pax_biz=15,pax_com=15,avg_fare=18.0,fare_growth=0.5,current_time=480,upgrade_time=300,hsr_time=160,vot_biz=22.0,vot_com=9.0,vot_lei=5.0,vot_growth=2.5,co2_price=80.0,co2_per_mpax=15000,modal_shift_air=10,modal_shift_car=10,generated_share=15,accident_ben=0.3,congestion=3.0,webs_pct=10,discount=4.0,appraisal_yrs=40,residual_pct=30,counterfactual_capex=1200.0,counterfactual_opex_yr=40.0,access_egress_hsr=20,access_egress_conv=12),
    "🇪🇺 Rail Baltica": dict(line_length_km=870,pct_tunnel=1,pct_viaduct=3,cost_at_grade=22.0,cost_tunnel=80.0,cost_viaduct=50.0,cost_signalling=2.0,cost_land=1.5,cost_stations=600.0,cost_rolling=800.0,cost_overrun=40,constr_years=12,opex_infra_maint=0.060,opex_energy=8.0,opex_staff=6.0,opex_rs_maint=5.0,opex_overhead=50.0,trains_day=30,op_days=350,annual_pax=4.0,demand_growth=2.0,pax_biz=20,pax_com=15,avg_fare=35.0,fare_growth=0.5,current_time=720,upgrade_time=540,hsr_time=270,vot_biz=22.0,vot_com=9.0,vot_lei=5.0,vot_growth=2.5,co2_price=80.0,co2_per_mpax=20000,modal_shift_air=20,modal_shift_car=10,generated_share=10,accident_ben=0.4,congestion=5.0,webs_pct=15,discount=4.0,appraisal_yrs=40,residual_pct=30,counterfactual_capex=4000.0,counterfactual_opex_yr=120.0,access_egress_hsr=25,access_egress_conv=15),
    "🇸🇰 Brno–Bratislava": dict(line_length_km=130,pct_tunnel=6,pct_viaduct=5,cost_at_grade=17.0,cost_tunnel=75.0,cost_viaduct=42.0,cost_signalling=1.5,cost_land=1.0,cost_stations=250.0,cost_rolling=350.0,cost_overrun=0,constr_years=6,opex_infra_maint=0.060,opex_energy=8.0,opex_staff=6.0,opex_rs_maint=5.0,opex_overhead=20.0,trains_day=40,op_days=350,annual_pax=5.0,demand_growth=1.5,pax_biz=25,pax_com=30,avg_fare=18.0,fare_growth=0.5,current_time=90,upgrade_time=65,hsr_time=35,vot_biz=26.0,vot_com=11.0,vot_lei=6.0,vot_growth=2.0,co2_price=80.0,co2_per_mpax=12000,modal_shift_air=5,modal_shift_car=20,generated_share=12,accident_ben=0.4,congestion=10.0,webs_pct=12,discount=4.0,appraisal_yrs=40,residual_pct=30,counterfactual_capex=600.0,counterfactual_opex_yr=25.0,access_egress_hsr=10,access_egress_conv=6),
}

FLYVBJERG_COST_UPLIFT = 0.447   # Flyvbjerg et al. (2002): median rail cost overrun
FLYVBJERG_DEMAND_FACTOR = 0.487 # Flyvbjerg et al. (2005): median demand shortfall

# ════════════════════════════════════════════════════════════════
# DEFAULT PARAMETER VALUES (used when no preset is active)
# ════════════════════════════════════════════════════════════════
DEFAULTS = dict(
    line_length_km=230, pct_tunnel=10, pct_viaduct=8,
    cost_at_grade=18.0, cost_tunnel=80.0, cost_viaduct=45.0,
    cost_signalling=1.5, cost_land=1.0, cost_stations=400.0,
    cost_rolling=600.0, cost_overrun=0, constr_years=8,
    counterfactual_capex=1500.0, counterfactual_opex_yr=55.0,
    opex_infra_maint=0.060, opex_energy=8.0, opex_staff=6.0,
    opex_rs_maint=5.0, opex_overhead=30.0, trains_day=60, op_days=350,
    annual_pax=9.0, demand_growth=1.5, pax_biz=25, pax_com=30,
    modal_shift_air=10, modal_shift_car=20, generated_share=15,
    avg_fare=25.0, fare_growth=0.5,
    current_time=150, upgrade_time=100, hsr_time=60,
    vot_biz=28.0, vot_com=12.0, vot_lei=7.0, vot_growth=2.0,
    co2_price=80.0, co2_per_mpax=15000, accident_ben=0.5,
    congestion=15.0, webs_pct=15,
    discount=4.0, appraisal_yrs=40, residual_pct=30,
    access_egress_hsr=12, access_egress_conv=8,
    # Socio-economic toggles
    include_webs=True, include_congestion=True,
    include_accidents=True, include_freq_rel=True,
    include_env_air=True, include_env_car=True,
)

# ════════════════════════════════════════════════════════════════
# CBA ENGINE
# ════════════════════════════════════════════════════════════════

def build_inputs(sidebar_vals):
    """Merge sidebar values with defaults to produce a complete param dict."""
    p = DEFAULTS.copy()
    p.update(sidebar_vals)
    return p


def compute_capex(p):
    """Calculate total HSR CAPEX from route geometry and unit costs."""
    L = p['line_length_km']
    pt = p['pct_tunnel'] / 100
    pv = p['pct_viaduct'] / 100
    pa = max(0, 1 - pt - pv)
    infra = L * (pa * p['cost_at_grade'] + pt * p['cost_tunnel']
                 + pv * p['cost_viaduct'] + p['cost_signalling'] + p['cost_land'])
    capex_hsr = (infra + p['cost_stations'] + p['cost_rolling']) * (1 + p['cost_overrun'] / 100)
    return capex_hsr


def run_cba(p):
    """
    Core CBA engine. Returns (summary_dict, annual_cashflow_DataFrame).

    The model is strictly incremental: all net benefits are computed as
    HSR scenario minus counterfactual (conventional upgrade).
    """
    L = p['line_length_km']
    pt, pv = p['pct_tunnel'] / 100, p['pct_viaduct'] / 100
    pa = max(0, 1 - pt - pv)

    # --- CAPEX ---
    infra = L * (pa * p['cost_at_grade'] + pt * p['cost_tunnel']
                 + pv * p['cost_viaduct'] + p['cost_signalling'] + p['cost_land'])
    capex_hsr = (infra + p['cost_stations'] + p['cost_rolling']) * (1 + p['cost_overrun'] / 100)
    capex_cf = p['counterfactual_capex']
    capex_incr = capex_hsr - capex_cf

    CY = int(p['constr_years'])
    AY = int(p['appraisal_yrs'])
    dr = p['discount'] / 100
    train_km = p['trains_day'] * p['op_days'] * L

    # Passenger class shares
    biz_s = p['pax_biz'] / 100
    com_s = p['pax_com'] / 100
    lei_s = max(0, 1 - biz_s - com_s)

    # Demand source shares
    air_s = p['modal_shift_air'] / 100
    car_s = p['modal_shift_car'] / 100
    gen_s = p['generated_share'] / 100
    diverted_rail_s = max(0, 1 - air_s - car_s - gen_s)

    # Effective time saving (incl. access/egress)
    ae_hsr = p['access_egress_hsr']
    ae_conv = p['access_egress_conv']
    effective_saving_min = max(0, (p['upgrade_time'] + ae_conv) - (p['hsr_time'] + ae_hsr))

    # Toggle flags for benefit components
    inc_webs = p.get('include_webs', True)
    inc_cong = p.get('include_congestion', True)
    inc_acc = p.get('include_accidents', True)
    inc_freq = p.get('include_freq_rel', True)
    inc_env_air = p.get('include_env_air', True)
    inc_env_car = p.get('include_env_car', True)

    rows = []

    # --- Construction phase: spread CAPEX evenly ---
    capex_ann_hsr = capex_hsr / CY
    capex_ann_cf = capex_cf / CY
    for t in range(CY):
        df = 1 / (1 + dr) ** t
        rows.append(dict(
            year=t, phase='construction', pax=0,
            capex_hsr=capex_ann_hsr, capex_cf=capex_ann_cf,
            opex_hsr=0, opex_cf=0, revenue=0,
            time_biz=0, time_com=0, time_lei=0, time_gen=0,
            env_air=0, env_car=0, accident=0,
            congestion=0, webs=0, freq_rel=0, residual=0, df=df,
        ))

    # --- Operational phase ---
    for t in range(AY):
        yr = CY + t
        df = 1 / (1 + dr) ** yr
        pax = p['annual_pax'] * 1e6 * (1 + p['demand_growth'] / 100) ** t

        opex_hsr = (p['opex_infra_maint'] * L
                    + (p['opex_energy'] + p['opex_staff'] + p['opex_rs_maint']) * train_km / 1e6
                    + p['opex_overhead'])
        opex_cf = p['counterfactual_opex_yr']

        fare = p['avg_fare'] * (1 + p['fare_growth'] / 100) ** t
        rev = pax * fare / 1e6

        # Value-of-time by class (grows over time with GDP)
        vot_g = (1 + p['vot_growth'] / 100) ** t
        vot_biz_t = p['vot_biz'] * vot_g
        vot_com_t = p['vot_com'] * vot_g
        vot_lei_t = p['vot_lei'] * vot_g
        saving_hrs = effective_saving_min / 60

        # Time benefits by demand source and class
        pax_existing = pax * (diverted_rail_s + air_s + car_s)
        pax_generated = pax * gen_s

        # Existing passengers: full time benefit, split by class
        time_biz = pax_existing * biz_s * saving_hrs * vot_biz_t / 1e6
        time_com = pax_existing * com_s * saving_hrs * vot_com_t / 1e6
        time_lei = pax_existing * lei_s * saving_hrs * vot_lei_t / 1e6

        # Generated passengers: rule-of-half (50% of full benefit)
        vot_w = biz_s * vot_biz_t + com_s * vot_com_t + lei_s * vot_lei_t
        time_gen = pax_generated * saving_hrs * vot_w * 0.5 / 1e6

        # Environmental: only shifted passengers
        shifted_air_m = pax * air_s / 1e6
        shifted_car_m = pax * car_s / 1e6
        env_air = (shifted_air_m * p['co2_per_mpax'] * p['co2_price'] / 1e6) if inc_env_air else 0
        env_car = (shifted_car_m * (p['co2_per_mpax'] * 0.4) * p['co2_price'] / 1e6) if inc_env_car else 0

        # Accident benefit: only car shift
        acc = (shifted_car_m * p['accident_ben']) if inc_acc else 0

        # Congestion relief is anchored to base-year car shift and scales with shifted car passengers.
        base_shifted_car_m = p['annual_pax'] * car_s
        if inc_cong and base_shifted_car_m > 0:
            cong_unit = p['congestion'] / base_shifted_car_m
            cong = shifted_car_m * cong_unit
        else:
            cong = 0

        # WEBs as % of total time benefits
        total_time = time_biz + time_com + time_lei + time_gen
        webs = (total_time * p['webs_pct'] / 100) if inc_webs else 0

        # Frequency/reliability proxy (5% of time benefits)
        freq_rel = (total_time * 0.05) if inc_freq else 0

        rows.append(dict(
            year=yr, phase='operation', pax=pax / 1e6,
            capex_hsr=0, capex_cf=0, opex_hsr=opex_hsr, opex_cf=opex_cf,
            revenue=rev, time_biz=time_biz, time_com=time_com,
            time_lei=time_lei, time_gen=time_gen,
            env_air=env_air, env_car=env_car, accident=acc,
            congestion=cong, webs=webs, freq_rel=freq_rel, residual=0, df=df,
        ))

    # --- Residual value at end of appraisal ---
    resid_hsr = capex_hsr * p['residual_pct'] / 100
    resid_cf = capex_cf * p['residual_pct'] / 100
    rows[-1]['residual'] = resid_hsr - resid_cf

    df_all = pd.DataFrame(rows)
    df_all['time_full'] = df_all['time_biz'] + df_all['time_com'] + df_all['time_lei']

    # --- Present value columns ---
    df_all['pv_capex_incr'] = (df_all['capex_hsr'] - df_all['capex_cf']) * df_all['df']
    df_all['pv_opex_incr'] = (df_all['opex_hsr'] - df_all['opex_cf']) * df_all['df']
    df_all['pv_costs_incr'] = df_all['pv_capex_incr'] + df_all['pv_opex_incr']
    df_all['pv_capex_abs'] = df_all['capex_hsr'] * df_all['df']
    df_all['pv_opex_abs'] = df_all['opex_hsr'] * df_all['df']
    df_all['pv_costs_abs'] = df_all['pv_capex_abs'] + df_all['pv_opex_abs']

    benefit_cols = ['time_biz', 'time_com', 'time_lei', 'time_gen', 'time_full',
                    'env_air', 'env_car', 'accident', 'congestion', 'webs',
                    'freq_rel', 'residual', 'revenue']
    for col in benefit_cols:
        df_all[f'pv_{col}'] = df_all[col] * df_all['df']

    df_all['pv_benefits'] = (
        df_all['pv_time_full'] + df_all['pv_time_gen']
        + df_all['pv_env_air'] + df_all['pv_env_car']
        + df_all['pv_accident'] + df_all['pv_congestion']
        + df_all['pv_webs'] + df_all['pv_freq_rel'] + df_all['pv_residual']
    )

    # --- Summary dict ---
    S = {}
    S['capex_hsr'] = capex_hsr
    S['capex_cf'] = capex_cf
    S['capex_incr'] = capex_incr
    S['capex_per_km'] = capex_hsr / L if L > 0 else 0

    for col in ['capex_abs', 'opex_abs', 'costs_abs', 'capex_incr', 'opex_incr', 'costs_incr']:
        S[f'pv_{col}'] = df_all[f'pv_{col}'].sum()

    for col in ['time_biz', 'time_com', 'time_lei', 'time_gen', 'time_full',
                'env_air', 'env_car', 'accident', 'congestion', 'webs',
                'freq_rel', 'residual', 'revenue']:
        S[f'pv_{col}'] = df_all[f'pv_{col}'].sum()

    S['pv_time_total'] = S['pv_time_full'] + S['pv_time_gen']
    S['pv_env_total'] = S['pv_env_air'] + S['pv_env_car']
    S['pv_benefits'] = df_all['pv_benefits'].sum()

    S['bcr_abs'] = S['pv_benefits'] / S['pv_costs_abs'] if S['pv_costs_abs'] > 0 else 0
    S['bcr_incr'] = S['pv_benefits'] / S['pv_costs_incr'] if S['pv_costs_incr'] > 0 else None
    S['npv_abs'] = S['pv_benefits'] - S['pv_costs_abs']
    S['npv_incr'] = S['pv_benefits'] - S['pv_costs_incr']
    S['npv_fin'] = S['pv_revenue'] - S['pv_costs_abs']

    S['opex_yr1'] = (p['opex_infra_maint'] * L
                     + (p['opex_energy'] + p['opex_staff'] + p['opex_rs_maint']) * train_km / 1e6
                     + p['opex_overhead'])
    S['train_km_m'] = train_km / 1e6
    S['eff_saving_min'] = effective_saving_min

    # --- IRR on incremental social net flows (approximate via numpy) ---
    net_flows = []
    for _, row in df_all.iterrows():
        net = -(row['capex_hsr'] - row['capex_cf']) - (row['opex_hsr'] - row['opex_cf'])
        net += (row.get('time_full', 0) + row.get('time_gen', 0)
                + row.get('env_air', 0) + row.get('env_car', 0)
                + row.get('accident', 0) + row.get('congestion', 0)
                + row.get('webs', 0) + row.get('freq_rel', 0) + row.get('residual', 0))
        net_flows.append(net)
    try:
        S['irr'] = float(np.irr(net_flows)) * 100 if hasattr(np, 'irr') else _irr_manual(net_flows) * 100
    except Exception:
        S['irr'] = _irr_manual(net_flows) * 100

    # --- Payback on incremental social net flows ---
    discounted_net_flows = [nf * dfi for nf, dfi in zip(net_flows, df_all['df'])]

    cum_nom = 0
    S['payback_year_nominal'] = None
    for i, nf in enumerate(net_flows):
        cum_nom += nf
        if cum_nom >= 0 and i > 0:
            S['payback_year_nominal'] = i
            break

    cum_disc = 0
    S['payback_year_discounted'] = None
    for i, nf in enumerate(discounted_net_flows):
        cum_disc += nf
        if cum_disc >= 0 and i > 0:
            S['payback_year_discounted'] = i
            break

    # Backward-compatible alias for existing outputs.
    S['payback_year'] = S['payback_year_nominal']

    return S, df_all


def _irr_manual(flows):
    """Simple IRR via bisection when numpy.irr is unavailable."""
    lo, hi = -0.5, 2.0
    for _ in range(200):
        mid = (lo + hi) / 2
        npv = sum(f / (1 + mid) ** t for t, f in enumerate(flows))
        if npv > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def threshold_search(p, param, lo, hi, target_bcr=1.0, incremental=False):
    """Binary search for the value of `param` that yields BCR = target_bcr.

    Returns None when the target is not bracketed within [lo, hi].
    Assumes BCR changes monotonically over the tested interval.
    """
    def eval_bcr(value):
        pp = p.copy()
        pp[param] = value
        s, _ = run_cba(pp)
        return s['bcr_incr'] if incremental else s['bcr_abs']

    bcr_lo = eval_bcr(lo)
    bcr_hi = eval_bcr(hi)

    if bcr_lo is None or bcr_hi is None:
        return None

    if abs(bcr_lo - target_bcr) < 1e-9:
        return lo
    if abs(bcr_hi - target_bcr) < 1e-9:
        return hi

    min_bcr = min(bcr_lo, bcr_hi)
    max_bcr = max(bcr_lo, bcr_hi)
    if target_bcr < min_bcr or target_bcr > max_bcr:
        return None

    increasing = bcr_hi > bcr_lo

    for _ in range(60):
        mid = (lo + hi) / 2
        bcr_mid = eval_bcr(mid)
        if bcr_mid is None:
            return None
        if increasing:
            if bcr_mid < target_bcr:
                lo = mid
            else:
                hi = mid
        else:
            if bcr_mid < target_bcr:
                hi = mid
            else:
                lo = mid
    return (lo + hi) / 2


def run_monte_carlo(p, mc_config, n=5000):
    """
    User-configurable Monte Carlo simulation.
    mc_config: dict of {param_key: (dist_type, min_val, max_val)}
    dist_type: 'triangular', 'normal', 'uniform'
    """
    np.random.seed(42)
    results = []
    for _ in range(n):
        pp = p.copy()
        for param_key, (dist, lo, hi) in mc_config.items():
            base = p[param_key]
            if dist == 'triangular':
                pp[param_key] = max(lo, np.random.triangular(lo, base, hi))
            elif dist == 'normal':
                sigma = (hi - lo) / 4  # ±2σ covers ~95%
                pp[param_key] = max(lo, np.random.normal(base, sigma))
            elif dist == 'uniform':
                pp[param_key] = np.random.uniform(lo, hi)
            # Integer params
            if isinstance(p[param_key], int):
                pp[param_key] = int(round(pp[param_key]))
        s, _ = run_cba(pp)
        results.append(s)
    return pd.DataFrame(results)


def generate_documentation(p, S, df_all, country_name, corridor_name, overrides_count):
    """Generate a self-contained markdown documentation report."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lei_s = max(0, 100 - p['pax_biz'] - p['pax_com'])
    div_rail = max(0, 100 - p['modal_shift_air'] - p['modal_shift_car'] - p['generated_share'])
    implied_speed = p['line_length_km'] / (p['hsr_time'] / 60) if p['hsr_time'] > 0 else 0

    doc = f"""# HSR Social CBA — Documentation Report
Generated: {now}

## Project Overview
| Item | Value |
|------|-------|
| Country profile | {country_name} |
| Corridor preset | {corridor_name} |
| Parameters overridden | {overrides_count} |

## Corridor Geometry
| Parameter | Value | Unit |
|-----------|-------|------|
| Line length | {p['line_length_km']} | km |
| Tunnel share | {p['pct_tunnel']} | % |
| Viaduct share | {p['pct_viaduct']} | % |
| At-grade share | {max(0, 100 - p['pct_tunnel'] - p['pct_viaduct'])} | % |
| Implied avg speed | {implied_speed:.0f} | km/h |

## Construction Costs
| Parameter | Value | Unit |
|-----------|-------|------|
| At-grade cost | {p['cost_at_grade']} | €m/km |
| Tunnel cost | {p['cost_tunnel']} | €m/km |
| Viaduct cost | {p['cost_viaduct']} | €m/km |
| Signalling | {p['cost_signalling']} | €m/km |
| Land acquisition | {p['cost_land']} | €m/km |
| Stations | {p['cost_stations']} | €m |
| Rolling stock | {p['cost_rolling']} | €m |
| Cost overrun uplift | {p['cost_overrun']} | % |
| Construction period | {p['constr_years']} | years |
| **Total HSR CAPEX** | **{S['capex_hsr']:,.0f}** | **€m** |
| CAPEX per km | {S['capex_per_km']:.1f} | €m/km |

## Counterfactual (Upgrade)
| Parameter | Value | Unit |
|-----------|-------|------|
| Upgrade CAPEX | {p['counterfactual_capex']:,.0f} | €m |
| Upgrade annual OPEX | {p['counterfactual_opex_yr']} | €m/yr |
| Incremental CAPEX | {S['capex_incr']:,.0f} | €m |

## Demand & Revenue
| Parameter | Value | Unit |
|-----------|-------|------|
| Annual passengers (base year) | {p['annual_pax']} | million |
| Demand growth | {p['demand_growth']} | %/yr |
| Business / Commuter / Leisure | {p['pax_biz']} / {p['pax_com']} / {lei_s} | % |
| Average fare | {p['avg_fare']} | €/pax |
| Fare growth | {p['fare_growth']} | %/yr |
| Modal split: air / car / gen. / div. rail | {p['modal_shift_air']} / {p['modal_shift_car']} / {p['generated_share']} / {div_rail} | % |

## Time Savings & Value of Time
| Parameter | Value | Unit |
|-----------|-------|------|
| Current journey time | {p['current_time']} | min |
| Counterfactual (upgrade) time | {p['upgrade_time']} | min |
| HSR journey time | {p['hsr_time']} | min |
| Access/egress HSR | {p['access_egress_hsr']} | min |
| Access/egress conventional | {p['access_egress_conv']} | min |
| **Effective time saving** | **{S['eff_saving_min']:.0f}** | **min** |
| VOT business | {p['vot_biz']} | €/hr |
| VOT commuter | {p['vot_com']} | €/hr |
| VOT leisure | {p['vot_lei']} | €/hr |
| VOT growth | {p['vot_growth']} | %/yr |

## Externalities
| Parameter | Value | Unit |
|-----------|-------|------|
| CO₂ price | {p['co2_price']} | €/t |
| CO₂ saved per m shifted pax | {p['co2_per_mpax']} | t |
| Accident benefit | {p['accident_ben']} | €m/m car pax |
| Congestion relief | {p['congestion']} | €m/yr |
| WEBs | {p['webs_pct']} | % of time benefits |

## Appraisal Settings
| Parameter | Value | Unit |
|-----------|-------|------|
| Discount rate | {p['discount']} | % |
| Appraisal period | {p['appraisal_yrs']} | years |
| Residual value | {p['residual_pct']} | % of CAPEX |

## Methodology

### Demand Model
Ridership grows at a constant compound rate from the base-year figure.
Passengers are split by purpose (business, commuter, leisure) and by origin
(diverted from air, car, conventional rail, or generated/induced).

### Time Savings
Effective time saving = (counterfactual time + access/egress conventional)
− (HSR time + access/egress HSR).

For **existing passengers** (diverted from other modes and rail), the full time
saving is monetised: `pax × saving_hours × VOT_class`.

For **generated passengers**, the **rule-of-half** applies: only 50% of the
time saving is counted, reflecting that these trips did not exist before and
the average consumer surplus is half the full saving.

### Value of Time
Each passenger class has its own VOT that grows annually in real terms (proxy
for GDP/capita growth). The weighted average VOT determines the aggregate
time-benefit stream.

### Externalities
- **CO₂**: Shifted air passengers save `co2_per_mpax` tonnes per million pax;
  shifted car passengers save 40% of that rate. Valued at the shadow CO₂ price.
- **Accidents**: Avoided road accidents valued per million car passengers shifted.
- **Congestion**: Base-year annual road-congestion relief tied to base-year car shift and scaled with shifted car passengers (simplified).
- **WEBs**: Wider Economic Benefits modelled as a percentage of user time savings.
- **Frequency/reliability**: Proxy benefit at 5% of time savings.

### Discounting & NPV
All future cash flows are discounted at the social discount rate.
`NPV = PV(benefits) − PV(costs)`. BCR = PV(benefits) / PV(costs).

**Absolute perspective**: compares total HSR costs with total benefits.
**Incremental perspective**: deducts counterfactual costs from HSR costs.

If incremental PV costs are non-positive ($PV_{{costs,incr}} \le 0$), incremental BCR is
reported as `N/A` because the ratio is not economically interpretable in that case.
Interpretation should rely on incremental NPV instead.

### Residual Value
At the end of the appraisal period, a percentage of original CAPEX is
credited as residual (net of counterfactual residual).

### IRR
Internal Rate of Return here is computed on **incremental social net flows**
(HSR minus counterfactual), i.e. it is aligned with the incremental perspective.
It is solved numerically via bisection.

## Base-Case Results
| Metric | Value |
|--------|-------|
| NPV Social (absolute) | {S['npv_abs']:,.0f} €m |
| NPV Social (incremental) | {S['npv_incr']:,.0f} €m |
| NPV Financial | {S['npv_fin']:,.0f} €m |
| BCR (absolute) | {S['bcr_abs']:.3f} |
| BCR (incremental) | {format_bcr(S['bcr_incr'])} |
| IRR (incremental) | {S['irr']:.1f}% |
| Payback year (nominal, undiscounted) | {S['payback_year_nominal'] if S['payback_year_nominal'] is not None else 'Not reached'} |
| Discounted payback year (DPP) | {S['payback_year_discounted'] if S['payback_year_discounted'] is not None else 'Not reached'} |
| Commercially viable | {'Yes' if S['npv_fin'] > 0 else 'No'} |
| Socially desirable (BCR ≥ 1) | {'Yes' if S['bcr_abs'] >= 1.0 else 'No'} |

### PV Breakdown (€m)
| Component | PV (€m) |
|-----------|---------|
| Time savings (business) | {S['pv_time_biz']:,.0f} |
| Time savings (commuter) | {S['pv_time_com']:,.0f} |
| Time savings (leisure) | {S['pv_time_lei']:,.0f} |
| Time savings (generated, ½) | {S['pv_time_gen']:,.0f} |
| WEBs | {S['pv_webs']:,.0f} |
| Frequency & reliability | {S['pv_freq_rel']:,.0f} |
| Environment (air shift) | {S['pv_env_air']:,.0f} |
| Environment (car shift) | {S['pv_env_car']:,.0f} |
| Accident benefits | {S['pv_accident']:,.0f} |
| Congestion relief | {S['pv_congestion']:,.0f} |
| Residual value | {S['pv_residual']:,.0f} |
| **Total PV Benefits** | **{S['pv_benefits']:,.0f}** |
| CAPEX HSR (PV) | {S['pv_capex_abs']:,.0f} |
| OPEX HSR (PV) | {S['pv_opex_abs']:,.0f} |
| **Total PV Costs (abs)** | **{S['pv_costs_abs']:,.0f}** |
| Revenue (PV) | {S['pv_revenue']:,.0f} |

---
*Report generated by HSR Social CBA Sensitivity Analyser. Model limitations:
simplified cashflow, no distributional analysis, no phasing/real options,
deterministic counterfactual.*
"""
    return doc


# ════════════════════════════════════════════════════════════════
# STREAMLIT UI
# ════════════════════════════════════════════════════════════════

st.markdown("# 🚄 HSR Social CBA Sensitivity Analyser")
st.markdown(
    "Interactive tool for social cost–benefit analysis of high-speed rail corridors. "
    "Select a country profile and corridor preset, adjust parameters, and explore results."
)

# ──────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────

with st.sidebar:
    # ── Presets ──
    st.header("⚡ Presets")

    country_name = st.selectbox(
        "Country socio-economic profile",
        list(COUNTRY_PRESETS.keys()),
        help="Sets default values for VOT, discount rate, CO₂ price, and other "
             "socio-economic parameters based on national appraisal guidelines.",
    )
    country_profile = COUNTRY_PRESETS.get(country_name, {})

    corridor_name = st.selectbox(
        "Project / corridor preset",
        list(CORRIDOR_PRESETS.keys()),
        help="Loads corridor-specific engineering and demand parameters. "
             "You can override any value below.",
    )
    corridor_preset = CORRIDOR_PRESETS.get(corridor_name, {})

    # Merge: corridor overrides country, user overrides both
    merged_preset = {}
    merged_preset.update(country_profile)
    merged_preset.update(corridor_preset)

    def pv(key):
        """Get effective default: preset > DEFAULTS."""
        return merged_preset.get(key, DEFAULTS[key])

    # Track overrides for badge
    if 'user_overrides' not in st.session_state:
        st.session_state['user_overrides'] = set()

    def track_slider(key, val):
        preset_val = merged_preset.get(key, DEFAULTS[key])
        if val != preset_val:
            st.session_state['user_overrides'].add(key)
        else:
            st.session_state['user_overrides'].discard(key)

    overrides_count = len(st.session_state.get('user_overrides', set()))
    if overrides_count > 0:
        st.caption(f"🔧 {overrides_count} parameter(s) modified from preset")
    else:
        st.caption("All parameters at preset defaults")

    # ── Geometry & Infrastructure ──
    st.header("📐 Geometry & Infrastructure")
    with st.expander("ℹ️ About this section"):
        st.markdown(
            "Route geometry drives construction cost. Tunnel and viaduct shares "
            "multiply the per-km cost significantly. Access/egress times affect "
            "the *effective* journey-time saving, which feeds into time-benefit "
            "calculations."
        )

    line_length_km = st.slider("Line length (km)", 50, 1200, pv('line_length_km'), 10,
        help="Total route length. Enters CAPEX = Σ(share × unit_cost × length) and OPEX (maintenance per km).")
    pct_tunnel = st.slider("Tunnel share (%)", 0, 60, pv('pct_tunnel'),
        help="Tunnels cost 3–10× more than at-grade. Typical: 0–40%.")
    pct_viaduct = st.slider("Viaduct share (%)", 0, 40, pv('pct_viaduct'),
        help="Viaducts cost 2–4× more than at-grade. Typical: 0–20%.")
    at_grade_pct = max(0, 100 - pct_tunnel - pct_viaduct)
    st.caption(f"At-grade share: {at_grade_pct}%")
    access_egress_hsr = st.slider("Access/egress HSR (min)", 0, 45, pv('access_egress_hsr'),
        help="Door-to-platform time for HSR station. Affects effective time saving.")
    access_egress_conv = st.slider("Access/egress conventional (min)", 0, 30, pv('access_egress_conv'),
        help="Door-to-platform time for conventional station.")

    # ── Construction Costs ──
    st.header("🏗️ Construction Costs")
    with st.expander("ℹ️ About this section"):
        st.markdown(
            "Total CAPEX = infrastructure (at-grade + tunnel + viaduct + signalling + land) × length "
            "+ stations + rolling stock, all uplifted by the cost-overrun factor.\n\n"
            "**Formula**: `CAPEX = [L × (pa×C_ag + pt×C_tu + pv×C_vi + C_sig + C_land) + Stations + RS] × (1 + overrun%)`"
        )

    cost_at_grade = st.slider("At-grade (€m/km)", 5.0, 80.0, pv('cost_at_grade'), 0.5,
        help="Surface-level track. Typical: 8–55 €m/km depending on terrain and land cost.")
    cost_tunnel = st.slider("Tunnel (€m/km)", 20.0, 250.0, pv('cost_tunnel'), 5.0,
        help="Bored or cut-and-cover tunnel. Typical: 40–200 €m/km.")
    cost_viaduct = st.slider("Viaduct (€m/km)", 15.0, 150.0, pv('cost_viaduct'), 5.0,
        help="Elevated structure. Typical: 25–100 €m/km.")
    cost_signalling = st.slider("Signalling (€m/km)", 0.5, 5.0, pv('cost_signalling'), 0.1,
        help="ERTMS/ETCS and control systems. Typical: 1–3 €m/km.")
    cost_land = st.slider("Land acquisition (€m/km)", 0.2, 8.0, pv('cost_land'), 0.2,
        help="Right-of-way purchase. Typical: 0.5–6 €m/km (higher near cities).")
    cost_stations = st.slider("Stations total (€m)", 50.0, 3000.0, pv('cost_stations'), 50.0,
        help="All station construction/renovation. Major terminus can exceed 1 bn €.")
    cost_rolling = st.slider("Rolling stock (€m)", 0.0, 4000.0, pv('cost_rolling'), 50.0,
        help="Fleet purchase. Set 0 if operator-supplied (e.g. HS1/Eurostar).")
    cost_overrun = st.slider("Cost overrun uplift (%)", 0, 100, pv('cost_overrun'),
        help="Optimism-bias adjustment. Flyvbjerg reference: +44.7% median for rail.")
    constr_years = st.slider("Construction period (yr)", 3, 20, pv('constr_years'),
        help="Ground-breaking to revenue service. CAPEX is spread linearly.")

    # Derived info
    capex_preview = compute_capex(dict(
        line_length_km=line_length_km, pct_tunnel=pct_tunnel, pct_viaduct=pct_viaduct,
        cost_at_grade=cost_at_grade, cost_tunnel=cost_tunnel, cost_viaduct=cost_viaduct,
        cost_signalling=cost_signalling, cost_land=cost_land,
        cost_stations=cost_stations, cost_rolling=cost_rolling, cost_overrun=cost_overrun,
    ))
    st.caption(f"💰 Implied total CAPEX: **{capex_preview:,.0f} €m** · {capex_preview / line_length_km:.1f} €m/km")

    # ── Counterfactual ──
    st.header("🔀 Counterfactual (Upgrade)")
    with st.expander("ℹ️ About this section"):
        st.markdown(
            "The counterfactual is the alternative investment — typically upgrading "
            "the existing conventional rail line. The CBA measures the *incremental* "
            "value of HSR over this baseline. Higher counterfactual costs improve "
            "the incremental BCR."
        )
    counterfactual_capex = st.slider("Upgrade CAPEX total (€m)", 0.0, 10000.0, pv('counterfactual_capex'), 100.0,
        help="Total capital cost of the do-minimum or upgrade scenario.")
    counterfactual_opex_yr = st.slider("Upgrade annual OPEX (€m)", 0.0, 300.0, pv('counterfactual_opex_yr'), 5.0,
        help="Annual operating cost of the counterfactual network.")

    # ── Operating Costs ──
    st.header("🔧 Operating Costs (HSR)")
    with st.expander("ℹ️ About this section"):
        st.markdown(
            "Annual OPEX = infrastructure maintenance (per km) + variable costs "
            "(energy, staff, RS maintenance per train-km) + fixed overhead.\n\n"
            "**Formula**: `OPEX = maint×L + (energy + staff + RS_maint) × train_km / 1e6 + overhead`"
        )
    opex_infra_maint = st.slider("Infra maint. (€m/km/yr)", 0.020, 0.150, pv('opex_infra_maint'), 0.005,
        help="Annual infrastructure maintenance cost per route-km. Typical: 0.03–0.10.")
    opex_energy = st.slider("Energy (€/train-km)", 2.0, 25.0, pv('opex_energy'), 0.5,
        help="Traction electricity cost. Typical: 5–15 €/train-km.")
    opex_staff = st.slider("Staff (€/train-km)", 2.0, 20.0, pv('opex_staff'), 0.5,
        help="On-board + operations staff cost. Typical: 4–12 €/train-km.")
    opex_rs_maint = st.slider("RS maintenance (€/train-km)", 1.0, 15.0, pv('opex_rs_maint'), 0.5,
        help="Rolling stock maintenance. Typical: 3–8 €/train-km.")
    opex_overhead = st.slider("Overhead (€m/yr)", 5.0, 100.0, pv('opex_overhead'), 5.0,
        help="Fixed annual costs: admin, insurance, marketing, etc.")
    trains_day = st.slider("Trains per day", 10, 200, pv('trains_day'), 5,
        help="Both directions. Drives total train-km and OPEX.")
    op_days = st.slider("Operating days/yr", 300, 365, pv('op_days'), 5,
        help="Revenue service days (exclude maintenance windows).")
    # Derived
    _train_km = trains_day * op_days * line_length_km
    st.caption(f"🚆 Annual train-km: {_train_km / 1e6:.1f} million")

    # ── Demand & Fares ──
    st.header("👥 Demand & Fares")
    with st.expander("ℹ️ About this section"):
        st.markdown(
            "Base-year ridership grows at a constant compound rate. Passengers are "
            "split by trip purpose (business, commuter, leisure) — this determines "
            "the weighted value of time. Demand is further split by origin: shifted "
            "from air, car, conventional rail, or newly generated."
        )
    annual_pax = st.slider("Annual passengers (million)", 1.0, 60.0, pv('annual_pax'), 0.5,
        help="Base-year ridership. Multiplied by demand growth each year.")
    demand_growth = st.slider("Demand growth (%/yr)", 0.0, 5.0, pv('demand_growth'), 0.1,
        help="Compound annual growth. Typical: 0.5–2.5% for mature markets.")
    pax_biz = st.slider("Business share (%)", 5, 60, pv('pax_biz'),
        help="Higher VOT passengers. Typical: 15–40%.")
    pax_com = st.slider("Commuter share (%)", 5, 60, pv('pax_com'),
        help="Regular commuters. Typical: 15–35%.")
    lei_s_pct = max(0, 100 - pax_biz - pax_com)
    st.caption(f"Leisure share: {lei_s_pct}%")
    avg_fare = st.slider("Average fare (€/pax)", 5.0, 120.0, pv('avg_fare'), 1.0,
        help="Mean ticket price, base year. Revenue = pax × fare.")
    fare_growth = st.slider("Real fare growth (%/yr)", 0.0, 3.0, pv('fare_growth'), 0.1,
        help="Above-inflation annual fare increase.")
    # Derived
    implied_pax_km = annual_pax * 1e6 * line_length_km
    cost_per_pax_km = (capex_preview * 1e6 / (implied_pax_km * int(pv('appraisal_yrs')))) if implied_pax_km > 0 else 0
    st.caption(f"💶 Implied fare/km: {avg_fare / line_length_km * 100:.1f} c€/km · Cost/pax-km (CAPEX only, undiscounted): {cost_per_pax_km:.3f} €")

    # ── Demand Source Split ──
    st.header("🔀 Demand Source Split")
    with st.expander("ℹ️ About this section"):
        st.markdown(
            "How HSR passengers are sourced:\n"
            "- **Shifted from air/car**: get full time benefits and externality benefits "
            "(CO₂, accidents, congestion).\n"
            "- **Diverted from conv. rail**: get full time benefits but no externality gains.\n"
            "- **Generated (induced)**: new trips that did not exist before. Only 50% of "
            "time benefit counted (rule-of-half)."
        )
    modal_shift_air = st.slider("Shifted from air (%)", 0, 60, pv('modal_shift_air'),
        help="Air passengers switching to HSR. CO₂ benefits apply.")
    modal_shift_car = st.slider("Shifted from car (%)", 0, 60, pv('modal_shift_car'),
        help="Car passengers switching. Accident + congestion benefits apply.")
    generated_share = st.slider("Generated demand (%)", 0, 40, pv('generated_share'),
        help="Induced trips. Rule-of-half for time benefits.")
    div_rail_pct = max(0, 100 - modal_shift_air - modal_shift_car - generated_share)
    st.caption(f"Diverted from conv. rail: {div_rail_pct}%")

    # ── Journey Times ──
    st.header("⏱️ Journey Times")
    with st.expander("ℹ️ About this section"):
        st.markdown(
            "Three journey-time scenarios are defined (excluding access/egress, which "
            "is handled separately). The effective time saving used in CBA is:\n\n"
            "`Δt = (upgrade_time + access_conv) − (hsr_time + access_hsr)`"
        )
    current_time = st.slider("Current journey (min)", 30, 600, pv('current_time'), 5,
        help="Today's journey time. For reference only (CBA uses upgrade vs HSR).")
    upgrade_time = st.slider("Upgrade counterfactual (min)", 20, 400, pv('upgrade_time'), 5,
        help="Journey time after the counterfactual upgrade investment.")
    hsr_time = st.slider("HSR journey (min)", 15, 240, pv('hsr_time'), 5,
        help="Journey time on the new HSR line.")
    # Derived
    eff_save = max(0, (upgrade_time + access_egress_conv) - (hsr_time + access_egress_hsr))
    implied_speed = line_length_km / (hsr_time / 60) if hsr_time > 0 else 0
    st.caption(f"⏱️ Effective time saving: **{eff_save} min** · Implied avg speed: **{implied_speed:.0f} km/h**")

    # ── Value of Time ──
    st.header("💰 Value of Time")
    with st.expander("ℹ️ About this section"):
        st.markdown(
            "VOT converts time savings into monetary values. Each passenger class has "
            "a different VOT. Business VOT is typically 2–5× leisure. VOT grows over "
            "time with GDP per capita (real growth).\n\n"
            "**Weighted VOT** = Σ(share_class × VOT_class). This enters: "
            "`Time benefit = pax × Δt_hours × weighted_VOT`."
        )
    vot_biz = st.slider("VOT business (€/hr)", 10.0, 90.0, pv('vot_biz'), 1.0,
        help="UK TAG: ~£31/hr ≈ €36; France: ~€46; Germany: ~€30.")
    vot_com = st.slider("VOT commuter (€/hr)", 4.0, 40.0, pv('vot_com'), 1.0,
        help="Typically 40–60% of business VOT.")
    vot_lei = st.slider("VOT leisure (€/hr)", 2.0, 25.0, pv('vot_lei'), 1.0,
        help="Typically 20–40% of business VOT.")
    vot_growth = st.slider("VOT real growth (%/yr)", 0.0, 4.0, pv('vot_growth'), 0.1,
        help="Linked to GDP/capita growth. EU CEE typical: 1.5–2.5%.")
    # Derived
    _wvot = (pax_biz / 100) * vot_biz + (pax_com / 100) * vot_com + (lei_s_pct / 100) * vot_lei
    st.caption(f"⚖️ Weighted average VOT: **{_wvot:.1f} €/hr**")

    # ── Externalities & WEBs ──
    st.header("🌍 Externalities & WEBs")
    with st.expander("ℹ️ About this section"):
        st.markdown(
            "External benefits accrue to society, not the operator:\n"
            "- **CO₂**: Emission savings from modal shift (air, car → rail).\n"
            "- **Accidents**: Avoided road deaths and injuries.\n"
            "- **Congestion**: Reduced road congestion from modal shift.\n"
            "- **WEBs** (Wider Economic Benefits): Agglomeration, labour market, "
            "and competition effects. Typically modelled as 10–25% of user time savings.\n\n"
            "The 'rule of half' note: WEBs are calculated on *all* time benefits "
            "(including the half-benefit for generated demand)."
        )
    co2_price = st.slider("CO₂ price (€/t)", 10.0, 300.0, pv('co2_price'), 5.0,
        help="Shadow carbon price. EU ETS 2024: ~60–80 €/t; social cost: 80–200 €/t.")
    co2_per_mpax = st.slider("CO₂ saved (t/m shifted pax)", 5000, 40000, pv('co2_per_mpax'), 1000,
        help="Tonnes CO₂ avoided per million pax shifted from air. Typical: 10k–25k.")
    accident_ben = st.slider("Accident benefit (€m/m car pax)", 0.0, 3.0, pv('accident_ben'), 0.1,
        help="Monetised avoided accidents per million car passengers shifted.")
    congestion = st.slider("Congestion relief (€m/yr)", 0.0, 80.0, pv('congestion'), 1.0,
        help="Annual road congestion cost reduction. Depends on corridor congestion level.")
    webs_pct = st.slider("WEBs (% of time benefits)", 0, 50, pv('webs_pct'),
        help="Wider Economic Benefits. UK DfT guidance: 10–25% for well-connected corridors.")

    # ── Socio-economic Settings (toggles) ──
    st.header("⚙️ Socio-economic Settings")
    with st.expander("ℹ️ About component toggles"):
        st.markdown(
            "Toggle individual benefit components on/off to see their impact on results. "
            "This is useful for understanding which benefits drive the BCR and for "
            "testing conservative scenarios."
        )
    include_webs = st.checkbox("Include WEBs", value=True,
        help="Wider Economic Benefits (agglomeration, competition, labour market).")
    include_congestion = st.checkbox("Include congestion relief", value=True,
        help="Road congestion reduction from modal shift.")
    include_accidents = st.checkbox("Include accident benefits", value=True,
        help="Avoided road accidents from car→rail shift.")
    include_freq_rel = st.checkbox("Include frequency/reliability proxy", value=True,
        help="Proxy for improved frequency and reliability (5% of time benefits).")
    include_env_air = st.checkbox("Include CO₂ savings (air shift)", value=True,
        help="CO₂ emission reductions from air→rail modal shift.")
    include_env_car = st.checkbox("Include CO₂ savings (car shift)", value=True,
        help="CO₂ emission reductions from car→rail modal shift.")

    # ── Appraisal Settings ──
    st.header("📊 Appraisal Settings")
    with st.expander("ℹ️ About this section"):
        st.markdown(
            "- **Discount rate**: reflects the social opportunity cost of capital. "
            "EU CBA guide suggests 3–5% for transport projects.\n"
            "- **Appraisal period**: how many operational years to evaluate. "
            "Typical: 30–60 years for rail infrastructure.\n"
            "- **Residual value**: share of original CAPEX assumed recoverable "
            "at appraisal end (infrastructure has long design life)."
        )
    discount = st.slider("Discount rate (%)", 1.0, 8.0, pv('discount'), 0.5,
        help="Social discount rate. EU standard: 3–5%. UK Green Book: 3.5%.")
    appraisal_yrs = st.slider("Appraisal period (yr)", 20, 60, pv('appraisal_yrs'), 5,
        help="Operating years in the appraisal. Typical: 30–60 for rail.")
    residual_pct = st.slider("Residual value (% capex)", 0, 60, pv('residual_pct'), 5,
        help="Share of CAPEX treated as residual value at end of appraisal.")

# ──────────────────────────────────────────
# BUILD PARAMS AND RUN CBA
# ──────────────────────────────────────────

params = build_inputs(dict(
    line_length_km=line_length_km, pct_tunnel=pct_tunnel, pct_viaduct=pct_viaduct,
    cost_at_grade=cost_at_grade, cost_tunnel=cost_tunnel, cost_viaduct=cost_viaduct,
    cost_signalling=cost_signalling, cost_land=cost_land, cost_stations=cost_stations,
    cost_rolling=cost_rolling, cost_overrun=cost_overrun, constr_years=constr_years,
    opex_infra_maint=opex_infra_maint, opex_energy=opex_energy, opex_staff=opex_staff,
    opex_rs_maint=opex_rs_maint, opex_overhead=opex_overhead, trains_day=trains_day,
    op_days=op_days, annual_pax=annual_pax, demand_growth=demand_growth,
    pax_biz=pax_biz, pax_com=pax_com, avg_fare=avg_fare, fare_growth=fare_growth,
    current_time=current_time, upgrade_time=upgrade_time, hsr_time=hsr_time,
    vot_biz=vot_biz, vot_com=vot_com, vot_lei=vot_lei, vot_growth=vot_growth,
    co2_price=co2_price, co2_per_mpax=co2_per_mpax, modal_shift_air=modal_shift_air,
    modal_shift_car=modal_shift_car, generated_share=generated_share,
    accident_ben=accident_ben, congestion=congestion, webs_pct=webs_pct,
    discount=discount, appraisal_yrs=appraisal_yrs, residual_pct=residual_pct,
    counterfactual_capex=counterfactual_capex, counterfactual_opex_yr=counterfactual_opex_yr,
    access_egress_hsr=access_egress_hsr, access_egress_conv=access_egress_conv,
    include_webs=include_webs, include_congestion=include_congestion,
    include_accidents=include_accidents, include_freq_rel=include_freq_rel,
    include_env_air=include_env_air, include_env_car=include_env_car,
))

S, df_all = run_cba(params)

# ════════════════════════════════════════════════════════════════
# RESULTS — Tabbed Layout
# ════════════════════════════════════════════════════════════════

tab_exec, tab_detail, tab_sens, tab_mc, tab_compare, tab_method, tab_audit, tab_doc = st.tabs([
    "📋 Executive Summary",
    "📊 Detailed Results",
    "🌪️ Sensitivity",
    "🎲 Monte Carlo",
    "🔄 Corridor Comparison",
    "📖 Methodology",
    "🔍 Audit Trail",
    "📄 Documentation",
])

# ──────────────────────────────────────────
# TAB: Executive Summary
# ──────────────────────────────────────────
with tab_exec:
    st.markdown("## Executive Summary")

    # Active preset info
    active_labels = []
    if country_name != "— No profile —":
        active_labels.append(f"Country: **{country_name}**")
    if corridor_name != "— Custom —":
        active_labels.append(f"Corridor: **{corridor_name}**")
    if active_labels:
        st.markdown(" · ".join(active_labels))

    # Key metrics row
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    bcr_emoji = "🟢" if S['bcr_abs'] >= 1 else ("🟡" if S['bcr_abs'] >= 0.7 else "🔴")
    c1.metric("Social BCR (abs)", f"{bcr_emoji} {S['bcr_abs']:.3f}")
    c2.metric("Social BCR (incr)", format_bcr(S['bcr_incr']))
    c3.metric("NPV Social (€m)", f"{S['npv_abs']:,.0f}")
    c4.metric("NPV Financial (€m)", f"{S['npv_fin']:,.0f}")
    c5.metric("IRR incr (%)", f"{S['irr']:.1f}", help="Computed on incremental social net flows (HSR minus counterfactual).")
    c6.metric(
        "Payback nom. (yr)",
        f"{S['payback_year_nominal']}" if S['payback_year_nominal'] is not None else "N/A",
        help="Undiscounted incremental payback period based on incremental social net flows.",
    )

    c7, c8, c9, c10 = st.columns(4)
    c7.metric("CAPEX total (€m)", f"{S['capex_hsr']:,.0f}")
    c8.metric("CAPEX/km (€m)", f"{S['capex_per_km']:.1f}")
    c9.metric("Eff. time saving (min)", f"{S['eff_saving_min']:.0f}")
    c10.metric("Annual OPEX (€m)", f"{S['opex_yr1']:.0f}")
    st.caption(
        f"Discounted payback (DPP, incr): "
        f"{S['payback_year_discounted'] if S['payback_year_discounted'] is not None else 'N/A'} years"
    )

    # Qualitative flags
    st.markdown("### Qualitative Assessment")
    flags_col1, flags_col2, flags_col3 = st.columns(3)
    with flags_col1:
        if S['bcr_abs'] >= 1.0:
            st.success("✅ Socially desirable (BCR ≥ 1.0)")
        elif S['bcr_abs'] >= 0.7:
            st.warning("⚠️ Marginal social case (0.7 ≤ BCR < 1.0)")
        else:
            st.error("❌ Poor social case (BCR < 0.7)")
    with flags_col2:
        if S['npv_fin'] > 0:
            st.success("✅ Commercially viable (NPV fin > 0)")
        else:
            st.warning("⚠️ Requires subsidy (NPV fin < 0)")
    with flags_col3:
        if not is_defined_metric(S['bcr_incr']):
            st.info("ℹ️ Incremental BCR not meaningful when incremental PV costs are non-positive.")
        elif S['bcr_incr'] >= 1.0:
            st.success("✅ Better than upgrade (incr BCR ≥ 1)")
        else:
            st.warning("⚠️ Upgrade may be preferable (incr BCR < 1)")

    # BCR gauge
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number", value=S['bcr_abs'],
        gauge=dict(
            axis=dict(range=[0, 3]),
            bar=dict(color="#20B2FF"),
            steps=[
                dict(range=[0, 0.7], color="#FF6B6B"),
                dict(range=[0.7, 1.0], color="#FFB347"),
                dict(range=[1.0, 1.5], color="#88D498"),
                dict(range=[1.5, 3.0], color="#1FBFAE"),
            ],
            threshold=dict(line=dict(color="white", width=3), value=1.0),
        ),
        title=dict(text="Social BCR (absolute)"),
    ))
    fig_gauge.update_layout(height=250, margin=dict(t=80, b=20, l=40, r=40))
    st.plotly_chart(fig_gauge, use_container_width=True)

    # Reference Class Forecasting
    st.markdown("---")
    st.markdown("### Reference Class Forecasting Check")
    st.caption("Flyvbjerg et al. (2002, 2005): median rail cost overrun +44.7%, demand at 48.7% of forecast")
    st.caption("RCF CAPEX first removes your current cost-overrun uplift to recover the pre-uplift base CAPEX, then applies the Flyvbjerg median uplift of +44.7%. This replaces your overrun assumption for the RCF check; it does not stack on top of it.")
    col_rcf1, col_rcf2 = st.columns(2)
    with col_rcf1:
        adj_capex = S['capex_hsr'] * (1 + FLYVBJERG_COST_UPLIFT) / (1 + cost_overrun / 100)
        adj_pax = annual_pax * FLYVBJERG_DEMAND_FACTOR
        st.metric("RCF-adjusted CAPEX (€m)", f"{adj_capex:,.0f}",
                  delta=f"+{(adj_capex - S['capex_hsr']):,.0f} vs your estimate", delta_color="inverse")
        st.metric("RCF-adjusted demand (m pax)", f"{adj_pax:.1f}",
                  delta=f"{(adj_pax - annual_pax):.1f} vs your estimate", delta_color="inverse")
    with col_rcf2:
        rcf_params = params.copy()
        rcf_params['cost_overrun'] = FLYVBJERG_COST_UPLIFT * 100
        rcf_params['annual_pax'] = adj_pax
        S_rcf, _ = run_cba(rcf_params)
        bcr_col_rcf = "🟢" if S_rcf['bcr_abs'] >= 1 else ("🟡" if S_rcf['bcr_abs'] >= 0.7 else "🔴")
        st.metric("RCF Social BCR (absolute)", f"{bcr_col_rcf} {S_rcf['bcr_abs']:.3f}")
        st.metric("RCF Social NPV (€m)", f"{S_rcf['npv_abs']:,.0f}")
        st.metric("RCF Social BCR (incremental)", format_bcr(S_rcf['bcr_incr']))


# ──────────────────────────────────────────
# TAB: Detailed Results
# ──────────────────────────────────────────
with tab_detail:
    st.markdown("## PV Breakdown (€m)")

    col_b, col_c = st.columns(2)
    with col_b:
        ben_items = [
            ("Time: business",           S['pv_time_biz'],   "#20B2FF"),
            ("Time: commuter",           S['pv_time_com'],   "#5BC8F5"),
            ("Time: leisure",            S['pv_time_lei'],   "#87CEEB"),
            ("Time: generated (½)",      S['pv_time_gen'],   "#B0E0E6"),
            ("WEBs",                     S['pv_webs'],       "#9B8AFF"),
            ("Freq. & reliability",      S['pv_freq_rel'],   "#C4B5FD"),
            ("Congestion relief",        S['pv_congestion'], "#1FBFAE"),
            ("Env. (air shift)",         S['pv_env_air'],    "#FFB347"),
            ("Env. (car shift)",         S['pv_env_car'],    "#FBBF24"),
            ("Accident savings",         S['pv_accident'],   "#88D498"),
            ("Residual value",           S['pv_residual'],   "#9AA0A6"),
        ]
        fig_b = go.Figure()
        for name, val, color in ben_items:
            fig_b.add_trace(go.Bar(
                x=[val], y=[name], orientation='h', marker_color=color,
                name=name, text=f"{val:.0f}", textposition='outside',
            ))
        fig_b.update_layout(title="PV Benefits", height=450, showlegend=False,
                            margin=dict(l=10, r=10, t=40, b=10), xaxis_title="€m")
        fig_b.update_traces(cliponaxis=False)
        st.plotly_chart(fig_b, use_container_width=True)

    with col_c:
        fig_c = go.Figure()
        fig_c.add_trace(go.Bar(x=[S['pv_capex_abs']], y=["CAPEX HSR"], orientation='h',
                               marker_color="#FF6B6B", text=f"{S['pv_capex_abs']:.0f}", textposition='outside'))
        fig_c.add_trace(go.Bar(x=[S['pv_opex_abs']], y=["OPEX HSR"], orientation='h',
                               marker_color="#FFB347", text=f"{S['pv_opex_abs']:.0f}", textposition='outside'))
        fig_c.add_trace(go.Bar(x=[S['pv_capex_incr']], y=["CAPEX incremental"], orientation='h',
                               marker_color="#9B8AFF", text=f"{S['pv_capex_incr']:.0f}", textposition='outside'))
        fig_c.add_trace(go.Bar(x=[S['pv_revenue']], y=["Revenue (financial)"], orientation='h',
                               marker_color="#1FBFAE", text=f"{S['pv_revenue']:.0f}", textposition='outside'))
        fig_c.update_layout(title="PV Costs & Revenue", height=300, showlegend=False,
                            margin=dict(l=10, r=10, t=40, b=10), xaxis_title="€m")
        fig_c.update_traces(cliponaxis=False)
        st.plotly_chart(fig_c, use_container_width=True)

    # Benefit composition pie
    ben_labels = [b[0] for b in ben_items]
    ben_vals = [b[1] for b in ben_items]
    ben_colors = [b[2] for b in ben_items]
    fig_pie = go.Figure(go.Pie(
        labels=ben_labels, values=[max(0, v) for v in ben_vals],
        marker=dict(colors=ben_colors), textinfo='percent+label', hole=0.4,
    ))
    fig_pie.update_layout(title="Benefit Composition", height=380, margin=dict(t=40, b=10))
    st.plotly_chart(fig_pie, use_container_width=True)

    # Detailed result table
    st.markdown("### Detailed Component Table")
    detail_data = {
        "Component": [
            "Time savings (business)", "Time savings (commuter)", "Time savings (leisure)",
            "Time savings (generated, ½)", "WEBs", "Frequency & reliability",
            "CO₂ savings (air)", "CO₂ savings (car)", "Accident savings",
            "Congestion relief", "Residual value", "——", "Total PV Benefits",
            "——", "CAPEX HSR (PV)", "OPEX HSR (PV)", "Total PV Costs (abs)",
            "——", "Revenue (PV)",
        ],
        "PV (€m)": [
            S['pv_time_biz'], S['pv_time_com'], S['pv_time_lei'],
            S['pv_time_gen'], S['pv_webs'], S['pv_freq_rel'],
            S['pv_env_air'], S['pv_env_car'], S['pv_accident'],
            S['pv_congestion'], S['pv_residual'], None, S['pv_benefits'],
            None, S['pv_capex_abs'], S['pv_opex_abs'], S['pv_costs_abs'],
            None, S['pv_revenue'],
        ],
        "Role": [
            "Benefit (existing pax)", "Benefit (existing pax)", "Benefit (existing pax)",
            "Benefit (generated pax, ½)", "Externality (all pax)", "Benefit (all pax)",
            "Externality (shifted air)", "Externality (shifted car)", "Externality (shifted car)",
            "Externality (shifted car)", "Appraisal", "", "",
            "", "Cost", "Cost", "", "", "Revenue (operator)",
        ],
    }
    detail_df = pd.DataFrame(detail_data)
    st.dataframe(detail_df, use_container_width=True, hide_index=True)

    # Threshold analysis
    st.markdown("### Threshold Analysis — Break-even for BCR = 1.0")
    st.caption("Each threshold is computed holding all other parameters at current values.")
    st.caption("`N/A` means BCR = 1.0 is outside the tested range for that parameter.")
    th1, th2, th3, th4 = st.columns(4)
    try:
        th_pax = threshold_search(params, 'annual_pax', 0.5, 80, 1.0)
        th1.metric("Min. annual pax (m)", f"{th_pax:.1f}" if th_pax is not None else "N/A")
    except Exception:
        th1.metric("Min. annual pax (m)", "N/A")
    try:
        th_cost = threshold_search(params, 'cost_at_grade', 1, 200, 1.0)
        th2.metric("Max. at-grade cost (€m/km)", f"{th_cost:.1f}" if th_cost is not None else "N/A")
    except Exception:
        th2.metric("Max. at-grade cost (€m/km)", "N/A")
    try:
        th_time = threshold_search(params, 'hsr_time', 1, 300, 1.0)
        if th_time is None:
            th3.metric("Min. eff. time saving (min)", "N/A")
        else:
            th_save = (upgrade_time + access_egress_conv) - (th_time + access_egress_hsr)
            th3.metric("Min. eff. time saving (min)", f"{max(0, th_save):.0f}")
    except Exception:
        th3.metric("Min. eff. time saving (min)", "N/A")
    try:
        th_vot = threshold_search(params, 'vot_biz', 5, 200, 1.0)
        th4.metric("Min. VOT business (€/hr)", f"{th_vot:.0f}" if th_vot is not None else "N/A")
    except Exception:
        th4.metric("Min. VOT business (€/hr)", "N/A")

    # Annual profile
    st.markdown("### Annual Cash-flow Profile")
    op_df = df_all[df_all['phase'] == 'operation'].copy()
    op_df['year_op'] = range(1, len(op_df) + 1)
    op_df['net_social'] = (
        op_df['time_full'] + op_df['time_gen'] + op_df['env_air'] + op_df['env_car']
        + op_df['accident'] + op_df['congestion'] + op_df['webs'] + op_df['freq_rel']
        - op_df['opex_hsr'] + op_df['opex_cf']
    )
    op_df['net_financial'] = op_df['revenue'] - op_df['opex_hsr']

    fig_annual = go.Figure()
    fig_annual.add_trace(go.Scatter(
        x=op_df['year_op'], y=op_df['time_full'] + op_df['time_gen'],
        name='Time benefits', fill='tozeroy', line=dict(color='#20B2FF'),
    ))
    fig_annual.add_trace(go.Scatter(
        x=op_df['year_op'], y=op_df['revenue'],
        name='Revenue', line=dict(color='#1FBFAE', dash='dash'),
    ))
    fig_annual.add_trace(go.Scatter(
        x=op_df['year_op'], y=op_df['opex_hsr'],
        name='OPEX', line=dict(color='#FF6B6B', dash='dot'),
    ))
    fig_annual.add_trace(go.Scatter(
        x=op_df['year_op'], y=op_df['net_social'],
        name='Net social (excl capex)', line=dict(color='#9B8AFF', width=2),
    ))
    fig_annual.update_layout(
        height=400, xaxis_title="Year of operation", yaxis_title="€m/year",
        legend=dict(orientation='h', y=1.12),
    )
    st.plotly_chart(fig_annual, use_container_width=True)


# ──────────────────────────────────────────
# TAB: Sensitivity
# ──────────────────────────────────────────
with tab_sens:
    st.markdown("## Sensitivity Analysis")

    sens_col1, sens_col2 = st.columns([1, 1])

    with sens_col1:
        st.markdown("### Tornado Diagram Settings")
        st.caption("Select parameters to include and set the variation range.")
        tornado_pct = st.slider("Variation range (±%)", 5, 50, 20, 5,
            help="Percentage variation applied symmetrically to each parameter.",
            key="tornado_pct")

    # Available parameters for tornado
    TORNADO_CANDIDATES = [
        ('annual_pax', 'Demand'), ('cost_at_grade', 'At-grade cost'),
        ('cost_tunnel', 'Tunnel cost'), ('pct_tunnel', 'Tunnel share'),
        ('vot_biz', 'VOT business'), ('vot_com', 'VOT commuter'),
        ('vot_lei', 'VOT leisure'),
        ('discount', 'Discount rate'), ('constr_years', 'Constr. period'),
        ('hsr_time', 'HSR time'), ('upgrade_time', 'Counterfact. time'),
        ('webs_pct', 'WEBs'), ('congestion', 'Congestion relief'),
        ('cost_overrun', 'Cost overrun'), ('trains_day', 'Trains/day'),
        ('modal_shift_air', 'Air shift'), ('modal_shift_car', 'Car shift'),
        ('access_egress_hsr', 'Access HSR'), ('co2_price', 'CO₂ price'),
        ('demand_growth', 'Demand growth'), ('cost_rolling', 'Rolling stock'),
        ('cost_stations', 'Stations cost'), ('generated_share', 'Generated demand'),
        ('residual_pct', 'Residual value %'),
    ]

    with sens_col2:
        default_tornado = [c[0] for c in TORNADO_CANDIDATES[:18]]
        selected_tornado = st.multiselect(
            "Parameters to include in tornado",
            options=[c[0] for c in TORNADO_CANDIDATES],
            default=default_tornado,
            format_func=lambda x: dict(TORNADO_CANDIDATES).get(x, x),
            key="tornado_params",
        )

    # Target metric
    sens_metric = st.radio(
        "Sensitivity target metric", ["BCR (absolute)", "BCR (incremental)", "NPV (absolute)"],
        horizontal=True, key="sens_metric",
    )

    # Compute tornado
    base_bcr = S['bcr_abs']
    base_bcr_incr = S['bcr_incr']
    base_npv = S['npv_abs']
    mult_lo = 1 - tornado_pct / 100
    mult_hi = 1 + tornado_pct / 100

    t_data = []
    label_map = dict(TORNADO_CANDIDATES)
    for pname in selected_tornado:
        label = label_map.get(pname, pname)
        bv = params[pname]
        for mult, direction in [(mult_lo, 'low'), (mult_hi, 'high')]:
            tv = bv * mult
            if bv == 0:
                tv = (20 if direction == 'high' else 0)
            tv = max(0, tv)
            if isinstance(bv, int):
                tv = int(round(tv))
            pp = params.copy()
            pp[pname] = tv
            ss, _ = run_cba(pp)
            if sens_metric == "BCR (absolute)":
                val = ss['bcr_abs']
            elif sens_metric == "BCR (incremental)":
                val = ss['bcr_incr']
            else:
                val = ss['npv_abs']
            t_data.append(dict(param=label, direction=direction, value=val))

    if sens_metric == "BCR (incremental)" and not is_defined_metric(base_bcr_incr):
        st.info("Incremental BCR tornado is unavailable when incremental PV costs are non-positive in the base case.")
    elif t_data:
        t_df = pd.DataFrame(t_data)
        if sens_metric == "BCR (incremental)":
            t_df = t_df.dropna(subset=['value'])
            valid_params = t_df.groupby('param')['direction'].nunique()
            valid_params = valid_params[valid_params == 2].index
            t_df = t_df[t_df['param'].isin(valid_params)]

        if t_df.empty:
            st.info("No valid incremental BCR points are available in the tested sensitivity range.")
        else:
            pivot = t_df.pivot(index='param', columns='direction', values='value').reset_index()
            pivot['range'] = abs(pivot['high'] - pivot['low'])
            pivot = pivot.sort_values('range', ascending=True)

            if sens_metric == "BCR (absolute)":
                base_val = base_bcr
                x_title = "Social BCR (absolute)"
            elif sens_metric == "BCR (incremental)":
                base_val = base_bcr_incr
                x_title = "Social BCR (incremental)"
            else:
                base_val = base_npv
                x_title = "Social NPV (€m)"

            fig_torn = go.Figure()
            fig_torn.add_trace(go.Bar(
                y=pivot['param'], x=pivot['low'] - base_val, base=base_val,
                orientation='h', name=f'−{tornado_pct}%', marker_color='#1FBFAE',
            ))
            fig_torn.add_trace(go.Bar(
                y=pivot['param'], x=pivot['high'] - base_val, base=base_val,
                orientation='h', name=f'+{tornado_pct}%', marker_color='#20B2FF',
            ))
            fig_torn.add_vline(x=base_val, line_dash="dash", line_color="white")
            if "BCR" in sens_metric:
                fig_torn.add_vline(x=1.0, line_dash="dot", line_color="#FF6B6B")
            else:
                fig_torn.add_vline(x=0, line_dash="dot", line_color="#FF6B6B")
            fig_torn.update_layout(
                barmode='overlay', height=max(400, len(pivot) * 28),
                legend=dict(orientation='h', y=1.05),
                xaxis_title=x_title, margin=dict(l=10),
            )
            st.plotly_chart(fig_torn, use_container_width=True)
    else:
        st.info("Select at least one parameter for the tornado diagram.")


# ──────────────────────────────────────────
# TAB: Monte Carlo
# ──────────────────────────────────────────
with tab_mc:
    st.markdown("## Monte Carlo Simulation")
    st.markdown(
        "Configure which parameters to vary, their ranges, and probability distributions. "
        "Results show the probability distribution of key CBA metrics."
    )

    MC_PARAMS = [
        ('annual_pax', 'Demand (m pax)'),
        ('cost_at_grade', 'At-grade cost (€m/km)'),
        ('cost_tunnel', 'Tunnel cost (€m/km)'),
        ('cost_overrun', 'Cost overrun (%)'),
        ('vot_biz', 'VOT business (€/hr)'),
        ('vot_com', 'VOT commuter (€/hr)'),
        ('demand_growth', 'Demand growth (%/yr)'),
        ('constr_years', 'Construction years'),
        ('discount', 'Discount rate (%)'),
        ('co2_price', 'CO₂ price (€/t)'),
        ('webs_pct', 'WEBs (%)'),
        ('generated_share', 'Generated demand (%)'),
    ]

    mc_n = st.slider("Number of simulations", 1000, 20000, 5000, 1000, key="mc_n",
        help="More simulations give smoother distributions but take longer.")

    st.markdown("### Parameter Distributions")
    st.caption("For each selected parameter, set the distribution type and min/max bounds. The base-case value is used as the mode (triangular) or mean (normal).")

    mc_config = {}
    mc_cols = st.columns(3)

    for idx, (pkey, plabel) in enumerate(MC_PARAMS):
        col = mc_cols[idx % 3]
        with col:
            with st.expander(f"**{plabel}**", expanded=(idx < 6)):
                base = params[pkey]
                include = st.checkbox(f"Include", value=(idx < 8), key=f"mc_inc_{pkey}")
                if include:
                    dist = st.selectbox("Distribution", ["triangular", "normal", "uniform"],
                                        key=f"mc_dist_{pkey}")
                    lo = st.number_input("Min", value=round(base * 0.5, 2), key=f"mc_lo_{pkey}")
                    hi = st.number_input("Max", value=round(base * 1.5, 2), key=f"mc_hi_{pkey}")
                    mc_config[pkey] = (dist, lo, hi)

    if st.button("▶️ Run Monte Carlo", key="run_mc"):
        with st.spinner(f"Running {mc_n:,} simulations..."):
            mc_df = run_monte_carlo(params, mc_config, n=mc_n)
        st.session_state['mc_results'] = mc_df

    if 'mc_results' in st.session_state:
        mc_df = st.session_state['mc_results']

        mc_col1, mc_col2, mc_col3, mc_col4 = st.columns(4)
        mc_col1.metric("P(BCR > 1.0)", f"{(mc_df['bcr_abs'] >= 1).mean() * 100:.1f}%")
        mc_col2.metric("P(NPV > 0)", f"{(mc_df['npv_abs'] > 0).mean() * 100:.1f}%")
        mc_col3.metric("Median BCR", f"{mc_df['bcr_abs'].median():.3f}")
        mc_col4.metric("P05–P95 BCR", f"{mc_df['bcr_abs'].quantile(0.05):.2f} – {mc_df['bcr_abs'].quantile(0.95):.2f}")

        mc_stat1, mc_stat2, mc_stat3, mc_stat4 = st.columns(4)
        mc_stat1.metric("Mean BCR", f"{mc_df['bcr_abs'].mean():.3f}")
        mc_stat2.metric("Mean NPV (€m)", f"{mc_df['npv_abs'].mean():,.0f}")
        mc_stat3.metric("Median NPV (€m)", f"{mc_df['npv_abs'].median():,.0f}")
        mc_stat4.metric("P05–P95 NPV", f"{mc_df['npv_abs'].quantile(0.05):,.0f} – {mc_df['npv_abs'].quantile(0.95):,.0f}")

        fig_mc = go.Figure()
        fig_mc.add_trace(go.Histogram(
            x=mc_df['bcr_abs'], nbinsx=80, marker_color='#20B2FF', opacity=0.7, name='BCR distribution',
        ))
        fig_mc.add_vline(x=1.0, line_dash="dash", line_color="#FF6B6B", annotation_text="BCR=1")
        fig_mc.add_vline(x=mc_df['bcr_abs'].median(), line_dash="dot", line_color="#1FBFAE", annotation_text="Median")
        fig_mc.update_layout(height=350, xaxis_title="Social BCR (absolute)", yaxis_title="Frequency", bargap=0.05)
        st.plotly_chart(fig_mc, use_container_width=True)

        fig_mc2 = go.Figure()
        fig_mc2.add_trace(go.Histogram(x=mc_df['npv_abs'], nbinsx=80, marker_color='#9B8AFF', opacity=0.7))
        fig_mc2.add_vline(x=0, line_dash="dash", line_color="#FF6B6B", annotation_text="NPV=0")
        fig_mc2.update_layout(height=300, xaxis_title="Social NPV absolute (€m)", yaxis_title="Frequency", bargap=0.05)
        st.plotly_chart(fig_mc2, use_container_width=True)
    else:
        st.info("Configure parameters above and click **Run Monte Carlo** to generate results.")


# ──────────────────────────────────────────
# TAB: Corridor Comparison
# ──────────────────────────────────────────
with tab_compare:
    st.markdown("## Corridor Comparison")
    st.caption("Runs all corridor presets through the CBA engine with your current country profile and socio-economic settings.")

    comp_rows = []
    for name, pdata in CORRIDOR_PRESETS.items():
        if not pdata:
            continue
        full_p = params.copy()
        full_p.update(pdata)
        ss, _ = run_cba(full_p)
        comp_rows.append(dict(
            Corridor=name,
            **{k: round(v, 2) if isinstance(v, float) else v for k, v in ss.items()},
        ))

    comp_df = pd.DataFrame(comp_rows)
    display_cols = ['Corridor', 'capex_hsr', 'capex_per_km', 'bcr_abs', 'bcr_incr',
                    'npv_abs', 'npv_fin', 'irr', 'eff_saving_min', 'opex_yr1']
    rename = {
        'capex_hsr': 'CAPEX (€m)', 'capex_per_km': '€m/km', 'bcr_abs': 'BCR abs',
        'bcr_incr': 'BCR incr', 'npv_abs': 'NPV soc (€m)', 'npv_fin': 'NPV fin (€m)',
        'irr': 'IRR incr (%)', 'eff_saving_min': 'Eff. Δt (min)', 'opex_yr1': 'OPEX yr1 (€m)',
    }
    available_cols = [c for c in display_cols if c in comp_df.columns]
    st.dataframe(
        comp_df[available_cols].rename(columns=rename).style.format({
            'CAPEX (€m)': '{:,.0f}', '€m/km': '{:.1f}', 'BCR abs': '{:.3f}',
            'BCR incr': lambda v: format_bcr(v), 'NPV soc (€m)': '{:,.0f}', 'NPV fin (€m)': '{:,.0f}',
            'IRR incr (%)': '{:.1f}', 'Eff. Δt (min)': '{:.0f}', 'OPEX yr1 (€m)': '{:.0f}',
        }),
        use_container_width=True, height=600,
    )

    # Scatter: BCR vs CAPEX
    if len(comp_rows) > 1:
        fig_scatter = px.scatter(
            comp_df, x='capex_hsr', y='bcr_abs', text='Corridor',
            labels={'capex_hsr': 'Total CAPEX (€m)', 'bcr_abs': 'Social BCR (absolute)'},
            title="BCR vs. CAPEX across corridors",
        )
        fig_scatter.add_hline(y=1.0, line_dash="dot", line_color="#FF6B6B")
        fig_scatter.update_traces(textposition='top center', marker=dict(size=12, color='#20B2FF'))
        fig_scatter.update_layout(height=400)
        st.plotly_chart(fig_scatter, use_container_width=True)


# ──────────────────────────────────────────
# TAB: Methodology
# ──────────────────────────────────────────
with tab_method:
    st.markdown("## Methodology & Assumptions")

    st.markdown("### Modelling Chain Overview")
    st.markdown("""
This tool implements a **social cost–benefit analysis (CBA)** framework for high-speed rail projects.
The analysis is **strictly incremental**: it compares the HSR investment against an explicit
counterfactual (conventional rail upgrade), and reports both incremental and absolute perspectives.
""")

    st.markdown("### Demand Model")
    st.markdown("""
- **Base-year ridership** grows at a constant compound annual rate over the appraisal period.
- Passengers are split by **trip purpose** (business, commuter, leisure) — each with distinct VOT.
- Passengers are further split by **origin**: diverted from air, car, conventional rail, or newly generated.
- **No endogenous mode-choice model** is used; modal shares are user-specified.
""")

    st.markdown("### Generalised Cost & Time Savings")
    st.markdown(r"""
The effective time saving is:

$$\Delta t = (t_{upgrade} + a_{conv}) - (t_{HSR} + a_{HSR})$$

where $t$ is in-vehicle time and $a$ is access/egress time.
""")

    st.markdown("### Monetisation of Time Benefits")
    st.markdown(r"""
For **existing passengers** (diverted from other modes), full time benefit applies:

$$B_{time}^{exist} = \sum_{class} pax_{exist} \times s_{class} \times \Delta t_{hours} \times VOT_{class}$$

For **generated (induced) passengers**, the **rule-of-half** applies:

$$B_{time}^{gen} = pax_{gen} \times \Delta t_{hours} \times \overline{VOT} \times 0.5$$

This reflects that generated trips value the improvement at half the full saving on average,
as these travellers were on the margin of travelling before the improvement.
""")

    st.markdown("### Externalities")
    st.markdown("""
| Category | Applied to | Formula |
|----------|-----------|---------|
| CO₂ savings (air) | Shifted air pax | shifted_air_m × CO₂_per_mpax × CO₂_price |
| CO₂ savings (car) | Shifted car pax | shifted_car_m × 0.4 × CO₂_per_mpax × CO₂_price |
| Accident savings | Shifted car pax | shifted_car_m × accident_benefit_rate |
| Congestion relief | Shifted car pax | shifted_car_m × congestion_unit, where congestion_unit is calibrated from the base year |
| WEBs | All pax (via time) | webs_pct% × total_time_benefits |
| Frequency/reliability | All pax (via time) | 5% × total_time_benefits (proxy) |
""")

    st.markdown("### Discounting, NPV, BCR, IRR")
    st.markdown(r"""
All future cash flows are discounted at the **social discount rate** $r$:

$$PV = \sum_{t=0}^{T} \frac{CF_t}{(1+r)^t}$$

- **NPV** = PV(benefits) − PV(costs)
- **BCR** = PV(benefits) / PV(costs)
- **IRR (incremental)** = the discount rate at which incremental social NPV = 0 (solved numerically)
- **Nominal payback (incremental)** = first year where cumulative **undiscounted** incremental net flow ≥ 0
- **Discounted payback, DPP (incremental)** = first year where cumulative **discounted** incremental net flow ≥ 0

**Absolute** perspective: PV(costs) includes all HSR CAPEX and OPEX.
**Incremental** perspective: PV(costs) deducts the counterfactual CAPEX and OPEX.

If incremental PV costs are non-positive ($PV_{costs,incr} \le 0$), incremental BCR is
reported as `N/A` because the ratio is not economically interpretable in that case.
Interpretation should rely on incremental NPV instead.
""")

    st.markdown("### Residual Value")
    st.markdown("""
At the end of the appraisal period, a percentage of original CAPEX is credited as residual value
(reflecting the long design life of rail infrastructure), net of the counterfactual's residual.
""")

    st.markdown("### Reference Class Forecasting")
    st.markdown("""
Based on Flyvbjerg et al. (2002, 2005):
- **Cost uplift**: median rail project cost overrun of +44.7%.
- **Demand shortfall**: actual demand is typically 48.7% of forecast.

For CAPEX, the RCF check first removes the user's current cost-overrun uplift to recover
the pre-uplift base CAPEX, and then applies the Flyvbjerg median uplift of +44.7%.
This means the RCF cost assumption **replaces** the user's overrun assumption rather than
stacking on top of it. The RCF check then reports the adjusted BCR/NPV.
""")

    st.markdown("### Key Limitations")
    st.markdown("""
1. **Simplified demand model**: constant growth, no endogenous mode choice.
2. **Linear construction profile**: CAPEX spread evenly over construction years.
3. **No distributional analysis**: equity and regional impacts not modelled.
4. **No real options or phasing**: the full project is evaluated as a single decision.
5. **Static counterfactual**: no dynamic feedback between scenarios.
6. **Average-cost externalities**: uses unit costs, not marginal damage functions.
7. **No agglomeration micro-model**: WEBs are a fixed percentage of time benefits.
""")


# ──────────────────────────────────────────
# TAB: Audit Trail
# ──────────────────────────────────────────
with tab_audit:
    st.markdown("## Audit Trail — Annual Cash Flows")
    st.markdown(
        "Complete year-by-year breakdown of all CBA components. "
        "Download as CSV for external audit or replication."
    )

    # Show key formulas
    with st.expander("📐 Formulas used in this model"):
        st.markdown("""
**CAPEX** = [L × (pa×C_atgrade + pt×C_tunnel + pv×C_viaduct + C_signal + C_land) + Stations + RS] × (1 + overrun%)

**Annual OPEX** = infra_maint × L + (energy + staff + rs_maint) × train_km/1e6 + overhead

**Time benefit (existing)** = pax_existing × Δt_hours × Σ(share_class × VOT_class × VOT_growth^t)

**Time benefit (generated)** = pax_generated × Δt_hours × weighted_VOT × 0.5

**Discount factor** = 1 / (1 + r)^t

**NPV** = Σ(benefits_t × df_t) − Σ(costs_t × df_t)

**BCR** = Σ(benefits_t × df_t) / Σ(costs_t × df_t)

**IRR (incremental)** = rate r* such that Σ(net_flow_incr,t / (1+r*)^t) = 0

**Nominal payback (incremental)** = first t where Σ(net_flow_incr,k) from k=0..t ≥ 0

**Discounted payback, DPP (incremental)** = first t where Σ(net_flow_incr,k/(1+r)^k) from k=0..t ≥ 0
        """)

    # Display annual data
    display_df = df_all.copy()
    display_df = display_df.round(3)
    st.dataframe(display_df, use_container_width=True, height=500)

    # Download buttons
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        summary_export = pd.DataFrame([S]).T
        summary_export.columns = ['Value']
        st.download_button(
            "📥 Download Summary (CSV)",
            summary_export.to_csv(), "hsr_cba_summary.csv", "text/csv",
        )
    with col_exp2:
        st.download_button(
            "📥 Download Annual Cash Flows (CSV)",
            df_all.to_csv(index=False), "hsr_cba_cashflows.csv", "text/csv",
        )

    # Parameter snapshot
    st.markdown("### Input Parameter Snapshot")
    param_snapshot = pd.DataFrame([
        {"Parameter": PARAM_META.get(k, (k, "", "", ""))[0],
         "Value": v,
         "Unit": PARAM_META.get(k, ("", "", "", ""))[1],
         "Role": PARAM_META.get(k, ("", "", "", ""))[3]}
        for k, v in sorted(params.items())
        if k in PARAM_META
    ])
    st.dataframe(param_snapshot, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────
# TAB: Documentation
# ──────────────────────────────────────────
with tab_doc:
    st.markdown("## Generate Documentation Report")
    st.markdown(
        "Produces a self-contained markdown report documenting all inputs, methodology, "
        "and base-case results. Suitable for external review and audit."
    )

    if st.button("📄 Generate Report", key="gen_doc"):
        doc_md = generate_documentation(params, S, df_all, country_name, corridor_name, overrides_count)
        st.session_state['doc_report'] = doc_md

    if 'doc_report' in st.session_state:
        doc_md = st.session_state['doc_report']
        st.download_button(
            "📥 Download Report (.md)",
            doc_md, "hsr_cba_report.md", "text/markdown",
        )
        with st.expander("Preview report", expanded=True):
            st.markdown(doc_md)


# ════════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("""
<div style='font-size:11px; color:#666;'>
<b>HSR Social CBA Sensitivity Analyser v3.0</b> — Extended model with country profiles, incremental analysis,
access/egress, demand source decomposition (rule-of-half for generated demand),
time-benefit breakdown by passenger class, frequency/reliability proxy, configurable Monte Carlo,
reference class forecasting, IRR, payback year, and corridor comparison.<br>
Companion to: <i>"When is HSR Worthwhile? Lessons from Western Europe and Implications for Central and Eastern Europe"</i>
(Nash, Jandová, Paleta, Król, 2026).<br>
Model limitations: simplified cashflow, no distributional analysis, no phasing/real options,
deterministic counterfactual. See Methodology tab for full documentation.
</div>
""", unsafe_allow_html=True)
