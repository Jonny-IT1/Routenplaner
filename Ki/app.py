import tkinter as tk
from tkinter import messagebox
import heapq, os, json, hashlib, shutil, math

# Geographically correct coordinates and elevations of Austrian cities (Longitude, Latitude, Elevation in meters)
CITIES_GEO = {
    "Bregenz": (9.74, 47.50, 427),
    "Dornbirn": (9.74, 47.41, 437),
    "Feldkirch": (9.60, 47.24, 458),
    "Bludenz": (9.82, 47.15, 587),
    "Landeck": (10.56, 47.14, 817),
    "Imst": (10.74, 47.24, 828),
    "Reutte": (10.72, 47.49, 850),
    "Innsbruck": (11.40, 47.26, 574),
    "Kufstein": (12.17, 47.58, 499),
    "Kitzbühel": (12.35, 47.45, 762),
    "Mittersill": (12.48, 47.28, 790),
    "Zell am See": (12.80, 47.32, 750),
    "Lienz": (12.77, 46.83, 673),
    "Salzburg": (13.04, 47.80, 424),
    "Bischofshofen": (13.22, 47.42, 544),
    "Schladming": (13.68, 47.39, 745),
    "Liezen": (14.24, 47.57, 664),
    "Spittal": (13.50, 46.80, 560),
    "Villach": (13.85, 46.61, 501),
    "Klagenfurt": (14.31, 46.62, 446),
    "Wolfsberg": (14.83, 46.84, 463),
    "Graz": (15.44, 47.07, 353),
    "Leoben": (15.09, 47.38, 541),
    "Bruck an der Mur": (15.27, 47.41, 491),
    "Steyr": (14.42, 48.04, 310),
    "Wels": (14.02, 48.16, 317),
    "Linz": (14.29, 48.30, 266),
    "Amstetten": (14.87, 48.12, 273),
    "St. Pölten": (15.63, 48.20, 272),
    "Krems an der Donau": (15.61, 48.41, 203),
    "Wien": (16.37, 48.21, 171),
    "Baden": (16.23, 48.01, 230),
    "Wiener Neustadt": (16.24, 47.81, 265),
    "Eisenstadt": (16.52, 47.84, 182)
}

# Bounds for mapping geo coordinates to canvas coordinates
LON_MIN, LON_MAX = 9.4, 16.8
LAT_MIN, LAT_MAX = 46.4, 48.5

class Edge:
    def __init__(self, a, b, dist, speed, vig=False, jam=False, risk=0.0, elev=0.0, fuel=0.0, co2_g=120):
        self.node_a, self.node_b, self.distance, self.speed_limit, self.has_vignette, self.traffic_jam, self.traffic_risk, self.elevation_diff, self.fuel_consumption, self.co2_emissions_g = a, b, dist, speed, vig, jam, risk, elev, fuel, co2_g
        self.eco_score = max(1, min(10, 11 - int(co2_g / 15)))

