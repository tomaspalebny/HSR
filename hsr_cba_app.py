import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="HSR CBA Analyser", layout="wide", page_icon="🚄")


def is_defined_metric(value):
    return value is not None and not pd.isna(value)


def format_bcr(value, digits=3):
    return f"{value:.{digits}f}" if is_defined_metric(value) else "N/A"

# ============================================================
# PRESETS
# ============================================================
PRESETS = {
    "— Custom —": {},
    "🇫🇷 TGV Paris–Lyon": dict(line_length_km=409,pct_tunnel=2,pct_viaduct=3,cost_at_grade=16.0,cost_tunnel=60.0,cost_viaduct=40.0,cost_signalling=1.2,cost_land=0.8,cost_stations=300.0,cost_rolling=800.0,cost_overrun=0,constr_years=6,opex_infra_maint=0.060,opex_energy=9.0,opex_staff=8.0,opex_rs_maint=6.0,opex_overhead=50.0,trains_day=150,op_days=360,annual_pax=52.0,demand_growth=0.5,pax_biz=35,pax_com=25,avg_fare=50.0,fare_growth=0.3,current_time=240,upgrade_time=180,hsr_time=120,vot_biz=50.0,vot_com=22.0,vot_lei=12.0,vot_growth=1.0,co2_price=80.0,co2_per_mpax=18000,modal_shift_air=30,modal_shift_car=15,generated_share=10,accident_ben=0.4,congestion=25.0,webs_pct=15,discount=4.0,appraisal_yrs=40,residual_pct=30,counterfactual_capex=2000.0,counterfactual_opex_yr=80.0,access_egress_hsr=15,access_egress_conv=10),
    "🇫🇷 LGV Est": dict(line_length_km=300,pct_tunnel=5,pct_viaduct=4,cost_at_grade=22.0,cost_tunnel=75.0,cost_viaduct=45.0,cost_signalling=1.5,cost_land=1.2,cost_stations=350.0,cost_rolling=500.0,cost_overrun=10,constr_years=8,opex_infra_maint=0.060,opex_energy=9.0,opex_staff=8.0,opex_rs_maint=6.0,opex_overhead=40.0,trains_day=50,op_days=355,annual_pax=14.0,demand_growth=1.0,pax_biz=30,pax_com=20,avg_fare=55.0,fare_growth=0.3,current_time=280,upgrade_time=200,hsr_time=140,vot_biz=50.0,vot_com=22.0,vot_lei=12.0,vot_growth=1.0,co2_price=80.0,co2_per_mpax=15000,modal_shift_air=20,modal_shift_car=10,generated_share=12,accident_ben=0.4,congestion=10.0,webs_pct=12,discount=4.0,appraisal_yrs=40,residual_pct=30,counterfactual_capex=1500.0,counterfactual_opex_yr=60.0,access_egress_hsr=12,access_egress_conv=8),
    "🇪🇸 AVE Madrid–Barcelona": dict(line_length_km=621,pct_tunnel=8,pct_viaduct=10,cost_at_grade=10.0,cost_tunnel=55.0,cost_viaduct=30.0,cost_signalling=1.2,cost_land=0.6,cost_stations=400.0,cost_rolling=700.0,cost_overrun=0,constr_years=10,opex_infra_maint=0.050,opex_energy=7.0,opex_staff=5.0,opex_rs_maint=4.5,opex_overhead=40.0,trains_day=45,op_days=360,annual_pax=5.0,demand_growth=1.5,pax_biz=25,pax_com=15,avg_fare=55.0,fare_growth=0.3,current_time=360,upgrade_time=280,hsr_time=155,vot_biz=38.0,vot_com=16.0,vot_lei=9.0,vot_growth=1.2,co2_price=80.0,co2_per_mpax=20000,modal_shift_air=35,modal_shift_car=8,generated_share=10,accident_ben=0.3,congestion=8.0,webs_pct=12,discount=4.0,appraisal_yrs=40,residual_pct=30,counterfactual_capex=2500.0,counterfactual_opex_yr=90.0,access_egress_hsr=20,access_egress_conv=12),
    "🇪🇸 AVE Madrid–Seville": dict(line_length_km=471,pct_tunnel=4,pct_viaduct=6,cost_at_grade=8.0,cost_tunnel=50.0,cost_viaduct=28.0,cost_signalling=1.0,cost_land=0.5,cost_stations=250.0,cost_rolling=400.0,cost_overrun=0,constr_years=6,opex_infra_maint=0.050,opex_energy=7.0,opex_staff=5.0,opex_rs_maint=4.5,opex_overhead=30.0,trains_day=35,op_days=360,annual_pax=7.0,demand_growth=1.0,pax_biz=25,pax_com=15,avg_fare=45.0,fare_growth=0.3,current_time=330,upgrade_time=240,hsr_time=140,vot_biz=35.0,vot_com=14.0,vot_lei=8.0,vot_growth=1.2,co2_price=80.0,co2_per_mpax=18000,modal_shift_air=25,modal_shift_car=10,generated_share=8,accident_ben=0.3,congestion=5.0,webs_pct=10,discount=4.0,appraisal_yrs=40,residual_pct=30,counterfactual_capex=1800.0,counterfactual_opex_yr=70.0,access_egress_hsr=18,access_egress_conv=10),
    "🇬🇧 HS1": dict(line_length_km=108,pct_tunnel=37,pct_viaduct=5,cost_at_grade=35.0,cost_tunnel=100.0,cost_viaduct=60.0,cost_signalling=2.5,cost_land=5.0,cost_stations=800.0,cost_rolling=0.0,cost_overrun=0,constr_years=7,opex_infra_maint=0.080,opex_energy=12.0,opex_staff=10.0,opex_rs_maint=7.0,opex_overhead=40.0,trains_day=55,op_days=360,annual_pax=26.0,demand_growth=1.5,pax_biz=40,pax_com=25,avg_fare=65.0,fare_growth=0.3,current_time=120,upgrade_time=90,hsr_time=55,vot_biz=60.0,vot_com=28.0,vot_lei=14.0,vot_growth=1.0,co2_price=80.0,co2_per_mpax=12000,modal_shift_air=30,modal_shift_car=5,generated_share=10,accident_ben=0.5,congestion=30.0,webs_pct=18,discount=3.5,appraisal_yrs=40,residual_pct=25,counterfactual_capex=1200.0,counterfactual_opex_yr=50.0,access_egress_hsr=10,access_egress_conv=8),
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

FLYVBJERG_COST_UPLIFT = 0.447
FLYVBJERG_DEMAND_FACTOR = 0.487

# ============================================================
# CBA ENGINE (extended)
# ============================================================
def run_cba(p):
    L = p['line_length_km']
    pt, pv = p['pct_tunnel']/100, p['pct_viaduct']/100
    pa = max(0, 1 - pt - pv)

    infra = L * (pa*p['cost_at_grade'] + pt*p['cost_tunnel'] + pv*p['cost_viaduct'] + p['cost_signalling'] + p['cost_land'])
    capex_hsr = (infra + p['cost_stations'] + p['cost_rolling']) * (1 + p['cost_overrun']/100)
    capex_cf = p['counterfactual_capex']
    capex_incr = capex_hsr - capex_cf

    CY, AY = int(p['constr_years']), int(p['appraisal_yrs'])
    dr = p['discount'] / 100
    train_km = p['trains_day'] * p['op_days'] * L

    biz_s = p['pax_biz']/100
    com_s = p['pax_com']/100
    lei_s = max(0, 1 - biz_s - com_s)

    air_s = p['modal_shift_air']/100
    car_s = p['modal_shift_car']/100
    gen_s = p['generated_share']/100
    diverted_rail_s = max(0, 1 - air_s - car_s - gen_s)

    ae_hsr = p['access_egress_hsr']
    ae_conv = p['access_egress_conv']
    effective_saving_min = (p['upgrade_time'] + ae_conv) - (p['hsr_time'] + ae_hsr)
    effective_saving_min = max(effective_saving_min, 0)

    rows = []

    # Construction
    capex_ann_hsr = capex_hsr / CY
    capex_ann_cf = capex_cf / CY
    for t in range(CY):
        df = 1/(1+dr)**t
        rows.append(dict(year=t, phase='construction', pax=0,
            capex_hsr=capex_ann_hsr, capex_cf=capex_ann_cf, opex_hsr=0, opex_cf=0,
            revenue=0, time_full=0, time_gen=0, env_air=0, env_car=0, accident=0,
            congestion=0, webs=0, freq_rel=0, residual=0, df=df))

    # Operation
    for t in range(AY):
        yr = CY + t
        df = 1/(1+dr)**yr
        pax = p['annual_pax']*1e6 * (1+p['demand_growth']/100)**t

        opex_hsr = (p['opex_infra_maint']*L + 
                    (p['opex_energy']+p['opex_staff']+p['opex_rs_maint'])*train_km/1e6 + 
                    p['opex_overhead'])
        opex_cf = p['counterfactual_opex_yr']

        fare = p['avg_fare'] * (1+p['fare_growth']/100)**t
        rev = pax * fare / 1e6

        vot_g = (1+p['vot_growth']/100)**t
        vot_w = (biz_s*p['vot_biz'] + com_s*p['vot_com'] + lei_s*p['vot_lei']) * vot_g
        saving_hrs = effective_saving_min / 60

        # Time benefits by demand source
        pax_existing = pax * (diverted_rail_s + air_s + car_s)
        pax_generated = pax * gen_s
        time_full = pax_existing * saving_hrs * vot_w / 1e6
        time_gen = pax_generated * saving_hrs * vot_w * 0.5 / 1e6  # rule of half

        # Environmental: only shifted pax
        shifted_air = pax * air_s / 1e6
        shifted_car = pax * car_s / 1e6
        env_air = shifted_air * p['co2_per_mpax'] * p['co2_price'] / 1e6
        env_car = shifted_car * (p['co2_per_mpax']*0.4) * p['co2_price'] / 1e6

        # Accident: only car shift
        acc = shifted_car * p['accident_ben']

        # Congestion is anchored to base-year car shift and scales with shifted car passengers.
        base_shifted_car = p['annual_pax'] * car_s
        if base_shifted_car > 0:
            cong_unit = p['congestion'] / base_shifted_car
            cong = shifted_car * cong_unit
        else:
            cong = 0

        # WEBs
        total_time = time_full + time_gen
        webs = total_time * p['webs_pct']/100

        # Frequency/reliability proxy (5% of time benefits)
        freq_rel = total_time * 0.05

        rows.append(dict(year=yr, phase='operation', pax=pax/1e6,
            capex_hsr=0, capex_cf=0, opex_hsr=opex_hsr, opex_cf=opex_cf,
            revenue=rev, time_full=time_full, time_gen=time_gen,
            env_air=env_air, env_car=env_car, accident=acc,
            congestion=cong, webs=webs, freq_rel=freq_rel, residual=0, df=df))

    # Residual
    resid_hsr = capex_hsr * p['residual_pct']/100
    resid_cf = capex_cf * p['residual_pct']/100
    rows[-1]['residual'] = resid_hsr - resid_cf

    df_all = pd.DataFrame(rows)

    # PV calculations
    # Incremental costs
    df_all['pv_capex_incr'] = (df_all['capex_hsr'] - df_all['capex_cf']) * df_all['df']
    df_all['pv_opex_incr'] = (df_all['opex_hsr'] - df_all['opex_cf']) * df_all['df']
    df_all['pv_costs_incr'] = df_all['pv_capex_incr'] + df_all['pv_opex_incr']

    # Absolute costs
    df_all['pv_capex_abs'] = df_all['capex_hsr'] * df_all['df']
    df_all['pv_opex_abs'] = df_all['opex_hsr'] * df_all['df']
    df_all['pv_costs_abs'] = df_all['pv_capex_abs'] + df_all['pv_opex_abs']

    # Benefits (all are incremental by definition)
    for col in ['time_full','time_gen','env_air','env_car','accident','congestion','webs','freq_rel','residual','revenue']:
        df_all[f'pv_{col}'] = df_all[col] * df_all['df']

    df_all['pv_benefits'] = (df_all['pv_time_full'] + df_all['pv_time_gen'] + df_all['pv_env_air'] + 
                              df_all['pv_env_car'] + df_all['pv_accident'] + df_all['pv_congestion'] + 
                              df_all['pv_webs'] + df_all['pv_freq_rel'] + df_all['pv_residual'])

    S = {}
    S['capex_hsr'] = capex_hsr
    S['capex_cf'] = capex_cf
    S['capex_incr'] = capex_incr
    S['capex_per_km'] = capex_hsr / L
    S['pv_capex_abs'] = df_all['pv_capex_abs'].sum()
    S['pv_opex_abs'] = df_all['pv_opex_abs'].sum()
    S['pv_costs_abs'] = df_all['pv_costs_abs'].sum()
    S['pv_capex_incr'] = df_all['pv_capex_incr'].sum()
    S['pv_opex_incr'] = df_all['pv_opex_incr'].sum()
    S['pv_costs_incr'] = df_all['pv_costs_incr'].sum()

    for col in ['time_full','time_gen','env_air','env_car','accident','congestion','webs','freq_rel','residual','revenue']:
        S[f'pv_{col}'] = df_all[f'pv_{col}'].sum()

    S['pv_time_total'] = S['pv_time_full'] + S['pv_time_gen']
    S['pv_env_total'] = S['pv_env_air'] + S['pv_env_car']
    S['pv_benefits'] = df_all['pv_benefits'].sum()

    S['bcr_abs'] = S['pv_benefits'] / S['pv_costs_abs'] if S['pv_costs_abs'] > 0 else 0
    S['bcr_incr'] = S['pv_benefits'] / S['pv_costs_incr'] if S['pv_costs_incr'] > 0 else None
    S['npv_abs'] = S['pv_benefits'] - S['pv_costs_abs']
    S['npv_incr'] = S['pv_benefits'] - S['pv_costs_incr']
    S['npv_fin'] = S['pv_revenue'] - S['pv_costs_abs']

    S['opex_yr1'] = (p['opex_infra_maint']*L + (p['opex_energy']+p['opex_staff']+p['opex_rs_maint'])*train_km/1e6 + p['opex_overhead'])
    S['train_km_m'] = train_km / 1e6
    S['eff_saving_min'] = effective_saving_min

    return S, df_all

def threshold_search(p, param, lo, hi, target_bcr=1.0, incremental=False):
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

def monte_carlo(p, n=5000):
    np.random.seed(42)
    results = []
    for _ in range(n):
        pp = p.copy()
        pp['annual_pax'] = max(0.5, np.random.triangular(p['annual_pax']*0.4, p['annual_pax'], p['annual_pax']*1.3))
        pp['cost_at_grade'] = max(5, np.random.triangular(p['cost_at_grade']*0.8, p['cost_at_grade'], p['cost_at_grade']*1.6))
        pp['cost_tunnel'] = max(20, np.random.triangular(p['cost_tunnel']*0.8, p['cost_tunnel'], p['cost_tunnel']*1.5))
        overrun_draw = max(0, np.random.triangular(0, p['cost_overrun'], p['cost_overrun']+45))
        pp['cost_overrun'] = overrun_draw
        pp['vot_biz'] = max(5, np.random.normal(p['vot_biz'], p['vot_biz']*0.15))
        pp['vot_com'] = max(2, np.random.normal(p['vot_com'], p['vot_com']*0.15))
        pp['demand_growth'] = max(0, np.random.normal(p['demand_growth'], 0.5))
        pp['constr_years'] = max(3, int(np.random.triangular(p['constr_years']*0.9, p['constr_years'], p['constr_years']*1.5)))
        s, _ = run_cba(pp)
        results.append(s)
    return pd.DataFrame(results)

# ============================================================
# STREAMLIT UI
# ============================================================
st.markdown("# 🚄 HSR Social CBA Sensitivity Analyser")
st.markdown("*Interactive tool for high-speed rail corridor appraisal — extended model with incremental analysis, Monte Carlo, and reference class forecasting*")

# Sidebar
with st.sidebar:
    st.header("⚡ Preset")
    preset_name = st.selectbox("Load corridor preset", list(PRESETS.keys()))
    preset = PRESETS.get(preset_name, {})

    def pv(key, default):
        return preset.get(key, default)

    st.header("📐 Corridor")
    line_length_km = st.slider("Line length (km)", 50, 1200, pv('line_length_km',230), 10)
    pct_tunnel = st.slider("Tunnel share (%)", 0, 60, pv('pct_tunnel',10))
    pct_viaduct = st.slider("Viaduct share (%)", 0, 40, pv('pct_viaduct',8))
    access_egress_hsr = st.slider("Access/egress HSR station (min)", 0, 45, pv('access_egress_hsr',12))
    access_egress_conv = st.slider("Access/egress conventional (min)", 0, 30, pv('access_egress_conv',8))

    st.header("🏗️ Construction Costs")
    cost_at_grade = st.slider("At-grade (€m/km)", 5.0, 80.0, pv('cost_at_grade',18.0), 0.5)
    cost_tunnel = st.slider("Tunnel (€m/km)", 20.0, 250.0, pv('cost_tunnel',80.0), 5.0)
    cost_viaduct = st.slider("Viaduct (€m/km)", 15.0, 150.0, pv('cost_viaduct',45.0), 5.0)
    cost_signalling = st.slider("Signalling (€m/km)", 0.5, 5.0, pv('cost_signalling',1.5), 0.1)
    cost_land = st.slider("Land acquisition (€m/km)", 0.2, 8.0, pv('cost_land',1.0), 0.2)
    cost_stations = st.slider("Stations total (€m)", 50.0, 3000.0, pv('cost_stations',400.0), 50.0)
    cost_rolling = st.slider("Rolling stock (€m)", 0.0, 4000.0, pv('cost_rolling',600.0), 50.0)
    cost_overrun = st.slider("Cost overrun uplift (%)", 0, 100, pv('cost_overrun',0))
    constr_years = st.slider("Construction period (yr)", 3, 20, pv('constr_years',8))

    st.header("🔀 Counterfactual (Upgrade)")
    counterfactual_capex = st.slider("Upgrade CAPEX total (€m)", 0.0, 10000.0, pv('counterfactual_capex',1500.0), 100.0)
    counterfactual_opex_yr = st.slider("Upgrade annual OPEX (€m)", 0.0, 300.0, pv('counterfactual_opex_yr',55.0), 5.0)

    st.header("🔧 Operating Costs (HSR)")
    opex_infra_maint = st.slider("Infra maint. (€m/km/yr)", 0.020, 0.150, pv('opex_infra_maint',0.060), 0.005)
    opex_energy = st.slider("Energy (€/train-km)", 2.0, 25.0, pv('opex_energy',8.0), 0.5)
    opex_staff = st.slider("Staff (€/train-km)", 2.0, 20.0, pv('opex_staff',6.0), 0.5)
    opex_rs_maint = st.slider("RS maintenance (€/train-km)", 1.0, 15.0, pv('opex_rs_maint',5.0), 0.5)
    opex_overhead = st.slider("Overhead (€m/yr)", 5.0, 100.0, pv('opex_overhead',30.0), 5.0)
    trains_day = st.slider("Trains per day", 10, 200, pv('trains_day',60), 5)
    op_days = st.slider("Operating days/yr", 300, 365, pv('op_days',350), 5)

    st.header("👥 Demand")
    annual_pax = st.slider("Annual passengers (million)", 1.0, 60.0, pv('annual_pax',9.0), 0.5)
    demand_growth = st.slider("Demand growth (%/yr)", 0.0, 5.0, pv('demand_growth',1.5), 0.1)
    pax_biz = st.slider("Business share (%)", 5, 60, pv('pax_biz',25))
    pax_com = st.slider("Commuter share (%)", 5, 60, pv('pax_com',30))
    st.caption(f"Leisure share: {max(0, 100-pax_biz-pax_com)}%")

    st.header("🔀 Demand Source Split")
    modal_shift_air = st.slider("Shifted from air (%)", 0, 60, pv('modal_shift_air',10))
    modal_shift_car = st.slider("Shifted from car (%)", 0, 60, pv('modal_shift_car',20))
    generated_share = st.slider("Generated demand (%)", 0, 40, pv('generated_share',15))
    st.caption(f"Diverted from conv. rail: {max(0, 100-modal_shift_air-modal_shift_car-generated_share)}%")

    st.header("🎫 Revenue")
    avg_fare = st.slider("Average fare (€/pax)", 5.0, 120.0, pv('avg_fare',25.0), 1.0)
    fare_growth = st.slider("Real fare growth (%/yr)", 0.0, 3.0, pv('fare_growth',0.5), 0.1)

    st.header("⏱️ Journey Times")
    current_time = st.slider("Current journey (min)", 30, 600, pv('current_time',150), 5)
    upgrade_time = st.slider("Upgrade counterfactual (min)", 20, 400, pv('upgrade_time',100), 5)
    hsr_time = st.slider("HSR journey (min)", 15, 240, pv('hsr_time',60), 5)

    st.header("💰 Value of Time")
    vot_biz = st.slider("VOT business (€/hr)", 10.0, 90.0, pv('vot_biz',28.0), 1.0)
    vot_com = st.slider("VOT commuter (€/hr)", 4.0, 40.0, pv('vot_com',12.0), 1.0)
    vot_lei = st.slider("VOT leisure (€/hr)", 2.0, 25.0, pv('vot_lei',7.0), 1.0)
    vot_growth = st.slider("VOT real growth (%/yr)", 0.0, 4.0, pv('vot_growth',2.0), 0.1)

    st.header("🌍 Externalities")
    co2_price = st.slider("CO₂ price (€/t)", 10.0, 300.0, pv('co2_price',80.0), 5.0)
    co2_per_mpax = st.slider("CO₂ saved (t/m shifted pax)", 5000, 40000, pv('co2_per_mpax',15000), 1000)
    accident_ben = st.slider("Accident benefit (€m/m car pax)", 0.0, 3.0, pv('accident_ben',0.5), 0.1)
    congestion = st.slider("Congestion relief (€m/yr)", 0.0, 80.0, pv('congestion',15.0), 1.0)
    webs_pct = st.slider("WEBs (% of time benefits)", 0, 50, pv('webs_pct',15))

    st.header("📊 Appraisal")
    discount = st.slider("Discount rate (%)", 1.0, 8.0, pv('discount',4.0), 0.5)
    appraisal_yrs = st.slider("Appraisal period (yr)", 20, 60, pv('appraisal_yrs',40), 5)
    residual_pct = st.slider("Residual value (% capex)", 0, 60, pv('residual_pct',30), 5)

# Collect params
params = dict(
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
)

S, df_all = run_cba(params)

# ============================================================
# RESULTS
# ============================================================

# Reference class warning
st.markdown("---")
col_rcf1, col_rcf2 = st.columns(2)
with col_rcf1:
    st.markdown("### 🔍 Reference Class Forecasting Check")
    adj_capex = S['capex_hsr'] * (1 + FLYVBJERG_COST_UPLIFT) / (1 + cost_overrun/100)
    adj_pax = annual_pax * FLYVBJERG_DEMAND_FACTOR
    st.caption("RCF CAPEX removes the current user overrun uplift, recovers pre-uplift base CAPEX, and then applies the Flyvbjerg median uplift of +44.7%. It replaces the user overrun assumption; it does not stack on top of it.")
    st.metric("RCF-adjusted CAPEX (€m)", f"{adj_capex:,.0f}", 
              delta=f"+{(adj_capex - S['capex_hsr']):,.0f} vs your estimate", delta_color="inverse")
    st.metric("RCF-adjusted demand (m pax)", f"{adj_pax:.1f}", 
              delta=f"{(adj_pax - annual_pax):.1f} vs your estimate", delta_color="inverse")
with col_rcf2:
    rcf_params = params.copy()
    rcf_params['cost_overrun'] = FLYVBJERG_COST_UPLIFT * 100
    rcf_params['annual_pax'] = adj_pax
    S_rcf, _ = run_cba(rcf_params)
    st.markdown("### After RCF Adjustment")
    bcr_col = "🟢" if S_rcf['bcr_abs'] >= 1 else ("🟡" if S_rcf['bcr_abs'] >= 0.7 else "🔴")
    st.metric("RCF Social BCR (absolute)", f"{bcr_col} {S_rcf['bcr_abs']:.3f}")
    st.metric("RCF Social NPV (€m)", f"{S_rcf['npv_abs']:,.0f}")
    st.caption("Flyvbjerg et al. (2002): +44.7% cost uplift, demand at 48.7% of forecast")

st.markdown("---")

# Key metrics
c1, c2, c3, c4, c5, c6 = st.columns(6)
bcr_emoji = "🟢" if S['bcr_abs'] >= 1 else ("🟡" if S['bcr_abs'] >= 0.7 else "🔴")
c1.metric("Social BCR (abs)", f"{bcr_emoji} {S['bcr_abs']:.3f}")
c2.metric("Social BCR (incr)", format_bcr(S['bcr_incr']))
c3.metric("NPV Social abs (€m)", f"{S['npv_abs']:,.0f}")
c4.metric("NPV Financial (€m)", f"{S['npv_fin']:,.0f}")
c5.metric("CAPEX total (€m)", f"{S['capex_hsr']:,.0f}")
c6.metric("CAPEX/km (€m)", f"{S['capex_per_km']:.1f}")

c7, c8, c9, c10 = st.columns(4)
c7.metric("Eff. time saving (min)", f"{S['eff_saving_min']:.0f}", help="HSR vs upgrade, incl. access/egress")
c8.metric("Annual OPEX (€m)", f"{S['opex_yr1']:.0f}")
c9.metric("NPV Incremental (€m)", f"{S['npv_incr']:,.0f}", help="vs conventional upgrade counterfactual")
c10.metric("Annual train-km (m)", f"{S['train_km_m']:.1f}")

# BCR gauge
bcr_val = min(S['bcr_abs'], 3.0)
fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number", value=S['bcr_abs'],
    gauge=dict(axis=dict(range=[0,3]),
               bar=dict(color="#20B2FF"),
               steps=[dict(range=[0,0.7],color="#FF6B6B"),
                      dict(range=[0.7,1.0],color="#FFB347"),
                      dict(range=[1.0,1.5],color="#88D498"),
                      dict(range=[1.5,3.0],color="#1FBFAE")],
               threshold=dict(line=dict(color="white",width=3),value=1.0)),
    title=dict(text="Social BCR (absolute)")))
