"""
Generate all Tufte visualization examples using plotnine/dufte.
Principles: Maximize Data-Ink, Enforce Comparisons, Integrate Text & Graphics.
"""

from pathlib import Path

import numpy as np
import pandas as pd

# Wir gehen davon aus, dass dieses Modul lokal existiert, wie im Snippet angegeben.
from plot_dufte.plots import (
    dot_dash_plot,
    layered_focus,
    range_frame,
    slopegraph,
    small_multiples,
    sparklines,
    time_series,
)

OUTPUT = Path("output")
OUTPUT.mkdir(exist_ok=True)
np.random.seed(42)


def generate_random_walk(start_price, n, volatility=0.02):
    """Hilfsfunktion für realistische Aktienkurse (Geometrische Brownsche Bewegung)"""
    returns = np.random.normal(loc=0.0005, scale=volatility, size=n)
    price_path = start_price * (1 + returns).cumprod()
    return price_path


def main():
    print("Generating Tufte visualizations with realistic data context...\n")

    # ---------------------------------------------------------
    # 1. Range-Frame Plot (Boxplot Alternative)
    # Tufte Principle: Maximize Data-Ink.
    # Szenario: Michelson-Morley Lichtgeschwindigkeitsmessungen (historischer Kontext)
    # ---------------------------------------------------------
    print("... creating Range-Frame Plot (Michelson Speed of Light Data Proxy)")

    # Wir simulieren Messungen der Lichtgeschwindigkeit (km/s - 299000)
    # Experiment 1 hat höhere Varianz, Exp 3 ist präziser.
    n_meas = 40
    df_dist = pd.DataFrame(
        {
            "Experiment": np.repeat(
                ["Expt 1 (Winter)", "Expt 2 (Spring)", "Expt 3 (Summer)"], n_meas
            ),
            "Velocity_Deviation": np.concatenate(
                [
                    np.random.normal(850, 40, n_meas),  # Streuung hoch
                    np.random.normal(790, 25, n_meas),  # Streuung mittel
                    np.random.normal(740, 15, n_meas),  # Streuung niedrig (Lerneffekt)
                ]
            ),
        }
    )

    df_dist["Experiment"] = pd.Categorical(
        df_dist["Experiment"],
        categories=["Expt 1 (Winter)", "Expt 2 (Spring)", "Expt 3 (Summer)"],
        ordered=True,
    )

    range_frame(
        df_dist,
        "Experiment",
        "Velocity_Deviation",
        title="Speed of Light Measurements (Deviation from 299,000 km/s)",
    ).save(OUTPUT / "1_range_frame.png", width=6, height=4, dpi=300)

    # ---------------------------------------------------------
    # 2. Dot-Dash Plot (Scatterplot mit Randverteilung)
    # Tufte Principle: Escape Flatland / Integration of marginal distributions.
    # Szenario: Zusammenhang zwischen BIP pro Kopf und Lebenserwartung (Log-Scale Proxy)
    # ---------------------------------------------------------
    print("... creating Dot-Dash Plot (GDP vs Life Expectancy)")

    n_countries = 60
    # Simulierte logarithmische Verteilung für BIP
    gdp = np.exp(np.random.normal(9, 1, n_countries))
    # Lebenserwartung korreliert mit log(BIP) mit Sättigungseffekt
    life_exp = 45 + 5 * np.log(gdp / 100) + np.random.normal(0, 3, n_countries)
    life_exp = np.clip(life_exp, 50, 85)  # Realistische Grenzen

    df_scatter = pd.DataFrame(
        {"GDP per Capita ($)": gdp, "Life Expectancy (Years)": life_exp}
    )

    dot_dash_plot(
        df_scatter,
        "GDP per Capita ($)",
        "Life Expectancy (Years)",
        title="Wealth & Health of Nations (Dot-Dash)",
    ).save(OUTPUT / "2_dot_dash_plot.png", width=7, height=7, dpi=300)

    # ---------------------------------------------------------
    # 3. Slopegraph
    # Tufte Principle: Macro/Micro Readings.
    # Szenario: "The Tufte Classic" -
    # Krebs-Überlebensraten über 5 Jahre oder Steuereinnahmen.
    # Wir nehmen hier: Government Receipts as % of GDP
    # (1970 vs 1979) - ein Klassiker.
    # ---------------------------------------------------------
    print("... creating Slopegraph (Government Receipts % GDP)")

    countries = [
        "Switzerland",
        "USA",
        "Germany",
        "UK",
        "France",
        "Sweden",
        "Japan",
        "Italy",
    ]
    # Werte ähnlich dem Tufte-Buch "Visual Display"
    y1970 = [25.0, 31.0, 38.0, 42.0, 39.0, 46.0, 20.0, 30.0]
    y1979 = [
        31.0,
        30.5,
        43.0,
        38.0,
        44.0,
        58.0,
        26.0,
        34.0,
    ]  # Sweden exploded, UK dropped

    data_slope = []
    for country, v70, v79 in zip(countries, y1970, y1979, strict=False):
        # Bestimme Trend für Färbung (Micro-Reading)
        trend = "Increase" if v79 > v70 else "Decrease"
        data_slope.append(
            {"Country": country, "Year": "1970", "Value": v70, "Trend": trend}
        )
        data_slope.append(
            {"Country": country, "Year": "1979", "Value": v79, "Trend": trend}
        )

    df_slope = pd.DataFrame(data_slope)

    p3 = slopegraph(
        df_slope,
        "Country",  # Labels
        "Year",  # X-Achse
        "Value",  # Y-Achse
        title="Government Receipts as % of GDP (1970 vs 1979)",
    )
    p3.save(OUTPUT / "3_slopegraph.png", width=6, height=7, dpi=300)

    # ---------------------------------------------------------
    # 4. Small Multiples
    # Tufte Principle: Comparisons / Enforce visual scope.
    # Szenario: Monatliche Arbeitslosenquote in verschiedenen Sektoren (Saisonalität)
    # ---------------------------------------------------------
    print("... creating Small Multiples (Unemployment by Sector)")

    months = np.arange(1, 13)

    dfs = []
    # Construction: Hohe Saisonalität (Winter arbeitslos)
    dfs.append(
        pd.DataFrame(
            {
                "Month": months,
                "Rate": 8
                + 4 * np.cos((months - 1) / 12 * 2 * np.pi)
                + np.random.normal(0, 0.2, 12),
                "Sector": "Construction",
            }
        )
    )
    # Retail: Peak im Januar (nach Weihnachten Entlassungen)
    dfs.append(
        pd.DataFrame(
            {
                "Month": months,
                "Rate": 5 + 2 * np.exp(-(months - 1)) + np.random.normal(0, 0.2, 12),
                "Sector": "Retail",
            }
        )
    )
    # Tech: Wachstumstrend (fallende Arbeitslosigkeit)
    dfs.append(
        pd.DataFrame(
            {
                "Month": months,
                "Rate": np.linspace(4, 2.5, 12) + np.random.normal(0, 0.1, 12),
                "Sector": "Tech",
            }
        )
    )
    # Healthcare: Stabil
    dfs.append(
        pd.DataFrame(
            {
                "Month": months,
                "Rate": np.full(12, 3.5) + np.random.normal(0, 0.1, 12),
                "Sector": "Healthcare",
            }
        )
    )

    df_multi = pd.concat(dfs)

    p4 = small_multiples(
        df_multi,
        "Month",
        "Rate",
        "Sector",
        ncol=2,
        title="Unemployment Rate % by Sector (Seasonal Patterns)",
        x_label="Month",
        y_label="Rate %",
    )
    p4.save(OUTPUT / "4_small_multiples.png", width=8, height=6, dpi=300)

    # ---------------------------------------------------------
    # 5. Sparklines
    # Tufte Principle: Data Intensity / Word-sized graphics.
    # Szenario: Währungskurse (High frequency noise + Trend)
    # ---------------------------------------------------------
    print("... creating Sparklines (Currency Trends)")

    n_days = 60
    time_points = np.arange(n_days)
    currencies = ["EUR/USD", "GBP/USD", "JPY/USD", "CHF/USD", "AUD/USD"]
    start_vals = [1.10, 1.30, 0.009, 1.05, 0.70]

    spark_data = []
    for curr, start in zip(currencies, start_vals, strict=False):
        values = generate_random_walk(start, n_days, volatility=0.01)
        for t, v in zip(time_points, values, strict=False):
            spark_data.append({"Currency": curr, "Day": t, "Rate": v})

    df_sparklines = pd.DataFrame(spark_data)

    p5 = sparklines(
        df_sparklines,
        "Currency",  # Kategorien
        "Day",  # X
        "Rate",  # Y
        title="60-Day Currency Trends (Sparklines)",
    )
    p5.save(OUTPUT / "5_sparklines.png", width=5, height=6, dpi=300)

    # ---------------------------------------------------------
    # 6. Focus Sparkline / Spaghetti Plot with Highlight
    # Tufte Principle: Layering and Separation.
    # Szenario: Identische Daten wie oben, Fokus auf EUR/USD Performance
    # ---------------------------------------------------------
    print("... creating Focus Sparkline")

    p6 = layered_focus(
        df_sparklines,
        "Day",
        "Rate",
        "Currency",  # Grouping
        "EUR/USD",  # Highlight
        title="Euro vs. Major Currencies (Contextual Layering)",
    )
    p6.save(OUTPUT / "6_layered_focus.png", width=7, height=4, dpi=300)

    # ---------------------------------------------------------
    # 7. Time Series
    # Tufte Principle: Annotations and Context.
    # Szenario: CO2-Konzentration (Keeling Curve Proxy - stetiger Anstieg)
    # ---------------------------------------------------------
    print("... creating Time Series (Keeling Curve Proxy)")

    years = np.arange(1960, 2025, 5)
    # Basiswert 315ppm + exponentieller Anstieg
    co2 = 315 + 1.5 * (years - 1960) + 0.01 * (years - 1960) ** 2

    df_line = pd.DataFrame({"Year": years, "CO2 (ppm)": co2})

    p7 = time_series(
        df_line,
        "Year",
        "CO2 (ppm)",
        title="Atmospheric CO2 Concentration (Mauna Loa Proxy)",
    )
    p7.save(OUTPUT / "7_time_series.png", width=6, height=4, dpi=300)

    print(
        "\n✓ Fertig! Alle Tufte-Style Plots wurden mit realistischen Daten generiert."
    )


if __name__ == "__main__":
    main()
