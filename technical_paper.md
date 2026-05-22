# HSR Social Cost–Benefit Analysis Sensitivity Analyser: A Computational Framework for Appraising High-Speed Rail Investments

## Abstract

This paper presents a computational framework for social cost–benefit analysis (CBA) of high-speed rail (HSR) projects. The framework implements a strictly incremental appraisal methodology, comparing a proposed HSR investment against an explicit counterfactual scenario (conventional rail upgrade). It computes standard decision metrics—net present value (NPV), benefit–cost ratio (BCR), internal rate of return (IRR), and payback period—under both absolute and incremental perspectives, following the methodological guidance of the European Commission Handbook on the External Costs of Transport (EC, 2020), the UK Green Book (HM Treasury, 2022), and the HEATCO harmonisation framework (HEATCO, 2006). Beyond deterministic base-case analysis, the framework incorporates Reference Class Forecasting correction factors derived from Flyvbjerg et al. (2002, 2005), configurable construction-phase spend profiles, one-way sensitivity (tornado) analysis, user-configurable Monte Carlo simulation with probabilistic parameter distributions, and binary-search threshold (break-even) analysis. The model monetises user benefits through class-stratified values of travel time, applies the rule-of-half to generated demand, and accounts for environmental externalities (CO₂ savings from modal shift), accident reduction, congestion relief, wider economic benefits (WEBs), and a frequency/reliability proxy. A Multi-Criteria Analysis (MCA) module complements the quantitative CBA with eight non-monetary criteria, producing a weighted score and a Combined Decision Index that integrates quantitative and qualitative evidence. Built-in corridor presets for 15 European HSR lines and 10 country socio-economic profiles provide defensible starting values sourced from published appraisals. We describe the analytical framework in full detail, document its assumptions and data requirements, and discuss its capabilities and limitations as a tool for transport project appraisal and academic research.

**Keywords:** high-speed rail, cost–benefit analysis, sensitivity analysis, Monte Carlo simulation, Reference Class Forecasting, value of travel time, wider economic benefits, multi-criteria analysis

---

## 1. Introduction

High-speed rail (HSR) represents one of the most capital-intensive categories of transport infrastructure, with construction costs routinely exceeding €20 million per kilometre in Western Europe (UIC, 2018). The social viability of such investments hinges on whether the stream of future benefits—time savings, environmental gains, agglomeration effects—outweighs the enormous upfront costs, often spread over decades of construction and operation. Formal cost–benefit analysis (CBA) is the standard appraisal methodology mandated by most European national frameworks and EU structural fund regulations (EC, 2014; HM Treasury, 2022).

However, standard CBA implementations typically report single-point estimates of NPV and BCR, obscuring the profound uncertainty that pervades every input parameter. Construction costs are systematically underestimated (Flyvbjerg et al., 2002); demand forecasts are systematically optimistic (Flyvbjerg et al., 2005); and values of travel time, environmental prices, and wider economic benefit multipliers vary across national appraisal traditions. Without explicit treatment of these uncertainties, decision-makers cannot assess the robustness of a positive BCR or understand which parameters drive outcomes.

This paper presents a computational framework—the **HSR Social CBA Sensitivity Analyser**—designed to address these gaps. Implemented as an interactive Streamlit application, it provides:

1. A rigorous incremental CBA engine that compares HSR against a specified counterfactual.
2. Reference Class Forecasting (RCF) adjustments based on empirical evidence of systematic bias in rail project appraisals.
3. One-way sensitivity (tornado) analysis identifying the most influential parameters.
4. Probabilistic Monte Carlo simulation quantifying the likelihood of favourable outcomes.
5. Threshold (break-even) analysis determining the parameter values required for viability.
6. Cross-coridor comparison using built-in presets for 15 European HSR lines.
7. Multi-Criteria Analysis (MCA) scoring and visualisation of non-monetary criteria, integrated with CBA results.

Section 2 describes the analytical framework and modelling chain. Section 3 details the data inputs and presets. Section 4 presents the CBA engine. Section 5 covers the sensitivity and risk analysis features. Section 6 discusses outputs and visualisation capabilities including the MCA module. Section 7 addresses assumptions and limitations. Section 8 covers regression testing. Section 9 concludes.

---

## 2. Analytical Framework

### 2.1 Incremental CBA Methodology

The framework adopts a strictly **incremental** approach: all benefits and costs are computed as the difference between the HSR scenario and the counterfactual (a conventional rail upgrade). This follows established practice in transport appraisal (EC, 2014; HM Treasury, 2022; HEATCO, 2006), where the relevant question is not "Is HSR worthwhile in isolation?" but rather "Does HSR generate more net social benefit than the next-best alternative?"

Both absolute and incremental perspectives are reported:
- **Absolute**: PV(benefits) / PV(HSR costs) — the overall return on the HSR investment.
- **Incremental**: PV(benefits) / PV(HSR costs − counterfactual costs) — the return on the *additional* resources committed beyond the counterfactual.

Incremental BCR is undefined when the counterfactual is more expensive than HSR (negative incremental costs), reflecting that the metric loses interpretive meaning in this case.

### 2.2 Benefit Categories

The framework monetises six categories of social benefit, each toggleable by the user:

1. **User time savings** — The primary benefit category. Monetised through class-stratified values of travel time (VOT) for business, commuter, and leisure travellers, with annual real growth linked to income projections.

2. **Environmental externalities (CO₂)** — Savings from passengers shifting from air and car to rail, valued at a shadow carbon price. Air-to-rail shifts receive full CO₂ credit; car-to-rail shifts receive 40% of the per-passenger air credit, reflecting the lower carbon intensity differential for short-distance car journeys.

3. **Accident reduction** — Avoided road accident costs from car-to-rail modal shift.

4. **Congestion relief** — Reduction in road congestion costs, anchored to a base-year value and scaled proportionally with shifted car passengers over time.