fig_gauge.update_layout(height=250, margin=dict(t=80,b=20,l=40,r=40))
st.plotly_chart(fig_gauge, use_container_width=True)

# ============================================================
# BENEFITS & COSTS BREAKDOWN
# ============================================================
st.markdown("## 📊 PV Breakdown (€m)")
col_b, col_c = st.columns(2)

with col_b:
    ben_items = [
        ("Time savings (existing)", S['pv_time_full'], "#20B2FF"),
        ("Time savings (generated, ½)", S['pv_time_gen'], "#5BC8F5"),
        ("WEBs", S['pv_webs'], "#9B8AFF"),
        ("Freq. & reliability", S['pv_freq_rel'], "#C4B5FD"),
        ("Congestion relief", S['pv_congestion'], "#1FBFAE"),
        ("Env. (air shift)", S['pv_env_air'], "#FFB347"),
        ("Env. (car shift)", S['pv_env_car'], "#FBBF24"),
        ("Accident", S['pv_accident'], "#88D498"),
        ("Residual value", S['pv_residual'], "#9AA0A6"),
    ]
    fig_b = go.Figure()
    for name, val, color in ben_items:
        fig_b.add_trace(go.Bar(x=[val], y=[name], orientation='h', marker_color=color, name=name, text=f"{val:.0f}", textposition='outside'))
    fig_b.update_layout(title="PV Benefits", height=400, showlegend=False, margin=dict(l=10,r=10,t=40,b=10), xaxis_title="€m")
    fig_b.update_traces(cliponaxis=False)
    st.plotly_chart(fig_b, use_container_width=True)

