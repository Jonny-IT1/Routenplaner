import tkinter as tk
from tkinter import messagebox
import heapq, os, json, hashlib, shutil

# Try loading from the KI folder, otherwise fallback to the old manual dataset and Dijkstra
try:
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    
    from Ki.app import CITIES_GEO, EDGES, a_star, hash_password, reset_data_directory
    
    LON_MIN, LON_MAX = 9.4, 16.8
    LAT_MIN, LAT_MAX = 46.4, 48.5
    
    CITIES = {}
    for name, (lon, lat, _) in CITIES_GEO.items():
        x = 50 + (lon - LON_MIN) / (LON_MAX - LON_MIN) * 900
        y = 600 - 50 - (lat - LAT_MIN) / (LAT_MAX - LAT_MIN) * 500
        CITIES[name] = (int(x), int(y))
        
    def dijkstra(start, dest, mode, avoid_vignette, avoid_traffic, additional_focus="None"):
        return a_star(start, dest, mode, avoid_vignette, avoid_traffic, additional_focus)

except Exception as e:
    # FALLBACK: Use the original manual layout and standard Dijkstra algorithm from fallback module
    from fallback import CITIES, EDGES, dijkstra, hash_password, reset_data_directory

def save_route_to_files(start, dest, mode, avoid_vignette, avoid_traffic, path_nodes, path_edges):
    os.makedirs("data", exist_ok=True)
    if not path_nodes:
        with open("data/weg.txt", "w", encoding="utf-8") as f: f.write("Kein Weg gefunden!\n")
        return
    dist = sum(e.distance for e in path_edges)
    fuel = sum(e.fuel_consumption for e in path_edges)
    elev = sum(e.elevation_diff for e in path_edges)
    eco = sum(e.eco_score for e in path_edges) / len(path_edges)
    time_h = sum((e.distance / e.speed_limit) * (3.0 if e.traffic_jam else 1.0) for e in path_edges)
    time_str = f"{int(time_h)} Std. {int(round((time_h - int(time_h)) * 60))} Min."
    
    # Save JSON
    json_data = {
        "start": start, "destination": dest, "mode": mode, "total_distance_km": dist, "actual_time_formatted": time_str,
        "total_fuel_liters": round(fuel, 1), "total_elevation_gain_m": elev, "average_eco_score": round(eco, 1),
        "route": path_nodes
    }
    with open("data/weg.json", "w", encoding="utf-8") as f: json.dump(json_data, f, indent=4, ensure_ascii=False)
        
    # Save TXT
    with open("data/weg.txt", "w", encoding="utf-8") as f:
        f.write(f"Start: {start} -> Ziel: {dest}\nModus: {mode}\nDistanz: {dist:.1f} km\nZeit: {time_str}\nVerbrauch: {fuel:.1f} L\nHöhenmeter: {elev} m\nEco: {eco:.1f}/10\nRoute: {' -> '.join(path_nodes)}\n")

class RouteFinderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Antigravity Route Finder")
        self.root.geometry("1150x700")
        self.root.configure(bg="#1E1E24")
        
        self.bg_dark, self.bg_sidebar, self.bg_card, self.fg_white = "#1E1E24", "#2B2D42", "#3F4257", "#EDF2F4"
        self.color_start, self.color_dest, self.color_path, self.color_vignette, self.color_traffic = "#3A86C8", "#EF233C", "#06D6A0", "#FF9F1C", "#D90429"
        
        self.start_city, self.dest_city, self.selected_edge = "Wien", "Bregenz", None
        self.path_nodes, self.path_edges = [], []
        self.zoom_factor = 1.0
        self.additional_focus_mode_val = "None"
        
        self.show_login_screen()

    def show_login_screen(self):
        self.login_frame = tk.Frame(self.root, bg=self.bg_dark)
        self.login_frame.pack(expand=True, fill="both")
        
        tk.Label(self.login_frame, text="Anmeldung", bg=self.bg_dark, fg=self.color_path, font=("Segoe UI", 16, "bold")).pack(pady=10)
        form = tk.Frame(self.login_frame, bg=self.bg_sidebar, padx=15, pady=15)
        form.pack(pady=10)
        
        tk.Label(form, text="Username:", bg=self.bg_sidebar, fg=self.fg_white).grid(row=0, column=0, pady=5, sticky="w")
        self.ent_user = tk.Entry(form, bg=self.bg_card, fg=self.fg_white, bd=0)
        self.ent_user.grid(row=0, column=1, pady=5)
        
        tk.Label(form, text="Password:", bg=self.bg_sidebar, fg=self.fg_white).grid(row=1, column=0, pady=5, sticky="w")
        self.ent_pwd = tk.Entry(form, show="*", bg=self.bg_card, fg=self.fg_white, bd=0)
        self.ent_pwd.grid(row=1, column=1, pady=5)
        
        btn_f = tk.Frame(self.login_frame, bg=self.bg_dark)
        btn_f.pack(pady=10)
        tk.Button(btn_f, text="Anmelden", command=self.handle_login, bg=self.color_path, fg=self.bg_dark, bd=0).pack(side="left", padx=5)
        tk.Button(btn_f, text="Registrieren", command=self.handle_register, bg="#4A4E69", fg=self.fg_white, bd=0).pack(side="right", padx=5)
        tk.Button(self.login_frame, text="Daten zurücksetzen (data/ leeren)", command=reset_data_directory, bg=self.color_dest, fg=self.fg_white, bd=0).pack(pady=15)

    def handle_login(self):
        user, pwd = self.ent_user.get().strip(), self.ent_pwd.get()
        if not user or not pwd: return
        cred_path = os.path.join(".venv", "user_credentials.json")
        if not os.path.exists(cred_path): return messagebox.showerror("Fehler", "Keine Benutzer registriert!")
        with open(cred_path, "r", encoding="utf-8") as f: credentials = json.load(f)
        if credentials.get(user) == hash_password(pwd, user):
            self.login_frame.destroy()
            self.create_main_layout()
            self.calculate_route()
            self.center_map()
        else: messagebox.showerror("Fehler", "Falsche Anmeldedaten!")

    def handle_register(self):
        user, pwd = self.ent_user.get().strip(), self.ent_pwd.get()
        if not user or not pwd: return
        cred_path = os.path.join(".venv", "user_credentials.json")
        credentials = {}
        if os.path.exists(cred_path):
            with open(cred_path, "r", encoding="utf-8") as f: credentials = json.load(f)
        if user in credentials: return messagebox.showerror("Fehler", "Bereits vergeben!")
        credentials[user] = hash_password(pwd, user)
        os.makedirs(".venv", exist_ok=True)
        with open(cred_path, "w", encoding="utf-8") as f: json.dump(credentials, f, indent=4)
        messagebox.showinfo("Erfolg", "Registrierung erfolgreich!")

    def create_main_layout(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        map_frame = tk.Frame(self.root, bg=self.bg_dark)
        map_frame.grid(row=0, column=0, sticky="nsew")
        map_frame.rowconfigure(0, weight=1)
        map_frame.columnconfigure(0, weight=1)
        
        self.canvas = tk.Canvas(map_frame, bg=self.bg_dark, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        self.canvas.bind("<ButtonPress-1>", lambda e: self.canvas.scan_mark(e.x, e.y))
        self.canvas.bind("<B1-Motion>", lambda e: self.canvas.scan_dragto(e.x, e.y, gain=1))
        self.canvas.bind("<MouseWheel>", self.on_canvas_zoom)
        
        sidebar = tk.Frame(self.root, bg=self.bg_sidebar, padx=10, pady=10, width=320)
        sidebar.grid(row=0, column=1, sticky="nsew")
        sidebar.grid_propagate(False)
        
        tk.Label(sidebar, text="Österreich Routenplaner", bg=self.bg_sidebar, fg=self.fg_white, font=("Segoe UI", 12, "bold")).pack(pady=5)
        
        # Dropdowns
        self.start_var, self.dest_var = tk.StringVar(value=self.start_city), tk.StringVar(value=self.dest_city)
        tk.Label(sidebar, text="Start:", bg=self.bg_sidebar, fg=self.fg_white).pack(anchor="w")
        tk.OptionMenu(sidebar, self.start_var, *sorted(CITIES.keys()), command=self.on_dropdown_change).pack(fill="x", pady=2)
        tk.Label(sidebar, text="Ziel:", bg=self.bg_sidebar, fg=self.fg_white).pack(anchor="w")
        tk.OptionMenu(sidebar, self.dest_var, *sorted(CITIES.keys()), command=self.on_dropdown_change).pack(fill="x", pady=2)
        
        # Routing Modes OptionMenu
        self.routing_mode = tk.StringVar(value="Fastest")
        modes = {"Schnellste": "Fastest", "Kürzeste": "Shortest", "Kraftstoff": "Fuel", "Eco": "Eco", "Flachste": "Flat"}
        tk.Label(sidebar, text="Optimierung:", bg=self.bg_sidebar, fg=self.fg_white).pack(anchor="w", pady=(10, 0))
        tk.OptionMenu(sidebar, self.routing_mode, *modes.keys(), command=lambda val: self.on_mode_change(modes[val])).pack(fill="x", pady=2)
        
        # Additional Focus Modes
        self.additional_focus_mode = tk.StringVar(value="Keiner")
        add_focus_options = {
            "Keiner": "None",
            "Schnellste": "Fastest",
            "Kürzeste": "Shortest",
            "Kraftstoff": "Fuel",
            "Eco": "Eco",
            "Flachste": "Flat"
        }
        tk.Label(sidebar, text="Zusätzlicher Fokus:", bg=self.bg_sidebar, fg=self.fg_white).pack(anchor="w", pady=(10, 0))
        tk.OptionMenu(sidebar, self.additional_focus_mode, *add_focus_options.keys(), command=lambda val: self.on_add_focus_change(add_focus_options[val])).pack(fill="x", pady=2)
        
        # Checkboxes
        self.avoid_vignette_var, self.avoid_traffic_var = tk.BooleanVar(value=False), tk.BooleanVar(value=True)
        tk.Checkbutton(sidebar, text="Vignette meiden", variable=self.avoid_vignette_var, command=self.calculate_route, bg=self.bg_sidebar, fg=self.fg_white, selectcolor=self.bg_dark).pack(anchor="w", pady=2)
        tk.Checkbutton(sidebar, text="Stau meiden", variable=self.avoid_traffic_var, command=self.calculate_route, bg=self.bg_sidebar, fg=self.fg_white, selectcolor=self.bg_dark).pack(anchor="w", pady=2)
        
        # Stats Label
        self.lbl_stats = tk.Label(sidebar, text="", bg=self.bg_sidebar, fg=self.color_path, justify="left", font=("Segoe UI", 9, "bold"))
        self.lbl_stats.pack(anchor="w", pady=10)
        
        # Editor Card
        self.editor_card = tk.Frame(sidebar, bg=self.bg_card, padx=10, pady=10)
        self.editor_card.pack(fill="x", pady=5)
        self.editor_card.pack_forget()
        
        # Center Buttons
        tk.Button(sidebar, text="Zentrieren", command=self.center_map, bg="#4A4E69", fg=self.fg_white, bd=0).pack(fill="x", side="bottom", pady=2)
        tk.Button(sidebar, text="Verkehr reset", command=self.reset_all_roads, bg="#4A4E69", fg=self.fg_white, bd=0).pack(fill="x", side="bottom", pady=2)

    def draw_graph(self):
        self.canvas.delete("all")
        self.edge_by_line_id, self.node_by_oval_id = {}, {}
        
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
                self.canvas.create_line(pt_a[0], pt_a[1], pt_b[0], pt_b[1], fill="#FFFFFF", width=1, dash=(3, 5))
            if e.traffic_risk > 0.0 and not e.traffic_jam:
                self.canvas.create_oval((pt_a[0]+pt_b[0])/2-4, (pt_a[1]+pt_b[1])/2-4, (pt_a[0]+pt_b[0])/2+4, (pt_a[1]+pt_b[1])/2+4, fill="#E6C229", outline="")
            
            self.canvas.create_text((pt_a[0]+pt_b[0])/2, (pt_a[1]+pt_b[1])/2 - 8, text=f"{e.distance}km", fill=self.fg_white, font=("Segoe UI", 7))

        for name, pt in CITIES.items():
            fill_c = self.color_start if name == self.start_city else (self.color_dest if name == self.dest_city else (self.color_path if name in self.path_nodes else "#3A3E5B"))
            radius = 12 if name in (self.start_city, self.dest_city) else 8
            oval_id = self.canvas.create_oval(pt[0] - radius, pt[1] - radius, pt[0] + radius, pt[1] + radius, fill=fill_c, outline=self.fg_white, width=2, tags="node")
            self.node_by_oval_id[oval_id] = name
            self.canvas.create_text(pt[0], pt[1] - radius - 8, text=name, fill=self.fg_white, font=("Segoe UI", 9, "bold"))

        self.canvas.tag_bind("node", "<Button-1>", lambda ev: self.on_node_click(ev, left=True))
        self.canvas.tag_bind("node", "<Button-3>", lambda ev: self.on_node_click(ev, left=False))
        self.canvas.tag_bind("node", "<Double-Button-1>", lambda ev: self.on_node_click(ev, left=False))
        self.canvas.tag_bind("edge", "<Button-1>", self.on_edge_click)
        self.apply_zoom()

    def on_dropdown_change(self, val):
        self.start_city, self.dest_city = self.start_var.get(), self.dest_var.get()
        self.calculate_route()

    def on_mode_change(self, val):
        self.routing_mode.set(val)
        self.calculate_route()

    def on_add_focus_change(self, val):
        self.additional_focus_mode_val = val
        self.calculate_route()

    def on_node_click(self, event, left):
        item = self.canvas.find_withtag("current")[0]
        name = self.node_by_oval_id.get(item)
        if not name: return
        if left:
            if name == self.dest_city: return
            self.start_city = name
            self.start_var.set(name)
        else:
            if name == self.start_city: return
            self.dest_city = name
            self.dest_var.set(name)
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
        self.editor_card.pack(fill="x", pady=5)
        
        tk.Label(self.editor_card, text=f"{edge.node_a} ↔ {edge.node_b}", bg=self.bg_card, fg=self.color_path, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(self.editor_card, text=f"{edge.distance}km | {edge.speed_limit}km/h | {edge.fuel_consumption}L\n+{edge.elevation_diff}m | Eco: {edge.eco_score}/10", bg=self.bg_card, fg=self.fg_white, justify="left").pack(anchor="w")
        
        self.edit_vignette_var = tk.BooleanVar(value=edge.has_vignette)
        tk.Checkbutton(self.editor_card, text="Maut nötig", variable=self.edit_vignette_var, command=self.save_edge_edits, bg=self.bg_card, fg=self.fg_white, selectcolor=self.bg_sidebar).pack(anchor="w")
        
        self.edit_traffic_var = tk.BooleanVar(value=edge.traffic_jam)
        tk.Checkbutton(self.editor_card, text="Aktiver Stau", variable=self.edit_traffic_var, command=self.save_edge_edits, bg=self.bg_card, fg=self.fg_white, selectcolor=self.bg_sidebar).pack(anchor="w")
        
        tk.Label(self.editor_card, text=f"Staugefahr: {int(edge.traffic_risk*100)}%", bg=self.bg_card, fg=self.fg_white).pack(anchor="w")
        slider = tk.Scale(self.editor_card, from_=0.0, to=1.0, resolution=0.01, orient="horizontal", bg=self.bg_card, fg=self.fg_white, bd=0, highlightthickness=0)
        slider.set(edge.traffic_risk)
        slider.pack(fill="x", pady=2)
        slider.bind("<ButtonRelease-1>", lambda ev: self.on_risk_slider_release(slider.get()))
        tk.Button(self.editor_card, text="Schließen", command=self.hide_edge_editor, bg="#4A4E69", fg=self.fg_white, bd=0).pack(fill="x", pady=2)

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
        for edge in EDGES: edge.traffic_jam, edge.traffic_risk = False, 0.0
        for edge in EDGES:
            if edge.node_a == "Linz" and edge.node_b == "St. Pölten": edge.traffic_risk = 0.3
            elif edge.node_a == "St. Pölten" and edge.node_b == "Wien": edge.traffic_jam = True
            elif edge.node_a == "Wien" and edge.node_b == "Graz": edge.traffic_risk = 0.15
        self.selected_edge = None
        self.editor_card.pack_forget()
        self.calculate_route()

    def calculate_route(self):
        mode, avoid_vignette, avoid_traffic = self.routing_mode.get(), self.avoid_vignette_var.get(), self.avoid_traffic_var.get()
        cost, self.path_nodes, self.path_edges = dijkstra(self.start_city, self.dest_city, mode, avoid_vignette, avoid_traffic, self.additional_focus_mode_val)
        save_route_to_files(self.start_city, self.dest_city, mode, avoid_vignette, avoid_traffic, self.path_nodes, self.path_edges)
        
        if self.path_nodes:
            dist = sum(e.distance for e in self.path_edges)
            fuel = sum(e.fuel_consumption for e in self.path_edges)
            elev = sum(e.elevation_diff for e in self.path_edges)
            eco = sum(e.eco_score for e in self.path_edges) / len(self.path_edges)
            time_h = sum((e.distance / e.speed_limit) * (3.0 if e.traffic_jam else 1.0) for e in self.path_edges)
            time_str = f"{int(time_h)}h {int(round((time_h - int(time_h)) * 60))}m"
            vigs = any(e.has_vignette for e in self.path_edges)
            
            self.lbl_stats.config(text=f"Distanz: {dist:.1f} km\nZeit: {time_str}\nVerbrauch: {fuel:.1f} L\nHöhenmeter: {elev} m\nEco-Score: {eco:.1f}/10\nMaut: {'Ja' if vigs else 'Nein'}")
        else:
            self.lbl_stats.config(text="Keine Route gefunden!")
        self.draw_graph()

    def center_map(self):
        self.zoom_factor = 1.0
        self.canvas.xview_moveto(0.0)
        self.canvas.yview_moveto(0.0)
        self.canvas.configure(scrollregion=(0, 0, 1000, 600))
        self.draw_graph()

    def on_canvas_zoom(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        self.zoom_factor *= factor
        if not (0.5 <= self.zoom_factor <= 3.0):
            self.zoom_factor /= factor
            return
        self.canvas.scale("all", event.x, event.y, factor, factor)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def apply_zoom(self):
        self.canvas.configure(scrollregion=(0, 0, int(1000 * self.zoom_factor), int(600 * self.zoom_factor)))

if __name__ == "__main__":
    root = tk.Tk()
    app = RouteFinderApp(root)
    root.mainloop()