5. **Wider Economic Benefits (WEBs)** — Agglomeration and labour market effects estimated as a fixed percentage of total user time savings, following the methodology of Venables (2007) and Graham (2007).

6. **Frequency and reliability** — A proxy benefit set at 5% of total time savings, acknowledging that higher service frequency and improved punctuality generate additional user value not captured by pure journey-time reduction (SACTRA, 1999).

In addition to these toggleable benefit components, the framework includes two further socio-economic parameters:

- **Capacity release benefit** (`released_capacity_benefit`, €m/yr) — A constant annual benefit representing the monetised value of freed capacity on the conventional rail network, available for freight or regional passenger services after HSR diverts long-distance traffic. Per UK TAG Unit A5.4 (UK DfT, 2023), released capacity is a genuine economic benefit when the conventional network is capacity-constrained. Default: 0 (user must supply a project-specific estimate).

- **Post-COVID demand dip** (`post_covid_dip`, %) — A temporary ridership reduction applied to the first five operating years, linearly recovering to zero by year 5. This parameter accounts for structural shifts in travel demand following the COVID-19 pandemic—remote working, video conferencing substitution, and changes in business travel norms (ITF, 2023). The dip factor for operating year t is: dip_factor(t) = 1 − (dip%/100) × (1 − t/5) for t < 5, and 1.0 thereafter. Default: 0%.

### 2.3 Treatment of Generated Demand

Generated (induced) demand—passengers who would not have travelled without HSR—receives the **rule-of-half**: they are assigned 50% of the time benefit enjoyed by existing passengers, reflecting that marginal travellers experience smaller net gains than inframarginal ones (HEATCO, 2006; EC, 2014).

### 2.4 Discounting and Appraisal Period

All cash flows are discounted to the base year of construction start using a configurable social discount rate. The EU Guide recommends 3–5% (EC, 2014); country presets use nationally appropriate values (3.5% for the UK, 4% for most continental European countries, 5% for emerging economies). Discount factors follow the standard formulation:

DF(t) = 1 / (1 + r)^t

where r is the discount rate and t is the year index. The appraisal period is configurable (default: 40 years of operation), with residual value at the end of the appraisal period treated as a terminal benefit.

---

## 3. Data Inputs and Presets

### 3.1 User-Supplied Parameters

All model inputs are supplied via the application sidebar, organised into logical groups:

| Group | Parameters | Role |
|-------|-----------|------|
| Geometry & Infrastructure | Line length, tunnel/viaduct shares, access/egress times | Cost/benefit |
| Construction Costs | Unit costs (at-grade, tunnel, viaduct, signalling, land), stations, rolling stock, cost overrun uplift, construction period, spend profile | Cost |
| Counterfactual | Upgrade CAPEX, upgrade annual OPEX | Cost |
| Operating Costs (HSR) | Infrastructure maintenance, energy, staff, rolling-stock maintenance, overhead, trains/day, operating days | Cost |
| Demand & Fares | Annual passengers, demand growth, passenger class shares, average fare, fare growth | Benefit |
| Demand Source Split | Modal shift from air, car; generated share | Externality/benefit |
| Journey Times | Current, upgrade, HSR journey times | Benefit |
| Value of Time | VOT by class, VOT real growth | Benefit |
| Externalities & WEBs | CO₂ price, CO₂ saved, accident benefit, congestion relief, WEBs percentage | Externality |
| Capacity & Demand Adjustments | Released capacity benefit (€m/yr), post-COVID demand dip (%) | Benefit |
| Socio-economic Settings | Toggles for each benefit component | Appraisal |
| Appraisal Settings | Discount rate, appraisal period, residual value | Appraisal |

Each parameter includes a label, unit, and descriptive help text drawn from a centralised metadata dictionary (`PARAM_META`), facilitating future internationalisation.

### 3.2 Country Socio-Economic Profiles

Ten built-in country/regional profiles supply default values for VOTs, discount rates, carbon prices, externality parameters, and cost-overrun uplifts:

| Profile | Discount Rate | VOT Business (€/hr) | CO₂ Price (€/t) | Source Basis |
|---------|:---:|:---:|:---:|------|
| France | 4.0% | 50 | 90 | CGEDD/CGE (2020); EC (2020) |
| Spain | 4.0% | 38 | 80 | Ministerio de Transportes (2020); EC (2020) |
| United Kingdom | 3.5% | 60 | 100 | UK DfT TAG A1.3 (2023); HM Treasury (2022); UK DESNZ (2023) |
| Netherlands | 4.0% | 55 | 100 | KiM/Significance (2024); EC (2020) |
| Italy | 4.0% | 45 | 80 | MIT/Prefabbricati (2019); EC (2020) |
| Czech Republic | 4.0% | 28 | 80 | CDV (2019); EC (2020); ITF/OECD (2020) |
| Poland | 4.0% | 25 | 80 | CPK (2023); EC (2020); ITF/OECD (2020) |
| Generic EU | 4.0% | 40 | 80 | EC (2014, 2020); HEATCO (2006) |
| OECD High-income | 3.5% | 50 | 100 | OECD (2022); ITF (2023); Small (2012) |
| Emerging Economy | 5.0% | 18 | 50 | World Bank (2021); EC (2014) |

These profiles provide defensible starting points; users are expected to override them with project-specific data where available. Key sources for each profile are:

- **France:** The VOT values follow the *Commission Générale du Développement Durable* report on the value of time in passenger transport (CGEDD/CGE, 2020), which provides official French appraisal parameters. The discount rate of 4% is per the French *Commissariat Général à la Stratégie et à la Prospective* guidance.

- **Spain:** VOT values are based on the *Recomendaciones para la evaluación económica de proyectos de transporte* published by the Spanish Ministry of Transport (Ministerio de Transportes y Movilidad Sostenible, 2020). Cost overrun uplift reflects the lower incidence of overruns observed in Spanish HSR construction relative to Northern European projects.

