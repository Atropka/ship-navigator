from ports.models import Port, RouteSegment

def create_demo_ports_and_segments():
    Port.objects.all().delete()
    RouteSegment.objects.all().delete()

    # Порты в СПб
    spb_ports = {
        'A': Port.objects.create(name="Порт A", latitude=59.9343, longitude=30.3351),
        'B': Port.objects.create(name="Порт B", latitude=59.9570, longitude=30.3080),
        'C': Port.objects.create(name="Порт C", latitude=59.9420, longitude=30.2500),
        'D': Port.objects.create(name="Порт D", latitude=59.9100, longitude=30.3200),
        'E': Port.objects.create(name="Порт E", latitude=59.9800, longitude=30.3600),
    }

    # Связи между портами (представим как речные маршруты)
    RouteSegment.objects.bulk_create([
        RouteSegment(start_port=spb_ports['A'], end_port=spb_ports['B'], distance=3.2),
        RouteSegment(start_port=spb_ports['B'], end_port=spb_ports['E'], distance=4.5),
        RouteSegment(start_port=spb_ports['A'], end_port=spb_ports['C'], distance=5.0),
        RouteSegment(start_port=spb_ports['C'], end_port=spb_ports['D'], distance=2.7),
        RouteSegment(start_port=spb_ports['D'], end_port=spb_ports['E'], distance=4.0),
        # Обратные направления
        RouteSegment(start_port=spb_ports['B'], end_port=spb_ports['A'], distance=3.2),
        RouteSegment(start_port=spb_ports['E'], end_port=spb_ports['B'], distance=4.5),
    ])

    print("✅ Тестовые порты и маршруты добавлены.")
