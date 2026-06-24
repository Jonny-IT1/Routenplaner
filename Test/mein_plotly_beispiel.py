import io
import pandas as pd
import plotly.express as px


def karte_erstellen():
    # Garantiert fehlerfreie, lokale CSV-Daten mit echten Salzburg-Koordinaten
    csv_daten = """Infrastruktur,Breitengrad,Längengrad,Kategorie,Auslastung
HTL Salzburg,47.8223,13.0412,Schule,Hoch
Salzburg Hauptbahnhof,47.8128,13.0456,Verkehrsknoten,Sehr Hoch
Mirabellplatz,47.8056,13.0418,Bushaltestelle,Hoch
Residenzplatz,47.7981,13.0461,Tourismus,Mittel
Volksgarten Parkplatz,47.7994,13.0592,Parkplatz,Niedrig
Mülln-Altstadt Station,47.8075,13.0335,S-Bahn-Station,Mittel
Airport Salzburg,47.7933,13.0042,Flughafen,Hoch
"""

    try:
        # CSV-String direkt als DataFrame einlesen (kein Internet/HTTP-Request nötig)
        data = pd.read_csv(io.StringIO(csv_daten))

        # Karte zeichnen mit der aktuellen scatter_map (ersetzt scatter_mapbox)
        fig = px.scatter_map(
            data,
            lat="Breitengrad",
            lon="Längengrad",
            hover_name="Infrastruktur",
            hover_data=["Kategorie", "Auslastung"],
            color="Auslastung",
            color_discrete_map={
                "Sehr Hoch": "red",
                "Hoch": "orange",
                "Mittel": "yellow",
                "Niedrig": "green",
            },
            zoom=12,
            height=750,
        )

        # Open-Street-Map Layout ohne Token setzen
        fig.update_layout(map_style="open-street-map")
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

        fig.show()

    except Exception as e:
        print(f"Fehler bei der Kartenerstellung: {e}")


karte_erstellen()