import requests
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
import networkx as nx
from .models import Port
import logging
import math
from collections import defaultdict
from typing import List, Tuple
from geopy.distance import geodesic

from .serializers import PortSerializer

logger = logging.getLogger(__name__)

class PortViewSet(viewsets.ModelViewSet):
    queryset = Port.objects.all()
    serializer_class = PortSerializer

# Вручную заданные дополнительные узлы
additional_water_nodes_1 = [
    (59.952857, 30.196559),
    (59.955189, 30.183226),
    (59.946255, 30.175376),
    (59.929382, 30.187150),
    (59.926011, 30.227226),
    (59.918239, 30.255534),
]

additional_water_nodes_2 = [
    (59.869512, 30.215736),
    (59.872049, 30.208534),
    (59.884741, 30.181521),
]

additional_water_nodes_3 = [
    (59.891065, 30.171466),
    (59.927359, 30.187860),
]

def fetch_water_paths_from_overpass(lat: float, lon: float, radius: int = 10000) -> List[List[Tuple[float, float]]]:
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      way["waterway"~"^(river|canal|stream|ditch)$"](around:{radius},{lat},{lon});way["natural"="bay"](around:{radius},{lat},{lon});way["harbour"](around:{radius},{lat},{lon});
    );
    (._;>;);
    out body;
    """
    response = requests.post(overpass_url, data={'data': overpass_query})
    if response.status_code != 200:
        logger.error(f"Overpass API error: status {response.status_code}")
        return []

    data = response.json()
    nodes = {el["id"]: el for el in data["elements"] if el["type"] == "node"}
    ways = [el for el in data["elements"] if el["type"] == "way"]
    water_paths = []
    for way in ways:
        path = []
        for node_id in way.get("nodes", []):
            node = nodes.get(node_id)
            if node and "lat" in node and "lon" in node:
                path.append((node["lat"], node["lon"]))
        if len(path) >= 2:
            water_paths.append(path)

    return water_paths

def haversine_distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, [*a, *b])
    R = 6371  # km
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a_calc = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    return R * 2 * math.atan2(math.sqrt(a_calc), math.sqrt(1 - a_calc))

def build_graph(
    paths: List[List[Tuple[float, float]]],
    additional_nodes_1: List[Tuple[float, float]] = None,
    additional_nodes_2: List[Tuple[float, float]] = None,
    additional_nodes_3: List[Tuple[float, float]] = None
) -> defaultdict:
    graph = defaultdict(list)

    # Строим основной граф из путей
    for path in paths:
        for i in range(len(path) - 1):
            a, b = path[i], path[i + 1]
            if b not in graph[a]:
                graph[a].append(b)
            if a not in graph[b]:
                graph[b].append(a)

    def add_additional_node_chain(graph, nodes):
        for i in range(len(nodes) - 1):
            a, b = nodes[i], nodes[i + 1]
            if b not in graph[a]:
                graph[a].append(b)
            if a not in graph[b]:
                graph[b].append(a)

    # Функция для подключения доп. узлов к основному графу
    def connect_additional_nodes(graph, additional_nodes):
        for add_node in additional_nodes:
            # Добавляем узел в граф, если его нет
            if add_node not in graph:
                graph[add_node] = []
            # Подключаем к ближайшим основным узлам на расстоянии < 500 м
            for main_node in graph:
                if main_node in additional_nodes:
                    continue  # не подключаем к самим себе
                dist = geodesic(add_node, main_node).meters
                if dist < 450:
                    if main_node not in graph[add_node]:
                        graph[add_node].append(main_node)
                    if add_node not in graph[main_node]:
                        graph[main_node].append(add_node)

    # Добавляем цепочки дополнительных узлов
    if additional_nodes_1:
        add_additional_node_chain(graph, additional_nodes_1)
        connect_additional_nodes(graph, additional_nodes_1)

    if additional_nodes_2:
        add_additional_node_chain(graph, additional_nodes_2)
        connect_additional_nodes(graph, additional_nodes_2)

    if additional_nodes_3:
        add_additional_node_chain(graph, additional_nodes_3)
        connect_additional_nodes(graph, additional_nodes_3)

    return graph

def find_nearest_node(point: Tuple[float, float], nodes: List[Tuple[float, float]], graph) -> Tuple[float, float]:
    valid_nodes = [n for n in nodes if len(graph[n]) >= 2 or n == point]
    if not valid_nodes:
        valid_nodes = nodes
    nearest = min(valid_nodes, key=lambda n: haversine_distance(point, n))
    logger.debug(f"Nearest valid node to {point} is {nearest}")
    return nearest

def build_complete_route(graph, start_point, end_point):
    all_nodes = list(graph.keys())

    # Найдем ближайший узел к старту
    nearest_start = find_nearest_node(start_point, all_nodes, graph)

    # Добавляем старт и конец в граф, если их там нет
    if start_point not in graph:
        graph[start_point] = []
    if end_point not in graph:
        graph[end_point] = []

    # Связываем стартовую точку с ближайшим узлом
    if nearest_start != start_point:
        graph[start_point].append(nearest_start)
        graph[nearest_start].append(start_point)

    # Строим граф NetworkX
    G = nx.Graph()
    for node, neighbors in graph.items():
        for nbr in neighbors:
            weight = haversine_distance(node, nbr)
            G.add_edge(node, nbr, weight=weight)

    # Определяем компоненту связности, в которой находится стартовая точка
    components = list(nx.connected_components(G))
    start_component = None
    for comp in components:
        if start_point in comp:
            start_component = comp
            break

    if start_component is None:
        logger.warning("Start point is not connected to any component")
        return []

    # Теперь ищем ближайший узел к конечной точке, но только среди узлов из компоненты стартовой точки
    nearest_end = find_nearest_node(end_point, list(start_component), graph)

    # Связываем конечную точку с найденным ближайшим узлом
    if nearest_end != end_point:
        graph[end_point].append(nearest_end)
        graph[nearest_end].append(end_point)

    # Обновляем граф после добавления конечной точки
    G.add_node(end_point)
    G.add_edge(end_point, nearest_end, weight=haversine_distance(end_point, nearest_end))

    try:
        route = nx.shortest_path(G, source=start_point, target=end_point, weight='weight')
        return route, G
    except nx.NetworkXNoPath:
        logger.warning("No path found between start and end in the same component")
        return []

# Кэш для путей
_water_paths_cache: List[List[Tuple[float, float]]] = []


def directed_edges_from_path(path):
    # Возвращаем множество ориентированных рёбер
    return set((path[i], path[i+1]) for i in range(len(path) - 1))

def find_alternative_routes(G, start, end, optimal_path, min_diff_m=1000, max_alternatives=3):
    alternatives = []
    optimal_length = nx.path_weight(G, optimal_path, weight='weight')
    optimal_edges = directed_edges_from_path(optimal_path)

    try:
        all_paths = nx.shortest_simple_paths(G, source=start, target=end, weight='weight')
        for path in all_paths:
            if path == optimal_path:
                continue

            length = nx.path_weight(G, path, weight='weight')

            # Минимальная разница по длине
            if abs(length - optimal_length) * 1000 < min_diff_m:
                continue

            candidate_edges = directed_edges_from_path(path)

            def is_too_similar(edges_set):
                # Проверяем долю совпадающих рёбер по направлению
                intersection = candidate_edges.intersection(edges_set)
                smaller_len = min(len(candidate_edges), len(edges_set))
                similarity_ratio = len(intersection) / smaller_len if smaller_len > 0 else 0

                # Если совпадает более 80% рёбер - слишком похожие маршруты
                return similarity_ratio > 0.8

            # Сравниваем с оптимальным маршрутом
            if is_too_similar(optimal_edges):
                continue

            # Сравниваем со всеми уже выбранными альтернативами
            if any(is_too_similar(directed_edges_from_path(alt[0])) for alt in alternatives):
                continue

            alternatives.append((path, length))

            if len(alternatives) >= max_alternatives:
                break

    except Exception as e:
        logger.warning(f"Failed to find alternative paths: {e}")

    return alternatives

@csrf_exempt
def route_calculation(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed.'}, status=405)

    try:
        data = json.loads(request.body)
        start_port_id = data.get('start_port_id')
        end_port_id = data.get('end_port_id')

        if not start_port_id or not end_port_id:
            return JsonResponse({'error': 'Start and end port IDs are required.'}, status=400)

        start_port = Port.objects.get(id=start_port_id)
        end_port = Port.objects.get(id=end_port_id)

        global _water_paths_cache
        if not _water_paths_cache:
            logger.info("Fetching water paths from Overpass API")
            _water_paths_cache = fetch_water_paths_from_overpass(start_port.latitude, start_port.longitude)

        graph = build_graph(_water_paths_cache, additional_water_nodes_1, additional_water_nodes_2, additional_water_nodes_3)

        start_point = (float(start_port.latitude), float(start_port.longitude))
        end_point = (float(end_port.latitude), float(end_port.longitude))

        route, G = build_complete_route(graph, start_point, end_point)

        # Расчёт расстояния
        total_distance_km = 0.0
        for i in range(1, len(route)):
            total_distance_km += geodesic(route[i - 1], route[i]).kilometers

        route = nx.shortest_path(G, source=start_point, target=end_point, weight='weight')
        optimal_distance_km = nx.path_weight(G, route, weight='weight')

        # Ищем альтернативные маршруты
        alternatives = find_alternative_routes(G, start_point, end_point, route, min_diff_m=200)

        routes = [{
            'route': [(float(lat), float(lon)) for lat, lon in route],
            'distance_km': round(optimal_distance_km, 2),
            'is_optimal': True
        }]

        for alt_path, alt_len in alternatives:
            routes.append({
                'route': [(float(lat), float(lon)) for lat, lon in alt_path],
                'distance_km': round(alt_len, 2),
                'is_optimal': False
            })

        return JsonResponse({
            'routes': routes,
            'start_port': {
                'id': start_port.id,
                'name': start_port.name,
                'latitude': float(start_port.latitude),
                'longitude': float(start_port.longitude),
            },
            'end_port': {
                'id': end_port.id,
                'name': end_port.name,
                'latitude': float(end_port.latitude),
                'longitude': float(end_port.longitude),
            },
        })
    except Port.DoesNotExist:
        return JsonResponse({'error': 'Port not found.'}, status=404)
    except Exception as e:
        logger.exception("Error during route calculation")
        return JsonResponse({'error': str(e)}, status=500)



def get_current_water_graph_edges(graph):
    edge_list = []
    for a, neighbors in graph.items():
        for b in neighbors:
            # Чтобы не дублировать (a, b) и (b, a)
            if a < b:
                edge_list.append([[a[0], a[1]], [b[0], b[1]]])
    return edge_list

@csrf_exempt
def get_water_graph(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET requests are allowed.'}, status=405)

    try:
        global _water_paths_cache

        # Если кэш пуст, заполняем его (например, по первому порту)
        if not _water_paths_cache:
            first_port = Port.objects.first()
            if not first_port:
                return JsonResponse({'error': 'No ports found in database.'}, status=400)

            logger.info("Fetching water paths from Overpass API in get_water_graph")
            _water_paths_cache = fetch_water_paths_from_overpass(first_port.latitude, first_port.longitude)

        # Строим граф из кэша, без добавления дополнительных узлов
        graph = build_graph(_water_paths_cache, additional_water_nodes_1, additional_water_nodes_2, additional_water_nodes_3)

        # Получаем ребра графа в формате для фронта
        edge_list = get_current_water_graph_edges(graph)
        return JsonResponse({'edges': edge_list})

    except Exception as e:
        logger.exception("Ошибка при получении графа")
        return JsonResponse({'error': str(e)}, status=500)