with col_c:
    cost_items = [
        ("CAPEX HSR (PV)", S['pv_capex_abs'], "#FF6B6B"),
        ("OPEX HSR (PV)", S['pv_opex_abs'], "#FFB347"),
        ("minus: Counterfact. CAPEX", -S['pv_capex_abs']+S['pv_capex_incr']+S['pv_capex_abs'], "#9AA0A6"),
    ]
    fig_c = go.Figure()
    fig_c.add_trace(go.Bar(x=[S['pv_capex_abs']], y=["CAPEX HSR"], orientation='h', marker_color="#FF6B6B", text=f"{S['pv_capex_abs']:.0f}", textposition='outside'))
    fig_c.add_trace(go.Bar(x=[S['pv_opex_abs']], y=["OPEX HSR"], orientation='h', marker_color="#FFB347", text=f"{S['pv_opex_abs']:.0f}", textposition='outside'))
    fig_c.add_trace(go.Bar(x=[S['pv_capex_incr']], y=["CAPEX incremental"], orientation='h', marker_color="#9B8AFF", text=f"{S['pv_capex_incr']:.0f}", textposition='outside'))
    fig_c.add_trace(go.Bar(x=[S['pv_revenue']], y=["Revenue (financial)"], orientation='h', marker_color="#1FBFAE", text=f"{S['pv_revenue']:.0f}", textposition='outside'))
    fig_c.update_layout(title="PV Costs & Revenue", height=300, showlegend=False, margin=dict(l=10,r=10,t=40,b=10), xaxis_title="€m")
    fig_c.update_traces(cliponaxis=False)
    st.plotly_chart(fig_c, use_container_width=True)

