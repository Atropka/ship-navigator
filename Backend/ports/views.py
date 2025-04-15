import requests
import json
import math
from typing import List, Tuple, Dict
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from .models import Port, WaterPath
from .serializers import PortSerializer
from collections import defaultdict
import heapq

# Кэш водных путей
_water_paths_cache: List[List[tuple]] = []

# Дополнительные вручную заданные узлы
additional_water_nodes = [
    (59.931320, 30.187563),
    (59.946255, 30.175376),
    (59.869512, 30.215736),
    (59.886023, 30.180421)
]

def fetch_water_paths_from_overpass(lat: float, lon: float, radius: int = 20000) -> List[List[Tuple[float, float]]]:
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    way["waterway"](around:{radius},{lat},{lon});
    (._;>;);
    out body;
    """

    response = requests.post(overpass_url, data={'data': overpass_query})
    if response.status_code != 200:
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
    R = 6371
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def build_graph(paths: List[List[Tuple[float, float]]]) -> Dict[Tuple[float, float], List[Tuple[float, float]]]:
    graph = defaultdict(list)
    for path in paths:
        for i in range(len(path) - 1):
            a, b = path[i], path[i + 1]
            graph[a].append(b)
            graph[b].append(a)
    return graph


def find_nearest_node(point: Tuple[float, float], nodes: List[Tuple[float, float]]) -> Tuple[float, float]:
    return min(nodes, key=lambda n: haversine_distance(point, n))


def find_connected_components(graph: Dict[Tuple[float, float], List[Tuple[float, float]]]) -> List[List[Tuple[float, float]]]:
    visited = set()
    components = []

    def dfs(node, component):
        stack = [node]
        while stack:
            current = stack.pop()
            if current not in visited:
                visited.add(current)
                component.append(current)
                for neighbor in graph.get(current, []):
                    if neighbor not in visited:
                        stack.append(neighbor)

    for node in graph:
        if node not in visited:
            component = []
            dfs(node, component)
            components.append(component)

    return components


def dijkstra(graph: Dict[Tuple[float, float], List[Tuple[float, float]]], start: Tuple[float, float], end: Tuple[float, float]):
    queue = [(0, start, [start])]
    visited = set()

    while queue:
        cost, current, path = heapq.heappop(queue)
        if current in visited:
            continue
        if current == end:
            return path
        visited.add(current)
        for neighbor in graph[current]:
            if neighbor not in visited:
                total_cost = cost + haversine_distance(current, neighbor)
                heapq.heappush(queue, (total_cost, neighbor, path + [neighbor]))
    return []


class PortViewSet(viewsets.ModelViewSet):
    queryset = Port.objects.all()
    serializer_class = PortSerializer


@csrf_exempt
def route_calculation(request):
    global _water_paths_cache

    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed.'}, status=405)

    try:
        data = json.loads(request.body)
        start_port_id = data.get('start_port_id')
        end_port_id = data.get('end_port_id')

        if not start_port_id or not end_port_id:
            return JsonResponse({'error': 'Both start and end port IDs are required.'}, status=400)

        start_port = Port.objects.get(id=start_port_id)
        end_port = Port.objects.get(id=end_port_id)

        if not _water_paths_cache:
            _water_paths_cache = fetch_water_paths_from_overpass(start_port.latitude, start_port.longitude)

        if not _water_paths_cache:
            return JsonResponse({'error': 'No water paths found.'}, status=404)

        all_points = [pt for path in _water_paths_cache for pt in path]
        all_points += additional_water_nodes

        # Построим граф
        full_paths = _water_paths_cache + [[a, b] for a, b in zip(additional_water_nodes, additional_water_nodes[1:])]
        graph = build_graph(full_paths)

        # Находим компоненты графа
        components = find_connected_components(graph)
        if not components:
            return JsonResponse({'error': 'No connected components found in the graph.'}, status=500)

        # Найдём ближайшие водные точки к портам
        start = find_nearest_node((start_port.latitude, start_port.longitude), list(graph.keys()))
        end = find_nearest_node((end_port.latitude, end_port.longitude), list(graph.keys()))

        # Проверяем, что начальная и конечная точки находятся в одном компоненте
        start_component = end_component = None
        for component in components:
            if start in component:
                start_component = component
            if end in component:
                end_component = component

        if start_component != end_component:
            # Ищем альтернативные точки в другом компоненте для одной из точек
            alternative_start = None
            alternative_end = None

            for component in components:
                if start not in component:
                    alternative_start = find_nearest_node((start_port.latitude, start_port.longitude), component)
                if end not in component:
                    alternative_end = find_nearest_node((end_port.latitude, end_port.longitude), component)

            if not alternative_start or not alternative_end:
                return JsonResponse({'error': 'Unable to find valid alternative nodes for route calculation.'}, status=400)

            # Пробуем новый маршрут с альтернативными точками
            route = dijkstra(graph, alternative_start, alternative_end)
            if not route:
                return JsonResponse({'error': 'Маршрут по воде не найден.'}, status=404)

            distance = sum(haversine_distance(route[i], route[i + 1]) for i in range(len(route) - 1))
            return JsonResponse({
                "route_coords": route,
                "distance": distance,
                "points": len(route)
            })

        # Перезапускаем поиск маршрута с оригинальными точками
        route = dijkstra(graph, start, end)

        if not route:
            return JsonResponse({'error': 'Маршрут по воде не найден.'}, status=404)

        distance = sum(haversine_distance(route[i], route[i + 1]) for i in range(len(route) - 1))
        return JsonResponse({
            "route_coords": route,
            "distance": distance,
            "points": len(route)
        })

    except Port.DoesNotExist:
        return JsonResponse({'error': 'Port not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
