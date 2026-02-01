import pandas as pd
from plotnine import aes, element_text, facet_wrap, geom_line, ggplot, labs, theme

from ..config_theme import TUFTE_DARK, TUFTE_FONT, TUFTE_LINE_WIDTH, tufte_theme


def small_multiples(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    facet_col: str,
    title: str = "Small Multiples",
    ncol: int = 4,
    x_label: str | None = None,
    y_label: str | None = None,
    **kwargs,
) -> ggplot:
    """
    Erstellt kleine Mehrfachplots (Small Multiples) für kategoriale Datenreihen.
    Zeigt mehrere Linienplots nebeneinander, getrennt nach der Facettenkategorie.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame mit den Daten für den Plot.
    x_col : str
        Name der Spalte für die X-Achse (kategorisch oder kontinuierlich).
    y_col : str
        Name der Spalte für die Y-Achse (numerisch).
    facet_col : str
        Name der Spalte für die Facettenkategorie.
    title : str (Standardwert="Small Multiples")
        Titel des Plots.
    ncol : int (Standardwert=4)
        Anzahl der Spalten für die Facettenanordnung.
    x_label : str
        Beschriftung der X-Achse.
    y_label : str
        Beschriftung der Y-Achse.
    **kwargs :
        Zusätzliche Argumente für geom_line (z.B. color, alpha).

    Returns
    -------
    plot : plotnine.ggplot
        Ein ggplot-Objekt mit den kleinen Mehrfachplots.

    """
    line_color = kwargs.get("color", TUFTE_DARK)
    additional_kwargs = {k: v for k, v in kwargs.items() if k != "color"}

    plot = (
        ggplot(df, aes(x=x_col, y=y_col))
        +
        # Linien definieren
        geom_line(size=TUFTE_LINE_WIDTH, color=line_color, **additional_kwargs)
        +
        # Facetten anlegen
        facet_wrap(f"~{facet_col}", ncol=ncol, scales="fixed")
        +
        # Beschriftung
        labs(title=title or "Small Multiples", x=x_label, y=y_label)
        +
        # Tufte-Theme
        tufte_theme()
        + theme(
            panel_spacing_x=0.05,
            panel_spacing_y=0.05,
            strip_text=element_text(
                size=10, weight="bold", ha="left", family=TUFTE_FONT
            ),
            axis_text_x=element_text(size=7, angle=45, hjust=1, family=TUFTE_FONT),
            axis_text_y=element_text(size=7, family=TUFTE_FONT),
        )
    )

    return plot
