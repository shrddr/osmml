import overpass
import json
from math import floor
import os.path

# everything here returns list of tuples (lat, lng)

def readjson(filename):
    with open(filename) as json_file:
        data = json.load(json_file)
        out = [(e['lat'], e['lon']) for e in data['elements']]
    print("input len", len(out))
    return out

def bbox(W, S, E, N):
    iW = floor(W*1000000)
    iS = floor(S*1000000)
    iE = floor(E*1000000)
    iN = floor(N*1000000)
    fname = f"./in/bbox{iW}_{iS}_{iE}_{iN}.json"
    if os.path.isfile(fname):
        return readjson(fname)
    
    api = overpass.API()
    response = api.get(f"node[\"highway\"=\"street_lamp\"]({S}, {W}, {N}, {E})", responseformat='json')
    with open(fname, 'w') as json_file:
        json.dump(response, json_file)
    out = [(e['lat'], e['lon']) for e in response['elements']]
    print("input len", len(out))
    return out

def poly(bounds):
    pass

if __name__ == "__main__":
    start = time.time()
    print(bbox(27.4583,53.9621,27.5956,53.9739))
    print(time.time() - start)