EDGES = [
    # Bregenz
    Edge("Bregenz", "Dornbirn", 12, 100, vig=True, elev=10, fuel=0.8, co2_g=130),
    Edge("Bregenz", "Reutte", 90, 80, vig=False, elev=900, fuel=8.2, co2_g=115),
    
    # Dornbirn
    Edge("Dornbirn", "Feldkirch", 23, 100, vig=True, elev=20, fuel=1.5, co2_g=130),
    
    # Feldkirch
    Edge("Feldkirch", "Bludenz", 20, 100, vig=True, elev=100, fuel=1.8, co2_g=130),
    
    # Bludenz
    Edge("Bludenz", "Landeck", 65, 80, vig=False, elev=800, fuel=6.8, co2_g=110),
    
    # Landeck
    Edge("Landeck", "Imst", 23, 100, vig=True, elev=50, fuel=1.8, co2_g=130),
    Edge("Landeck", "Reutte", 65, 80, vig=False, elev=500, fuel=5.8, co2_g=115),
    Edge("Landeck", "Innsbruck", 75, 130, vig=True, elev=150, fuel=6.0, co2_g=150),
    Edge("Landeck", "Lienz", 145, 80, vig=False, elev=1200, fuel=13.5, co2_g=110),
    
    # Imst
    Edge("Imst", "Innsbruck", 55, 130, vig=True, elev=100, fuel=4.4, co2_g=150),
    Edge("Imst", "Reutte", 45, 80, vig=False, elev=600, fuel=4.2, co2_g=115),
    
    # Reutte
    Edge("Reutte", "Innsbruck", 95, 90, vig=False, elev=400, fuel=8.0, co2_g=120),
    
    # Innsbruck
    Edge("Innsbruck", "Kufstein", 75, 130, vig=True, elev=80, fuel=5.8, co2_g=150),
    Edge("Innsbruck", "Salzburg", 185, 130, vig=True, elev=400, fuel=15.5, co2_g=150),
    Edge("Innsbruck", "Lienz", 180, 80, vig=False, elev=1500, fuel=16.0, co2_g=110),
    
    # Kufstein
    Edge("Kufstein", "Kitzbühel", 30, 80, vig=False, elev=150, fuel=2.4, co2_g=120),
    Edge("Kufstein", "Salzburg", 100, 130, vig=True, elev=50, fuel=7.8, co2_g=150),
    
    # Kitzbühel
    Edge("Kitzbühel", "Zell am See", 50, 80, vig=False, elev=200, fuel=3.8, co2_g=120),
    Edge("Kitzbühel", "Mittersill", 30, 80, vig=False, elev=400, fuel=2.8, co2_g=120),
    
    # Mittersill
    Edge("Mittersill", "Zell am See", 28, 100, vig=False, elev=50, fuel=2.1, co2_g=125),
    Edge("Mittersill", "Lienz", 55, 80, vig=False, elev=900, fuel=5.6, co2_g=110),
    
    # Zell am See
    Edge("Zell am See", "Bischofshofen", 45, 80, vig=False, elev=100, fuel=3.5, co2_g=120),
    Edge("Zell am See", "Lienz", 85, 80, vig=False, elev=1800, fuel=10.5, co2_g=95),
    
    # Lienz
    Edge("Lienz", "Spittal", 75, 80, vig=False, elev=200, fuel=5.8, co2_g=120),
    
    # Spittal
    Edge("Spittal", "Villach", 40, 130, vig=True, elev=50, fuel=3.2, co2_g=150),
    Edge("Spittal", "Bischofshofen", 90, 100, vig=True, elev=600, fuel=8.5, co2_g=140),
    
    # Salzburg
    Edge("Salzburg", "Bischofshofen", 55, 130, vig=True, elev=200, fuel=4.5, co2_g=150),
    Edge("Salzburg", "Wels", 100, 130, vig=True, elev=200, fuel=8.2, co2_g=150),
    
    # Bischofshofen
    Edge("Bischofshofen", "Schladming", 45, 90, vig=False, elev=250, fuel=3.6, co2_g=120),
    
    # Schladming
    Edge("Schladming", "Liezen", 50, 90, vig=False, elev=100, fuel=3.8, co2_g=125),
    
    # Liezen
    Edge("Liezen", "Graz", 130, 100, vig=True, elev=500, fuel=11.5, co2_g=140),
    Edge("Liezen", "Bruck an der Mur", 90, 100, vig=False, elev=400, fuel=8.0, co2_g=130),
    Edge("Liezen", "Villach", 130, 100, vig=True, elev=700, fuel=12.0, co2_g=140),
    Edge("Liezen", "Steyr", 80, 80, vig=False, elev=600, fuel=6.8, co2_g=115),
    Edge("Liezen", "Leoben", 75, 100, vig=True, elev=150, fuel=5.8, co2_g=135),
    
    # Villach
    Edge("Villach", "Klagenfurt", 40, 130, vig=True, elev=100, fuel=3.2, co2_g=150),
    
    # Klagenfurt
    Edge("Klagenfurt", "Wolfsberg", 60, 130, vig=True, elev=300, fuel=4.8, co2_g=150),
    Edge("Klagenfurt", "Graz", 140, 130, vig=True, elev=800, fuel=13.0, co2_g=150),
    
    # Wolfsberg
    Edge("Wolfsberg", "Graz", 70, 130, vig=True, elev=400, fuel=5.6, co2_g=150),
    
    # Leoben
    Edge("Leoben", "Bruck an der Mur", 16, 100, vig=True, elev=50, fuel=1.2, co2_g=135),
    
    # Bruck an der Mur
    Edge("Bruck an der Mur", "Graz", 55, 130, vig=True, elev=150, fuel=4.8, co2_g=150),
    Edge("Bruck an der Mur", "St. Pölten", 110, 80, vig=False, elev=700, fuel=9.8, co2_g=120),
    
    # Steyr
    Edge("Steyr", "Linz", 40, 90, vig=False, elev=60, fuel=3.2, co2_g=125),
    Edge("Steyr", "Wels", 35, 90, vig=False, elev=50, fuel=2.8, co2_g=125),
    
    # Wels
    Edge("Wels", "Linz", 30, 130, vig=True, elev=50, fuel=2.5, co2_g=150),
    
    # Linz
    Edge("Linz", "Amstetten", 50, 130, vig=True, elev=80, fuel=4.0, co2_g=150),
    Edge("Linz", "St. Pölten", 125, 130, vig=True, risk=0.3, elev=150, fuel=10.2, co2_g=150),
    
    # Amstetten
    Edge("Amstetten", "St. Pölten", 50, 130, vig=True, elev=100, fuel=4.0, co2_g=150),
    
    # St. Pölten
    Edge("St. Pölten", "Krems an der Donau", 30, 100, vig=True, elev=40, fuel=2.4, co2_g=135),
    Edge("St. Pölten", "Wien", 65, 130, vig=True, jam=True, elev=100, fuel=5.3, co2_g=150),
    
    # Krems an der Donau
    Edge("Krems an der Donau", "Wien", 75, 100, vig=False, elev=60, fuel=5.8, co2_g=125),
    
    # Wien
    Edge("Wien", "Baden", 30, 130, vig=True, elev=30, fuel=2.4, co2_g=150),
    Edge("Wien", "Eisenstadt", 60, 130, vig=True, elev=80, fuel=4.8, co2_g=150),
    Edge("Wien", "Wiener Neustadt", 50, 130, vig=True, elev=100, fuel=4.0, co2_g=150),
    
    # Baden
    Edge("Baden", "Wiener Neustadt", 20, 130, vig=True, elev=20, fuel=1.6, co2_g=150),
    
    # Wiener Neustadt
    Edge("Wiener Neustadt", "Eisenstadt", 35, 100, vig=False, elev=50, fuel=2.8, co2_g=130),
    Edge("Wiener Neustadt", "Graz", 150, 130, vig=True, elev=600, fuel=12.5, co2_g=150),
    
    # Eisenstadt
    Edge("Eisenstadt", "Graz", 170, 100, vig=False, elev=500, fuel=13.5, co2_g=130)
]