- **United Kingdom:** VOTs follow the UK Department for Transport's Transport Analysis Guidance Unit A1.3 (UK DfT, 2023). In 2022 prices, the TAG Data Book reports business travel time at approximately £47–50/hr, commuting at £20–25/hr, and non-work/leisure at approximately £6.60/hr (FCA, 2023; UK DfT, 2023). Converting to EUR at the prevailing rate (~€1.15/£) yields approximately €54–58 (business), €23–29 (commuting), and €7–8 (leisure). The preset values of €60 (business), €28 (commuter), and €14 (leisure) are deliberately set above the strict conversion for leisure to reflect the broader range of non-work purposes captured under "leisure" in HSR appraisal—including visiting friends/relatives and tourism day trips, which the UK TAG methodology values higher than the headline leisure average. Users should note this upward adjustment and refer to the raw TAG Data Book for mode- and purpose-specific values. The discount rate of 3.5% follows the HM Treasury Green Book (HM Treasury, 2022). CO₂ pricing uses the UK DESNZ (2023) carbon valuation tables. Cost overrun uplift of 25% reflects the well-documented HS2 cost escalation (National Audit Office, 2024).

- **Netherlands:** VOT values are sourced from the *Values of Travel Time, Reliability and Comfort in the Netherlands* study by KiM and Significance (KiM/Significance, 2024), which provides the most recent Dutch national VOT estimates. The high cost overrun uplift (75%) reflects the well-known HSL-Zuid cost overrun case (Cantarelli et al., 2012).

- **Italy:** VOT values reflect Italian transport appraisal practice as documented in MIT guidelines (MIT, 2019). The cost overrun uplift of 50% reflects documented overruns on Italian HSR projects (de Vos, 2014; Beria et al., 2018).

- **Czech Republic:** VOT values are estimated from the Transport Research Centre (CDV) methodology for quantifying transport externalities (CDV, 2019) and cross-referenced with the ITF/OECD comparative study on mobility practices and values of time across Europe (ITF, 2020). Higher VOT growth (2%/yr) reflects rapid income convergence toward Western European levels.

- **Poland:** VOT values follow Centralny Port Komunikacyjny (CPK) feasibility study estimates (CPK, 2023), supplemented by the ITF/OECD (2020) cross-country VOT comparison. Higher VOT growth mirrors the Czech assumption.

- **Generic EU and OECD High-income:** These composite profiles aggregate parameters from the EU CBA Guide (EC, 2014), the EU Handbook on External Costs of Transport (EC, 2020), and the OECD/ITF comparative VOT studies (Small, 2012; ITF, 2020).

- **Emerging Economy:** This profile uses World Bank transport appraisal guidelines for middle-income countries (World Bank, 2021), with a higher discount rate (5%) reflecting the opportunity cost of capital in developing economies and lower VOTs reflecting income differentials.

### 3.3 Corridor Presets

Fifteen corridor presets capture the engineering, cost, and demand characteristics of existing and planned European HSR lines:

| Corridor | Length (km) | Tunnel % | CAPEX/km (€m) | Annual Pax (M) |
|----------|:-----------:|:--------:|:--------------:|:---------------:|
| TGV Paris–Lyon | 409 | 2 | ~17 | 52.0 |
| LGV Est | 300 | 5 | ~24 | 14.0 |
| AVE Madrid–Barcelona | 621 | 8 | ~13 | 5.0 |
| AVE Madrid–Seville | 471 | 4 | ~10 | 7.0 |
| HS1 (CTRL) | 108 | 37 | ~84 | 26.0 |
| HS2 Phase 1 | 225 | 25 | ~118 | 18.0 |
| HSL-Zuid | 125 | 12 | ~62 | 8.0 |
| Torino–Milano | 125 | 15 | ~43 | 15.0 |
| VRT Praha–Brno | 230 | 10 | ~23 | 9.0 |
| VRT Brno–Ostrava | 160 | 12 | ~24 | 6.0 |
| CPK Y-line | 450 | 5 | ~19 | 12.0 |
| Budapest–Belgrade | 350 | 3 | ~16 | 3.0 |
| Rail Baltica | 870 | 1 | ~25 | 4.0 |
| Brno–Bratislava | 130 | 6 | ~21 | 5.0 |

Preset values are drawn from published appraisals and official sources: TGV Paris–Lyon data from SNCF Réseau and Statista infrastructure cost compilations (Statista, 2014); LGV Est from railway-technology.com project profiles and French government audit reports; AVE corridors from ADIF and Spanish Ministry of Transport data (Ministerio de Transportes, 2020); HS1 from the UK Office of Rail and Road cost review (ORR/Arup, 2007); HS2 Phase 1 from National Audit Office reports (NAO, 2024); HSL-Zuid from Dutch parliamentary inquiry documentation (Cantarelli et al., 2012); Torino–Milano from RFI/Italferr data and ex-post CBA studies (Beria et al., 2018); Czech VRT corridors from Správa železnic feasibility study procurement notices and CDV methodology (CDV, 2019); CPK from the Polish Central Communication Port programme documentation (CPK, 2023); Budapest–Belgrade from Hungarian government financing agreements and European Commission TEN-T corridor assessments; Rail Baltica from the RB CBA Final Report (Rail Baltica Global Express, 2022); Brno–Bratislava from Slovak Ministry of Transport feasibility study announcements (MDVaSR, 2023). Each preset can be modified by the user after loading.

---

## 4. The CBA Engine

### 4.1 CAPEX Computation

Total HSR CAPEX is computed from route geometry and unit costs:

CAPEX_HSR = [L × (p_a × c_grade + p_t × c_tunnel + p_v × c_viaduct + c_signalling + c_land) + c_stations + c_rolling] × (1 + overrun/100)

