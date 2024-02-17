import osmnx as ox
import matplotlib.pyplot as plt
import csv
import os

# Получаем граф OpenStreetMap в заданной области
G = ox.graph_from_place("Yakutsk", network_type="drive", simplify=True)

# Создаем папку maps
map_folder = "maps/"
if not os.path.exists(map_folder):
    os.makedirs(map_folder)


class Courier:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def getDistance(self, order):
        start = ox.distance.nearest_nodes(G, X=self.x, Y=self.y)
        dest = ox.distance.nearest_nodes(G, order.x_start, order.y_start)
        # Получаем кратчайшую длину маршрута
        route = ox.shortest_path(G, start, dest, weight="length")
        route_total = [order.route, route]
        edge_lengths = ox.utils_graph.route_to_gdf(G, route)["length"]
        route_length = round(sum(edge_lengths))
        route_length += order.route_length
        return route_total, route_length


class Order:
    def __init__(
        self, x_start: float, y_start: float, x_dest: float, y_dest: float, price: float
    ):
        self.x_start = x_start
        self.y_start = y_start
        self.x_dest = x_dest
        self.y_dest = y_dest
        self.price = price
        self.route, self.route_length = self.get_dist_btw_two_points()

    def get_dist_btw_two_points(self):
        start = ox.distance.nearest_nodes(G, X=self.x_start, Y=self.y_start)
        dest = ox.distance.nearest_nodes(G, X=self.x_dest, Y=self.y_dest)
        # Получаем кратчайшую длину маршрута
        route = ox.shortest_path(G, start, dest, weight="length")
        edge_lengths = ox.utils_graph.route_to_gdf(G, route)["length"]
        route_length = round(sum(edge_lengths))
        return route, route_length


def find_best_couriers(orders_list, couriers_list):
    length_list = []
    for order_index, order in enumerate(orders_list):
        for courier_index, courier in enumerate(couriers_list):
            route_total, length = courier.getDistance(order)
            length_list.append([courier_index, order_index, length, route_total])
    sorted_length_list = sorted(length_list, key=lambda x: (x[2], x[1], x[0]))
    best_couriers = []
    for lengths in sorted_length_list:
        courier_index, order_index, length, route_total = lengths
        courier_found = any(x[0] == courier_index for x in best_couriers)
        order_found = any(y[1] == order_index for y in best_couriers)
        if not courier_found and not order_found:
            best_couriers.append([courier_index, order_index, length, route_total])
    return sorted(best_couriers, key=lambda x: x[0])


# Загружаем данные из csv файла
couriers_list = []
with open("datasets/couriers.csv", newline="") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        x = float(row["x"])
        y = float(row["y"])
        courier = Courier(x, y)
        couriers_list.append(courier)

orders_list = []
with open("datasets/orders.csv", newline="") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        x1 = float(row["x1"])
        y1 = float(row["y1"])
        x2 = float(row["x2"])
        y2 = float(row["y2"])
        price = float(row["price"])
        order = Order(x1, y1, x2, y2, price)
        orders_list.append(order)


for order in orders_list:
    print(
        f"X_a = {order.x_start}, Y_a = {order.y_start}, X_b = {order.x_dest}, Y_b = {order.y_dest}, Расстояние между точками А и B = {order.route_length}"
    )

best_couriers = find_best_couriers(orders_list, couriers_list)
for courier in best_couriers:
    print(
        f"Курьер №{courier[0]} | Заказ №{courier[1]} | Цена заказа {orders_list[courier[1]].price} | Итоговое расстояние {courier[2]} метров"
    )

nodes, edges = ox.graph_to_gdfs(G)
for i, courier in enumerate(best_couriers):
    courier_index, order_index, length, route_total = courier
    gdfs = (ox.utils_graph.route_to_gdf(G, route) for route in route_total)
    m = edges.explore(color="maroon", tiles="cartodbdarkmatter")
    colors = ["yellow", "green"]
    for i, route_edges in enumerate(gdfs):
        m = route_edges.explore(m=m, color=colors[i], style_kwds={"weight": 5})
    m.save(f"maps/courier_{courier_index}_order_{order_index}_path.html")