def hash_password(password, salt):
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()

def reset_data_directory():
    if os.path.exists("data"):
        for f in os.listdir("data"):
            p = os.path.join("data", f)
            shutil.rmtree(p) if os.path.isdir(p) else os.unlink(p)
        messagebox.showinfo("Erfolg", "Daten gelöscht!")

def calculate_cost(e, mode, avoid_vignette, avoid_traffic):
    costs = {
        "Shortest": e.distance,
        "Fastest": (e.distance / e.speed_limit) * (1.0 + (2.0 if e.traffic_jam else 0) + (e.traffic_risk * 1.5 if avoid_traffic else 0)),
        "Fuel": e.fuel_consumption,
        "Eco": (e.distance * e.co2_emissions_g) / 1000.0,
        "Flat": e.elevation_diff
    }
    cost = costs.get(mode, e.distance)
    if avoid_vignette and e.has_vignette:
        cost += {"Shortest": 500.0, "Fastest": 5.0, "Fuel": 50.0, "Eco": 100.0, "Flat": 2000.0}.get(mode, 500.0)
    if avoid_traffic and mode != "Fastest":
        cost += (150.0 if e.traffic_jam else 0) + e.traffic_risk * 75.0
    return cost

def haversine_distance(c1, c2):
    lon1, lat1 = c1[0], c1[1]
    lon2, lat2 = c2[0], c2[1]
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def get_heuristic(curr, dest, mode):
    coord_curr = CITIES_GEO[curr]
    coord_dest = CITIES_GEO[dest]
    dist_km = haversine_distance(coord_curr, coord_dest)
    if mode == "Shortest":
        return dist_km
    elif mode == "Fastest":
        return dist_km / 130.0
    elif mode == "Fuel":
        return dist_km * 0.04
    elif mode == "Eco":
        return dist_km * 0.095
    elif mode == "Flat":
        return abs(coord_curr[2] - coord_dest[2])
    return dist_km

def a_star(start, dest, mode, avoid_vig, avoid_traf):
    adj = {n: [] for n in CITIES_GEO}
    for e in EDGES:
        cost = calculate_cost(e, mode, avoid_vig, avoid_traf)
        adj[e.node_a].append((e.node_b, cost, e))
        adj[e.node_b].append((e.node_a, cost, e))
        
    h_start = get_heuristic(start, dest, mode)
    q = [(h_start, 0.0, start, [start], [])]
    
    best_g = {n: float("inf") for n in CITIES_GEO}
    best_g[start] = 0.0
    
    while q:
        f, g, curr, path_n, path_e = heapq.heappop(q)
        if curr == dest:
            return g, path_n, path_e
        if g > best_g[curr]:
            continue
        for neighbor, edge_cost, edge in adj[curr]:
            next_g = g + edge_cost
            if next_g < best_g.get(neighbor, float("inf")):
                best_g[neighbor] = next_g
                h = get_heuristic(neighbor, dest, mode)
                next_f = next_g + h
                heapq.heappush(q, (next_f, next_g, neighbor, path_n + [neighbor], path_e + [edge]))
    return None, None, None

