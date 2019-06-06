import overpass
import json
import os.path
import time
import datetime

from helpers import mil

def readjson(filename):
    # extracts list of tuples (lat, lng) from a file
    with open(filename) as json_file:
        data = json.load(json_file)
        timestamp = data['osm3s']['timestamp_osm_base']
        then = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
        delta = datetime.datetime.utcnow() - then
        if delta > datetime.timedelta(hours=24):
            pass
        out = [(e['lat'], e['lon']) for e in data['elements']]
    print("input len:", len(out))
    return out

def bbox(W, S, E, N):
    # queries overpass or returns cached result if available
    fname = f"./in/bbox{mil(W)}_{mil(S)}_{mil(E)}_{mil(N)}.json"
    if os.path.isfile(fname):
        return readjson(fname)
    
    api = overpass.API()
    response = api.get(f"node[\"highway\"=\"street_lamp\"]({S}, {W}, {N}, {E})", responseformat='json')
    with open(fname, 'w') as json_file:
        json.dump(response, json_file)
    out = [(e['lat'], e['lon']) for e in response['elements']]
    print("input len:", len(out))
    return out

def poly(bounds):
    # returns points enclosed by a polygon
    pass

if __name__ == "__main__":
    start = time.time()
    r = bbox(27.4583,53.9621,27.5956,53.9739)
    print(r[:10])
    print("elapsed:", time.time() - start)