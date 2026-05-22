# Nápady na vylepšení HSR CBA Analyseru

> Generováno s Hermes Agent, 4. 5. 2026

---

## 🔥 High-impact (přidá nejvíc hodnoty)

| Feature | Proč | Náročnost |
|---------|------|-----------|
| **Scenario manager** – Uložení/načtení celé konfigurace (JSON/YAML) | Teď musíš vše ručně přenastavovat. S exportem/importem scénářů můžeš porovnávat varianty a sdílet je. | Nízká |
| **Multi-Criteria Analysis (MCA) tab** – Vážené skóre pro nepeněžní kritéria | EU i české metodiky (MD ČR) vyžadují vedle CBA i MCA: strategický fit, regionální soudržnost, environmentální dopady. Bez toho to není kompletní appraisal. | Střední |
| **Wider Economic Impacts (WEIs)** – Aglomerační benefity, přesun do produktivnějších prací | Máš citace na Venablese a Grahama, ale samotný model WEI nepočítá. UK TAG Level 3 – efektivnější trh práce díky HSR. U koridorových projektů to může být 10–30 % dodatečných benefitů. | Vysoká |
| **Funding / spolufinancování EU** – Výpočet s granty (CEF, IROP), různá míra kofinancování | V ČR/SR realita: bez dotace EU nic nestojí. Mít možnost zadat % dotace a vidět "financial NPV" vs "economic NPV" (jak to chce Evropská komise). | Střední |

## 📊 Střední priorita

| Feature | Proč | Náročnost |
|---------|------|-----------|
| **Distribuční analýza** – Kdo získává? Podle regionu, příjmové skupiny | Moderní CBA metodiky (UK TAG, nové EU guidelines) to čím dál víc vyžadují. Benefit-cost ratio podle regionu. | Střední |
| **Růst hodnoty času v čase** – Income elasticita VOT (default ~1.0 dle UK TAG) | Dneska máš fixní VOT. Reálně roste s HDP – u projektu na 60 let to dělá zásadní rozdíl v NPV. | Nízká |
| **Detailnější emisní model** – Stínové ceny CO₂ podle scénářů (low/high), scénáře dekarbonizace gridu | Teď tam asi máš jednu hodnotu za CO₂. EU ETS cena + sociální náklady uhlíku + trajektorie dekarbonizace elektřiny pro elektrické HSR. | Nízká |
| **Zbytková hodnota podle typu aktiva** – Různé životnosti: infrastruktura 60 let vs vozidla 30 let | Lepší než jednoduchá perpetuita. Dělá to rozdíl hlavně u projektů s drahými vozidly. | Nízká |

## 🛠️ Kvalita života / UX

| Feature | Proč | Náročnost |
|---------|------|-----------|
| **Side-by-side porovnání 2–3 scénářů** v jednom view | Teď máš corridor comparison, ale neumíš porovnat dva různé designy jednoho koridoru. | Střední |
| **Waterfall chart** – Rozklad NPV na jednotlivé složky benefitů/nákladů | Lepší komunikace než tabulka. "Proč je NPV záporné? Která složka to táhne dolů?" | Nízká |
| **Validace vstupů s warningy** – "Tvoje VOT je mimo typický rozsah pro CEE" | Pro studenty a policy makery super – červené/oranžové flagy, že zadali nesmysl. | Nízká |
| **Risk matrix** vedle Monte Carla – Kvalitativní rizika (legislativa, politická vůle, geologie) | Monte Carlo pokrývá kvantitativní, ale vedle toho by měla být matice s mitigací. | Nízká |

## 🧪 Pro publikaci / akademické využití

| Feature | Proč |
|---------|------|
| **Automatický report do LaTeX/PDF** | Teď generuješ `.md` – super. Ale pro akademickou publikaci by LaTeX výstup umožnil rovnou vložit do článku. |
| **Input data z reálných projektů jako presety** – HS2, Rail Baltica, VRT Praha–Brno, Lyon–Turin | Máš tam nějaké presety, ale reálné hodnoty z appraisalu by to posunuly do "učebnicového nástroje". |
| **Citace na konkrétní parametry** – Tooltip "odkud tahle hodnota?" | Teď máš obecný seznam citací. Ale u každého slideru tooltip "Doporučená hodnota dle HEATCO (2006) Table 5.2" by byla akademická lahůdka. |

---

## 🎯 Top 3 (doporučené pořadí implementace)

1. **Scenario manager** – největší poměr užitek/práce
2. **MCA tab** – bez toho to není plnohodnotný appraisal nástroj pro EU projekty
3. **VOT růst + lepší zbytková hodnota** – málo práce, velký dopad na přesnost výsledků