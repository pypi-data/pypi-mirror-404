import pandas as pd
from plotnine import aes, element_blank, geom_point, geom_segment, ggplot, labs, theme

from ..config_theme import TUFTE_DARK, TUFTE_GREY, TUFTE_POINT_SIZE_MEDIUM, tufte_theme


def range_frame(
    df: pd.DataFrame, x_col: str, y_col: str, title: str = "Range-Frame Plot", **kwargs
) -> ggplot:
    """
    Erstellt einen Range-Frame-Plot (Tufte's minimalistischer Boxplot).
    Zeigt Median, Quartile (Q1, Q3) und Range (Min, Max) ohne die Box.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame mit den Daten für den Plot.
    x_col : str
        Name der Spalte für die X-Achse (kategorisch oder kontinuierlich).
    y_col : str
        Name der Spalte für die Y-Achse (numerisch).
    title : str (Standardwert="Range-Frame Plot")
        Titel des Plots.
    **kwargs :
        Zusätzliche Argumente für geom_point (z.B. color, alpha).

    Returns
    -------
    plot : plotnine.ggplot
        Ein ggplot-Objekt mit dem Range-Frame-Plot.

    """
    # Berechnung der benötigten Statistiken
    stats = (
        df.groupby(x_col)[y_col]
        .agg(
            [
                ("q1", lambda x: x.quantile(0.25)),
                ("median", "median"),
                ("q3", lambda x: x.quantile(0.75)),
                ("min", "min"),
                ("max", "max"),
            ]
        )
        .reset_index()
    )

    # Standardfarbe nutzen, falls nicht übergeben
    color = kwargs.get("color", TUFTE_DARK)
    additional_kwargs = {k: v for k, v in kwargs.items() if k != "color"}

    return (
        ggplot(stats, aes(x=x_col))
        +
        # Whiskers
        geom_segment(
            aes(x=x_col, xend=x_col, y="min", yend="q1"), size=0.6, color=TUFTE_DARK
        )
        + geom_segment(
            aes(x=x_col, xend=x_col, y="q3", yend="max"), size=0.6, color=TUFTE_DARK
        )
        +
        # Medianmarkierung
        geom_point(
            aes(y="median"),
            size=TUFTE_POINT_SIZE_MEDIUM,
            color=color,
            **additional_kwargs,
        )
        +
        # Q1/Q3 Markierungen
        geom_point(aes(y="q1"), size=1.5, color=TUFTE_GREY, shape="_")
        + geom_point(aes(y="q3"), size=1.5, color=TUFTE_GREY, shape="_")
        +
        # Beschriftung
        labs(title=title, x=None, y=y_col)
        +
        # Tufte-Theme
        tufte_theme()
        + theme(axis_line=element_blank(), axis_ticks=element_blank())
    )