def save_route_to_files(start, dest, mode, avoid_vig, avoid_traf, path_nodes, path_edges):
    os.makedirs("data", exist_ok=True)
    if not path_nodes:
        return
    dist = sum(e.distance for e in path_edges)
    fuel = sum(e.fuel_consumption for e in path_edges)
    elev = sum(e.elevation_diff for e in path_edges)
    co2 = sum(e.distance * e.co2_emissions_g for e in path_edges) / 1000.0
    time_h = sum((e.distance / e.speed_limit) * (3.0 if e.traffic_jam else 1.0) for e in path_edges)
    time_str = f"{int(time_h)} Std. {int(round((time_h - int(time_h)) * 60))} Min."
    
    json_data = {
        "start": start, "destination": dest, "mode": mode, "total_distance_km": dist, "actual_time_formatted": time_str,
        "total_fuel_liters": round(fuel, 1), "total_elevation_gain_m": elev, "total_co2_emissions_kg": round(co2, 1),
        "route": path_nodes
    }
    with open("data/weg.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=4, ensure_ascii=False)
    with open("data/weg.txt", "w", encoding="utf-8") as f:
        f.write(f"Start: {start} -> Ziel: {dest}\nModus: {mode}\nDistanz: {dist:.1f} km\nZeit: {time_str}\nVerbrauch: {fuel:.1f} L\nHöhenmeter: {elev} m\nCO2: {co2:.1f} kg\nRoute: {' -> '.join(path_nodes)}\n")

class RouteFinderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Antigravity Route Finder (KI-Edition)")
        self.root.geometry("1200x820")
        self.root.configure(bg="#F3F5F7")
        
        # Color Theme: Premium Light Mode
        self.bg_light = "#F3F5F7"
        self.bg_sidebar = "#FFFFFF"
        self.bg_card = "#F8F9FA"
        self.fg_dark = "#1A1D20"
        self.fg_muted = "#5A626A"
        self.color_start = "#10B981"
        self.color_dest = "#EF4444"
        self.color_path = "#3B82F6"
        self.color_vignette = "#F59E0B"
        self.color_traffic = "#EF4444"
        
        self.start_city, self.dest_city, self.selected_edge = "Wien", "Bregenz", None
        self.path_nodes, self.path_edges = [], []
        self.zoom_factor = 1.0
        self.animating = False
        
        self.show_login_screen()

    def bind_hover(self, widget, hover_color, normal_color):
        widget.bind("<Enter>", lambda e: widget.config(bg=hover_color))
        widget.bind("<Leave>", lambda e: widget.config(bg=normal_color))

    def show_login_screen(self):
        self.login_frame = tk.Frame(self.root, bg=self.bg_light)
        self.login_frame.pack(expand=True, fill="both")
        
        # UI Container Card
        card = tk.Frame(self.login_frame, bg=self.bg_sidebar, padx=30, pady=30, highlightthickness=1, highlightbackground="#DFE3E6")
        card.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(card, text="Antigravity Wegfinder", bg=self.bg_sidebar, fg=self.color_path, font=("Segoe UI", 20, "bold")).pack(pady=(0, 5))
        tk.Label(card, text="KI-optimiertes Routennetzwerk", bg=self.bg_sidebar, fg=self.fg_muted, font=("Segoe UI", 10)).pack(pady=(0, 20))
        
        form = tk.Frame(card, bg=self.bg_sidebar)
        form.pack(pady=10)
        
        tk.Label(form, text="Benutzername:", bg=self.bg_sidebar, fg=self.fg_dark, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, pady=8, sticky="w")
        self.ent_user = tk.Entry(form, bg=self.bg_card, fg=self.fg_dark, bd=1, relief="solid", font=("Segoe UI", 10), insertbackground=self.fg_dark, width=22)
        self.ent_user.grid(row=0, column=1, pady=8, padx=(10, 0))
        
        tk.Label(form, text="Passwort:", bg=self.bg_sidebar, fg=self.fg_dark, font=("Segoe UI", 10, "bold")).grid(row=1, column=0, pady=8, sticky="w")
        self.ent_pwd = tk.Entry(form, show="*", bg=self.bg_card, fg=self.fg_dark, bd=1, relief="solid", font=("Segoe UI", 10), insertbackground=self.fg_dark, width=22)
        self.ent_pwd.grid(row=1, column=1, pady=8, padx=(10, 0))
        
        btn_f = tk.Frame(card, bg=self.bg_sidebar)
        btn_f.pack(pady=15)
        
        btn_login = tk.Button(btn_f, text="Anmelden", command=self.handle_login, bg=self.color_path, fg="#FFFFFF", font=("Segoe UI", 10, "bold"), bd=0, padx=20, pady=6, cursor="hand2")
        btn_login.pack(side="left", padx=8)
        self.bind_hover(btn_login, "#2563EB", self.color_path)
        
        btn_reg = tk.Button(btn_f, text="Registrieren", command=self.handle_register, bg="#6C757D", fg="#FFFFFF", font=("Segoe UI", 10, "bold"), bd=0, padx=20, pady=6, cursor="hand2")
        btn_reg.pack(side="right", padx=8)
        self.bind_hover(btn_reg, "#4B5563", "#6C757D")
        
        btn_reset = tk.Button(card, text="Daten zurücksetzen (data/ leeren)", command=reset_data_directory, bg="#EF4444", fg="#FFFFFF", font=("Segoe UI", 9, "bold"), bd=0, padx=15, pady=6, cursor="hand2")
        btn_reset.pack(pady=(15, 0))
        self.bind_hover(btn_reset, "#DC2626", "#EF4444")

    def handle_login(self):
        user, pwd = self.ent_user.get().strip(), self.ent_pwd.get()
        if not user or not pwd:
            return
        cred_path = os.path.join(".venv", "user_credentials.json")
        if not os.path.exists(cred_path):
            return messagebox.showerror("Fehler", "Keine Benutzer registriert!")
        with open(cred_path, "r", encoding="utf-8") as f:
            credentials = json.load(f)
        if credentials.get(user) == hash_password(pwd, user):
            self.login_frame.destroy()
            self.create_main_layout()
            self.calculate_route()
            self.center_map()
        else:
            messagebox.showerror("Fehler", "Falsche Anmeldedaten!")

    def handle_register(self):
        user, pwd = self.ent_user.get().strip(), self.ent_pwd.get()
        if not user or not pwd:
            return
        cred_path = os.path.join(".venv", "user_credentials.json")
        credentials = {}
        if os.path.exists(cred_path):
            with open(cred_path, "r", encoding="utf-8") as f:
                credentials = json.load(f)
        if user in credentials:
            return messagebox.showerror("Fehler", "Bereits vergeben!")
        credentials[user] = hash_password(pwd, user)
        os.makedirs(".venv", exist_ok=True)
        with open(cred_path, "w", encoding="utf-8") as f:
            json.dump(credentials, f, indent=4)
        messagebox.showinfo("Erfolg", "Registrierung erfolgreich!")

    def get_canvas_coords(self, city_name):
        lon, lat, _ = CITIES_GEO[city_name]
        w, h = 950, 580
        x = 50 + (lon - LON_MIN) / (LON_MAX - LON_MIN) * (w - 100)
        y = h - 50 - (lat - LAT_MIN) / (LAT_MAX - LAT_MIN) * (h - 100)
        return int(x), int(y)

    def create_main_layout(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        map_frame = tk.Frame(self.root, bg=self.bg_light)
        map_frame.grid(row=0, column=0, sticky="nsew")
        map_frame.rowconfigure(0, weight=1)
        map_frame.columnconfigure(0, weight=1)
        
        self.canvas = tk.Canvas(map_frame, bg="#EBF1F5", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        self.canvas.bind("<ButtonPress-1>", lambda e: self.canvas.scan_mark(e.x, e.y))
        self.canvas.bind("<B1-Motion>", lambda e: self.canvas.scan_dragto(e.x, e.y, gain=1))
        self.canvas.bind("<MouseWheel>", self.on_canvas_zoom)
        
        # Sidebar with white background and thin border
        sidebar = tk.Frame(self.root, bg=self.bg_sidebar, padx=15, pady=15, width=330, highlightthickness=1, highlightbackground="#DFE3E6")
        sidebar.grid(row=0, column=1, sticky="nsew")
        sidebar.grid_propagate(False)
        
        tk.Label(sidebar, text="Österreich Routenplaner", bg=self.bg_sidebar, fg=self.fg_dark, font=("Segoe UI", 14, "bold")).pack(pady=5, anchor="w")
        tk.Label(sidebar, text="KI-Optimierte A* Navigation", bg=self.bg_sidebar, fg=self.fg_muted, font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 10))
        
        # Dropdowns
        self.start_var, self.dest_var = tk.StringVar(value=self.start_city), tk.StringVar(value=self.dest_city)
        tk.Label(sidebar, text="Startpunkt:", bg=self.bg_sidebar, fg=self.fg_muted, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(8, 0))
        
        opt_start = tk.OptionMenu(sidebar, self.start_var, *sorted(CITIES_GEO.keys()), command=self.on_dropdown_change)
        opt_start.config(bg=self.bg_card, fg=self.fg_dark, font=("Segoe UI", 9), relief="solid", bd=1)
        opt_start.pack(fill="x", pady=2)
        
        tk.Label(sidebar, text="Zielpunkt:", bg=self.bg_sidebar, fg=self.fg_muted, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(8, 0))
        opt_dest = tk.OptionMenu(sidebar, self.dest_var, *sorted(CITIES_GEO.keys()), command=self.on_dropdown_change)
        opt_dest.config(bg=self.bg_card, fg=self.fg_dark, font=("Segoe UI", 9), relief="solid", bd=1)
        opt_dest.pack(fill="x", pady=2)
        
        # Routing Modes
        self.routing_mode = tk.StringVar(value="Fastest")
        modes = {"Schnellste Route": "Fastest", "Kürzeste Route": "Shortest", "Kraftstoffsparend": "Fuel", "Klimaneutral (Eco)": "Eco", "Flachste Route": "Flat"}
        tk.Label(sidebar, text="Optimierungs-Modus:", bg=self.bg_sidebar, fg=self.fg_muted, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(10, 0))
        opt_mode = tk.OptionMenu(sidebar, self.routing_mode, *modes.keys(), command=lambda val: self.on_mode_change(modes[val]))
        opt_mode.config(bg=self.bg_card, fg=self.fg_dark, font=("Segoe UI", 9), relief="solid", bd=1)
        opt_mode.pack(fill="x", pady=2)
        
        # Checkboxes
        self.avoid_vignette_var, self.avoid_traffic_var = tk.BooleanVar(value=False), tk.BooleanVar(value=True)
        tk.Checkbutton(sidebar, text="Mautstraßen meiden", variable=self.avoid_vignette_var, command=self.calculate_route, bg=self.bg_sidebar, fg=self.fg_dark, activebackground=self.bg_sidebar, activeforeground=self.fg_dark, font=("Segoe UI", 9)).pack(anchor="w", pady=2)
        tk.Checkbutton(sidebar, text="Staus meiden", variable=self.avoid_traffic_var, command=self.calculate_route, bg=self.bg_sidebar, fg=self.fg_dark, activebackground=self.bg_sidebar, activeforeground=self.fg_dark, font=("Segoe UI", 9)).pack(anchor="w", pady=2)
        
        # Klimaschutz Card (Dedicated Eco details)
        self.eco_frame = tk.LabelFrame(sidebar, text=" 🌱 Klimaschutz & CO2-Bilanz ", bg="#E8F5E9", fg="#2E7D32", font=("Segoe UI", 9, "bold"), padx=10, pady=10, relief="solid", bd=1)
        self.eco_frame.pack(fill="x", pady=8)
        self.lbl_eco_saving = tk.Label(self.eco_frame, text="Wähle eine Route...", bg="#E8F5E9", fg="#2E7D32", justify="left", font=("Segoe UI", 9, "bold"))
        self.lbl_eco_saving.pack(fill="x")
        
        # Stats Label
        stats_frame = tk.LabelFrame(sidebar, text=" Routen-Statistiken ", bg=self.bg_sidebar, fg=self.fg_dark, font=("Segoe UI", 9, "bold"), padx=10, pady=10, relief="solid", bd=1)
        stats_frame.pack(fill="x", pady=5)
        self.lbl_stats = tk.Label(stats_frame, text="", bg=self.bg_sidebar, fg=self.fg_dark, justify="left", font=("Segoe UI", 9))
        self.lbl_stats.pack(fill="x")
        
        # Editor Card
        self.editor_card = tk.LabelFrame(sidebar, text=" Straße bearbeiten ", bg=self.bg_card, fg=self.fg_dark, font=("Segoe UI", 9, "bold"), padx=10, pady=10, relief="solid", bd=1)
        self.editor_card.pack(fill="x", pady=5)
        self.editor_card.pack_forget()
        
        # Buttons
        btn_center = tk.Button(sidebar, text="Karte zentrieren", command=self.center_map, bg=self.color_path, fg="#FFFFFF", font=("Segoe UI", 9, "bold"), bd=0, pady=5, cursor="hand2")
        btn_center.pack(fill="x", side="bottom", pady=2)
        self.bind_hover(btn_center, "#2563EB", self.color_path)
        
        btn_res_road = tk.Button(sidebar, text="Verkehr zurücksetzen", command=self.reset_all_roads, bg="#6C757D", fg="#FFFFFF", font=("Segoe UI", 9, "bold"), bd=0, pady=5, cursor="hand2")
        btn_res_road.pack(fill="x", side="bottom", pady=2)
        self.bind_hover(btn_res_road, "#4B5563", "#6C757D")

    def draw_graph(self):
        self.canvas.delete("all")
        self.edge_by_line_id, self.node_by_oval_id = {}, {}
        
        # Soft background grid lines
        for x in range(0, 1500, 85):
            self.canvas.create_line(x, 0, x, 1000, fill="#E1E7EC", width=1)
        for y in range(0, 1000, 85):
            self.canvas.create_line(0, y, 1500, y, fill="#E1E7EC", width=1)
            
        route_edges_set = set(self.path_edges)
        
        # Draw Edges
        for e in EDGES:
            pt_a, pt_b = self.get_canvas_coords(e.node_a), self.get_canvas_coords(e.node_b)
            is_on_route = e in route_edges_set
            
            # Base Road Line Styling
            if e.traffic_jam:
                color, width = self.color_traffic, 5
            elif e == self.selected_edge:
                color, width = "#FF00FF", 5
            elif is_on_route:
                color, width = self.color_path, 6
            elif e.has_vignette:
                color, width = self.color_vignette, 3
            else:
                color, width = "#B9C6CD", 3
                
            # Draw glow underneath low-emission eco-friendly roads
            if e.co2_emissions_g < 120 and not is_on_route:
                # Semi-transparent green glow representation in standard canvas (dashed mint green line offset)
                self.canvas.create_line(pt_a[0], pt_a[1], pt_b[0], pt_b[1], fill="#A7F3D0", width=6)
                
            line_id = self.canvas.create_line(pt_a[0], pt_a[1], pt_b[0], pt_b[1], fill=color, width=width, tags="edge")
            self.edge_by_line_id[line_id] = e
            
            # White dash line overlay inside vignette highways
            if e.has_vignette and not is_on_route and not e.traffic_jam and e != self.selected_edge:
                self.canvas.create_line(pt_a[0], pt_a[1], pt_b[0], pt_b[1], fill="#FFFFFF", width=1, dash=(3, 4))
                
            # Traffic Risk indicator dot
            if e.traffic_risk > 0.0 and not e.traffic_jam:
                mx, my = (pt_a[0]+pt_b[0])/2, (pt_a[1]+pt_b[1])/2
                self.canvas.create_oval(mx-5, my-5, mx+5, my+5, fill="#F59E0B", outline="")
            
            # Distance text
            mx, my = (pt_a[0]+pt_b[0])/2, (pt_a[1]+pt_b[1])/2
            self.canvas.create_text(mx, my - 9, text=f"{e.distance}km", fill=self.fg_muted, font=("Segoe UI", 7, "bold"))

        # Draw Nodes with Soft Shadow
        for name, pt in CITIES_GEO.items():
            pt = self.get_canvas_coords(name)
            is_path_node = name in self.path_nodes
            fill_c = self.color_start if name == self.start_city else (self.color_dest if name == self.dest_city else (self.color_path if is_path_node else "#FFFFFF"))
            outline_c = "#FFFFFF" if name in (self.start_city, self.dest_city) else "#4B5563"
            radius = 12 if name in (self.start_city, self.dest_city) else 8
            
            # Soft shadow oval
            self.canvas.create_oval(pt[0] - radius + 2, pt[1] - radius + 2, pt[0] + radius + 2, pt[1] + radius + 2, fill="#CFD8DC", outline="", tags="shadow")
            
            # Foreground oval
            oval_id = self.canvas.create_oval(pt[0] - radius, pt[1] - radius, pt[0] + radius, pt[1] + radius, fill=fill_c, outline=outline_c, width=2, tags="node")
            self.node_by_oval_id[oval_id] = name
            
            # Text label
            self.canvas.create_text(pt[0], pt[1] - radius - 8, text=name, fill=self.fg_dark, font=("Segoe UI", 9, "bold"))

        # Interactive Canvas Bindings
        self.canvas.tag_bind("node", "<Button-1>", lambda ev: self.on_node_click(ev, left=True))
        self.canvas.tag_bind("node", "<Button-3>", lambda ev: self.on_node_click(ev, left=False))
        self.canvas.tag_bind("node", "<Double-Button-1>", lambda ev: self.on_node_click(ev, left=False))
        self.canvas.tag_bind("edge", "<Button-1>", self.on_edge_click)
        
        # Legend drawing in top-left
        self.draw_legend()
        self.apply_zoom()

    def draw_legend(self):
        leg_x, leg_y = 20, 20
        self.canvas.create_rectangle(leg_x, leg_y, leg_x + 190, leg_y + 130, fill="#FFFFFF", outline="#DFE3E6", width=1)
        self.canvas.create_text(leg_x + 95, leg_y + 12, text="Karte-Legende", fill=self.fg_dark, font=("Segoe UI", 8, "bold"))
        
        items = [
            ("#10B981", "Startpunkt"),
            ("#EF4444", "Zielpunkt"),
            ("#3B82F6", "Berechneter Pfad"),
            ("#F59E0B", "Mautstraße (Vignette)"),
            ("#EF4444", "Stau (Blockiert)"),
            ("#A7F3D0", "Klimafreundlich (<120g/km)")
        ]
        
        for idx, (color, label) in enumerate(items):
            cy = leg_y + 28 + (idx * 16)
            if label == "Klimafreundlich (<120g/km)":
                self.canvas.create_line(leg_x + 10, cy, leg_x + 25, cy, fill=color, width=4)
            elif label in ("Mautstraße (Vignette)", "Berechneter Pfad"):
                self.canvas.create_line(leg_x + 10, cy, leg_x + 25, cy, fill=color, width=3)
            else:
                self.canvas.create_oval(leg_x + 12, cy - 4, leg_x + 20, cy + 4, fill=color, outline="#4B5563")
            self.canvas.create_text(leg_x + 35, cy, text=label, fill=self.fg_muted, font=("Segoe UI", 8), anchor="w")

    def on_dropdown_change(self, val):
        self.start_city, self.dest_city = self.start_var.get(), self.dest_var.get()
        self.calculate_route()

    def on_mode_change(self, val):
        self.routing_mode.set(val)
        self.calculate_route()

    def on_node_click(self, event, left):
        item = self.canvas.find_withtag("current")[0]
        name = self.node_by_oval_id.get(item)
        if not name or self.animating:
            return
        if left:
            if name == self.dest_city:
                return
            self.start_city = name
            self.start_var.set(name)
        else:
            if name == self.start_city:
                return
            self.dest_city = name
            self.dest_var.set(name)
        self.calculate_route()

    def on_edge_click(self, event):
        item = self.canvas.find_withtag("current")[0]
        edge = self.edge_by_line_id.get(item)
        if edge and not self.animating:
            self.selected_edge = edge
            self.draw_graph()
            self.show_edge_editor(edge)

    def show_edge_editor(self, edge):
        for child in self.editor_card.winfo_children():
            child.destroy()
        self.editor_card.pack(fill="x", pady=5)
        
        tk.Label(self.editor_card, text=f"{edge.node_a} ↔ {edge.node_b}", bg=self.bg_card, fg=self.fg_dark, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(self.editor_card, text=f"{edge.distance}km | {edge.speed_limit}km/h | {edge.fuel_consumption}L\n+{edge.elevation_diff}m | CO2: {edge.co2_emissions_g}g/km", bg=self.bg_card, fg=self.fg_muted, justify="left", font=("Segoe UI", 8)).pack(anchor="w")
        
        self.edit_vignette_var = tk.BooleanVar(value=edge.has_vignette)
        tk.Checkbutton(self.editor_card, text="Vignette nötig", variable=self.edit_vignette_var, command=self.save_edge_edits, bg=self.bg_card, fg=self.fg_dark, selectcolor=self.bg_light).pack(anchor="w")
        
        self.edit_traffic_var = tk.BooleanVar(value=edge.traffic_jam)
        tk.Checkbutton(self.editor_card, text="Aktiver Stau", variable=self.edit_traffic_var, command=self.save_edge_edits, bg=self.bg_card, fg=self.fg_dark, selectcolor=self.bg_light).pack(anchor="w")
        
        tk.Label(self.editor_card, text=f"Staugefahr: {int(edge.traffic_risk*100)}%", bg=self.bg_card, fg=self.fg_dark).pack(anchor="w")
        slider = tk.Scale(self.editor_card, from_=0.0, to=1.0, resolution=0.01, orient="horizontal", bg=self.bg_card, fg=self.fg_dark, bd=0, highlightthickness=0)
        slider.set(edge.traffic_risk)
        slider.pack(fill="x", pady=2)
        slider.bind("<ButtonRelease-1>", lambda ev: self.on_risk_slider_release(slider.get()))
        
        btn_close = tk.Button(self.editor_card, text="Schließen", command=self.hide_edge_editor, bg="#6C757D", fg="#FFFFFF", bd=0, pady=3, cursor="hand2")
        btn_close.pack(fill="x", pady=2)
        self.bind_hover(btn_close, "#4B5563", "#6C757D")

    def on_risk_slider_release(self, val):
        if self.selected_edge:
            self.selected_edge.traffic_risk = round(float(val), 2)
            self.calculate_route()

    def save_edge_edits(self):
        if self.selected_edge:
            self.selected_edge.has_vignette = self.edit_vignette_var.get()
            self.selected_edge.traffic_jam = self.edit_traffic_var.get()
            self.calculate_route()

    def hide_edge_editor(self):
        self.selected_edge = None
        self.editor_card.pack_forget()
        self.draw_graph()

    def reset_all_roads(self):
        if self.animating:
            return
        for edge in EDGES:
            edge.traffic_jam, edge.traffic_risk = False, 0.0
        for edge in EDGES:
            if edge.node_a == "Linz" and edge.node_b == "St. Pölten":
                edge.traffic_risk = 0.3
            elif edge.node_a == "St. Pölten" and edge.node_b == "Wien":
                edge.traffic_jam = True
            elif edge.node_a == "Wien" and edge.node_b == "Graz":
                edge.traffic_risk = 0.15
        self.selected_edge = None
        self.editor_card.pack_forget()
        self.calculate_route()

    def calculate_route(self):
        mode = self.routing_mode.get()
        avoid_vig = self.avoid_vignette_var.get()
        avoid_traf = self.avoid_traffic_var.get()
        
        cost, self.path_nodes, self.path_edges = a_star(self.start_city, self.dest_city, mode, avoid_vig, avoid_traf)
        save_route_to_files(self.start_city, self.dest_city, mode, avoid_vig, avoid_traf, self.path_nodes, self.path_edges)
        
        if self.path_nodes:
            dist = sum(e.distance for e in self.path_edges)
            fuel = sum(e.fuel_consumption for e in self.path_edges)
            elev = sum(e.elevation_diff for e in self.path_edges)
            co2 = sum(e.distance * e.co2_emissions_g for e in self.path_edges) / 1000.0
            
            time_h = sum((e.distance / e.speed_limit) * (3.0 if e.traffic_jam else 1.0) for e in self.path_edges)
            time_str = f"{int(time_h)}h {int(round((time_h - int(time_h)) * 60))}m"
            vigs = any(e.has_vignette for e in self.path_edges)
            
            stats_text = f"Distanz: {dist:.1f} km\nZeit: {time_str}\nVerbrauch: {fuel:.1f} L\nHöhenstufe: +{elev} m\nCO2-Ausstoß: {co2:.1f} kg\nMaut/Vignette: {'Ja' if vigs else 'Nein'}"
            self.lbl_stats.config(text=stats_text)
            
            # Climate protection calculation
            self.update_climate_savings(co2, avoid_vig, avoid_traf)
            self.start_route_animation()
        else:
            self.lbl_stats.config(text="Keine Route gefunden!")
            self.lbl_eco_saving.config(text="Kein Weg für CO2-Vergleich.")
            self.draw_graph()

    def update_climate_savings(self, current_co2, avoid_vig, avoid_traf):
        # Calculate fastest and eco paths to run comparison
        _, _, fast_edges = a_star(self.start_city, self.dest_city, "Fastest", avoid_vig, avoid_traf)
        _, _, eco_edges = a_star(self.start_city, self.dest_city, "Eco", avoid_vig, avoid_traf)
        
        if not fast_edges or not eco_edges:
            self.lbl_eco_saving.config(text="🌱 CO2-Vergleich nicht möglich.")
            return
            
        fast_co2 = sum(e.distance * e.co2_emissions_g for e in fast_edges) / 1000.0
        eco_co2 = sum(e.distance * e.co2_emissions_g for e in eco_edges) / 1000.0
        
        mode = self.routing_mode.get()
        if mode == "Eco":
            # Show savings compared to the fastest route
            saved_co2 = fast_co2 - current_co2
            if fast_co2 > 0 and saved_co2 > 0:
                saved_pct = (saved_co2 / fast_co2) * 100
                self.lbl_eco_saving.config(text=f"Klimaschutz:\nSie sparen {saved_co2:.1f} kg CO2\n({saved_pct:.1f}% weniger als die\nschnellste Route! 🎉)")
            else:
                self.lbl_eco_saving.config(text="Klimaschutz:\nSie fahren bereits auf der\numweltfreundlichsten Route! 🌱")
        else:
            # Recommend switching to Eco
            potential_saving = current_co2 - eco_co2
            if current_co2 > 0 and potential_saving > 0:
                saving_pct = (potential_saving / current_co2) * 100
                self.lbl_eco_saving.config(text=f"Klimatipp:\nEco-Modus spart {potential_saving:.1f} kg CO2\n({saving_pct:.1f}% weniger Ausstoß!\nÜberlegen Sie umzusteigen. 🌱)")
            else:
                self.lbl_eco_saving.config(text="Klimatipp:\nDies ist bereits eine sehr\numweltschonende Route! 🌱")

    def start_route_animation(self):
        self.animating = True
        self.draw_graph()
        self.animate_step(0)

    def animate_step(self, idx):
        if idx >= len(self.path_edges) or not self.animating:
            self.animating = False
            return
            
        e = self.path_edges[idx]
        from_node = self.path_nodes[idx]
        pt_a = self.get_canvas_coords(from_node)
        to_node = self.path_nodes[idx+1]
        pt_b = self.get_canvas_coords(to_node)
        
        # Highlight path segment actively
        self.canvas.create_line(pt_a[0], pt_a[1], pt_b[0], pt_b[1], fill=self.color_path, width=7, tags="route_anim")
        
        # Draw moving vehicle pulse
        self.draw_pulse(pt_a, pt_b, 0)
        
        # Delay before calculating the next leg
        self.root.after(220, lambda: self.animate_step(idx + 1))

    def draw_pulse(self, pt_a, pt_b, step):
        if step > 5:
            self.canvas.delete("pulse_dot")
            return
        t = step / 5.0
        x = pt_a[0] + (pt_b[0] - pt_a[0]) * t
        y = pt_a[1] + (pt_b[1] - pt_a[1]) * t
        
        self.canvas.delete("pulse_dot")
        self.canvas.create_oval(x-7, y-7, x+7, y+7, fill="#FFFFFF", outline=self.color_path, width=3, tags="pulse_dot")
        
        self.root.after(35, lambda: self.draw_pulse(pt_a, pt_b, step + 1))

    def center_map(self):
        if self.animating:
            return
        self.zoom_factor = 1.0
        self.canvas.xview_moveto(0.0)
        self.canvas.yview_moveto(0.0)
        self.canvas.configure(scrollregion=(0, 0, 1000, 600))
        self.draw_graph()

    def on_canvas_zoom(self, event):
        if self.animating:
            return
        factor = 1.1 if event.delta > 0 else 0.9
        self.zoom_factor *= factor
        if not (0.5 <= self.zoom_factor <= 3.0):
            self.zoom_factor /= factor
            return
        self.canvas.scale("all", event.x, event.y, factor, factor)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def apply_zoom(self):
        self.canvas.configure(scrollregion=(0, 0, int(1000 * self.zoom_factor), int(600 * self.zoom_factor)))
