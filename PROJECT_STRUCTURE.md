# 📘 HSR Social CBA Sensitivity Analyser – Project Structure

## Cíl projektu
Komplexní výpočetní framework pro social cost-benefit analysis (CBA) vysokorychlostních železničních projektů. Aplikace implementuje rigorózní inkrementální CBA metodologii dle EU guidelines, Reference Class Forecasting (Flyvbjerg), tornado analýzu, Monte Carlo simulaci a threshold (break-even) analýzu. Součástí je i akademický paper popisující framework.

## Struktura adresářů
```
HSR/
├── hsr_cba_app.py              # Hlavní aplikace (648 řádků) – Streamlit
├── hsr_cba_app_upg1.py         # Upgrade v1 – rozšířená verze
├── hsr_cba_app_upg2.py         # Upgrade v2 – aktuální verze (pre-citation fix)
├── patch_to_v4.py              # Patch skript pro migraci na v4
├── technical_paper.md          # Akademický paper (532 řádků, 8 sekcí)
├── paper_progress.json         # Progress tracker pro paper
├── citation_verification.json  # Verifikace citací
├── requirements.txt            # streamlit, plotly, pandas, numpy
├── LICENSE.txt                 # Copyright (c) 2026 Tomáš Paleta, All rights reserved
├── COPYRIGHT.md                # Copyright notice
├── backup_2026-04-26/          # Backup předchozí verze
│   ├── hsr_cba_app_v1.py
│   └── hsr_cba_app_upg1.py
└── backup_2026-04-27/          # Backup pre-citation fix
    └── hsr_cba_app_upg2_pre_citation_fix.py
```

## Klíčové algoritmy / Logika

### CBA Engine (`run_cba()`)
1. **Infrastructure costs**: line_length × (at_grade% × cost_at_grade + tunnel% × cost_tunnel + viaduct% × cost_viaduct + signalling + land) + stations + rolling_stock, včetně % overrun
2. **Incremental approach**: capex_incr = capex_hsr − capex_cf (counterfactual upgrade)
3. **Construction phase**: rovnoměrné rozložení CAPEX přes construction years, diskontování
4. **Operation phase**: 40 let provozu, každý rok:
   - Revenue = annual_pax × avg_fare × growth
   - Time savings: effective_saving_min × class-stratified VOT × passengers (plné pro diverted, rule-of-half pro generated)
   - CO₂ savings: modal shift from air/car × CO₂ price × CO₂ per million pax-km
   - Accident reduction, Congestion relief, WEBs (%), Frequency/reliability (5%)
5. **Discounting**: DF(t) = 1/(1+r)^t
6. **Residual value**: % of CAPEX at end of appraisal
7. **Output metrics**: NPV, BCR (absolute + incremental), IRR, payback period

### Reference Class Forecasting (Flyvbjerg)
- Cost uplift: +44.7% (systematické podhodnocení)
- Demand factor: ×0.487 (systematické nadhodnocení)
- Aplikovatelné přes toggle

### Sensitivity Analysis
- **Tornado**: One-way ±20% změna každého parametru, seřazeno dle dopadu na BCR
- **Monte Carlo**: Uživatelem konfigurovatelné distribuce (normal, uniform, triangular, lognormal), N iterací
- **Threshold**: Binary search hledající break-even hodnotu parametru

### Presets
- **15 evropských HSR koridorů**: TGV Paris–Lyon, LGV Est, AVE Madrid–Barcelona/Seville, HS1, HS2 Phase 1, HSL-Zuid, Torino–Milano, VRT Praha–Brno/Brno–Ostrava, CPK Y-line, Budapest–Belgrade, Rail Baltica, Brno–Bratislava
- **10 zemí**: socio-ekonomické profily (VOT, discount rate, CO₂ price)
- Každý preset obsahuje 50+ kalibrovaných parametrů

### Spend Profiles
- 3 profily rozložení CAPEX: equal, front-loaded, back-loaded, S-curve

### Datové toky
```
Uživatel → Streamlit sidebar (preset/prompt) → Session state → run_cba()
→ DataFrame roční CF → Plotly vizualizace + metrické karty
→ Tornado chart → Monte Carlo histogram → Threshold analysis
```

## Aktuální stav
✅ **Hotovo** – verze upg2 (aktuální). Obsahuje všechny CBA výpočty, všechny sensitivity nástroje, 15 presetů, 10 zemí. Paper draft hotový.

## Technické poznámky
- **Tech stack**: Streamlit, Plotly, Pandas, NumPy
- **Autor**: Tomáš Paleta, copyright 2026, all rights reserved
- **Metodologie**: EC Handbook on External Costs of Transport (2020), UK Green Book (HM Treasury, 2022), HEATCO (2006), Flyvbjerg et al. (2002, 2005)
- **Zálohy**: Dvě timestampované zálohy předchozích verzí
- **Paper**: 8-sekční akademický paper popisující celý framework (Abstract → Conclusion)
- **Citace**: citation_verification.json pro tracking zdrojů