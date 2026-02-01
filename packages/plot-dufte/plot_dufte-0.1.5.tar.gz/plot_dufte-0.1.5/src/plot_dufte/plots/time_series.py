import pandas as pd
from plotnine import aes, element_blank, geom_line, geom_point, ggplot, labs, theme

from ..config_theme import (
    TUFTE_DARK,
    TUFTE_LINE_WIDTH,
    TUFTE_POINT_SIZE_MEDIUM,
    tufte_theme,
)


def time_series(
    df: pd.DataFrame, x_col: str, y_col: str, title: str = "Time Series", **kwargs
) -> ggplot:
    """
    Erstellt einen minimalistischen Linienplot mit Punkten (Tufte-Stil).
    Ideal für Zeitreihen mit wenigen Datenpunkten.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame mit den Daten für den Plot.
    x_col : str
        Name der Spalte für die X-Achse (z.B. Jahre).
    y_col : str
        Name der Spalte für die Y-Achse (numerisch).
    title : str (Standardwert="Time Series")
        Titel des Plots.
    **kwargs :
        Zusätzliche Argumente für geom_point (z.B. color, alpha).

    Returns
    -------
    plot : plotnine.ggplot
        Ein ggplot-Objekt mit dem Linienplot.

    """
    # Kopie des DataFrames erstellen, um Originaldaten nicht zu verändern
    df_copy = df.copy()

    color = kwargs.get("color", TUFTE_DARK)
    additional_kwargs = {k: v for k, v in kwargs.items() if k != "color"}

    plot = (
        ggplot(df_copy, aes(x=x_col, y=y_col))
        # Linie
        + geom_line(size=TUFTE_LINE_WIDTH, color=TUFTE_DARK)
        # Punkte
        + geom_point(size=TUFTE_POINT_SIZE_MEDIUM, color=color, **additional_kwargs)
        # Beschriftung
        + labs(title=title, x=None, y=None)
        # Tufte-Theme
        + tufte_theme()
        + theme(axis_line=element_blank(), legend_position="none")
    )

    return plot
