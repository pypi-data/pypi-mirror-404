import pandas as pd
from plotnine import aes, element_blank, geom_point, geom_rug, ggplot, labs, theme

from ..config_theme import TUFTE_DARK, TUFTE_POINT_SIZE_SMALL, tufte_theme


def dot_dash_plot(
    df: pd.DataFrame, x_col: str, y_col: str, title: str = "Dot-Dash Plot", **kwargs
) -> ggplot:
    """
    Erstellt einen Dot-Dash-Plot (Tufte's minimalistischer Scatter-Plot).
    Zeigt die Punktwolke mit einer Verteilung der Daten an den Achsen.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame mit den Daten für den Plot.
    x_col : str
        Name der Spalte für die X-Achse (numerisch).
    y_col : str
        Name der Spalte für die Y-Achse (numerisch).
    title : str (Standardwert="Dot-Dash Plot")
        Titel des Plots.
    **kwargs :
        Zusätzliche Argumente für geom_point (z.B. color, alpha).

    Returns
    -------
    plot : plotnine.ggplot
        Ein ggplot-Objekt mit dem Dot-Dash-Plot.

    """
    # Standardwerte, falls nicht in kwargs
    kwargs.setdefault("color", TUFTE_DARK)
    kwargs.setdefault("size", TUFTE_POINT_SIZE_SMALL)
    kwargs.setdefault("alpha", 0.8)

    additional_kwargs = {k: v for k, v in kwargs.items() if k != "color"}

    plot = (
        ggplot(df, aes(x=x_col, y=y_col))
        # Punkte definieren
        + geom_point(color=kwargs["color"], **additional_kwargs)
        # Verteilungsränder hinzufügen
        + geom_rug(sides="bl", size=0.3, alpha=0.5, color=kwargs["color"])
        # Beschriftung
        + labs(title=title)
        # Tufte-Theme
        + tufte_theme()
        + theme(axis_line=element_blank())
    )
    return plot