# Benefit shares pie
ben_labels = [b[0] for b in ben_items]
ben_vals = [b[1] for b in ben_items]
ben_colors = [b[2] for b in ben_items]
fig_pie = go.Figure(go.Pie(labels=ben_labels, values=[max(0,v) for v in ben_vals], 
                           marker=dict(colors=ben_colors), textinfo='percent+label', hole=0.4))
fig_pie.update_layout(title="Benefit Composition", height=350, margin=dict(t=40,b=10))
st.plotly_chart(fig_pie, use_container_width=True)

# ============================================================
# THRESHOLD ANALYSIS
# ============================================================
st.markdown("## 🎯 Threshold Analysis — Break-even for BCR = 1.0")
st.caption("Each threshold computed holding all other parameters at current values")
st.caption("`N/A` means BCR = 1.0 is outside the tested range for that parameter.")

th1, th2, th3, th4 = st.columns(4)
try:
    th_pax = threshold_search(params, 'annual_pax', 0.5, 80, 1.0)
    th1.metric("Min. annual pax (m)", f"{th_pax:.1f}" if th_pax is not None else "N/A")
except: th1.metric("Min. annual pax (m)", "N/A")
try:
    th_cost = threshold_search(params, 'cost_at_grade', 1, 200, 1.0)
    th2.metric("Max. at-grade cost (€m/km)", f"{th_cost:.1f}" if th_cost is not None else "N/A")
