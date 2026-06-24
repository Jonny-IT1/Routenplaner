import tkinter as tk
from tkinter import ttk, messagebox
import heapq
import os
import json
import math

class Node:
    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y

class Edge:
    def __init__(self, node_a, node_b, distance_km, speed_limit_kmh, has_vignette=False, traffic_jam=False, traffic_risk=0.0):
        self.node_a = node_a
        self.node_b = node_b
        self.distance = distance_km
        self.speed_limit = speed_limit_kmh
        self.has_vignette = has_vignette
        self.traffic_jam = traffic_jam
        self.traffic_risk = traffic_risk  # 0.0 to 1.0

# Predefined graph data representing Austria's highway and road network
CITIES = {
    "Bregenz": Node("Bregenz", 80, 300),
    "Innsbruck": Node("Innsbruck", 200, 320),
    "Lienz": Node("Lienz", 300, 420),
    "Salzburg": Node("Salzburg", 400, 200),
    "Liezen": Node("Liezen", 520, 260),
    "Villach": Node("Villach", 500, 420),
    "Klagenfurt": Node("Klagenfurt", 580, 420),
    "Wels": Node("Wels", 530, 160),
    "Linz": Node("Linz", 590, 140),
    "St. Pölten": Node("St. Pölten", 730, 160),
    "Wien": Node("Wien", 840, 160),
    "Eisenstadt": Node("Eisenstadt", 880, 220),
    "Graz": Node("Graz", 700, 330),
    "Bruck an der Mur": Node("Bruck an der Mur", 690, 250),
}

EDGES = [
    Edge("Bregenz", "Innsbruck", 130, 100, has_vignette=True),
    Edge("Innsbruck", "Lienz", 180, 80, has_vignette=False),
    Edge("Innsbruck", "Salzburg", 185, 130, has_vignette=True),
    Edge("Lienz", "Villach", 110, 80, has_vignette=False),
    Edge("Salzburg", "Wels", 100, 130, has_vignette=True),
    Edge("Salzburg", "Liezen", 120, 100, has_vignette=True),
    Edge("Wels", "Linz", 30, 130, has_vignette=True),
    Edge("Wels", "Liezen", 80, 100, has_vignette=True),
    Edge("Liezen", "Graz", 130, 100, has_vignette=True),
    Edge("Liezen", "Bruck an der Mur", 90, 100, has_vignette=False),
    Edge("Liezen", "Villach", 130, 100, has_vignette=True),
    Edge("Villach", "Klagenfurt", 40, 130, has_vignette=True),
    Edge("Klagenfurt", "Graz", 140, 130, has_vignette=True),
    Edge("Graz", "Bruck an der Mur", 55, 130, has_vignette=True),
    Edge("Bruck an der Mur", "St. Pölten", 110, 80, has_vignette=False),
    Edge("Linz", "St. Pölten", 125, 130, has_vignette=True, traffic_risk=0.3),
    Edge("St. Pölten", "Wien", 65, 130, has_vignette=True, traffic_jam=True),
    Edge("Wien", "Eisenstadt", 60, 130, has_vignette=True),
    Edge("Wien", "Graz", 200, 130, has_vignette=True, traffic_risk=0.15),
    Edge("Eisenstadt", "Graz", 170, 100, has_vignette=False),
]

def calculate_cost(edge, mode, avoid_vignette, avoid_traffic):
    if mode == "Shortest":
        cost = edge.distance
        if avoid_vignette and edge.has_vignette:
            cost += 500.0  # Large virtual penalty
        if avoid_traffic:
            traffic_penalty = 0.0
            if edge.traffic_jam:
                traffic_penalty += 150.0
            traffic_penalty += edge.traffic_risk * 75.0
            cost += traffic_penalty
        return cost
    else:  # Fastest
        base_time = edge.distance / edge.speed_limit
        traffic_mult = 1.0
        if edge.traffic_jam:
            traffic_mult += 2.0  # Triples time if active traffic jam
        if avoid_traffic:
            traffic_mult += edge.traffic_risk * 1.5
            
        time = base_time * traffic_mult
        
        if avoid_vignette and edge.has_vignette:
            time += 5.0  # Add 5 hours virtual penalty
        return time