where:
- L = line length (km)
- p_a, p_t, p_v = at-grade, tunnel, and viaduct proportions (p_a = 1 − p_t − p_v)
- c_grade, c_tunnel, c_viaduct = unit construction costs (€m/km)
- c_signalling, c_land = per-km signalling and land acquisition costs
- c_stations, c_rolling = lump-sum station and rolling-stock costs
- overrun = cost-overrun uplift percentage

Incremental CAPEX = CAPEX_HSR − CAPEX_counterfactual

### 4.2 Construction-Phase Spend Profiles

CAPEX is distributed across the construction period according to one of three configurable profiles:

| Profile | Weight for Year t | Character |
|---------|:------------------|-----------|
| Linear | 1/CY | Equal annual spending |
| Front-loaded | (CY − t) / Σ | Higher spending in early years |
| Back-loaded | (t + 1) / Σ | Higher spending in later years |

where CY = number of construction years. The front-loaded profile reflects projects where advanced works (tunnelling, land acquisition) dominate early expenditures; the back-loaded profile reflects projects where fit-out and commissioning costs dominate.

**Limitation:** These are parametric shapes, not project-specific S-curves. Real construction schedules typically follow a sigmoid pattern (slow start → peak activity → taper). Users requiring S-curve allocation should override via external computation.

### 4.3 Operational-Phase Cash Flows

For each year of operation (t = 0 to appraisal_yrs − 1):

**Passengers:**
PAX(t) = PAX₀ × (1 + g_demand)^t

**Revenue:**
REV(t) = PAX(t) × fare₀ × (1 + g_fare)^t / 10⁶

**Operating costs (HSR):**
OPEX_HSR = (c_maint × L + (c_energy + c_staff + c_rs_maint) × train_km/10⁶ + overhead)

where train_km = trains_day × op_days × L.

**Time savings:**
Effective saving (minutes) = (upgrade_time + ae_conv) − (hsr_time + ae_hsr)

Existing passengers (diverted rail + air + car shift):
- Time_biz = PAX_existing × s_biz × Δhrs × VOT_biz(t)
- Time_com = PAX_existing × s_com × Δhrs × VOT_com(t)
- Time_lei = PAX_existing × s_lei × Δhrs × VOT_lei(t)

Generated passengers (rule-of-half):
- Time_gen = PAX_generated × Δhrs × VOT_weighted × 0.5

where VOT values grow annually: VOT(t) = VOT₀ × (1 + g_VOT)^t.

**Environmental benefits:**
- Env_air = shifted_air(M pax) × CO₂_per_Mpax × CO₂_price / 10⁶
- Env_car = shifted_car(M pax) × (CO₂_per_Mpax × 0.4) × CO₂_price / 10⁶

The 0.4 factor for car-shift CO₂ reflects that per-passenger car emissions are substantially lower than per-passenger air emissions on comparable corridors (EC, 2020; EEA, 2023).

**Accident and congestion:**
- Accident = shifted_car(M pax) × accident_benefit
- Congestion = shifted_car(M pax) × (congestion_base / base_shifted_car)

**Wider Economic Benefits and reliability:**
- WEBs = total_time_benefits × webs_pct / 100
- Freq/Rel = total_time_benefits × 0.05

### 4.4 Residual Value

At the end of the appraisal period, a residual value is credited:

Residual = CAPEX_HSR × residual_pct/100 − CAPEX_CF × residual_pct/100

This represents the unrealised service life of the infrastructure beyond the appraisal window.

### 4.5 Summary Metrics

Present values are computed for each component by multiplying annual flows by discount factors and summing across all years.

| Metric | Formula |
|--------|---------|
| BCR (absolute) | PV(benefits) / PV(HSR costs) |
| BCR (incremental) | PV(benefits) / PV(incremental costs) |
| NPV (absolute) | PV(benefits) − PV(HSR costs) |
| NPV (incremental) | PV(benefits) − PV(incremental costs) |
| Financial NPV | PV(revenue) − PV(HSR costs) |
| IRR | Discount rate at which NPV(incremental) = 0 (bisection) |
| Nominal payback | First year where cumulative undiscounted net flows ≥ 0 |
| Discounted payback | First year where cumulative discounted net flows ≥ 0 |

IRR is computed via bisection on the incremental social net cash flows, with a maximum of 60 iterations. If no sign change occurs in the net flow sequence, IRR is undefined.

---

## 5. Sensitivity and Risk Analysis

### 5.1 One-Way Sensitivity (Tornado) Analysis

One-way sensitivity varies each selected parameter independently by a user-defined percentage (default ±20%) while holding all others at base-case values. For each parameter, the CBA engine is re-run at the low and high values, and the resulting target metric (BCR absolute, BCR incremental, or NPV absolute) is recorded.

The results are displayed as a horizontal tornado diagram (Plotly bar chart), ordered by the range of metric variation—placing the most influential parameters at the top. This identifies which assumptions most warrant careful estimation and which have limited impact on outcomes.

Available sensitivity parameters include: annual passengers, at-grade cost, tunnel cost, viaduct cost, VOTs (business/commuter/leisure), discount rate, construction years, upgrade time, HSR time, WEBs percentage, congestion relief, cost overrun, trains per day, air shift, car shift, access/egress times, CO₂ price, demand growth, rolling-stock cost, stations cost, generated share, and residual value.

### 5.2 Monte Carlo Simulation

The Monte Carlo module enables probabilistic assessment of outcome uncertainty. Users select which parameters to stochasticise and specify distribution types and bounds:

| Distribution | Parameters | Description |
|-------------|-----------|-------------|
| Triangular | min, mode (= base case), max | Asymmetric uncertainty; suitable for bounded parameters |
| Normal | mean (= base case), σ derived from min/max | Symmetric uncertainty; may generate tails beyond bounds |
| Uniform | min, max | Equal probability across range; maximum ignorance prior |