except: th2.metric("Max. at-grade cost (€m/km)", "N/A")
try:
    th_time = threshold_search(params, 'hsr_time', 1, 300, 1.0)
    if th_time is None:
        th3.metric("Min. eff. time saving (min)", "N/A")
    else:
        th_save = (upgrade_time + access_egress_conv) - (th_time + access_egress_hsr)
        th3.metric("Min. eff. time saving (min)", f"{max(0,th_save):.0f}")
except: th3.metric("Min. eff. time saving (min)", "N/A")
try:
    th_vot = threshold_search(params, 'vot_biz', 5, 200, 1.0)
    th4.metric("Min. VOT business (€/hr)", f"{th_vot:.0f}" if th_vot is not None else "N/A")
except: th4.metric("Min. VOT business (€/hr)", "N/A")

# ============================================================
# ANNUAL PROFILE CHART
# ============================================================
st.markdown("## 📈 Annual Cashflow Profile")
op_df = df_all[df_all['phase']=='operation'].copy()
op_df['year_op'] = range(1, len(op_df)+1)
op_df['net_social'] = (op_df['time_full']+op_df['time_gen']+op_df['env_air']+op_df['env_car']+
                       op_df['accident']+op_df['congestion']+op_df['webs']+op_df['freq_rel'] - 
                       op_df['opex_hsr'] + op_df['opex_cf'])
