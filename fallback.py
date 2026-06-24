import heapq, os, json, hashlib, shutil
from tkinter import messagebox

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

def reset_data_directory():
    if os.path.exists("data"):
        for f in os.listdir("data"):
            p = os.path.join("data", f)
            shutil.rmtree(p) if os.path.isdir(p) else os.unlink(p)
        messagebox.showinfo("Erfolg", "Daten gelöscht!")

def calculate_cost(e, mode, avoid_vignette, avoid_traffic, additional_focus="None"):
    costs = {
        "Shortest": e.distance,
        "Fastest": (e.distance / e.speed_limit) * (1.0 + (2.0 if e.traffic_jam else 0.0) + (e.traffic_risk * 1.5 if avoid_traffic else 0.0)),
        "Fuel": e.fuel_consumption,
        "Eco": (11 - e.eco_score) * e.distance,
        "Flat": e.elevation_diff
    }
    cost = costs.get(mode, e.distance)
    if additional_focus and additional_focus != "None":
        sec_cost = costs.get(additional_focus, 0.0)
        cost += 0.5 * sec_cost
        
    if avoid_vignette and e.has_vignette:
        cost += {"Shortest": 500.0, "Fuel": 50.0, "Eco": 5000.0, "Flat": 2000.0}.get(mode, 5.0)
    if avoid_traffic and mode != "Fastest" and additional_focus != "Fastest":
        cost += (150.0 if e.traffic_jam else 0.0) + e.traffic_risk * 75.0
    return cost

def dijkstra(start, dest, mode, avoid_vignette, avoid_traffic, additional_focus="None"):
    adj = {n: [] for n in CITIES}
    for e in EDGES:
        cost = calculate_cost(e, mode, avoid_vignette, avoid_traffic, additional_focus)
        adj[e.node_a].append((e.node_b, cost, e))
        adj[e.node_b].append((e.node_a, cost, e))
        
    q, visited = [(0.0, start, [], [])], set()
    while q:
        cost, curr, path_n, path_e = heapq.heappop(q)
        if curr == dest: return cost, path_n + [curr], path_e
        if curr in visited: continue
        visited.add(curr)
        for neighbor, edge_cost, edge in adj[curr]:
            if neighbor not in visited:
                heapq.heappush(q, (cost + edge_cost, neighbor, path_n + [curr], path_e + [edge]))
    return None, None, None