The simulation runs N independent draws (default: 5,000) with a fixed random seed (42) for reproducibility. For each draw, a new parameter set is constructed by replacing selected base-case values with random draws, and `run_cba` is executed.

Outputs include:
- Probability that BCR > 1.0 (social viability)
- Probability that NPV > 0
- Median BCR and NPV
- 5th and 95th percentiles (90% confidence interval)
- Histograms of BCR and NPV distributions

**Limitation:** Parameter draws are independent—no correlation structure is imposed. In reality, parameters such as demand growth and VOT growth are positively correlated (both driven by GDP growth), and construction costs for different components may be correlated through shared input price indices. Ignoring these correlations likely understates the true variance of outcomes (though the direction of bias depends on the correlation sign).

### 5.3 Threshold (Break-Even) Analysis

The threshold module performs a binary search to find the parameter value at which a specified metric equals a target (default: BCR = 1.0). The search algorithm:

1. Receives a parameter key, a search interval [lo, hi], and a target metric.
2. Evaluates the CBA at the midpoint.
3. Narrows the interval based on whether the result is above or below the target.
4. Repeats for up to 60 iterations (precision ≈ (hi − lo) / 2⁶⁰).

Common threshold analyses include:
- Minimum annual passengers for BCR = 1.0
- Maximum at-grade cost for BCR = 1.0
- Minimum effective time saving (implied from HSR journey time) for BCR = 1.0
- Minimum business VOT for BCR = 1.0

If the target is not bracketed within the search interval, the function returns None, indicating that no solution exists in the specified range.

### 5.4 Reference Class Forecasting (Flyvbjerg Correction)

The framework incorporates Reference Class Forecasting (RCF) as a robustness check, applying empirically derived correction factors for systematic optimism bias in rail project appraisals:

