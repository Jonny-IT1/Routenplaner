import heapq
import os
import json
import hashlib
import shutil
import math
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

# Fallback dataset: Original 14 cities with layout coordinates
CITIES = {
    "Bregenz": (80, 300), "Innsbruck": (200, 320), "Lienz": (300, 420),
    "Salzburg": (400, 200), "Liezen": (520, 260), "Villach": (500, 420),
    "Klagenfurt": (580, 420), "Wels": (530, 160), "Linz": (590, 140),
    "St. Pölten": (730, 160), "Wien": (840, 160), "Eisenstadt": (880, 220),
    "Graz": (700, 330), "Bruck an der Mur": (690, 250)
}

class Edge:
    def __init__(self, a, b, dist, speed, vig=False, jam=False, risk=0.0, elev=0.0, fuel=0.0, eco=5.0):
        self.node_a, self.node_b, self.distance, self.speed_limit, self.has_vignette, self.traffic_jam, self.traffic_risk, self.elevation_diff, self.fuel_consumption, self.eco_score = a, b, dist, speed, vig, jam, risk, elev, fuel, eco

EDGES = [
    Edge("Bregenz", "Innsbruck", 130, 100, vig=True, elev=1200, fuel=12.5, eco=4),
    Edge("Innsbruck", "Lienz", 180, 80, elev=1500, fuel=16.0, eco=5),
    Edge("Innsbruck", "Salzburg", 185, 130, vig=True, elev=400, fuel=15.5, eco=6),
    Edge("Lienz", "Villach", 110, 80, elev=300, fuel=8.5, eco=7),
    Edge("Salzburg", "Wels", 100, 130, vig=True, elev=200, fuel=8.2, eco=6),
    Edge("Salzburg", "Liezen", 120, 100, vig=True, elev=800, fuel=11.2, eco=5),
    Edge("Wels", "Linz", 30, 130, vig=True, elev=50, fuel=2.5, eco=7),
    Edge("Wels", "Liezen", 80, 100, vig=True, elev=600, fuel=7.8, eco=5),
    Edge("Liezen", "Graz", 130, 100, vig=True, elev=500, fuel=11.5, eco=5),
    Edge("Liezen", "Bruck an der Mur", 90, 100, elev=400, fuel=8.0, eco=6),
    Edge("Liezen", "Villach", 130, 100, vig=True, elev=700, fuel=12.0, eco=5),
    Edge("Villach", "Klagenfurt", 40, 130, vig=True, elev=100, fuel=3.2, eco=8),
    Edge("Klagenfurt", "Graz", 140, 130, vig=True, elev=800, fuel=13.0, eco=5),
    Edge("Graz", "Bruck an der Mur", 55, 130, vig=True, elev=150, fuel=4.8, eco=7),
    Edge("Bruck an der Mur", "St. Pölten", 110, 80, elev=700, fuel=9.8, eco=6),
    Edge("Linz", "St. Pölten", 125, 130, vig=True, risk=0.3, elev=150, fuel=10.2, eco=6),
    Edge("St. Pölten", "Wien", 65, 130, vig=True, jam=True, elev=100, fuel=5.3, eco=6),
    Edge("Wien", "Eisenstadt", 60, 130, vig=True, elev=80, fuel=4.8, eco=8),
    Edge("Wien", "Graz", 200, 130, vig=True, risk=0.15, elev=700, fuel=16.8, eco=5),
    Edge("Eisenstadt", "Graz", 170, 100, elev=500, fuel=13.5, eco=6),
]

def hash_password(password, salt):
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()

def get_credentials_path():
    os.makedirs(".venv", exist_ok=True)
    return os.path.join(".venv", "user_credentials.json")

def reset_data_directory():
    if os.path.exists("data"):
        for f in os.listdir("data"):
            path = os.path.join("data", f)
            shutil.rmtree(path) if os.path.isdir(path) else os.unlink(path)
        messagebox.showinfo("Erfolg", "Alle Dateien im Ordner 'data/' wurden gelöscht!")
    else:
        messagebox.showinfo("Info", "Der Ordner 'data/' existiert nicht oder ist leer.")