def dijkstra(start_name, end_name, mode="Fastest", avoid_vignette=False, avoid_traffic=False):
    # Build adjacency list
    adj = {name: [] for name in CITIES}
    for edge in EDGES:
        cost = calculate_cost(edge, mode, avoid_vignette, avoid_traffic)
        adj[edge.node_a].append((edge.node_b, cost, edge))
        adj[edge.node_b].append((edge.node_a, cost, edge))
        
    queue = [(0.0, start_name, [], [])]
    visited = set()
    
    while queue:
        cost, current, path_nodes, path_edges = heapq.heappop(queue)
        
        if current == end_name:
            return cost, path_nodes + [current], path_edges
            
        if current in visited:
            continue
        visited.add(current)
        
        for neighbor, edge_cost, edge in adj[current]:
            if neighbor not in visited:
                heapq.heappush(queue, (cost + edge_cost, neighbor, path_nodes + [current], path_edges + [edge]))
                
    return None, None, None

def save_route_to_files(start, dest, mode, avoid_vignette, avoid_traffic, path_nodes, path_edges):
    os.makedirs("data", exist_ok=True)
    
    if not path_nodes:
        # Save empty/no route state
        no_route_data = {
            "start": start,
            "destination": dest,
            "mode": mode,
            "avoid_vignette": avoid_vignette,
            "avoid_traffic": avoid_traffic,
            "path_found": False
        }
        with open("data/weg.json", "w", encoding="utf-8") as f:
            json.dump(no_route_data, f, indent=4, ensure_ascii=False)
        with open("data/weg.txt", "w", encoding="utf-8") as f:
            f.write(f"Start: {start}\nZiel: {dest}\nKein Weg gefunden!\n")
        return

    total_dist = sum(edge.distance for edge in path_edges)
    actual_time_hours = 0.0
    vignette_count = 0
    traffic_jams_count = 0
    
    for edge in path_edges:
        leg_time = edge.distance / edge.speed_limit
        if edge.traffic_jam:
            leg_time *= 3.0
        actual_time_hours += leg_time
        if edge.has_vignette:
            vignette_count += 1
        if edge.traffic_jam:
            traffic_jams_count += 1
            
    hours = int(actual_time_hours)
    minutes = int(round((actual_time_hours - hours) * 60))
    if minutes == 60:
        hours += 1
        minutes = 0
        
    time_str = f"{hours} Std. {minutes} Min." if hours > 0 else f"{minutes} Min."
    
    # Save JSON file
    data_json = {
        "start": start,
        "destination": dest,
        "mode": mode,
        "avoid_vignette": avoid_vignette,
        "avoid_traffic": avoid_traffic,
        "path_found": True,
        "total_distance_km": total_dist,
        "actual_time_hours": actual_time_hours,
        "actual_time_formatted": time_str,
        "vignette_needed": vignette_count > 0,
        "vignette_roads_count": vignette_count,
        "traffic_jams_encountered": traffic_jams_count,
        "route": path_nodes,
        "legs": [
            {
                "from": edge.node_a if path_nodes[i] == edge.node_a else edge.node_b,
                "to": edge.node_b if path_nodes[i] == edge.node_a else edge.node_a,
                "distance_km": edge.distance,
                "speed_limit_kmh": edge.speed_limit,
                "vignette": edge.has_vignette,
                "traffic_jam": edge.traffic_jam,
                "traffic_risk": edge.traffic_risk
            }
            for i, edge in enumerate(path_edges)
        ]
    }
    
    with open("data/weg.json", "w", encoding="utf-8") as f:
        json.dump(data_json, f, indent=4, ensure_ascii=False)
        
    # Save Human-readable TXT file
    with open("data/weg.txt", "w", encoding="utf-8") as f:
        f.write("==================================================\n")
        f.write("               ROUTENBERECHNUNG                   \n")
        f.write("==================================================\n")
        f.write(f"Startpunkt:       {start}\n")
        f.write(f"Zielpunkt:        {dest}\n")
        f.write(f"Optimierung:      {'Schnellste Route' if mode == 'Fastest' else 'Kürzeste Route'}\n")
        f.write(f"Vignette meiden:  {'Ja' if avoid_vignette else 'Nein'}\n")
        f.write(f"Stau meiden:      {'Ja' if avoid_traffic else 'Nein'}\n")
        f.write("--------------------------------------------------\n")
        f.write(f"Wegstrecke:       {' -> '.join(path_nodes)}\n")
        f.write(f"Gesamtdistanz:    {total_dist:.1f} km\n")
        f.write(f"Reisezeit:        {time_str}\n")
        f.write(f"Maut/Vignette:    {'Ja' if vignette_count > 0 else 'Nein'} ({vignette_count} Abschnitt(e))\n")
        f.write(f"Staus auf Route:  {traffic_jams_count}\n")
        f.write("--------------------------------------------------\n")
        f.write("Wegbeschreibung:\n")
        for i, edge in enumerate(path_edges):
            from_n = edge.node_a if path_nodes[i] == edge.node_a else edge.node_b
            to_n = edge.node_b if path_nodes[i] == edge.node_a else edge.node_a
            leg_t = edge.distance / edge.speed_limit
            if edge.traffic_jam:
                leg_t *= 3.0
            leg_m = int(round(leg_t * 60))
            v_info = " [Vignette]" if edge.has_vignette else ""
            t_info = " [STAU!]" if edge.traffic_jam else ""
            f.write(f"  * {from_n} -> {to_n}: {edge.distance} km, ca. {leg_m} Min. ({edge.speed_limit} km/h){v_info}{t_info}\n")
        f.write("==================================================\n")

class RouteFinderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Antigravity Route Finder")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 650)
        
        # Application state
        self.start_city = "Wien"
        self.dest_city = "Bregenz"
        self.selected_edge = None
        
        self.path_nodes = []
        self.path_edges = []
        
        # Panning & Zooming attributes
        self.zoom_factor = 1.0
        self.pan_start_x = 0
        self.pan_start_y = 0
        
        # Styling Setup (Modern Dark Theme)
        self.bg_dark = "#1E1E24"
        self.bg_sidebar = "#2B2D42"
        self.bg_card = "#3F4257"
        self.fg_white = "#EDF2F4"
        self.fg_muted = "#8D99AE"
        
        self.color_normal = "#4A4E69"
        self.color_start = "#3A86C8"      # Blue
        self.color_dest = "#EF233C"       # Red
        self.color_path = "#06D6A0"       # Mint Green
        self.color_vignette = "#FF9F1C"   # Orange
        self.color_traffic = "#D90429"    # Dark Red
        
        self.setup_styles()
        self.create_layout()
        
        # Initial draw and route calculation
        self.calculate_route()
        self.center_map()
        
    def setup_styles(self):
        self.root.configure(bg=self.bg_dark)
        
        style = ttk.Style()
        style.theme_use("clam")
        
        # Frame
        style.configure("TFrame", background=self.bg_dark)
        style.configure("Sidebar.TFrame", background=self.bg_sidebar)
        style.configure("Card.TFrame", background=self.bg_card, borderwidth=1, relief="flat")
        
        # Labels
        style.configure("TLabel", background=self.bg_dark, foreground=self.fg_white, font=("Segoe UI", 10))
        style.configure("Sidebar.TLabel", background=self.bg_sidebar, foreground=self.fg_white, font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=self.bg_card, foreground=self.fg_white, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=self.bg_sidebar, foreground=self.fg_white, font=("Segoe UI", 14, "bold"))
        style.configure("Header.TLabel", background=self.bg_card, foreground=self.color_path, font=("Segoe UI", 11, "bold"))
        
        # Buttons
        style.configure("TButton", font=("Segoe UI", 10, "bold"), background=self.color_normal, foreground=self.fg_white, borderwidth=0, focuscolor=self.bg_dark)
        style.map("TButton",
                  background=[("active", "#5a5e7d"), ("pressed", "#3a3d54")])
        
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), background=self.color_dest, foreground=self.fg_white, borderwidth=0)
        style.map("Action.TButton",
                  background=[("active", "#ff4d5a"), ("pressed", "#bd1e2d")])
                  
        # Combo and Checkboxes
        style.configure("TCombobox", fieldbackground=self.bg_card, background=self.bg_sidebar, foreground=self.fg_white, arrowcolor=self.fg_white)
        style.configure("TCheckbutton", background=self.bg_sidebar, foreground=self.fg_white, font=("Segoe UI", 10))
        style.map("TCheckbutton", background=[("active", self.bg_sidebar)], foreground=[("active", self.fg_white)])
        
        style.configure("TRadiobutton", background=self.bg_sidebar, foreground=self.fg_white, font=("Segoe UI", 10))
        style.map("TRadiobutton", background=[("active", self.bg_sidebar)], foreground=[("active", self.fg_white)])

    def create_layout(self):
        # Config grid layout
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=0)
        self.root.rowconfigure(0, weight=1)
        
        # Map Frame (Left)
        map_frame = ttk.Frame(self.root, padding=5)
        map_frame.grid(row=0, column=0, sticky="nsew")
        map_frame.rowconfigure(0, weight=1)
        map_frame.columnconfigure(0, weight=1)
        
        # Canvas for Drawing Graph
        self.canvas = tk.Canvas(map_frame, bg=self.bg_dark, highlightthickness=1, highlightbackground=self.bg_card)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbars for Canvas
        hbar = ttk.Scrollbar(map_frame, orient="horizontal", command=self.canvas.xview)
        hbar.grid(row=1, column=0, sticky="ew")
        vbar = ttk.Scrollbar(map_frame, orient="vertical", command=self.canvas.yview)
        vbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        
        # Bind canvas mouse actions for scrolling/zooming
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<MouseWheel>", self.on_canvas_zoom)
        self.canvas.bind("<Button-4>", self.on_canvas_zoom)  # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_canvas_zoom)  # Linux scroll down
        
        # Sidebar Frame (Right)
        sidebar = ttk.Frame(self.root, style="Sidebar.TFrame", padding=15, width=360)
        sidebar.grid(row=0, column=1, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(sidebar, text="Österreich Routenplaner", style="Title.TLabel")
        title_label.grid(row=0, column=0, pady=(0, 15), sticky="w")
        
        # Card 1: Start/Dest Selection
        sel_card = ttk.Frame(sidebar, style="Card.TFrame", padding=10)
        sel_card.grid(row=1, column=0, fill="x", pady=(0, 15))
        sel_card.columnconfigure(1, weight=1)
        
        ttk.Label(sel_card, text="Start & Ziel", style="Header.TLabel").grid(row=0, column=0, columnspan=2, pady=(0, 8), sticky="w")
        
        ttk.Label(sel_card, text="Start:", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=5)
        self.start_combo = ttk.Combobox(sel_card, values=list(CITIES.keys()), state="readonly")
        self.start_combo.set(self.start_city)
        self.start_combo.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=5)
        self.start_combo.bind("<<ComboboxSelected>>", self.on_combo_change)
        
        ttk.Label(sel_card, text="Ziel:", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=5)
        self.dest_combo = ttk.Combobox(sel_card, values=list(CITIES.keys()), state="readonly")
        self.dest_combo.set(self.dest_city)
        self.dest_combo.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=5)
        self.dest_combo.bind("<<ComboboxSelected>>", self.on_combo_change)
        
        # Tip label
        tip_lbl = ttk.Label(sidebar, text="💡 Linksklick = Start | Rechtsklick = Ziel\n💡 Straße anklicken zum Bearbeiten", 
                            style="Sidebar.TLabel", font=("Segoe UI", 9, "italic"), foreground=self.fg_muted)
        tip_lbl.grid(row=2, column=0, pady=(0, 15), sticky="w")
        
        # Card 2: Routing preferences
        opt_card = ttk.Frame(sidebar, style="Card.TFrame", padding=10)
        opt_card.grid(row=3, column=0, fill="x", pady=(0, 15))
        
        ttk.Label(opt_card, text="Routen-Optionen", style="Header.TLabel").grid(row=0, column=0, columnspan=2, pady=(0, 8), sticky="w")
        
        self.routing_mode = tk.StringVar(value="Fastest")
        ttk.Radiobutton(opt_card, text="Schnellste Route (Zeit)", variable=self.routing_mode, value="Fastest", command=self.calculate_route, style="TRadiobutton").grid(row=1, column=0, columnspan=2, sticky="w", pady=3)
        ttk.Radiobutton(opt_card, text="Kürzeste Route (Strecke)", variable=self.routing_mode, value="Shortest", command=self.calculate_route, style="TRadiobutton").grid(row=2, column=0, columnspan=2, sticky="w", pady=3)
        
        ttk.Separator(opt_card, orient="horizontal").grid(row=3, column=0, columnspan=2, fill="x", pady=8)
        
        self.avoid_vignette_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_card, text="Vignette vermeiden", variable=self.avoid_vignette_var, command=self.calculate_route, style="TCheckbutton").grid(row=4, column=0, columnspan=2, sticky="w", pady=3)
        
        self.avoid_traffic_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_card, text="Stau / Verkehrsrisiko meiden", variable=self.avoid_traffic_var, command=self.calculate_route, style="TCheckbutton").grid(row=5, column=0, columnspan=2, sticky="w", pady=3)
        
        # Card 3: Route details
        self.stats_card = ttk.Frame(sidebar, style="Card.TFrame", padding=10)
        self.stats_card.grid(row=4, column=0, fill="x", pady=(0, 15))
        self.stats_card.columnconfigure(1, weight=1)
        
        ttk.Label(self.stats_card, text="Routen-Statistik", style="Header.TLabel").grid(row=0, column=0, columnspan=2, pady=(0, 8), sticky="w")
        
        ttk.Label(self.stats_card, text="Distanz:", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=2)
        self.lbl_dist = ttk.Label(self.stats_card, text="-", style="Card.TLabel", font=("Segoe UI", 10, "bold"))
        self.lbl_dist.grid(row=1, column=1, sticky="e", pady=2)
        
        ttk.Label(self.stats_card, text="Reisezeit:", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=2)
        self.lbl_time = ttk.Label(self.stats_card, text="-", style="Card.TLabel", font=("Segoe UI", 10, "bold"))
        self.lbl_time.grid(row=2, column=1, sticky="e", pady=2)
        
        ttk.Label(self.stats_card, text="Mautpflichtig:", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=2)
        self.lbl_toll = ttk.Label(self.stats_card, text="-", style="Card.TLabel", font=("Segoe UI", 10, "bold"))
        self.lbl_toll.grid(row=3, column=1, sticky="e", pady=2)
        
        ttk.Label(self.stats_card, text="Staus auf Route:", style="Card.TLabel").grid(row=4, column=0, sticky="w", pady=2)
        self.lbl_jams = ttk.Label(self.stats_card, text="-", style="Card.TLabel", font=("Segoe UI", 10, "bold"))
        self.lbl_jams.grid(row=4, column=1, sticky="e", pady=2)
        
        # Card 4: Interactive Road Editor
        self.editor_card = ttk.Frame(sidebar, style="Card.TFrame", padding=10)
        self.editor_card.grid(row=5, column=0, fill="x", pady=(0, 15))
        self.editor_card.columnconfigure(0, weight=1)
        self.editor_card.grid_remove()  # Hidden by default
        
        # Legend (At the bottom)
        legend_frame = ttk.Frame(sidebar, style="Sidebar.TFrame")
        legend_frame.grid(row=6, column=0, fill="x", sticky="ew", pady=(10, 0))
        legend_frame.columnconfigure((0,1,2), weight=1)
        
        # Map center and reset buttons
        btn_frame = ttk.Frame(sidebar, style="Sidebar.TFrame")
        btn_frame.grid(row=7, column=0, fill="x", pady=(0, 10), sticky="ew")
        btn_frame.columnconfigure((0,1), weight=1)
        
        ttk.Button(btn_frame, text="Karte zentrieren", command=self.center_map).grid(row=0, column=0, padx=2, sticky="ew")
        ttk.Button(btn_frame, text="Verkehr zurücksetzen", command=self.reset_all_roads).grid(row=0, column=1, padx=2, sticky="ew")

    def draw_graph(self):
        self.canvas.delete("all")
        self.edge_by_line_id = {}
        self.node_by_oval_id = {}
        
        # Draw tech grid in background
        for x in range(0, 1500, 80):
            self.canvas.create_line(x, 0, x, 1000, fill="#252530", width=1, tags="grid")
        for y in range(0, 1000, 80):
            self.canvas.create_line(0, y, 1500, y, fill="#252530", width=1, tags="grid")
            
        # Compile edges on current route for highlight checks
        route_edges_set = set()
        if self.path_edges:
            for edge in self.path_edges:
                route_edges_set.add(edge)
                
        # 1. Draw Edges (Roads)
        for edge in EDGES:
            node_a = CITIES[edge.node_a]
            node_b = CITIES[edge.node_b]
            
            # Determine styling based on state
            is_on_route = edge in route_edges_set
            
            # Base color
            if edge.traffic_jam:
                color = self.color_traffic
                width = 5
            elif edge == self.selected_edge:
                color = "#FFFFFF"
                width = 5
            elif is_on_route:
                color = self.color_path
                width = 6
            elif edge.has_vignette:
                color = self.color_vignette
                width = 3
            else:
                color = self.color_normal
                width = 3
                
            # Draw line
            line_id = self.canvas.create_line(node_a.x, node_a.y, node_b.x, node_b.y, fill=color, width=width, tags="edge")
            self.edge_by_line_id[line_id] = edge
            
            # Additional visual indicators
            if edge.has_vignette and not is_on_route and not edge.traffic_jam and edge != self.selected_edge:
                # Dashed overlay for vignette highways
                self.canvas.create_line(node_a.x, node_a.y, node_b.x, node_b.y, fill="#FFFFFF", width=1, dash=(3, 5), tags="edge_overlay")
                
            if edge.traffic_risk > 0.0 and not edge.traffic_jam:
                # Draw risk outline dots next to the road
                mid_x = (node_a.x + node_b.x) / 2
                mid_y = (node_a.y + node_b.y) / 2
                # Tiny yellow triangle/dot in middle
                self.canvas.create_oval(mid_x-4, mid_y-4, mid_x+4, mid_y+4, fill="#E6C229", outline="", tags="risk_dot")
                
            # Write distance text in the middle
            mid_x = (node_a.x + node_b.x) / 2
            mid_y = (node_a.y + node_b.y) / 2
            # Angle of text
            dx = node_b.x - node_a.x
            dy = node_b.y - node_a.y
            angle = math.degrees(math.atan2(dy, dx))
            if angle > 90: angle -= 180
            elif angle < -90: angle += 180
            
            self.canvas.create_text(mid_x, mid_y - 8, text=f"{edge.distance} km", fill=self.fg_muted, font=("Segoe UI", 8), tags="text")

        # 2. Draw Nodes (Cities)
        for name, node in CITIES.items():
            # Determine color
            if name == self.start_city:
                fill_color = self.color_start
                radius = 12
            elif name == self.dest_city:
                fill_color = self.color_dest
                radius = 12
            elif name in self.path_nodes:
                fill_color = self.color_path
                radius = 9
            else:
                fill_color = "#3A3E5B"
                radius = 8
                
            outline_color = self.fg_white
            outline_w = 2
            
            oval_id = self.canvas.create_oval(node.x - radius, node.y - radius, node.x + radius, node.y + radius, 
                                             fill=fill_color, outline=outline_color, width=outline_w, tags="node")
            self.node_by_oval_id[oval_id] = name
            
            # City Label
            label_y = node.y - radius - 8
            self.canvas.create_text(node.x, label_y, text=name, fill=self.fg_white, font=("Segoe UI", 10, "bold"), tags="text")

        # Bind clicks on nodes
        self.canvas.tag_bind("node", "<Button-1>", self.on_node_left_click)
        self.canvas.tag_bind("node", "<Button-3>", self.on_node_right_click)
        self.canvas.tag_bind("node", "<Double-Button-1>", self.on_node_double_click)
        self.canvas.tag_bind("edge", "<Button-1>", self.on_edge_click)
        
        # Apply scaling zoom factor
        self.apply_zoom()

    def on_combo_change(self, event):
        self.start_city = self.start_combo.get()
        self.dest_city = self.dest_combo.get()
        self.calculate_route()

    def on_node_left_click(self, event):
        item = self.canvas.find_withtag("current")[0]
        node_name = self.node_by_oval_id.get(item)
        if node_name:
            if node_name == self.dest_city:
                messagebox.showwarning("Fehler", "Start und Ziel können nicht gleich sein!")
                return
            self.start_city = node_name
            self.start_combo.set(node_name)
            self.calculate_route()

    def on_node_right_click(self, event):
        item = self.canvas.find_withtag("current")[0]
        node_name = self.node_by_oval_id.get(item)
        if node_name:
            if node_name == self.start_city:
                messagebox.showwarning("Fehler", "Start und Ziel können nicht gleich sein!")
                return
            self.dest_city = node_name
            self.dest_combo.set(node_name)
            self.calculate_route()
            
    def on_node_double_click(self, event):
        item = self.canvas.find_withtag("current")[0]
        node_name = self.node_by_oval_id.get(item)
        if node_name:
            if node_name == self.start_city:
                return
            self.dest_city = node_name
            self.dest_combo.set(node_name)
            self.calculate_route()

    def on_edge_click(self, event):
        item = self.canvas.find_withtag("current")[0]
        edge = self.edge_by_line_id.get(item)
        if edge:
            self.selected_edge = edge
            self.draw_graph()
            self.show_edge_editor(edge)

    def show_edge_editor(self, edge):
        # Clear previous editor contents
        for child in self.editor_card.winfo_children():
            child.destroy()
            
        self.editor_card.grid()  # Show the card
        
        ttk.Label(self.editor_card, text=f"Straße: {edge.node_a} ↔ {edge.node_b}", style="Header.TLabel").grid(row=0, column=0, columnspan=2, pady=(0, 8), sticky="w")
        
        # Info details
        ttk.Label(self.editor_card, text=f"Distanz: {edge.distance} km", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Label(self.editor_card, text=f"Tempolimit: {edge.speed_limit} km/h", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=2)
        
        # Vignette toggle
        self.edit_vignette_var = tk.BooleanVar(value=edge.has_vignette)
        chk_vig = ttk.Checkbutton(self.editor_card, text="Maut/Vignette nötig", variable=self.edit_vignette_var, command=self.save_edge_edits, style="TCheckbutton")
        chk_vig.grid(row=3, column=0, columnspan=2, sticky="w", pady=5)
        
        # Traffic jam toggle
        self.edit_traffic_var = tk.BooleanVar(value=edge.traffic_jam)
        chk_traf = ttk.Checkbutton(self.editor_card, text="Aktiver Stau", variable=self.edit_traffic_var, command=self.save_edge_edits, style="TCheckbutton")
        chk_traf.grid(row=4, column=0, columnspan=2, sticky="w", pady=5)
        
        # Traffic risk slider
        ttk.Label(self.editor_card, text="Staugefahr (Risiko):", style="Card.TLabel").grid(row=5, column=0, sticky="w", pady=(5, 0))
        self.lbl_risk_val = ttk.Label(self.editor_card, text=f"{int(edge.traffic_risk * 100)}%", style="Card.TLabel", font=("Segoe UI", 10, "bold"))
        self.lbl_risk_val.grid(row=5, column=1, sticky="e", pady=(5, 0))
        
        self.edit_risk_slider = ttk.Scale(self.editor_card, from_=0.0, to=1.0, value=edge.traffic_risk, command=self.on_risk_slider_move)
        self.edit_risk_slider.grid(row=6, column=0, columnspan=2, fill="x", pady=(0, 5))
        
        btn_close = ttk.Button(self.editor_card, text="Schließen", command=self.hide_edge_editor)
        btn_close.grid(row=7, column=0, columnspan=2, pady=(10, 0), sticky="ew")

    def on_risk_slider_move(self, val):
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
        # Reset traffic jams and risks to default
        for edge in EDGES:
            edge.traffic_jam = False
            edge.traffic_risk = 0.0
            
        # Re-apply defaults for specific routes
        for edge in EDGES:
            if edge.node_a == "Linz" and edge.node_b == "St. Pölten":
                edge.traffic_risk = 0.3
            elif edge.node_a == "St. Pölten" and edge.node_b == "Wien":
                edge.traffic_jam = True
            elif edge.node_a == "Wien" and edge.node_b == "Graz":
                edge.traffic_risk = 0.15
                
        self.selected_edge = None
        self.editor_card.grid_remove()
        self.calculate_route()

    def calculate_route(self):
        mode = self.routing_mode.get()
        avoid_vignette = self.avoid_vignette_var.get()
        avoid_traffic = self.avoid_traffic_var.get()
        
        cost, self.path_nodes, self.path_edges = dijkstra(
            self.start_city, self.dest_city, mode, avoid_vignette, avoid_traffic
        )
        
        # Save output files (data/weg.txt and data/weg.json)
        save_route_to_files(
            self.start_city, self.dest_city, mode, avoid_vignette, avoid_traffic, self.path_nodes, self.path_edges
        )
        
        # Update UI Stats Card
        if self.path_nodes:
            # Distance
            total_dist = sum(edge.distance for edge in self.path_edges)
            self.lbl_dist.configure(text=f"{total_dist:.1f} km", foreground=self.color_path)
            
            # Time
            actual_time_hours = 0.0
            vignette_needed = False
            traffic_jams_count = 0
            
            for edge in self.path_edges:
                leg_time = edge.distance / edge.speed_limit
                if edge.traffic_jam:
                    leg_time *= 3.0
                actual_time_hours += leg_time
                if edge.has_vignette:
                    vignette_needed = True
                if edge.traffic_jam:
                    traffic_jams_count += 1
                    
            hours = int(actual_time_hours)
            minutes = int(round((actual_time_hours - hours) * 60))
            if minutes == 60:
                hours += 1
                minutes = 0
                
            time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            self.lbl_time.configure(text=time_str, foreground=self.color_path)
            
            # Toll/Vignette
            if vignette_needed:
                self.lbl_toll.configure(text="Ja", foreground=self.color_vignette)
            else:
                self.lbl_toll.configure(text="Nein", foreground="#06D6A0")
                
            # Traffic jams
            if traffic_jams_count > 0:
                self.lbl_jams.configure(text=f"{traffic_jams_count} Stau(s)", foreground=self.color_traffic)
            else:
                self.lbl_jams.configure(text="Freie Fahrt", foreground="#06D6A0")
        else:
            self.lbl_dist.configure(text="-", foreground=self.fg_muted)
            self.lbl_time.configure(text="-", foreground=self.fg_muted)
            self.lbl_toll.configure(text="-", foreground=self.fg_muted)
            self.lbl_jams.configure(text="-", foreground=self.fg_muted)
            
        self.draw_graph()

    # Panning & Zooming Handlers
    def center_map(self):
        self.zoom_factor = 1.0
        self.canvas.xview_moveto(0.0)
        self.canvas.yview_moveto(0.0)
        self.canvas.configure(scrollregion=(0, 0, 1000, 600))
        self.draw_graph()

    def on_canvas_press(self, event):
        # Record mouse positions for drag scroll
        self.canvas.scan_mark(event.x, event.y)
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def on_canvas_drag(self, event):
        # Built-in Tkinter drag scroll
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def on_canvas_zoom(self, event):
        # Calculate scale factor
        if event.num == 4 or event.delta > 0:  # Zoom In
            factor = 1.1
            self.zoom_factor *= 1.1
        elif event.num == 5 or event.delta < 0:  # Zoom Out
            factor = 0.9
            self.zoom_factor *= 0.9
        else:
            return
            
        # Restrict zoom boundaries
        if self.zoom_factor < 0.5:
            self.zoom_factor = 0.5
            return
        if self.zoom_factor > 3.0:
            self.zoom_factor = 3.0
            return
            
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.canvas.scale("all", x, y, factor, factor)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def apply_zoom(self):
        # We handle scaling by multiplying coords directly or using canvas scale
        # Since we redraw the whole graph from scratch coordinates, we apply the zoom factor:
        self.canvas.configure(scrollregion=(0, 0, int(1000 * self.zoom_factor), int(600 * self.zoom_factor)))

if __name__ == "__main__":
    root = tk.Tk()
    app = RouteFinderApp(root)
    root.mainloop()