op_df['net_financial'] = op_df['revenue'] - op_df['opex_hsr']

fig_annual = go.Figure()
fig_annual.add_trace(go.Scatter(x=op_df['year_op'], y=op_df['time_full']+op_df['time_gen'], name='Time benefits', fill='tozeroy', line=dict(color='#20B2FF')))
fig_annual.add_trace(go.Scatter(x=op_df['year_op'], y=op_df['revenue'], name='Revenue', line=dict(color='#1FBFAE', dash='dash')))
fig_annual.add_trace(go.Scatter(x=op_df['year_op'], y=op_df['opex_hsr'], name='OPEX', line=dict(color='#FF6B6B', dash='dot')))
fig_annual.add_trace(go.Scatter(x=op_df['year_op'], y=op_df['net_social'], name='Net social (excl capex)', line=dict(color='#9B8AFF', width=2)))
fig_annual.update_layout(height=400, xaxis_title="Year of operation", yaxis_title="€m/year", 
                         legend=dict(orientation='h', y=1.12))
st.plotly_chart(fig_annual, use_container_width=True)

# ============================================================
# SENSITIVITY TORNADO
# ============================================================
st.markdown("## 🌪️ Sensitivity Tornado (±20%)")
tornado_params = [
    ('annual_pax', 'Demand'), ('cost_at_grade', 'At-grade cost'),
    ('cost_tunnel', 'Tunnel cost'), ('pct_tunnel', 'Tunnel share'),
    ('vot_biz', 'VOT business'), ('vot_com', 'VOT commuter'),
    ('discount', 'Discount rate'), ('constr_years', 'Constr. period'),
    ('hsr_time', 'HSR time'), ('upgrade_time', 'Counterfact. time'),
    ('webs_pct', 'WEBs'), ('congestion', 'Congestion relief'),
    ('cost_overrun', 'Cost overrun'), ('trains_day', 'Trains/day'),
    ('modal_shift_air', 'Air shift'), ('modal_shift_car', 'Car shift'),
    ('access_egress_hsr', 'Access HSR'), ('co2_price', 'CO₂ price'),
]
base_bcr = S['bcr_abs']
t_data = []
for pname, label in tornado_params:
    bv = params[pname]
    for mult, direction in [(0.8, 'low'), (1.2, 'high')]:
        tv = bv * mult
        if bv == 0: tv = (20 if direction == 'high' else 0)
        tv = max(0, tv)
        if isinstance(bv, int): tv = int(round(tv))
        pp = params.copy(); pp[pname] = tv
        ss, _ = run_cba(pp)
        t_data.append(dict(param=label, direction=direction, bcr=ss['bcr_abs']))
