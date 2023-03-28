import json


def read(filename):
    with open(filename) as file:
        return json.load(file)


condensed = read('example_wx_condensed.geojson')
uncommented = read('example_wx_uncommented.geojson')

# get indices for a single index for a single point
feature = 0
source = 'geps'
member = 0
index = 'temp'
x = condensed['features'][feature]['properties']['data'][source][member][list(condensed['indices'].keys()).index(index)]
y = uncommented['features'][feature]['properties']['data'][source][member][index]
assert x == y

# get indices for a single index for all points
source = 'geps'
member = 0
index = 'temp'
x = [f['properties']['data'][source][member][list(condensed['indices'].keys()).index(index)] for f in condensed['features']]
y = [f['properties']['data'][source][member][index] for f in uncommented['features']]
assert x == y

# get indices for a single index for all points for all models and members
index = 'temp'
x = [m[list(condensed['indices'].keys()).index(index)] for f in condensed['features'] for source, members in f['properties']['data'].items() for m in members]
y = [m[index] if type(m) == dict else members[m][index] for f in uncommented['features'] for source, members in f['properties']['data'].items() for m in members]
assert x == y
