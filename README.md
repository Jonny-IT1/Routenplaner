# Routenplaner & Wegfindung 

Ein interaktives Wegfindungs- und Routenplanungssystem für Österreich in Python unter Verwendung von **Tkinter** für die Benutzeroberfläche und **Dijkstra** für die Pfadberechnung. 

## Funktionen

* **DIe Karte von Österreich**: Enthält wichtige Städte (Wien, Linz, Salzburg, Graz, Innsbruck, Klagenfurt, Bregenz, etc.).
* **Flexible Interaktion**:
  * **Knoten-Interaktion**: Linksklick setzt den Startpunkt, Rechtsklick/Doppelklick setzt das Ziel.
  * **Pannable $_{Verschiebar}$ & Zoomable**: Ziehen mit der linken Maustaste verschiebt den Bildausschnitt, Scrollen mit dem Mausrad zoomt hinein/hinaus.
  * **Straßen-Editor**: Durch Anklicken einer Straße können deren Parameter (Stau, Mautpflicht/Vignette, Staurisiko) live geändert und die Route dynamisch neu berechnet werden.
* **Erweiterte Routing-Gewichtungen**:
  * **Schnellste Route**: Minimiert die Fahrtzeit (beeinflusst durch Tempolimits und Staus).
  * **Kürzeste Route**: Minimiert die reine Distanz.
  * **Kraftstoffsparend**: Minimiert den Treibstoffverbrauch (berechnet aus Distanz, Steigung und Straßenart).
  * **Umweltschonend**: Minimiert Emissionen und maximiert den Eco-Score.
  * **Flachste Route**: Minimiert die zu überwindenden Höhenmeter.
* **Maut & Stau meiden**: Optionale Schalter zur vollständigen oder teilweisen Vermeidung von Vignettenstraßen und Staugebieten.
* **Sichere Benutzeranmeldung**:
  * Login- und Registrierungsmaske vor dem Programmstart.
  * Passwörter werden mit SHA-256 gehasht.
  * Benutzerdaten werden in `.venv/user_credentials.json` abgelegt und durch `.gitignore` vor dem Hochladen geschützt.
  * Ein Reset-Button auf dem Login-Bildschirm erlaubt das Leeren des `data/`-Verzeichnisses.
* **Datenexport**: Berechnete Routen werden als strukturierte JSON (`data/weg.json`) und als formatiertes Textprotokoll (`data/weg.txt`) exportiert.
## KI-Optimierte Version (Ordner `Ki/`)

Dieses Projekt verfügt über eine fortschrittliche, KI-optimierte Version des Routenplaners:
* Die Source-Module befinden sich im Unterverzeichnis [Ki/](file:///c:/Users/hi20-/Documents/Bla/VSC/Schule/SEW/3_Schuljahr/Abschluss/Ki/).
* Die `main.py` im Hauptordner lädt und startet automatisch diese KI-optimierten Module.
* Eine detaillierte Aufstellung der Unterschiede (A*-Algorithmus, 34 Städte, Light-Mode-Ausschnitt, Animationen und Klimaschutz-Bilanzen) ist in der [Ki/README.md](file:///c:/Users/hi20-/Documents/Bla/VSC/Schule/SEW/3_Schuljahr/Abschluss/Ki/README.md) dokumentiert.

## Installation & Ausführung

Stellen Sie sicher, dass `uv` auf Ihrem System installiert ist. Führen Sie im Hauptverzeichnis des Projekts aus:

```bash
# Projekt und Abhängigkeiten starten
uv run python main.py
```

---

## Haftungsausschluss (Disclaimer)

**ACHTUNG: DIES IST EIN SCHULPROJEKT!**
Die in diesem Programm bereitgestellten Navigationsdaten, Distanzen, Fahrzeiten, Höhenprofile, Kraftstoffangaben und Mautinformationen sind rein fiktiv oder stark vereinfacht, können stark abweichen und dienen ausschließlich Demonstrations- und Bildungszwecken im Rahmen des Unterrichts. 

Dieses Programm darf **unter keinen Umständen** für echte Fahrzeugnavigation, Verkehrsplanung, Reiseplanung oder Sicherheitsbewertungen herangezogen werden. Der Autor übernimmt keinerlei Haftung für Schäden, Verspätungen, Unfälle, Bußgelder (z.B. wegen fehlender Vignette) oder sonstige Nachteile, die durch die Nutzung oder Fehlfunktion dieser Software entstehen.

---

## Lizenz (License)

Dieses Projekt ist unter den Bedingungen der **MIT-Lizenz** lizenziert.

Copyright (c) 2026 Jonas Hofer

---

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

**THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.**