- **Cost uplift:** +44.7% (average rail cost overrun from Flyvbjerg et al., 2002, confirmed in the larger sample of Flyvbjerg, 2006)
- **Demand factor:** ×0.486 (= actual demand scaled down to48.6% of forecast per Flyvbjerg 2005; factor0.486 = (−51.4% mean rail demand shortfall)

Note on the demand factor: Flyvbjerg et al. (2005) finds a mean rail demand shortfall of −51.4% (SD = 281%). This means actual demand averages 48.6% of forecasts — so the correction factor multiples demand by 0.486. The median shortfall is -50% in the extended dataset (Flyvbjerg, 2006, Table4); the mean is used here because it better captures the right-skewed distribution of forecasting optimism.

The RCF adjustment replaces (not supplements) the user's current cost-overrun uplift:

1. Remove user's cost-overrun uplift to recover pre-uplift base CAPEX.
2. Apply the Flyvbjerg average uplift (+44.7%) to the pre-uplift base.
3. Replace base-year demand with base-year × 0.486 (reflecting mean shortfall of 51.4%).
4. Re-run the full CBA with adjusted parameters.

This "replace, don't stack" approach avoids double-counting: if a user has already applied a 25% cost overrun (as in the HS2 preset), the RCF correction replaces it with the Flyvbjerg 44.7% uplift rather than adding them. The resulting RCF-adjusted BCR and NPV represent a pessimistic-but-empirically-grounded scenario.

---

## 6. Output Capabilities

### 6.1 Executive Summary

The executive summary tab displays:
- Key metrics (BCR absolute/incremental, NPV absolute/incremental/financial, IRR, payback periods)
- Qualitative flags (e.g., "Socially viable" when BCR > 1.0)
- A BCR gauge chart
- RCF-adjusted metrics as a robustness check

### 6.2 Detailed Results

- Present-value breakdown bar charts (costs vs. benefits, by component)
- Benefit composition pie chart
- Component-by-component present value table
- Threshold analysis results
- Annual cash-flow profile chart

### 6.3 Sensitivity

- Interactive tornado diagram with selectable parameters and target metric
- Configurable variation range (±10%, ±20%, ±30%)

### 6.4 Monte Carlo

- Parameter distribution configuration panel
- Simulation execution and progress
- Results summary (probability of viability, median, percentiles)
- BCR and NPV histograms

### 6.5 Corridor Comparison

- Runs all 15 corridor presets with the currently selected country socio-economic profile
- Comparative table of key metrics
- BCR-vs-CAPEX scatter plot identifying clusters of viable and non-viable corridors

### 6.6 Multi-Criteria Analysis (MCA)

The framework implements a Weighted Sum Model (WSM) of nine non-monetary criteria, derived from EU and national appraisal guidance. The criteria framework follows the MD Č/SFDI Rezortní metodika (2023, aktualizace 2025) §4.5 — which requires explicit non-monetary criteria alongside CBA — and aligns with JASPERS/DG REGIO (2021) Economic Appraisal Vademecum Table p.7 recommending MCA for project selection with non-monetisable criteria. The scoring follows the Analytic Hierarchy Process (AHP) framework of Saaty (1980) and MCDA methodology of Belton & Stewart (2002).

**Criterion definitions and sources:**

1. **Strategic Fit** — alignment with national/EU transport strategies and TEN-T corridors.  
   *Source: MD ČR/SFDI (2023) §4.5 — strategický soulad*

2. **Regional Cohesion** — impact on reducing regional disparities and access to services.  
   *Source: JASPERS (2021) §2.3 EU Cohesion objective*

3. **Environmental Sustainability** — beyond CO₂ monetization: biodiversity, landscape, noise.  
   *Source: MD ČR/SFDI (2023) §4.5; EC Handbook on External Costs (2020)*

4. **Safety** — modern safety systems (ETCS Level ≥2) and accident risk reductions.  
   *Source: MD ČR/SFDI (2023) §4.5; EC Cohesion Policy Objective 3*

5. **Access & Connectivity** — integration with existing networks, feeder services.  
   *Source: MD ČR/SFDI (2023) §4.5; JASPERS (2021) Table p.7 connectivity criteria*

6. **Implementation Feasibility** — institutional capacity, land acquisition.  
   *Source: JASPERS (2021) §2.3 institutional capacity criterion; MD ČR/SFDI (2023)*

7. **Innovation & Technology** — ERTMS/ETCS deployment, digitalization, interoperability.  
   *Source: MD ČR/SFDI (2025) Metodika digitalizace; JASPERS (2021) innovation dimension*

8. **Social Acceptance** — public support, political endorsement, stakeholder consensus.  
   *Source: Expert criterion per Belton & Stewart (2002); EC Stakeholder Engagement guidance*

9. **Capacity Release** — freight and regional service potential on freed conventional rail capacity.  
   *Source: UK DfT (2023) TAG Unit A5.4 — Released capacity benefits; MD ČR/SFDI (2023) §4.5*

**Data Provenance:**

Corridor-specific MCA scor s are expert estimates based on publicly available project documentation — feasibility studies, National Audit Office (NAO) / European Court of Auditors (ECA) reports, parliamentary committee reviews, CBA appraisals (HS2, Rail Bltica), and EU corridor assessments (INFRAS/UIC). The methodology documents define the criteria framework; per-project scoring requires appraisal-specific assessment beyond what any individual document provide . Default scores are intended as reasoned starting points that should be calibrated against project-specific data.

Each scoring set includes source justification embedded in the code, citing the public document or report from which the reasoning is derived.

The MCA tab provides:

- **Adjustable weight sliders** — each criterion 0–100%, auto-normalsed to 100%.
- **Adjustable score sliders** — per-corridor defaults with visible source annotation.
- **Radar (spider) chart** (Plotly) — visual profile of all eight criteria dimensions.
- **Weighted Score Table** — weight × score = contribution to overall MCA score (max 5.00).
- **Combined Decision Index** — normalized CBA score (1–5 scale) averaged with MCA weighted score (1–5). Score ≥ 3.5 → strong non-monetary case; 2.5–3.0 → adequate; <2.5 → weak.
- **Qualitative verdict** — integrating CBA and MCA results for holistic project assessment.

### 6.7 Audit Trail and Documentation

- Full annual cash-flow DataFrame (construction + operation phases, all components)
- CSV download of cash flows
- Parameter snapshot recording all input values
- One-click generation of a self-contained Markdown documentation file covering methodology, results, and references

---

## 7. Assumptions and Limitations

### 7.1 Structural Assumptions

1. **Single-point demand forecast.** The model uses a deterministic demand projection (base ridership × compound growth). There is no endogenous mode-choice model, no competition from other modes at the demand-formation stage, and no induced-demand feedback loop. Demand uncertainty is addressed only ex-post through sensitivity and Monte Carlo analysis.

2. **Static counterfactual.** The conventional-rail upgrade counterfactual is characterised by fixed CAPEX, OPEX, and journey time. There is no dynamic feedback between the two scenarios—for example, the counterfactual does not respond to HSR-induced changes in rail network capacity or congestion.

3. **Parametric spend profiles.** Construction expenditure follows one of three simple shapes (linear, front-loaded, back-loaded). Real projects exhibit S-curve spending patterns, which can be approximated but not exactly replicated by these profiles.

4. **No phasing or real options.** The model evaluates a single, irrevocable investment decision. It does not consider staged construction, deferment options, or adaptive management strategies that could significantly affect expected value (OECD, 2022).

5. **No distributional analysis.** All benefits and costs are aggregated across society. The model does not identify who gains and who loses, nor does it weigh benefits accruing to different income groups differently. Equity-weighted CBA would require distributional weights not currently implemented.

### 7.2 Benefit Estimation Limitations

6. **Average unit externalities.** Environmental, accident, and congestion benefits use average unit costs (€/tonne CO₂, €/accident avoided, €/congestion relieved), not marginal damage functions. In congested networks, marginal costs may substantially exceed averages; in uncongested contexts, they may be near zero (INFRAS/IWW, 2004; EC, 2020).

7. **WEBs as a fixed percentage.** Wider economic benefits (agglomeration, thick-market effects, labour market pooling) are estimated as a fixed percentage of time savings rather than computed from an explicit spatial economic model. This shortcut, while common in practice (Venables, 2007; Graham, 2007), can over- or understate WEBs depending on corridor characteristics.

8. **Frequency/reliability as 5% proxy.** The 5% of time savings assigned to frequency and reliability is an arbitrary rule of thumb, not derived from a service-quality valuation model.

9. **Car CO₂ at 40% of air CO₂.** The 0.4 factor for car-to-rail CO₂ savings is a simplification. Actual per-passenger car emissions depend on occupancy, vehicle type, trip length, and driving conditions. Project-specific emission factor analysis is recommended.

10. **Congestion scaling.** Congestion relief is assumed to scale linearly with shifted car passengers. In reality, the marginal congestion benefit of removing one car from a highly congested road is much greater than from a free-flowing road—this non-linearity is not captured.

### 7.3 Data and Calibration Limitations

11. **Uncalibrated vulnerability of VOT parameters.** The VOT values in country presets are drawn from national appraisal guidelines (UK TAG, CGEDD, etc.) but may not reflect the specific characteristics of the corridor under analysis. VOT varies by trip purpose, distance, income, and context.

12. **Monte Carlo independence.** Stochastic parameter draws are uncorrelated. Introducing a correlation matrix (e.g., demand growth ↔ VOT growth ↔ GDP growth) would produce more realistic joint distributions.

13. **Fixed operating-cost structure.** HSR operating costs are decomposed into infrastructure maintenance, energy, staff, rolling-stock maintenance, and overhead—but each is a flat per-unit amount. Economies of density, load-factor effects, and technology improvements over the appraisal period are not modelled.

14. **Residual value approximation.** The residual value is a fixed percentage of CAPEX, independent of asset condition, remaining service life, or technological obsolescence. A more sophisticated approach would model residual value as a function of depreciation and remaining utility.

15. **No reinvestment modelling.** Major mid-life renewals (track replacement, signalling upgrades, rolling-stock overhaul) are not distinguished from annual maintenance. Lumping them into the maintenance line item may understate periodic capital needs.

### 7.4 Computational Notes

16. **IRR bisection.** The IRR solver uses bisection, which converges reliably but assumes a single sign change in the net cash-flow sequence. Projects with multiple sign changes (e.g., large mid-life reinvestments) may have multiple IRRs; only one will be found.

17. **Sensitivity is one-way only.** Multi-way sensitivity (combinatorial exploration of parameter interactions) is not implemented. Parameters that are individually benign may become critical in combination—a limitation of all one-at-a-time approaches.

18. **Corridor comparison uses current settings.** When comparing corridors, only the corridor-specific engineering/demand parameters change; the country profile remains fixed. This means the VOT, discount rate, and externality values of the current profile are applied to all corridors, including those in different countries.

---

## 8. Regression Testing

The framework includes an automated regression test suite (`regression_test()`) that validates core functionality:

| Test | Condition |
|------|-----------|
| CAPEX positive | CAPEX_HSR > 0 |
| BCR in range | 0 < BCR_absolute < 3 |
| NPV finite | NPV is finite |
| IRR finite | IRR is finite |
| Effective saving non-negative | Δtime ≥ 0 |
| Benefits positive | PV(benefits) > 0 |
| Costs positive | PV(costs) > 0 |
| Revenue positive | PV(revenue) > 0 |
| Time benefits positive | PV(time_savings) > 0 |
| Row count matches | len(rows) = constr_years + appraisal_yrs |
| All spend profiles run | linear, front-loaded, back-loaded complete without error |

Tests use the VRT Praha–Brno corridor preset with the Czech Republic country profile. The regression test prints PASS/FAIL for each check and returns a boolean aggregate, enabling continuous integration validation.

---

## 9. Conclusion

This paper has presented the HSR Social CBA Sensitivity Analyser, a computational framework that extends standard transport cost–benefit analysis with explicit treatment of uncertainty. By incorporating Reference Class Forecasting, probabilistic Monte Carlo simulation, and systematic sensitivity analysis, the framework enables decision-makers to move beyond single-point BCR estimates toward a richer understanding of the conditions under which HSR investments deliver positive social returns.

The framework's principal contributions are:

1. **Unified incremental appraisal** with both absolute and incremental perspectives, following EU and UK methodological guidance.
2. **Empirical optimism-bias correction** via Flyvbjerg RCF factors, grounded in the largest available sample of rail project outcomes.
3. **Probabilistic risk quantification** through user-configurable Monte Carlo simulation, revealing the probability distribution of outcomes rather than a single deterministic result.
4. **Systematic sensitivity decomposition** via tornado analysis, identifying the parameters that most warrant careful estimation.
5. **Cross-corridor benchmarking** using built-in presets for 15 European HSR lines, enabling rapid comparative analysis.

The primary limitations—the absence of endogenous mode choice, the parametric spend profiles, the lack of distributional analysis, and the independence of Monte Carlo draws—define clear directions for future development. As richer datasets and more sophisticated behavioural models become available, each of these simplifications can be relaxed within the existing modular architecture.

The framework is designed to serve both as a practical appraisal tool for transport planners and as a transparent, reproducible platform for academic research on the economics of high-speed rail.

---

## References

COWI. (2004). *Cost–Benefit Analysis and Overloads on the Road Network*. Final Report for the European Commission, DG TREN.

de Vos, P. (2014). Appraisal of large transport projects: An analysis of construction cost overruns in Dutch rail infrastructure. *Proceedings of the European Transport Conference*.

Elmaghraby, Z., & Kabadayi, S. (2022). Demand forecasting accuracy in transportation: A systematic review. *Transport Reviews*, 42(3), 351–377.

European Commission. (2014). *Guide to Cost–Benefit Analysis of Investment Projects*: Economic appraisal tool for Cohesion Policy 2014–2020. DG Regional and Urban Policy.

European Commission. (2020). *Handbook on the External Costs of Transport*, Version 2020–1. DG MOVE. https://ec.europa.eu/transport/sites/default/files/handbook-on-external-costs-of-transport-2020.pdf

European Environment Agency. (2023). *Transport emissions of air pollutants*. EEA Indicator CSI 004. https://www.eea.europa.eu/en/topics/in-depth/air-pollution

Flyvbjerg, B., Holm, M. S., & Buhl, S. (2002). Underestimating costs in public works projects: Error or lie? *Journal of the American Planning Association*, 68(3), 279–295. https://doi.org/10.1080/01944360208976258

Flyvbjerg, B., Holm, M. S., & Buhl, S. (2005). How (in)accurate are demand forecasts in public works projects? The case of transportation. *Journal of the American Planning Association*, 71(2), 131–146. https://doi.org/10.1080/01944360508976688

Flyvbjerg, B. (2006). Cost overruns and demand shortfalls in urban rail and other infrastructure. *Transportation Research Record*, 1977(1), 1–10. https://doi.org/10.1177/03611981061977001101

Financial Conduct Authority. (2023). *Valuing consumers' time in our cost benefit analysis*. FCA, London. http://www.fca.org.uk/publication/external-research/valuing-consumers-time-cost-benefit-analysis.pdf

Graham, D. J. (2007). *Agglomeration Economies and Transport Investment*. Discussion Paper 2007-11, ITF/OECD. https://www.itf-oecd.org/sites/default/files/docs/rtoct07graham.pdf

HEATCO. (2006). *Developing Harmonised European Approaches for Transport Costing and Project Assessment*. FP6 Project, Deliverable D5. https://aramis.admin.ch/Grunddaten/?ProjectID=18790

HM Treasury. (2022). *The Green Book: Central Government Guidance on Appraisal and Evaluation*. https://www.gov.uk/government/publications/the-green-book-appraisal-and-evaluation-in-central-government

INFRAS/IWW. (2004). *External Costs of Transport: Update Study*. Final Report for the International Union of Railways (UIC). https://uic.org/IMG/pdf/external_cost_of_transport.pdf

ITF. (2023). *ITF Transport Outlook 2023*. OECD Publishing, Paris. https://doi.org/10.1787/b6cc9ad5-en

National Audit Office. (2024). *High Speed Two: A progress update*. NAO, London. https://www.nao.org.uk/press-releases/high-speed-two-a-progress-update/

Rail Baltica Global Express. (2022). *Rail Baltica Cost–Benefit Analysis Report*. https://www.sam.gov.lv/en/article/rail-baltica-introduces-outcomes-updated-cost-benefit-analysis

Small, K. A. (2012). Valuation of travel time. *Economics of Transportation*, 1(1–2), 2–14. https://doi.org/10.1016/j.ecotra.2012.09.002

OECD. (2022). *Cost–Benefit Analysis and the Environment: Further Developments and Policy Use*. OECD Publishing, Paris. https://doi.org/10.1787/9789264085169-en

SACTRA. (1999). *Transport and the Economy*. Standing Advisory Committee on Trunk Road Assessment, UK DETR.

UIC. (2018). *High Speed Rail: Fast Track to Sustainable Mobility*. International Union of Railways, Paris. https://uic.org/high-speed

UK Department for Transport. (2023). *Transport Analysis Guidance: Values of Travel Time Savings*, TAG Unit A1.3. https://www.gov.uk/government/publications/tag-unit-a1-3-values-of-travel-time-savings

UK Department for Transport. (2023). *Transport Analysis Guidance: Wider Impacts*, TAG Unit A5.4, Section 4 — Released Capacity. https://www.gov.uk/government/publications/tag-unit-a5-4-wider-impacts

UK DESNZ. (2023). *Green Book supplementary guidance: Valuation of energy use and greenhouse gas emissions for appraisal*, Table 3. https://www.gov.uk/government/publications/valuation-of-energy-use-and-greenhouse-gas-emissions-for-appraisal

Venables, A. J. (2007). Evaluating urban transport improvements: Cost–benefit analysis in the presence of agglomeration and income taxation. *Journal of Transport Economics and Policy*, 41(2), 173–188. https://doi.org/10.3828/jtep.2007.41.2.173

Cantarelli, C. C., Flyvbjerg, B., Molin, E. J. E., & van Wee, B. (2012). Cost overruns in large-scale transportation infrastructure projects: Explanations and their theoretical roots. *Transport Policy*, 22, 7–9. https://doi.org/10.1016/j.tranpol.2012.04.01

CDV. (2019). *Metodika kvantifikace externalit z dopravy* [Methodology for quantifying transport externalities]. Transport Research Centre, Brno. https://tacr.gov.cz/dokums_raw/metodiky/TB010MD017_metodika.pdf

CGEDD/CGE. (2020). *Valeur du temps et prix implicites dans les déplacements*. Rapport no. 012593-01. https://igedd.documentation.developpement-durable.gouv.fr/documents/Affaires-0012727/014363-01_rapport-publie.pdf

CPK. (2023). *Program for Polish High-Speed Railway Network: Feasibility Study Update*. Centralny Port Komunikacyjny, Warsaw. https://railmarket.com/news/infrastructure/28077-cpk-eur-18-billion-for-development-of-high-speed-railway-in-poland

ITF. (2020). *What is the Value of Saving Travel Time?* OECD Publishing, Paris. https://www.oecd.org/content/dam/oecd/en/publications/reports/2019/10/what-is-the-value-of-saving-travel-time_b418a6d2/eeb102ea-en.pdf

KiM/Significance. (2024). *Values of Travel Time, Reliability and Comfort in the Netherlands 2022*. Netherlands Institute for Transport Policy Analysis. https://english.kimnet.nl/site/binaries/site-content/collections/documents/2024/04/03/new-values-of-travel-time-reliability-and-comfort-in-the-netherlands/

Beria, P., Grimaldi, R., Alves, V., & Boscacci, F. (2018). An ex-post cost benefit analysis of Italian high speed train, five years after. *Research in Transportation Business & Management*, 28, 36–49. https://doi.org/10.1016/j.rtbm.2018.10.002

MDVaSR. (2023). *Feasibility Study: High-Speed Rail Bratislava–Brno*. Ministry of Transport and Construction of the Slovak Republic. https://www.railtarget.cz/technologies-and-infrastructure/slovakia-high-speed-rail-bratislava-czech-austria-feasibility-study-11927.html

Ministerio de Transportes y Movilidad Sostenible. (2020). *Recomendaciones para la evaluación económica, coste-beneficio de proyectos de transporte*. Madrid. https://cdn.transportes.gob.es/portal-web-transportes/carreteras/normativa_tecnica/05_estudios_proyectos/0410901.pdf

MIT. (2019). *Linee guida per la valutazione costi–benefici dei progetti di investimento in infrastrutture di trasporto*. Ministero delle Infrastrutture e dei Trasporti, Rome.

ORR/Arup. (2007). *HS1 Cost Review Report*. Office of Rail and Road, London. https://www.orr.gov.uk/sites/default/files/om/hs1-cost-review-report-by-Arup.pdf

Statista. (2014). Cost of TGV lines per kilometre in France. https://www.statista.com/statistics/764486/cost-construction-lines-lgv-by-kilometer-la-france/

World Bank. (2021). *Quality Infrastructure Investment: Principles and Practice*. World Bank Group, Washington, DC. https://doi.org/10.1596/978-1-4648-1749-7
