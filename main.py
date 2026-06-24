import sys
import os
import tkinter as tk

# Versuche die KI-Edition (Light Mode, 34 Staedte, A*, Animationen, CO2-Bilanz) zu laden
try:
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    from Ki.app import RouteFinderApp
    print("KI-Edition erfolgreich geladen!")
except Exception as e:
    # Falls das Laden fehlschlaegt (z.B. Ki/ Ordner fehlt oder Fehler beim Import), verwende die Fallback-Edition
    print(f"KI-Edition konnte nicht geladen werden: {e}. Verwende Fallback-Edition.")
    from fallback import RouteFinderApp

if __name__ == "__main__":
    root = tk.Tk()
    app = RouteFinderApp(root)
    root.mainloop()
