from json_format import read, save

import random
from generate_data import generate

FILE_CONDENSED = '../example_wx_condensed.geojson'
FILE_UNCOMMENTED = '../example_wx_uncommented.geojson'

condensed = read(FILE_CONDENSED)
uncommented = read(FILE_UNCOMMENTED)


def randomize_wx():
    # want to make 'realistic' weather
    random.seed(0)
    for feature in condensed['features']:
        for source, members in feature['properties']['data'].items():
            feature['properties']['data'][source] = [[generate(list(condensed['indices'].keys())[i], len(member[i])) for i in range(len(member))] for member in members]
    # make sure it's the same for both file formats
    random.seed(0)
    for feature in uncommented['features']:
        for source, members in feature['properties']['data'].items():
            def gen_members(member):
                return {k: generate(k, len(member[k])) for k in member.keys()}
            if dict == type(feature['properties']['data'][source]):
                feature['properties']['data'][source] = {k: gen_members(v) for k, v in members.items()}
            else:
                feature['properties']['data'][source] = [gen_members(v) for v in members]


randomize_wx()

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


save(condensed, FILE_CONDENSED)
save(uncommented, FILE_UNCOMMENTED)
