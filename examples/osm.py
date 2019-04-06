from imposm.parser import OSMParser
from shapely import geometry, ops

import axi
import math
import sys

# put your lat/lng here
LAT, LNG = 42.0000, -71.0000

MAP_WIDTH_KM = 1.61 * 2.0

LANE_WIDTH_M = 3.7
EARTH_RADIUS_KM = 6371

MARGIN = 1.2 # Percentage

WEIGHTS = {
    'motorway': 2,
    'motorway_link': 2,
    'trunk_link': 2,
    'trunk': 2,
    'primary_link': 1.75,
    'primary': 1.75,
    'secondary': 1.5,
    'secondary_link': 1.5,
    'tertiary_link': 1.25,
    'tertiary': 1.25,
    'living_street': 1,
    'unclassified': 1,
    'residential': 1,
    'service': 0,
    'railway': 0,
}

def paths_to_shapely(paths):
    return geometry.MultiLineString(paths)

def shapely_to_paths(g):
    if isinstance(g, geometry.LineString):
        return [list(g.coords)]
    elif isinstance(g, (geometry.MultiLineString, geometry.MultiPolygon, geometry.collection.GeometryCollection)):
        paths = []
        for x in g:
            paths.extend(shapely_to_paths(x))
        return paths
    elif isinstance(g, geometry.Polygon):
        paths = []
        paths.append(list(g.exterior.coords))
        for interior in g.interiors:
            paths.extend(shapely_to_paths(interior))
        return paths
    else:
        raise Exception('unhandled shapely geometry: %s' % type(g))

def crop(g, w, h):
    w *= 0.5
    h *= 0.5
    box = geometry.Polygon([(-w, -h), (w, -h), (w, h), (-w, h)])
    return g.intersection(box)

def box(w, h):
    w *= 0.5
    h *= 0.5
    return [(-w, -h), (w, -h), (w, h), (-w, h), (-w, -h)]

def haversine(lat1, lng1, lat2, lng2):
    lng1, lat1, lng2, lat2 = map(math.radians, [lng1, lat1, lng2, lat2])
    dlng = lng2 - lng1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    return math.asin(math.sqrt(a)) * 2 * EARTH_RADIUS_KM

class LambertAzimuthalEqualAreaProjection(object):
    def __init__(self, lat, lng):
        self.lat = lat
        self.lng = lng
        self.scale = 1
        self.scale = self.kilometer_scale()
    def project(self, lat, lng):
        lng, lat = math.radians(lng), math.radians(lat)
        clng, clat = math.radians(self.lng), math.radians(self.lat)
        k = math.sqrt(2 / (1 + math.sin(clat)*math.sin(lat) + math.cos(clat)*math.cos(lat)*math.cos(lng-clng)))
        x = k * math.cos(lat) * math.sin(lng-clng)
        y = k * (math.cos(clat)*math.sin(lat) - math.sin(clat)*math.cos(lat)*math.cos(lng-clng))
        s = self.scale
        return (x * s, -y * s)
    def kilometer_scale(self):
        e = 1e-3
        lat, lng = self.lat, self.lng
        km_per_lat = haversine(lat - e, lng, lat + e, lng) / (2 * e)
        km_per_lng = haversine(lat, lng - e, lat, lng + e) / (2 * e)
        x1, y1 = self.project(lat - 1 / km_per_lat, lng - 1 / km_per_lng)
        x2, y2 = self.project(lat + 1 / km_per_lat, lng + 1 / km_per_lng)
        sx = 2 / (x2 - x1)
        sy = 2 / (y1 - y2)
        return (sx + sy) / 2

class Handler(object):
    def __init__(self):
        self.coords = {}
        self.ways = {}
    def on_nodes(self, nodes):
        pass
    def on_ways(self, ways):
        for osmid, tags, refs in ways:
            if 'highway' in tags:
                self.ways.setdefault(tags['highway'], []).append(refs)
            if 'railway' in tags:
                self.ways.setdefault('railway', []).append(refs)
    def on_relations(self, relations):
        pass
    def on_coords(self, coords):
        for (osmid, lng, lat) in coords:
            self.coords[osmid] = (lat, lng)

def circle(cx, cy, r, n):
    points = []
    for i in range(n + 1):
        a = 5 * math.pi * i / n
        x = cx + math.cos(a) * r
        y = cy + math.sin(a) * r
        points.append((x, y))
    return points

def main():
    cli = axi.cli()
    cli.add_argument("osm_file", help=".osm map file to read from")
    args = cli.parse_args()

    handler = Handler()
    p = OSMParser(
        concurrency=1,
        nodes_callback=handler.on_nodes,
        ways_callback=handler.on_ways,
        relations_callback=handler.on_relations,
        coords_callback=handler.on_coords)
    p.parse(args.osm_file)

    projection = LambertAzimuthalEqualAreaProjection(LAT, LNG)

    w = MAP_WIDTH_KM
    #h = w * 12 / 8.5
    h = w * args.height / args.width

    gs = []
    for key, ways in handler.ways.items():
        if key not in WEIGHTS:
            continue
        weight = WEIGHTS[key]
        paths = []
        for way in ways:
            coords = [projection.project(*handler.coords[x]) for x in way]
            paths.append(coords)
        g = paths_to_shapely(paths)
        if weight:
            g = g.buffer(LANE_WIDTH_M / 1000.0 * weight)
        g = crop(g, w * MARGIN, h * MARGIN)
        gs.append(g)
    g = ops.cascaded_union(gs)
    g = crop(g, w, h)

    paths = shapely_to_paths(g)
    #paths.append(circle(0, 0, 9 / 1000.0, 1000))
    #paths.append(circle(0, 0, 6 / 1000.0, 1000))
    #paths.append(circle(0, 0, 3 / 1000.0, 1000))

    paths.append(box(w, h))
    paths.append(box(w - 5.0 / 1000, h - 5.0 / 1000))
    paths.append(box(w - 10.0 / 1000, h - 10.0 / 1000))

    d = axi.Drawing(paths)
    cli.draw(d)

if __name__ == '__main__':
    main()