def calculate_cost(e, mode, avoid_vig, avoid_traf):
    costs = {
        "Shortest": e.distance,
        "Fastest": (e.distance / e.speed_limit) * (1.0 + (2.0 if e.traffic_jam else 0) + (e.traffic_risk * 1.5 if avoid_traf else 0)),
        "Fuel": e.fuel_consumption,
        "Eco": (11 - e.eco_score) * e.distance,
        "Flat": e.elevation_diff
    }
    cost = costs.get(mode, e.distance)
    if avoid_vig and e.has_vignette:
        cost += {"Shortest": 500.0, "Fastest": 5.0, "Fuel": 50.0, "Eco": 5000.0, "Flat": 2000.0}.get(mode, 500.0)
    if avoid_traf and mode != "Fastest":
        cost += (150.0 if e.traffic_jam else 0) + e.traffic_risk * 75.0
    return cost

def dijkstra(start_name, end_name, mode="Fastest", avoid_vignette=False, avoid_traffic=False, additional_focus="None"):
    adj = {name: [] for name in CITIES}
    for e in EDGES:
        cost = calculate_cost(e, mode, avoid_vignette, avoid_traffic)
        adj[e.node_a].append((e.node_b, cost, e))
        adj[e.node_b].append((e.node_a, cost, e))
        
    queue, visited = [(0.0, start_name, [], [])], set()
    while queue:
        cost, curr, path_n, path_e = heapq.heappop(queue)
        if curr == end_name: return cost, path_n + [curr], path_e
        if curr in visited: continue
        visited.add(curr)
        for neighbor, edge_cost, edge in adj[curr]:
            if neighbor not in visited:
                heapq.heappush(queue, (cost + edge_cost, neighbor, path_n + [curr], path_e + [edge]))
    return None, None, None

def save_route_to_files(start, dest, mode, avoid_vignette, avoid_traffic, path_nodes, path_edges):
    os.makedirs("data", exist_ok=True)
    if not path_nodes:
        data = {"start": start, "destination": dest, "mode": mode, "avoid_vignette": avoid_vignette, "avoid_traffic": avoid_traffic, "path_found": False}
        with open("data/weg.json", "w", encoding="utf-8") as f: json.dump(data, f, indent=4, ensure_ascii=False)
        with open("data/weg.txt", "w", encoding="utf-8") as f: f.write(f"Start: {start}\nZiel: {dest}\nKein Weg gefunden!\n")
        return

    dist = sum(e.distance for e in path_edges)
    fuel = sum(e.fuel_consumption for e in path_edges)
    elev = sum(e.elevation_diff for e in path_edges)
    eco = sum(e.eco_score for e in path_edges) / len(path_edges)
    
    time_h = sum((e.distance / e.speed_limit) * (3.0 if e.traffic_jam else 1.0) for e in path_edges)
    hours, mins = int(time_h), int(round((time_h - int(time_h)) * 60))
    if mins == 60: hours, mins = hours + 1, 0
    time_str = f"{hours} Std. {mins} Min." if hours > 0 else f"{mins} Min."
    
    vigs = sum(1 for e in path_edges if e.has_vignette)
    jams = sum(1 for e in path_edges if e.traffic_jam)
    mode_names = {"Fastest": "Schnellste Route", "Shortest": "Kürzeste Route", "Fuel": "Kraftstoffsparend", "Eco": "Umweltschonend", "Flat": "Flachste Route"}
    
    # Save JSON
    json_data = {
        "start": start, "destination": dest, "mode": mode, "mode_name": mode_names.get(mode, mode),
        "avoid_vignette": avoid_vignette, "avoid_traffic": avoid_traffic, "path_found": True,
        "total_distance_km": dist, "actual_time_hours": time_h, "actual_time_formatted": time_str,
        "total_fuel_liters": round(fuel, 1), "total_elevation_gain_m": elev, "average_eco_score": round(eco, 1),
        "vignette_needed": vigs > 0, "vignette_roads_count": vigs, "traffic_jams_encountered": jams,
        "route": path_nodes,
        "legs": [
            {
                "from": path_nodes[i], "to": path_nodes[i+1], "distance_km": e.distance,
                "speed_limit_kmh": e.speed_limit, "vignette": e.has_vignette, "traffic_jam": e.traffic_jam,
                "traffic_risk": e.traffic_risk, "elevation_diff_m": e.elevation_diff,
                "fuel_consumption_l": e.fuel_consumption, "eco_score": e.eco_score
            }
            for i, e in enumerate(path_edges)
        ]
    }
    with open("data/weg.json", "w", encoding="utf-8") as f: json.dump(json_data, f, indent=4, ensure_ascii=False)
        
    # Save TXT
    with open("data/weg.txt", "w", encoding="utf-8") as f:
        f.write(f"==================================================\n"
                f"               ROUTENBERECHNUNG                   \n"
                f"==================================================\n"
                f"Startpunkt:         {start}\nZielpunkt:          {dest}\n"
                f"Optimierung:        {mode_names.get(mode, mode)}\n"
                f"Vignette meiden:    {'Ja' if avoid_vignette else 'Nein'}\n"
                f"Stau meiden:        {'Ja' if avoid_traffic else 'Nein'}\n"
                f"--------------------------------------------------\n"
                f"Wegstrecke:         {' -> '.join(path_nodes)}\n"
                f"Gesamtdistanz:      {dist:.1f} km\nReisezeit:          {time_str}\n"
                f"Kraftstoffbedarf:   {fuel:.1f} Liter\nHöhenmeter gesamt:  {elev} Meter\n"
                f"Durchschn. Eco:     {eco:.1f}/10\nMaut/Vignette:      {'Ja' if vigs > 0 else 'Nein'} ({vigs} Abschnitte)\n"
                f"Staus auf Route:    {jams}\n"
                f"--------------------------------------------------\n"
                f"Wegbeschreibung:\n")
        for i, e in enumerate(path_edges):
            t_leg = (e.distance / e.speed_limit) * (3.0 if e.traffic_jam else 1.0)
            f.write(f"  * {path_nodes[i]} -> {path_nodes[i+1]}: {e.distance} km, ca. {int(round(t_leg*60))} Min. ({e.speed_limit} km/h), +{e.elevation_diff}m, {e.fuel_consumption}L, Eco: {e.eco_score}/10"
                    f"{' [Vignette]' if e.has_vignette else ''}{' [STAU!]' if e.traffic_jam else ''}\n")
        f.write("==================================================\n")

class RouteFinderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Antigravity Route Finder")
        self.root.geometry("1200x820")
        self.root.minsize(1050, 700)
        self.root.configure(bg="#1E1E24")
        
        # Color Theme Constants
        self.bg_dark, self.bg_sidebar, self.bg_card, self.fg_white, self.fg_muted = "#1E1E24", "#2B2D42", "#3F4257", "#EDF2F4", "#8D99AE"
        self.color_start, self.color_dest, self.color_path, self.color_vignette, self.color_traffic = "#3A86C8", "#EF233C", "#06D6A0", "#FF9F1C", "#D90429"
        
        # Initial State
        self.start_city, self.dest_city, self.selected_edge = "Wien", "Bregenz", None
        self.path_nodes, self.path_edges = [], []
        self.zoom_factor = 1.0
        
        # First show login screen
        self.show_login_screen()

    def show_login_screen(self):
        self.login_frame = tk.Frame(self.root, bg=self.bg_dark)
        self.login_frame.pack(expand=True, fill="both")
        
        tk.Label(self.login_frame, text="Benutzeranmeldung", bg=self.bg_dark, fg=self.color_path, font=("Segoe UI", 18, "bold")).pack(pady=20)
        
        form = tk.Frame(self.login_frame, bg=self.bg_sidebar, bd=0, padx=20, pady=20)
        form.pack(padx=20, fill="x", maxsize=(400, 200))
        
        def add_input(lbl_text, row, show=None):
            tk.Label(form, text=lbl_text, bg=self.bg_sidebar, fg=self.fg_white, font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", pady=5)
            ent = tk.Entry(form, show=show, bg=self.bg_card, fg=self.fg_white, insertbackground=self.fg_white, bd=0, font=("Segoe UI", 10))
            ent.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
            return ent
            
        self.ent_user = add_input("Benutzername:", 0)
        self.ent_pwd = add_input("Passwort:", 1, show="*")
        form.columnconfigure(1, weight=1)
        
        btn_frame = tk.Frame(self.login_frame, bg=self.bg_dark)
        btn_frame.pack(pady=15, fill="x", padx=20)
        tk.Button(btn_frame, text="Anmelden", command=self.handle_login, bg=self.color_path, fg=self.bg_dark, font=("Segoe UI", 10, "bold"), bd=0, height=1).pack(side="left", padx=5, expand=True, fill="x")
        tk.Button(btn_frame, text="Registrieren", command=self.handle_register, bg="#4A4E69", fg=self.fg_white, font=("Segoe UI", 10, "bold"), bd=0, height=1).pack(side="right", padx=5, expand=True, fill="x")
        
        tk.Frame(self.login_frame, height=1, bg=self.bg_card).pack(fill="x", padx=20, pady=10)
        tk.Button(self.login_frame, text="Daten zurücksetzen (data/ Ordner leeren)", command=reset_data_directory, bg=self.color_dest, fg=self.fg_white, font=("Segoe UI", 9, "bold"), bd=0, height=1).pack(fill="x", padx=25, pady=5)

    def handle_login(self):
        user, pwd = self.ent_user.get().strip(), self.ent_pwd.get()
        if not user or not pwd: return messagebox.showerror("Fehler", "Bitte füllen Sie alle Felder aus!")
        cred_path = get_credentials_path()
        if not os.path.exists(cred_path): return messagebox.showerror("Fehler", "Keine Benutzer registriert! Bitte zuerst registrieren.")
        
        with open(cred_path, "r", encoding="utf-8") as f: credentials = json.load(f)
        if credentials.get(user) == hash_password(pwd, user):
            self.login_frame.destroy()
            self.create_main_layout()
            self.calculate_route()
            self.center_map()
        else:
            messagebox.showerror("Fehler", "Falsches Passwort oder Benutzername!")

    def handle_register(self):
        user, pwd = self.ent_user.get().strip(), self.ent_pwd.get()
        if not user or not pwd: return messagebox.showerror("Fehler", "Bitte füllen Sie alle Felder aus!")
        if len(user) < 3 or len(pwd) < 4: return messagebox.showerror("Fehler", "Username min. 3, Passwort min. 4 Zeichen!")
        cred_path = get_credentials_path()
        credentials = {}
        if os.path.exists(cred_path):
            with open(cred_path, "r", encoding="utf-8") as f: credentials = json.load(f)
        if user in credentials: return messagebox.showerror("Fehler", "Benutzername bereits vergeben!")
        
        credentials[user] = hash_password(pwd, user)
        with open(cred_path, "w", encoding="utf-8") as f: json.dump(credentials, f, indent=4)
        messagebox.showinfo("Erfolg", "Registrierung erfolgreich!")

    def create_main_layout(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Map Left
        map_frame = tk.Frame(self.root, bg=self.bg_dark, padx=5, pady=5)
        map_frame.grid(row=0, column=0, sticky="nsew")
        map_frame.rowconfigure(0, weight=1)
        map_frame.columnconfigure(0, weight=1)
        
        self.canvas = tk.Canvas(map_frame, bg=self.bg_dark, highlightthickness=1, highlightbackground=self.bg_card)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        hbar = tk.Scrollbar(map_frame, orient="horizontal", command=self.canvas.xview)
        hbar.grid(row=1, column=0, sticky="ew")
        vbar = tk.Scrollbar(map_frame, orient="vertical", command=self.canvas.yview)
        vbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<MouseWheel>", self.on_canvas_zoom)
        self.canvas.bind("<Button-4>", self.on_canvas_zoom)
        self.canvas.bind("<Button-5>", self.on_canvas_zoom)
        
        # Sidebar Right
        sidebar = tk.Frame(self.root, bg=self.bg_sidebar, padx=15, pady=15, width=370)
        sidebar.grid(row=0, column=1, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.columnconfigure(0, weight=1)
        
        tk.Label(sidebar, text="Österreich Routenplaner", bg=self.bg_sidebar, fg=self.fg_white, font=("Segoe UI", 14, "bold")).grid(row=0, column=0, pady=(0, 10), sticky="w")
        
        # Comboboxes Start/Dest Card
        sel_card = tk.Frame(sidebar, bg=self.bg_card, padx=10, pady=10)
        sel_card.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        sel_card.columnconfigure(1, weight=1)
        tk.Label(sel_card, text="Start & Ziel", bg=self.bg_card, fg=self.color_path, font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 8), sticky="w")
        
        tk.Label(sel_card, text="Start:", bg=self.bg_card, fg=self.fg_white).grid(row=1, column=0, sticky="w", pady=5)
        self.start_combo = ttk.Combobox(sel_card, values=list(CITIES.keys()), state="readonly")
        self.start_combo.set(self.start_city)
        self.start_combo.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=5)
        self.start_combo.bind("<<ComboboxSelected>>", self.on_combo_change)
        
        tk.Label(sel_card, text="Ziel:", bg=self.bg_card, fg=self.fg_white).grid(row=2, column=0, sticky="w", pady=5)
        self.dest_combo = ttk.Combobox(sel_card, values=list(CITIES.keys()), state="readonly")
        self.dest_combo.set(self.dest_city)
        self.dest_combo.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=5)
        self.dest_combo.bind("<<ComboboxSelected>>", self.on_combo_change)
        
        # Options Card
        opt_card = tk.Frame(sidebar, bg=self.bg_card, padx=10, pady=10)
        opt_card.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        tk.Label(opt_card, text="Optimierungs-Kriterien", bg=self.bg_card, fg=self.color_path, font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 6), sticky="w")
        
        self.routing_mode = tk.StringVar(value="Fastest")
        modes = [
            ("Schnellste Route (Reisezeit)", "Fastest"),
            ("Kürzeste Route (Strecke)", "Shortest"),
            ("Kraftstoffsparend (Verbrauch)", "Fuel"),
            ("Umweltschonend (Eco-Score)", "Eco"),
            ("Flachste Route (Höhenprofil)", "Flat")
        ]
        for i, (text, val) in enumerate(modes):
            tk.Radiobutton(opt_card, text=text, variable=self.routing_mode, value=val, command=self.calculate_route, bg=self.bg_card, fg=self.fg_white, selectcolor=self.bg_sidebar, activebackground=self.bg_card, activeforeground=self.fg_white).grid(row=i+1, column=0, columnspan=2, sticky="w", pady=2)
            
        tk.Frame(opt_card, height=1, bg=self.bg_sidebar).grid(row=6, column=0, columnspan=2, sticky="ew", pady=6)
        
        self.avoid_vignette_var = tk.BooleanVar(value=False)
        tk.Checkbutton(opt_card, text="Vignette vermeiden", variable=self.avoid_vignette_var, command=self.calculate_route, bg=self.bg_card, fg=self.fg_white, selectcolor=self.bg_sidebar, activebackground=self.bg_card, activeforeground=self.fg_white).grid(row=7, column=0, columnspan=2, sticky="w", pady=2)
        
        self.avoid_traffic_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_card, text="Stau / Verkehrsrisiko meiden", variable=self.avoid_traffic_var, command=self.calculate_route, bg=self.bg_card, fg=self.fg_white, selectcolor=self.bg_sidebar, activebackground=self.bg_card, activeforeground=self.fg_white).grid(row=8, column=0, columnspan=2, sticky="w", pady=2)
        
        # Stats Card
        self.stats_card = tk.Frame(sidebar, bg=self.bg_card, padx=10, pady=10)
        self.stats_card.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        self.stats_card.columnconfigure(1, weight=1)
        tk.Label(self.stats_card, text="Routen-Statistik", bg=self.bg_card, fg=self.color_path, font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 6), sticky="w")
        
        self.stats_labels = {}
        stat_configs = [
            ("Distanz:", "dist"), ("Reisezeit:", "time"), ("Treibstoffbedarf:", "fuel"),
            ("Höhenmeter gesamt:", "elev"), ("Durchschn. Eco-Wert:", "eco"), ("Mautpflichtig:", "toll")
        ]
        for i, (label_text, key) in enumerate(stat_configs):
            tk.Label(self.stats_card, text=label_text, bg=self.bg_card, fg=self.fg_white).grid(row=i+1, column=0, sticky="w", pady=1)
            lbl = tk.Label(self.stats_card, text="-", bg=self.bg_card, fg=self.fg_white, font=("Segoe UI", 10, "bold"))
            lbl.grid(row=i+1, column=1, sticky="e", pady=1)
            self.stats_labels[key] = lbl
            
        # Editor Card
        self.editor_card = tk.Frame(sidebar, bg=self.bg_card, padx=10, pady=10)
        self.editor_card.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        self.editor_card.columnconfigure(0, weight=1)
        self.editor_card.grid_remove()
        
        # Controls Frame (Bottom)
        btn_frame = tk.Frame(sidebar, bg=self.bg_sidebar)
        btn_frame.grid(row=5, column=0, sticky="ew", pady=(5, 5))
        btn_frame.columnconfigure((0,1), weight=1)
        tk.Button(btn_frame, text="Karte zentrieren", command=self.center_map, bg="#4A4E69", fg=self.fg_white, font=("Segoe UI", 9, "bold"), bd=0, height=1).grid(row=0, column=0, padx=2, sticky="ew")
        tk.Button(btn_frame, text="Verkehr zurücksetzen", command=self.reset_all_roads, bg="#4A4E69", fg=self.fg_white, font=("Segoe UI", 9, "bold"), bd=0, height=1).grid(row=0, column=1, padx=2, sticky="ew")

    def draw_graph(self):
        self.canvas.delete("all")
        self.edge_by_line_id, self.node_by_oval_id = {}, {}
        
        for x in range(0, 1500, 80): self.canvas.create_line(x, 0, x, 1000, fill="#252530", width=1, tags="grid")
        for y in range(0, 1000, 80): self.canvas.create_line(0, y, 1500, y, fill="#252530", width=1, tags="grid")
            
        route_edges_set = set(self.path_edges)
        for e in EDGES:
            pt_a, pt_b = CITIES[e.node_a], CITIES[e.node_b]
            is_on_route = e in route_edges_set
            
            if e.traffic_jam: color, width = self.color_traffic, 5
            elif e == self.selected_edge: color, width = "#FFFFFF", 5
            elif is_on_route: color, width = self.color_path, 6
            elif e.has_vignette: color, width = self.color_vignette, 3
            else: color, width = "#8D99AE", 3
                
            line_id = self.canvas.create_line(pt_a[0], pt_a[1], pt_b[0], pt_b[1], fill=color, width=width, tags="edge")
            self.edge_by_line_id[line_id] = e
            
            if e.has_vignette and not is_on_route and not e.traffic_jam and e != self.selected_edge:
                self.canvas.create_line(pt_a[0], pt_a[1], pt_b[0], pt_b[1], fill="#FFFFFF", width=1, dash=(3, 5), tags="edge_overlay")
            if e.traffic_risk > 0.0 and not e.traffic_jam:
                mx, my = (pt_a[0] + pt_b[0]) / 2, (pt_a[1] + pt_b[1]) / 2
                self.canvas.create_oval(mx-4, my-4, mx+4, my+4, fill="#E6C229", outline="", tags="risk_dot")
                
            mx, my = (pt_a[0] + pt_b[0]) / 2, (pt_a[1] + pt_b[1]) / 2
            self.canvas.create_text(mx, my - 8, text=f"{e.distance}km/{e.elevation_diff}m", fill=self.fg_muted, font=("Segoe UI", 7), tags="text")

        for name, pt in CITIES.items():
            if name == self.start_city: fill_color, radius = self.color_start, 12
            elif name == self.dest_city: fill_color, radius = self.color_dest, 12
            elif name in self.path_nodes: fill_color, radius = self.color_path, 9
            else: fill_color, radius = "#3A3E5B", 8
                
            oval_id = self.canvas.create_oval(pt[0] - radius, pt[1] - radius, pt[0] + radius, pt[1] + radius, fill=fill_color, outline=self.fg_white, width=2, tags="node")
            self.node_by_oval_id[oval_id] = name
            self.canvas.create_text(pt[0], pt[1] - radius - 8, text=name, fill=self.fg_white, font=("Segoe UI", 10, "bold"), tags="text")

        self.canvas.tag_bind("node", "<Button-1>", lambda ev: self.on_node_click(ev, left=True))
        self.canvas.tag_bind("node", "<Button-3>", lambda ev: self.on_node_click(ev, left=False))
        self.canvas.tag_bind("node", "<Double-Button-1>", lambda ev: self.on_node_click(ev, left=False))
        self.canvas.tag_bind("edge", "<Button-1>", self.on_edge_click)
        self.apply_zoom()

    def on_combo_change(self, event):
        self.start_city = self.start_combo.get()
        self.dest_city = self.dest_combo.get()
        self.calculate_route()

    def on_node_click(self, event, left):
        item = self.canvas.find_withtag("current")[0]
        name = self.node_by_oval_id.get(item)
        if not name: return
        if left:
            if name == self.dest_city: return messagebox.showwarning("Fehler", "Start und Ziel können nicht gleich sein!")
            self.start_city = name
            if hasattr(self, "start_combo"): self.start_combo.set(name)
        else:
            if name == self.start_city: return messagebox.showwarning("Fehler", "Start und Ziel können nicht gleich sein!")
            self.dest_city = name
            if hasattr(self, "dest_combo"): self.dest_combo.set(name)
        self.calculate_route()

    def on_edge_click(self, event):
        item = self.canvas.find_withtag("current")[0]
        edge = self.edge_by_line_id.get(item)
        if edge:
            self.selected_edge = edge
            self.draw_graph()
            self.show_edge_editor(edge)

    def show_edge_editor(self, edge):
        for child in self.editor_card.winfo_children(): child.destroy()
        self.editor_card.grid()
        
        tk.Label(self.editor_card, text=f"Straße: {edge.node_a} ↔ {edge.node_b}", bg=self.bg_card, fg=self.color_path, font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 6), sticky="w")
        tk.Label(self.editor_card, text=f"Distanz: {edge.distance} km | Speed: {edge.speed_limit} km/h\nVerbrauch: {edge.fuel_consumption} L | Höhenstufe: {edge.elevation_diff} m\nEco-Wert: {edge.eco_score}/10", bg=self.bg_card, fg=self.fg_white, justify="left").grid(row=1, column=0, columnspan=2, sticky="w", pady=2)
        
        self.edit_vignette_var = tk.BooleanVar(value=edge.has_vignette)
        tk.Checkbutton(self.editor_card, text="Maut/Vignette nötig", variable=self.edit_vignette_var, command=self.save_edge_edits, bg=self.bg_card, fg=self.fg_white, selectcolor=self.bg_sidebar, activebackground=self.bg_card, activeforeground=self.fg_white).grid(row=2, column=0, columnspan=2, sticky="w", pady=3)
        
        self.edit_traffic_var = tk.BooleanVar(value=edge.traffic_jam)
        tk.Checkbutton(self.editor_card, text="Aktiver Stau", variable=self.edit_traffic_var, command=self.save_edge_edits, bg=self.bg_card, fg=self.fg_white, selectcolor=self.bg_sidebar, activebackground=self.bg_card, activeforeground=self.fg_white).grid(row=3, column=0, columnspan=2, sticky="w", pady=3)
        
        tk.Label(self.editor_card, text="Staugefahr (Risiko):", bg=self.bg_card, fg=self.fg_white).grid(row=4, column=0, sticky="w", pady=(3, 0))
        self.lbl_risk_val = tk.Label(self.editor_card, text=f"{int(edge.traffic_risk * 100)}%", bg=self.bg_card, fg=self.fg_white, font=("Segoe UI", 10, "bold"))
        self.lbl_risk_val.grid(row=4, column=1, sticky="e", pady=(3, 0))
        
        self.edit_risk_slider = tk.Scale(self.editor_card, from_=0.0, to=1.0, resolution=0.01, orient="horizontal", bg=self.bg_card, fg=self.fg_white, highlightthickness=0, bd=0, activebackground=self.color_path)
        self.edit_risk_slider.set(edge.traffic_risk)
        self.edit_risk_slider.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        self.edit_risk_slider.bind("<ButtonRelease-1>", lambda ev: self.on_risk_slider_release(self.edit_risk_slider.get()))
        
        tk.Button(self.editor_card, text="Schließen", command=self.hide_edge_editor, bg="#4A4E69", fg=self.fg_white, font=("Segoe UI", 9, "bold"), bd=0).grid(row=6, column=0, columnspan=2, pady=(5, 0), sticky="ew")

    def on_risk_slider_release(self, val):
        risk = float(val)
        self.lbl_risk_val.configure(text=f"{int(risk * 100)}%")
        if self.selected_edge:
            self.selected_edge.traffic_risk = round(risk, 2)
            self.calculate_route()

    def save_edge_edits(self):
        if self.selected_edge:
            self.selected_edge.has_vignette = self.edit_vignette_var.get()
            self.selected_edge.traffic_jam = self.edit_traffic_var.get()
            self.calculate_route()

    def hide_edge_editor(self):
        self.selected_edge = None
        self.editor_card.grid_remove()
        self.draw_graph()

    def reset_all_roads(self):
        for edge in EDGES:
            edge.traffic_jam, edge.traffic_risk = False, 0.0
        for edge in EDGES:
            if edge.node_a == "Linz" and edge.node_b == "St. Pölten": edge.traffic_risk = 0.3
            elif edge.node_a == "St. Pölten" and edge.node_b == "Wien": edge.traffic_jam = True
            elif edge.node_a == "Wien" and edge.node_b == "Graz": edge.traffic_risk = 0.15
        self.selected_edge = None
        self.editor_card.grid_remove()
        self.calculate_route()

    def calculate_route(self):
        mode, avoid_vig, avoid_traf = self.routing_mode.get(), self.avoid_vignette_var.get(), self.avoid_traffic_var.get()
        cost, self.path_nodes, self.path_edges = dijkstra(self.start_city, self.dest_city, mode, avoid_vig, avoid_traf)
        save_route_to_files(self.start_city, self.dest_city, mode, avoid_vig, avoid_traf, self.path_nodes, self.path_edges)
        
        if self.path_nodes:
            dist = sum(e.distance for e in self.path_edges)
            fuel = sum(e.fuel_consumption for e in self.path_edges)
            elev = sum(e.elevation_diff for e in self.path_edges)
            eco = sum(e.eco_score for e in self.path_edges) / len(self.path_edges)
            
            time_h = sum((e.distance / e.speed_limit) * (3.0 if e.traffic_jam else 1.0) for e in self.path_edges)
            hours, mins = int(time_h), int(round((time_h - int(time_h)) * 60))
            if mins == 60: hours, mins = hours + 1, 0
            time_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
            vigs = any(e.has_vignette for e in self.path_edges)
            
            self.stats_labels["dist"].configure(text=f"{dist:.1f} km", fg=self.color_path)
            self.stats_labels["time"].configure(text=time_str, fg=self.color_path)
            self.stats_labels["fuel"].configure(text=f"{fuel:.1f} L", fg=self.color_path)
            self.stats_labels["elev"].configure(text=f"{elev} m", fg=self.color_path)
            self.stats_labels["eco"].configure(text=f"{eco:.1f}/10", fg=self.color_path)
            self.stats_labels["toll"].configure(text="Ja" if vigs else "Nein", fg=self.color_vignette if vigs else "#06D6A0")
        else:
            for lbl in self.stats_labels.values(): lbl.configure(text="-", fg=self.fg_muted)
        self.draw_graph()

    def center_map(self):
        self.zoom_factor = 1.0
        self.canvas.xview_moveto(0.0)
        self.canvas.yview_moveto(0.0)
        self.canvas.configure(scrollregion=(0, 0, 1000, 600))
        self.draw_graph()

    def on_canvas_press(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def on_canvas_drag(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def on_canvas_zoom(self, event):
        factor = 1.1 if (event.num == 4 or event.delta > 0) else 0.9
        self.zoom_factor *= factor
        if not (0.5 <= self.zoom_factor <= 3.0):
            self.zoom_factor /= factor
            return
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.canvas.scale("all", x, y, factor, factor)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def apply_zoom(self):
        self.canvas.configure(scrollregion=(0, 0, int(1000 * self.zoom_factor), int(600 * self.zoom_factor)))

if __name__ == "__main__":
    root = tk.Tk()
    app = RouteFinderApp(root)
    root.mainloop()
