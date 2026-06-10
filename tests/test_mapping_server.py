import backend.server as server


def _handler(path):
    handler = object.__new__(server.RobotStationHandler)
    handler.path = path
    return handler


class FakeMappingManager:
    def __init__(self):
        self.read_names = []

    def list_saved_maps(self):
        return {
            "ok": True,
            "code": "MAP-SAVED-LIST",
            "maps": [{"name": "map_a", "sizeBytes": 16, "mtimeMs": 1234}],
        }

    def read_saved_map_frame(self, name):
        self.read_names.append(name)
        return {
            "ok": True,
            "code": "MAP-SAVED-FRAME",
            "body": b"0123456789abcdef",
            "contentType": "application/octet-stream",
            "pointCount": 1,
            "sourcePointCount": 2,
            "strideFloats": 4,
            "fields": ["x", "y", "z", "intensity"],
            "mapName": name,
            "sizeBytes": 16,
            "mtimeMs": 1234,
        }


def test_mapping_maps_endpoint_lists_saved_maps(monkeypatch):
    manager = FakeMappingManager()
    responses = []
    handler = _handler("/api/mapping/maps")
    handler.write_json = lambda payload, status=200, headers=None: responses.append((payload, status))
    monkeypatch.setattr(server, "get_mapping_manager", lambda: manager)

    server.RobotStationHandler.do_GET(handler)

    assert responses == [(manager.list_saved_maps(), 200)]


def test_mapping_saved_map_frame_endpoint_returns_point_cloud_headers(monkeypatch):
    manager = FakeMappingManager()
    responses = []
    handler = _handler("/api/mapping/maps/map_a/frame")
    handler.write_json = lambda payload, status=200, headers=None: responses.append(("json", payload, status))
    handler.write_binary = lambda body, content_type, status=200, headers=None: responses.append(
        ("binary", body, content_type, status, headers)
    )
    monkeypatch.setattr(server, "get_mapping_manager", lambda: manager)

    server.RobotStationHandler.do_GET(handler)

    assert manager.read_names == ["map_a"]
    assert responses[0][0] == "binary"
    assert responses[0][1] == b"0123456789abcdef"
    assert responses[0][2] == "application/octet-stream"
    assert responses[0][4]["X-Robot-Station-PointCloud-Point-Count"] == "1"
    assert responses[0][4]["X-Robot-Station-PointCloud-Source-Point-Count"] == "2"
    assert responses[0][4]["X-Robot-Station-PointCloud-Fields"] == "x,y,z,intensity"
    assert responses[0][4]["X-Robot-Station-Mapping-Map-Size-Bytes"] == "16"