t_df = pd.DataFrame(t_data)
pivot = t_df.pivot(index='param', columns='direction', values='bcr').reset_index()
pivot['range'] = abs(pivot['high'] - pivot['low'])
pivot = pivot.sort_values('range', ascending=True)

fig_torn = go.Figure()
fig_torn.add_trace(go.Bar(y=pivot['param'], x=pivot['low']-base_bcr, base=base_bcr, orientation='h', name='−20%', marker_color='#1FBFAE'))
fig_torn.add_trace(go.Bar(y=pivot['param'], x=pivot['high']-base_bcr, base=base_bcr, orientation='h', name='+20%', marker_color='#20B2FF'))
fig_torn.add_vline(x=base_bcr, line_dash="dash", line_color="white")
fig_torn.add_vline(x=1.0, line_dash="dot", line_color="#FF6B6B")
fig_torn.update_layout(barmode='overlay', height=550, legend=dict(orientation='h', y=1.05), 
                       xaxis_title="Social BCR", margin=dict(l=10))
st.plotly_chart(fig_torn, use_container_width=True)

# ============================================================
# MONTE CARLO
# ============================================================
st.markdown("## 🎲 Monte Carlo Simulation")
st.caption("5,000 draws with triangular/normal distributions on key parameters (demand, costs, VOT, construction time)")

