# KI-Optimierte Wegfindung (Source-Module)

Dieser Ordner enthält die KI-generierten Source-Module für den erweiterten Routenplaner. Im Gegensatz zum manuell geschriebenen Basis-Routenplaner wurde dieser Bereich des Projektes mithilfe von künstlicher Intelligenz (KI) entworfen und optimiert.

## Besondere Features der KI-Module:

1. **A*-Suchalgorithmus**:
   Nutzt den A*-Algorithmus für eine signifikant effizientere Routenberechnung als der Standard-Dijkstra. Die Heuristik schätzt die Restdistanz mithilfe der **Haversine-Formel** (exakte Großkreis-Distanz auf einer Kugel) basierend auf echten Längen- und Breitengraden.
   
2. **Detaillierte Österreich-Karte (34 Städte)**:
   Enthält ein erweitertes Straßennetz mit 34 österreichischen Städten, inklusive präziser Höhenprofile zur Berechnung der flachsten Route. Die geografische Projektion auf den Bildschirm ist pixelgenau.

3. **Premium Light Mode UI**:
   Ein modernes, helles Oberflächendesign mit harmonischer Farbpalette, sauberer visueller Strukturierung und interaktiven Hover-Effekten auf allen Bedienelementen.

4. **Klimaschutz-Fokus**:
   - Automatische Anzeige von CO2-Einsparungen (in % und kg) im Vergleich zur schnellsten Route im Sidebar-Klimaschutz-Panel.
   - Visuelle Kennzeichnung klimafreundlicher Streckenabschnitte (< 120 g/km) durch einen weichen grünen Schein auf der Karte.

5. **Weg-Animationen**:
   Animierte Pfadzeichnung Segment für Segment, bei der ein weißer Lichtpuls den Streckenverlauf live abfährt.
