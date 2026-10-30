"""Prepare the municipality GeoJSON used by the application."""
import sys
from shapely.geometry import mapping, shape
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT_ROOT / "data" / "raw" / "tokyo.geojson"
DESTINATION = PROJECT_ROOT / "app" / "data" / "tokyo_simplified.geojson"

EXCLUDED_NAMES = {
    "所属未定地",
    "大島町",
    "利島村",
    "新島村",
    "神津島村",
    "三宅村",
    "御蔵島村",
    "八丈町",
    "青ヶ島村",
    "小笠原村",
}


def _distance_to_segment(point: list[float], start: list[float], end: list[float]) -> float:
    """Return the squared distance from a point to a line segment."""
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    if dx == 0 and dy == 0:
        return (point[0] - start[0]) ** 2 + (point[1] - start[1]) ** 2
    ratio = ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / (dx * dx + dy * dy)
    ratio = max(0.0, min(1.0, ratio))
    projection = [start[0] + ratio * dx, start[1] + ratio * dy]
    return (point[0] - projection[0]) ** 2 + (point[1] - projection[1]) ** 2


def _simplify_line(points: list[list[float]], tolerance: float) -> list[list[float]]:
    """Simplify a line with Ramer-Douglas-Peucker while preserving its endpoints."""
    if len(points) <= 2:
        return points

    largest_distance = tolerance * tolerance
    split_at = 0
    for index in range(1, len(points) - 1):
        distance = _distance_to_segment(points[index], points[0], points[-1])
        if distance > largest_distance:
            largest_distance = distance
            split_at = index

    if split_at == 0:
        return [points[0], points[-1]]
    return (
        _simplify_line(points[: split_at + 1], tolerance)[:-1]
        + _simplify_line(points[split_at:], tolerance)
    )


def _simplify_coordinates(coordinates: Any, tolerance: float) -> Any:
    if not coordinates:
        return coordinates
    if isinstance(coordinates[0][0], (int, float)):
        closed = coordinates[0] == coordinates[-1]
        simplified = _simplify_line(coordinates[:-1] if closed else coordinates, tolerance)
        if closed:
            simplified.append(simplified[0])
        return simplified
    return [_simplify_coordinates(value, tolerance) for value in coordinates]


def _simplify_geometry(geometry: dict[str, Any], tolerance: float) -> dict[str, Any]:
    result = dict(geometry)
    if "coordinates" in result:
        result["coordinates"] = _simplify_coordinates(result["coordinates"], tolerance)
    return result


def prepare_geojson(tolerance: float = 0.0001) -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8-sig"))
    features = [
        {
            **feature,
            "geometry": _simplify_geometry(feature["geometry"], tolerance),
        }
        for feature in source["features"]
        if feature.get("properties", {}).get("ward_ja") not in EXCLUDED_NAMES
    ]
    output = {
        "type": source["type"],
        "crs": source.get("crs"),
        "features": features,
    }
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    DESTINATION.write_text(
        json.dumps(output, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    def main() -> None:
        source = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        project_root = Path(__file__).resolve().parents[1]
        destination = project_root / "app" / "data" / "tokyo_simplified.geojson"

        def round_coordinates(value):
            if isinstance(value, (list, tuple)):
                if value and isinstance(value[0], (int, float)):
                    return [round(number, 5) for number in value]
                return [round_coordinates(item) for item in value]
            return value

        features = []
        for feature in source["features"]:
            properties = feature.get("properties", {})
            if properties.get("code") is None or properties.get("area_ja") == "島嶼部":
                continue

            simplified = shape(feature["geometry"]).simplify(
                0.0005,
                preserve_topology=True,
            )
            geometry = mapping(simplified)
            geometry["coordinates"] = round_coordinates(geometry["coordinates"])
            features.append(
                {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {
                        key: properties.get(key)
                        for key in ("ward_ja", "ward_en", "area_ja", "code")
                    },
                }
            )

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(
                {"type": "FeatureCollection", "features": features},
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
        print(f"{len(features)} features kept; {destination.stat().st_size / 1024:.2f} KB")


    if __name__ == "__main__":
        main()

if __name__ == "__main__":
    prepare_geojson()