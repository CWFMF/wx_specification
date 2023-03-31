from json_format import read, save
import json

import random
from generate_data import generate, generate_coord

FILE_CONDENSED = '../example_wx_condensed.geojson'
FILE_UNCOMMENTED = '../example_wx_uncommented.geojson'

condensed = read(FILE_CONDENSED)
uncommented = read(FILE_UNCOMMENTED)


def randomize_wx():
    # want to make 'realistic' weather
    random.seed(0)
    for feature in condensed['features']:
        for source in feature['properties']['data'].keys():
            members = condensed['data'][source].get('members', [0])
            member = feature['properties']['data'][source][0]
            n = len(condensed['data'][source]['time']['values'])
            def gen_member(member):
                return [generate(list(condensed['indices'].keys())[i], n) if isinstance(member[i], list) else None for i in range(len(member))]
            feature['properties']['data'][source] = [gen_member(member) for i in range(len(members))]
    # make sure it's the same for both file formats
    random.seed(0)
    for feature in uncommented['features']:
        for source in feature['properties']['data'].keys():
            n = len(uncommented['data'][source]['time']['values'])
            members = condensed['data'][source].get('members', None)
            def gen_members(member):
                return {k: generate(k, n) for k in member.keys()}
            if members is None:
                member = feature['properties']['data'][source][0]
                feature['properties']['data'][source] = [gen_members(member)]
            else:
                # use first item as template for keys to use for members
                member = list(feature['properties']['data'][source].values())[0]
                feature['properties']['data'][source] = {k: gen_members(member) for k in members}



randomize_wx()

# get indices for a single index for a single point
feature = 0
source = 'idps'
member = 0
index = 'temp'
x = condensed['features'][feature]['properties']['data'][source][member][list(condensed['indices'].keys()).index(index)]
y = uncommented['features'][feature]['properties']['data'][source][member][index]
assert x == y

# get indices for a single index for all points
source = 'idps'
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


def dumps_min(data):
    return json.dumps(data, separators=(',', ':'))


def find_size(data):
    return len(dumps_min(data))


# make an imaginary reference minimum size based on somehow being able
# to just put data in the right order without any keys
def make_min(data):
    if isinstance(data, list):
        return '[' + ','.join([make_min(v) for v in data]) + ']'
    elif isinstance(data, dict):
        # just look at size of data and not keys
        return make_min([v for k, v in data.items() if k != 'type'])
    return dumps_min(data)




def overhead(data):
    # use condensed since it has null values for things where uncommented has no keys
    min_size = len(make_min(condensed))
    return (find_size(data) - min_size) / min_size


def summarize(name, data):
    return(f'Overhead for {name} format is {(overhead(data) * 100):0.2f}%')

print(summarize("condensed", condensed))
print(summarize("uncommented", uncommented))


# try to figure out how much overhead there would be with an actual set of data
MEMBERS = [str(x) for x in range(40)] + ["control"]

condensed['data']['iefs']['members'] = MEMBERS
uncommented['data']['iefs']['members'] = MEMBERS

# just use dump and load to make a deep copy
NUM_POINTS = 20
def randomize_pts(data):
    random.seed(0)
    pt = json.loads(json.dumps(data['features'][0]))
    def random_pt():
        p = json.loads(json.dumps(pt))
        p['geometry']['coordinates'] = generate_coord()
        return p
    data['features'] = [random_pt() for i in range(NUM_POINTS)]

randomize_pts(condensed)
randomize_pts(uncommented)

randomize_wx()

save(condensed, FILE_CONDENSED.replace('.geojson', '_complete.geojson'))
save(uncommented, FILE_UNCOMMENTED.replace('.geojson', '_complete.geojson'))

print(summarize("condensed complete", condensed))
print(summarize("uncommented complete", uncommented))
