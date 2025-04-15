# route_calculator.py
from .models import Port
import networkx as nx  # Для графов


def calculate_route(start_port: Port, end_port: Port):
    # Пример расчёта маршрута
    # Вам нужно построить граф водных путей и найти кратчайший путь

    # Создаём граф
    G = nx.Graph()

    # Добавляем порты как узлы графа
    G.add_node(start_port.id, pos=(start_port.latitude, start_port.longitude))
    G.add_node(end_port.id, pos=(end_port.latitude, end_port.longitude))

    # Пример простого маршрута между двумя портами
    G.add_edge(start_port.id, end_port.id, weight=1)

    # Пример использования алгоритма для нахождения маршрута
    path = nx.shortest_path(G, source=start_port.id, target=end_port.id, weight='weight')

    # Преобразуем путь в координаты для отображения на карте
    route = []
    for node_id in path:
        port = Port.objects.get(id=node_id)
        route.append({"lat": port.latitude, "lon": port.longitude})

    return route
