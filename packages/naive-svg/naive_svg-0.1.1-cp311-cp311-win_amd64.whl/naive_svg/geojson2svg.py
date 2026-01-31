from __future__ import annotations

import colorsys
import json
import os
import random
from pathlib import Path
from typing import Union

import numpy as np
from pybind11_geobuf import geojson, tf

from naive_svg import SVG, Color

# Type alias for GeoJSON input: either a file path or a FeatureCollection object
GeoJSONInput = Union[str, geojson.FeatureCollection]

# Named colors mapping (subset of CSS named colors)
NAMED_COLORS = {
    "red": (255, 0, 0),
    "green": (0, 128, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "gray": (128, 128, 128),
    "grey": (128, 128, 128),
    "orange": (255, 165, 0),
    "purple": (128, 0, 128),
    "pink": (255, 192, 203),
    "brown": (165, 42, 42),
    "lime": (0, 255, 0),
    "navy": (0, 0, 128),
    "teal": (0, 128, 128),
    "maroon": (128, 0, 0),
    "olive": (128, 128, 0),
    "aqua": (0, 255, 255),
    "silver": (192, 192, 192),
    "fuchsia": (255, 0, 255),
}

# Default paint values
DEFAULT_PAINT = {
    "fill-color": "#4a9e54",
    "opacity": 1.0,
    "line-width": 1.0,
    "line-type": "solid",
    "radius": 5.0,
    "text-color": "#000000",
}


def parse_color(color_str: str) -> Color:
    """
    Parse color string to Color object.
    Supports: '#ff0000', '#f00', 'red', 'blue', etc.
    """
    if not color_str:
        return Color()

    color_str = color_str.strip().lower()

    # Named color
    if color_str in NAMED_COLORS:
        r, g, b = NAMED_COLORS[color_str]
        return Color(r, g, b)

    # Hex color
    if color_str.startswith("#"):
        hex_val = color_str[1:]
        if len(hex_val) == 3:
            # Short form: #f00 -> #ff0000
            r = int(hex_val[0] * 2, 16)
            g = int(hex_val[1] * 2, 16)
            b = int(hex_val[2] * 2, 16)
        elif len(hex_val) == 6:
            r = int(hex_val[0:2], 16)
            g = int(hex_val[2:4], 16)
            b = int(hex_val[4:6], 16)
        else:
            return Color()
        return Color(r, g, b)

    return Color()


def merge_paint(feature_paint: dict, layer_paint: dict) -> dict:
    """
    Merge paint from feature and layer level.
    Priority: feature > layer > default
    """
    result = DEFAULT_PAINT.copy()
    result.update(layer_paint or {})
    result.update(feature_paint or {})
    return result


def apply_line_style(element, paint: dict):
    """Apply line styling to polyline element."""
    color = parse_color(paint.get("fill-color", DEFAULT_PAINT["fill-color"]))
    element.stroke(color)
    element.stroke_width(paint.get("line-width", DEFAULT_PAINT["line-width"]))

    if paint.get("line-type") == "dashed":
        element.dash_array("5,5")

    opacity = paint.get("opacity", 1.0)
    if opacity < 1.0:
        element.attrs(f"stroke-opacity='{opacity}'")

    return element


def apply_polygon_style(element, paint: dict):
    """Apply polygon styling."""
    color = parse_color(paint.get("fill-color", DEFAULT_PAINT["fill-color"]))
    element.fill(color)
    element.stroke(color)
    element.stroke_width(paint.get("line-width", DEFAULT_PAINT["line-width"]))

    opacity = paint.get("opacity", 1.0)
    if opacity < 1.0:
        element.attrs(f"fill-opacity='{opacity}' stroke-opacity='{opacity}'")

    return element


def apply_point_style(element, paint: dict):
    """Apply point (circle) styling."""
    color = parse_color(paint.get("fill-color", DEFAULT_PAINT["fill-color"]))
    element.fill(color)
    element.stroke(color)
    element.stroke_width(0.5)

    opacity = paint.get("opacity", 1.0)
    if opacity < 1.0:
        element.attrs(f"fill-opacity='{opacity}'")

    return element


def add_text_annotation(
    svg, point, properties: dict, paint: dict, fontsize: float = 1.0
):
    """
    Add text annotation based on text-field.
    """
    text_field = paint.get("text-field")
    if not text_field:
        return None

    # Get text value from properties
    text_value = properties.get(text_field)
    if text_value is None:
        return None

    text_color = parse_color(paint.get("text-color", DEFAULT_PAINT["text-color"]))
    text_elem = svg.add_text(point, text=str(text_value), fontsize=fontsize)
    text_elem.fill(text_color)

    return text_elem


def random_stroke():
    h, s, v = random.uniform(0, 1), random.uniform(0.4, 1), random.uniform(0.7, 1)
    r, g, b = (np.array(colorsys.hsv_to_rgb(h, s, v)) * 255).astype(np.uint8)
    return r, g, b


def _load_geojson(input_data: GeoJSONInput) -> geojson.FeatureCollection:
    """
    Load GeoJSON data from file path or return existing FeatureCollection.

    Args:
        input_data: Either a file path (str) or a FeatureCollection object

    Returns:
        FeatureCollection object
    """
    if isinstance(input_data, geojson.FeatureCollection):
        return input_data
    # Load from file path
    fc = geojson.FeatureCollection()
    fc.load(str(input_data))
    return fc


def _get_anchor_from_fc(fc: geojson.FeatureCollection) -> np.ndarray | None:
    """
    Extract first coordinate from FeatureCollection for anchor.

    Args:
        fc: FeatureCollection object

    Returns:
        3D coordinate array [lon, lat, alt] or None if empty
    """
    if len(fc) == 0:
        return None

    feat = fc[0]
    geom = feat.geometry()
    if geom.is_empty():
        return None

    # Get coordinates as numpy array
    arr = geom.as_numpy()
    if arr is None or len(arr) == 0:
        return None

    # Get first coordinate
    c = arr if arr.ndim == 1 else arr[0]

    # Ensure 3D
    return np.array([c[0], c[1], 0.0]) if len(c) == 2 else np.array(c[:3])


def geojson_to_enu(
    input_data: GeoJSONInput,
    *,
    anchor: np.ndarray | list | None = None,
    inplace: bool = False,
) -> geojson.FeatureCollection:
    """
    Convert GeoJSON coordinates from WGS84 (lon, lat, alt) to ENU coordinates.

    Args:
        input_data: Either a file path (str) or a FeatureCollection object
        anchor: Anchor point [lon, lat, alt] for ENU conversion. If None, uses
                the first coordinate of the first feature.
        inplace: If True, modify the input FeatureCollection in place (only works
                 when input_data is a FeatureCollection). If False, returns a clone.

    Returns:
        FeatureCollection with ENU coordinates
    """
    fc = _load_geojson(input_data)

    # Clone if not inplace or if input was a file path
    if not inplace or isinstance(input_data, str):
        fc = fc.clone()

    # Determine anchor
    if anchor is None:
        anchor_arr = _get_anchor_from_fc(fc)
        if anchor_arr is None:
            return fc  # Empty collection
    else:
        anchor_arr = np.array(anchor)
        if len(anchor_arr) == 2:
            anchor_arr = np.array([anchor_arr[0], anchor_arr[1], 0.0])

    # Convert each feature's coordinates
    for feat in fc:
        geom = feat.geometry()
        if geom.is_empty():
            continue

        llas = geom.as_numpy()
        if llas is None or len(llas) == 0:
            continue

        # Ensure 3D
        if llas.shape[1] == 2:
            llas = np.hstack([llas, np.zeros((len(llas), 1))])

        # Convert to ENU
        enus = tf.lla2enu(llas, anchor_lla=anchor_arr)
        geom.from_numpy(enus)

    return fc


def geojson_to_wgs84(
    input_data: GeoJSONInput,
    *,
    anchor: np.ndarray | list,
    inplace: bool = False,
) -> geojson.FeatureCollection:
    """
    Convert GeoJSON coordinates from ENU to WGS84 (lon, lat, alt) coordinates.

    Args:
        input_data: Either a file path (str) or a FeatureCollection object with ENU coordinates
        anchor: Anchor point [lon, lat, alt] used for the original ENU conversion.
                This is required to correctly convert back to WGS84.
        inplace: If True, modify the input FeatureCollection in place (only works
                 when input_data is a FeatureCollection). If False, returns a clone.

    Returns:
        FeatureCollection with WGS84 coordinates
    """
    fc = _load_geojson(input_data)

    # Clone if not inplace or if input was a file path
    if not inplace or isinstance(input_data, str):
        fc = fc.clone()

    # Prepare anchor
    anchor_arr = np.array(anchor)
    if len(anchor_arr) == 2:
        anchor_arr = np.array([anchor_arr[0], anchor_arr[1], 0.0])

    # Convert each feature's coordinates
    for feat in fc:
        geom = feat.geometry()
        if geom.is_empty():
            continue

        enus = geom.as_numpy()
        if enus is None or len(enus) == 0:
            continue

        # Ensure 3D
        if enus.shape[1] == 2:
            enus = np.hstack([enus, np.zeros((len(enus), 1))])

        # Convert to WGS84
        llas = tf.enu2lla(enus, anchor_lla=anchor_arr)
        geom.from_numpy(llas)

    return fc


def _process_feature(
    svg,
    feature_data: dict,
    anchor: np.ndarray,
    paint: dict,
    with_label: bool,
    idx: int,
    use_feature_style: bool,
    is_enu: bool = False,
) -> tuple:
    """
    Process a single GeoJSON feature and add it to SVG.
    Returns (enus_min, enus_max) for bbox calculation.
    """
    geom = feature_data.get("geometry", {})
    geom_type = geom.get("type", "")
    coords = geom.get("coordinates", [])
    props = feature_data.get("properties", {})

    if not coords:
        return None, None

    # Handle different geometry types
    if geom_type == "Point":
        llas = np.array([coords])
    elif geom_type in ("MultiPoint", "LineString"):
        llas = np.array(coords)
    elif geom_type == "MultiLineString":
        # Process each line separately
        emin, emax = None, None
        for line_coords in coords:
            sub_feature = {
                "geometry": {"type": "LineString", "coordinates": line_coords},
                "properties": props,
            }
            sub_min, sub_max = _process_feature(
                svg,
                sub_feature,
                anchor,
                paint,
                with_label,
                idx,
                use_feature_style,
                is_enu,
            )
            if sub_min is not None:
                if emin is None:
                    emin, emax = sub_min, sub_max
                else:
                    emin = np.minimum(emin, sub_min)
                    emax = np.maximum(emax, sub_max)
        return emin, emax
    elif geom_type == "Polygon":
        # Use the outer ring (first ring)
        llas = np.array(coords[0]) if coords else np.array([])
    elif geom_type == "MultiPolygon":
        # Process each polygon separately
        emin, emax = None, None
        for poly_coords in coords:
            sub_feature = {
                "geometry": {"type": "Polygon", "coordinates": poly_coords},
                "properties": props,
            }
            sub_min, sub_max = _process_feature(
                svg,
                sub_feature,
                anchor,
                paint,
                with_label,
                idx,
                use_feature_style,
                is_enu,
            )
            if sub_min is not None:
                if emin is None:
                    emin, emax = sub_min, sub_max
                else:
                    emin = np.minimum(emin, sub_min)
                    emax = np.maximum(emax, sub_max)
        return emin, emax
    else:
        return None, None

    if len(llas) == 0:
        return None, None

    # Ensure 3D coordinates (lon, lat, alt)
    if llas.ndim == 1:
        llas = llas.reshape(1, -1)
    if llas.shape[1] == 2:
        llas = np.hstack([llas, np.zeros((len(llas), 1))])

    # Convert to ENU coordinates
    enus = llas if is_enu else tf.lla2enu(llas, anchor_lla=anchor)

    # Draw geometry
    if geom_type == "Point":
        radius = paint.get("radius", DEFAULT_PAINT["radius"])
        circle = svg.add_circle(enus[0, :2], r=radius)
        if use_feature_style:
            apply_point_style(circle, paint)
        else:
            r, g, b = random_stroke()
            circle.fill(Color(r, g, b))

        # Add text annotation if text-field is specified
        if use_feature_style:
            add_text_annotation(svg, enus[0, :2], props, paint, fontsize=radius * 2)

    elif geom_type == "MultiPoint":
        radius = paint.get("radius", DEFAULT_PAINT["radius"])
        for pt in enus:
            circle = svg.add_circle(pt[:2], r=radius)
            if use_feature_style:
                apply_point_style(circle, paint)
            else:
                r, g, b = random_stroke()
                circle.fill(Color(r, g, b))

            if use_feature_style:
                add_text_annotation(svg, pt[:2], props, paint, fontsize=radius * 2)

    elif geom_type == "LineString":
        polyline = svg.add_polyline(enus[:, :2])
        if use_feature_style:
            apply_line_style(polyline, paint)
        else:
            r, g, b = random_stroke()
            polyline.stroke(Color(r, g, b)).stroke_width(0.2)

    elif geom_type == "Polygon":
        polygon = svg.add_polygon(enus[:, :2])
        if use_feature_style:
            apply_polygon_style(polygon, paint)
        else:
            r, g, b = random_stroke()
            polygon.stroke(Color(r, g, b)).fill(Color(r, g, b, 0.2)).stroke_width(0.2)

    # Add label if requested
    if with_label and len(enus) > 0:
        fid = props.get("id", f"f#{idx}")
        ftype = props.get("type", "unknown")
        svg.add_text(enus[0, :2], text=str(fid), fontsize=1.0).lines(
            [f"type:{ftype}", f"index={idx}"]
        )

    # Calculate bounding box
    emin = enus.min(axis=0)[:2]
    emax = enus.max(axis=0)[:2]
    return emin, emax


def geojson2svg(
    input_data: GeoJSONInput,
    output_path: str,
    *,
    is_enu: bool = False,
    with_label: bool = False,
    with_grid: bool = True,
    grid_step: float = 100.0,
    use_feature_style: bool = True,
):
    """
    Convert GeoJSON to SVG.

    Args:
        input_data: Path to input GeoJSON file or a FeatureCollection object
        output_path: Path to output SVG file
        is_enu: If True, input coordinates are already in ENU format (skip lla2enu conversion)
        with_label: Whether to add feature labels
        with_grid: Whether to add grid lines
        grid_step: Grid line spacing in meters
        use_feature_style: Whether to use paint styles from features
    """
    # Load data from file or use FeatureCollection directly
    if isinstance(input_data, geojson.FeatureCollection):
        # Convert FeatureCollection to dict for processing
        data = json.loads(input_data.to_rapidjson().dumps())
    else:
        with Path(input_data).open(encoding="utf-8") as f:
            data = json.load(f)

    svg = SVG(-1, -1)
    bbox = None
    anchor = None

    # For is_enu mode, use a dummy anchor since we don't need coordinate conversion
    if is_enu:
        anchor = np.array([0.0, 0.0, 0.0])

    def update_bbox(emin, emax):
        nonlocal bbox
        if emin is None:
            return
        if bbox is None:
            bbox = np.array([*emin, *emax])
        else:
            bbox[:2] = np.minimum(bbox[:2], emin)
            bbox[2:] = np.maximum(bbox[2:], emax)

    def get_anchor_from_feature(feature_data):
        """Extract first coordinate from feature for anchor."""
        geom = feature_data.get("geometry", {})
        coords = geom.get("coordinates", [])
        geom_type = geom.get("type", "")

        if not coords:
            return None

        if geom_type == "Point":
            c = coords
        elif geom_type in ("MultiPoint", "LineString"):
            c = coords[0] if coords else None
        elif geom_type in ("MultiLineString", "Polygon"):
            c = coords[0][0] if coords and coords[0] else None
        elif geom_type == "MultiPolygon":
            c = coords[0][0][0] if coords and coords[0] and coords[0][0] else None
        else:
            return None

        if c is None:
            return None

        # Ensure 3D coordinate
        if len(c) == 2:
            c = [c[0], c[1], 0.0]
        return np.array(c)

    # Check if this is layered GeoJSON format (has 'layers' array)
    if "layers" in data:
        # Layered GeoJSON format
        idx = 0
        for layer in data["layers"]:
            layer_meta = layer.get("meta", {})
            layer_paint = layer_meta.get("paint", {})
            layer_data = layer.get("data", {})
            features = layer_data.get("features", [])

            for feature in features:
                # Merge paint: feature > layer > default
                feature_props = feature.get("properties", {})
                feature_paint = feature_props.get("paint", {})
                merged_paint = merge_paint(feature_paint, layer_paint)

                # Get anchor from first feature
                if anchor is None:
                    anchor = get_anchor_from_feature(feature)

                if anchor is not None:
                    emin, emax = _process_feature(
                        svg,
                        feature,
                        anchor,
                        merged_paint,
                        with_label,
                        idx,
                        use_feature_style,
                        is_enu,
                    )
                    update_bbox(emin, emax)
                idx += 1
    else:
        # Standard GeoJSON format (FeatureCollection or single Feature)
        if data.get("type") == "FeatureCollection":
            features = data.get("features", [])
        elif data.get("type") == "Feature":
            features = [data]
        else:
            features = []

        for idx, feature in enumerate(features):
            feature_props = feature.get("properties", {})
            feature_paint = feature_props.get("paint", {}) if use_feature_style else {}
            merged_paint = merge_paint(feature_paint, {})

            # Get anchor from first feature
            if anchor is None:
                anchor = get_anchor_from_feature(feature)

            if anchor is not None:
                emin, emax = _process_feature(
                    svg,
                    feature,
                    anchor,
                    merged_paint,
                    with_label,
                    idx,
                    use_feature_style,
                    is_enu,
                )
                update_bbox(emin, emax)

    # Handle empty data
    if bbox is None or anchor is None:
        # Create minimal SVG
        svg.width(100).height(100)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        return svg.dump(output_path)

    # Add padding to bbox
    bbox[:2] -= 10.0
    bbox[2:] += 10.0
    width, height = bbox[2:] - bbox[:2]

    svg.width(width).height(height)
    if with_grid:
        svg.grid_step(grid_step)
    svg.view_box([*bbox[:2], width, height])

    # Convert bbox back to lat/lon for metadata (only for WGS84 input)
    if not is_enu:
        llas = tf.enu2lla([[*bbox[:2], 0.0], [*bbox[2:], 0.0]], anchor_lla=anchor)
        llas = llas.round(5)[:, :2]
        svg.attrs(f"bbox='{llas.reshape(-1).tolist()}'")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    return svg.dump(output_path)


if __name__ == "__main__":
    import fire

    fire.core.Display = lambda lines, out: print(*lines, file=out)
    fire.Fire({"geojson2svg": geojson2svg})
