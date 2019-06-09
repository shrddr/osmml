import overpass
import json
import os.path
import time
import datetime
from math import floor

import helpers
import layers

def mil(fp):
    return floor(fp*1000000)

def query_nodes(W, S, E, N):
    # queries overpass or fetches cached result if available
    # returns list of (lat, lng) tuples
    fname = f"./in/bbox{mil(W)}_{mil(S)}_{mil(E)}_{mil(N)}.json"
    if os.path.isfile(fname):
        with open(fname) as json_file:
            return json.load(json_file)
    
    api = overpass.API()
    query = f"node[\"highway\"=\"street_lamp\"]({S}, {W}, {N}, {E})"
    response = api.get(query, responseformat='json', verbosity='skel')
    
    nodes = [(e['lat'], e['lon']) for e in response['elements']]
    with open(fname, 'w') as json_file:
        json.dump(nodes, json_file)
        
    print("input len:", len(nodes))
    return nodes


def query_ways(W, S, E, N):
    fname = f"./in/ways_bbox{mil(W)}_{mil(S)}_{mil(E)}_{mil(N)}.json"
    if os.path.isfile(fname):
        with open(fname) as json_file:
            return json.load(json_file)
        
    api = overpass.API()
    query = f"""(
        way["highway"="trunk"]({S}, {W}, {N}, {E});
        way["highway"="primary"]({S}, {W}, {N}, {E});
        way["highway"="secondary"]({S}, {W}, {N}, {E});
        way["highway"="tertiary"]({S}, {W}, {N}, {E});
    );
    out skel;
    >;
    out skel;"""
    response = api.get(query, responseformat='json', verbosity='skel')
    
    nodedict = {}
    for e in response['elements']:
        if e['type'] == 'node':
            nodedict[e['id']] = (e['lat'], e['lon'])
    
    ways = {}
    for e in response['elements']:
        if e['type'] == 'way':
            nodes = [nodedict[i] for i in e['nodes']]
            ways[e['id']] = nodes
    
    with open(fname, 'w') as json_file:
        json.dump(ways, json_file)
    
    return ways

def query_poly(bounds):
    # returns points enclosed by a polygon
    # https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL#Polygon_evaluator
    pass
        

if __name__ == "__main__":   
    pass