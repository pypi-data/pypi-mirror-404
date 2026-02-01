import pandas as pd
from plotnine import aes, element_blank, geom_line, geom_text, ggplot, labs, theme

from ..config_theme import (
    TUFTE_FONT,
    TUFTE_GREY,
    TUFTE_LINE_WIDTH,
    TUFTE_RED,
    tufte_theme,
)


def layered_focus(
    df: pd.DataFrame,
    time_col: str,
    value_col: str,
    category_col: str,
    focus_category: str,
    title: str = "Layering & Separation (Context vs. Focus)",
    **kwargs,
) -> ggplot:
    """
    Erstellt einen Layering-Plot mit Fokus auf einer Kategorie.
    Alle anderen Kategorien werden als grauer Kontext im Hintergrund angezeigt,
    während die Fokus-Kategorie rot hervorgehoben wird.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame mit den Daten für den Plot.
        Muss die Spalten für Zeit, Wert und Kategorie enthalten.
    time_col : str
        Name der Spalte für die Zeitpunkte (x-Achse).
    value_col : str
        Name der Spalte für die Werte (y-Achse).
    category_col : str
        Name der Spalte für die Kategorien (Gruppierung).
    focus_category : str
        Name der Kategorie, welche hervorgehoben werden soll.
    title : str (Standardwert="Layering & Separation (Context vs. Focus)")
        Titel des Plots.

    Returns
    -------
    plot : plotnine.ggplot
        Ein ggplot-Objekt mit dem Layering-Plot.

    """
    # Kopie des DataFrames erstellen, um Originaldaten nicht zu verändern
    df_copy = df.copy()

    # Daten in Kontext (grau) und Fokus (rot) aufteilen
    df_context = df_copy[df_copy[category_col] != focus_category].copy()
    df_focus = df_copy[df_copy[category_col] == focus_category].copy()

    # Endpunkt für das Label ermitteln
    end_time = df_focus[time_col].max()
    end_point = df_focus[df_focus[time_col] == end_time].copy()
    end_point["label_text"] = focus_category

    # Fokus Farbe
    focus_color = kwargs.get("color", TUFTE_RED)
    additional_kwargs = {k: v for k, v in kwargs.items() if k != "color"}

    plot = (
        ggplot(df_copy, aes(x=time_col, y=value_col))
        # Kontext-Linien (grau, im Hintergrund)
        + geom_line(
            aes(group=category_col),
            data=df_context,
            color=TUFTE_GREY,
            alpha=0.5,
            size=TUFTE_LINE_WIDTH,
        )
        # Fokus-Linie (rot, hervorgehoben)
        + geom_line(data=df_focus, color=focus_color, size=1.2, **additional_kwargs)
        # Label für Fokus-Kategorie
        + geom_text(
            aes(label="label_text"),
            data=end_point,
            ha="left",
            nudge_x=0.5,
            size=10,
            color=focus_color,
            family=TUFTE_FONT,
        )
        # Beschriftung
        + labs(title=title, x=time_col, y=value_col)
        # Tufte-Theme
        + tufte_theme()
        + theme(axis_line=element_blank())
    )

    return plot