with st.spinner("Running Monte Carlo..."):
    mc_df = monte_carlo(params, n=5000)

mc_col1, mc_col2, mc_col3, mc_col4 = st.columns(4)
mc_col1.metric("P(BCR > 1.0)", f"{(mc_df['bcr_abs']>=1).mean()*100:.1f}%")
mc_col2.metric("P(BCR > 0.7)", f"{(mc_df['bcr_abs']>=0.7).mean()*100:.1f}%")
mc_col3.metric("Median BCR", f"{mc_df['bcr_abs'].median():.3f}")
mc_col4.metric("P5–P95 BCR", f"{mc_df['bcr_abs'].quantile(0.05):.2f} – {mc_df['bcr_abs'].quantile(0.95):.2f}")

fig_mc = go.Figure()
fig_mc.add_trace(go.Histogram(x=mc_df['bcr_abs'], nbinsx=80, marker_color='#20B2FF', opacity=0.7, name='BCR distribution'))
fig_mc.add_vline(x=1.0, line_dash="dash", line_color="#FF6B6B", annotation_text="BCR=1")
fig_mc.add_vline(x=mc_df['bcr_abs'].median(), line_dash="dot", line_color="#1FBFAE", annotation_text="Median")
fig_mc.update_layout(height=350, xaxis_title="Social BCR (absolute)", yaxis_title="Frequency",
                     bargap=0.05)
st.plotly_chart(fig_mc, use_container_width=True)

fig_mc2 = go.Figure()
fig_mc2.add_trace(go.Histogram(x=mc_df['npv_abs'], nbinsx=80, marker_color='#9B8AFF', opacity=0.7))
fig_mc2.add_vline(x=0, line_dash="dash", line_color="#FF6B6B", annotation_text="NPV=0")
fig_mc2.update_layout(height=300, xaxis_title="Social NPV absolute (€m)", yaxis_title="Frequency", bargap=0.05)
st.plotly_chart(fig_mc2, use_container_width=True)

# ============================================================
# CORRIDOR COMPARISON
# ============================================================
st.markdown("## 🔄 Quick Comparison: All Presets")
comp_rows = []
for name, pdata in PRESETS.items():
    if not pdata: continue
    full_p = params.copy()
    full_p.update(pdata)
    ss, _ = run_cba(full_p)
    comp_rows.append(dict(Corridor=name, **{k: round(v, 2) if isinstance(v, float) else v 
                                            for k, v in ss.items()}))
comp_df = pd.DataFrame(comp_rows)
display_cols = ['Corridor','capex_hsr','capex_per_km','bcr_abs','bcr_incr','npv_abs','npv_fin','eff_saving_min','opex_yr1']
rename = {'capex_hsr':'CAPEX (€m)','capex_per_km':'€m/km','bcr_abs':'BCR abs','bcr_incr':'BCR incr',
          'npv_abs':'NPV soc (€m)','npv_fin':'NPV fin (€m)','eff_saving_min':'Eff. Δt (min)','opex_yr1':'OPEX yr1 (€m)'}
st.dataframe(comp_df[display_cols].rename(columns=rename).style.format({
    'CAPEX (€m)': '{:,.0f}', '€m/km': '{:.1f}', 'BCR abs': '{:.3f}', 'BCR incr': lambda v: format_bcr(v),
    'NPV soc (€m)': '{:,.0f}', 'NPV fin (€m)': '{:,.0f}', 'Eff. Δt (min)': '{:.0f}', 'OPEX yr1 (€m)': '{:.0f}'
}).apply(lambda x: ['background-color: #1a3a2a' if isinstance(v, (int,float)) and v >= 1 else '' 
                     for v in x] if x.name in ['BCR abs','BCR incr'] else ['']*len(x)), 
    use_container_width=True, height=600)

# ============================================================
# DATA EXPORT
# ============================================================
st.markdown("## 💾 Export")
col_exp1, col_exp2 = st.columns(2)
with col_exp1:
    summary_export = pd.DataFrame([S]).T
    summary_export.columns = ['Value']
    st.download_button("📥 Download Summary (CSV)", summary_export.to_csv(), "hsr_cba_summary.csv", "text/csv")
with col_exp2:
    st.download_button("📥 Download Annual Cashflows (CSV)", df_all.to_csv(index=False), "hsr_cba_cashflows.csv", "text/csv")

st.markdown("---")
st.markdown("""
<div style='font-size:11px; color:#666;'>
<b>HSR Social CBA Sensitivity Analyser v2.0</b> — Extended model with incremental analysis, access/egress, demand source decomposition (rule of half for generated demand), 
frequency/reliability proxy, Monte Carlo simulation, reference class forecasting, and corridor comparison.<br>
Companion to: <i>"When is HSR Worthwhile? Lessons from Western Europe and Implications for Central and Eastern Europe"</i> (Nash, Jandová, Paleta, Król, 2026).<br>
Model limitations: simplified cashflow, no distributional analysis, no phasing/real options, deterministic counterfactual. See documentation for full methodology.
</div>
""", unsafe_allow_html=True)
