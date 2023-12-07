import datetime
import json
import os
import random
import re

import dateutil
import iso8601
import isoduration
import jsonschema
# import these to ensure they're installed so jsonschema will use them
import rfc3339_validator
from dateutil import parser
from dateutil.relativedelta import relativedelta
from generate_data import generate, generate_coord
from json_format import read, save

DIR_SCHEMAS = '../schemas'
DIR_EXAMPLES = "../examples"

FILE_CONDENSED = f'{DIR_EXAMPLES}/example_wx_condensed.geojson'
FILE_UNCOMMENTED = f'{DIR_EXAMPLES}/example_wx_uncommented.geojson'
FILE_MIXED = f'{DIR_EXAMPLES}/example_wx_mixed.geojson'
FILE_DAILY = f'{DIR_EXAMPLES}/example_daily_condensed.geojson'
FILE_FWI_STREAMS = f'{DIR_EXAMPLES}/example_wx_fwi_streams.geojson'
SCHEMA_BASE = f'{DIR_SCHEMAS}/cwfmf.json'
SCHEMA_FWI = f'{DIR_SCHEMAS}/cwfmf_fwi.json'
SCHEMA_FWI_DAILY = f'{DIR_SCHEMAS}/cwfmf_fwi_daily.json'


def parse_duration(duration):
    #    RFC3339
    #    dur-second        = 1*DIGIT "S"
    #    dur-minute        = 1*DIGIT "M" [dur-second]
    #    dur-hour          = 1*DIGIT "H" [dur-minute]
    #    dur-time          = "T" (dur-hour / dur-minute / dur-second)
    #    dur-day           = 1*DIGIT "D"
    #    dur-week          = 1*DIGIT "W"
    #    dur-month         = 1*DIGIT "M" [dur-day]
    #    dur-year          = 1*DIGIT "Y" [dur-month]
    #    dur-date          = (dur-day / dur-month / dur-year) [dur-time]
    #    duration          = "P" (dur-date / dur-time / dur-week)
    # examples:
    #   P5Y2M3W1DT7H3M8S
    #   P5Y2M3W1D
    #   PT7H3M8S
    # techinically not exactly right because you can't have anything after the T if it's not there
    date, time = re.fullmatch("P([^T]*)?T?(.*)?", duration).groups()
    def parse_components(regex, s):
        return [int(x[:-1]) if x else 0 for x in re.fullmatch(regex, s).groups()]
    # don't need to check if date or time are empty since they just match nothing if they area
    years, months, weeks, days = parse_components("(\d+Y)?(\d+M)?(\d+W)?(\d+D)?", date)
    hours, minutes, seconds = parse_components("(\d+H)?(\d+M)?(\d+S)?", time)
    return relativedelta(years=years, months=months, weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)


def parse_intervals(intervals):
    # seems like there should be a standard library for this
    i = []
    for span in intervals.split(","):
        cur = []
        begin, end, duration = span.split("/")
        d = parser.parse(begin)
        e = parser.parse(end)
        delta = parse_duration(duration)
        while d <= e:
            cur.append(d)
            d += delta
        i.append(cur)
    return i


def check_times(src):
    intervals = parse_intervals(src['datetime'])
    assert 1 == len(intervals)
    reference_time = src['time']['since']
    assert reference_time == src['reference-time']
    epoch = parser.parse(reference_time)
    units = parse_duration(src['time']['units'])
    values = [epoch + (x * units) for x in src['time']['values']]
    n = len(values)
    parsed = intervals[0]
    assert n == len(parsed)
    assert values == parsed
    return parsed


def validate(data, file_schema, parent_schema=SCHEMA_BASE):
    return jsonschema.validate(
        data,
        schema=read(file_schema),
        cls=jsonschema.Draft202012Validator,
        format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER,
        resolver=jsonschema.RefResolver(
                f'file:///{os.path.abspath(os.path.dirname(parent_schema))}/',
                                read(parent_schema)))


condensed = read(FILE_CONDENSED)
uncommented = read(FILE_UNCOMMENTED)
mixed = read(FILE_MIXED)
daily = read(FILE_DAILY)
fwi_streams = read(FILE_FWI_STREAMS)

# both formats should validate for the same schema now
validate(condensed, SCHEMA_BASE)
validate(condensed, SCHEMA_FWI)
validate(uncommented, SCHEMA_BASE)
validate(uncommented, SCHEMA_FWI)
validate(mixed, SCHEMA_BASE)
validate(mixed, SCHEMA_FWI)
validate(fwi_streams, SCHEMA_FWI)
validate(daily, SCHEMA_BASE)
validate(daily, SCHEMA_FWI)
validate(daily, SCHEMA_FWI_DAILY)


def randomize_wx():
    # want to make 'realistic' weather
    random.seed(0)
    for feature in condensed['features']:
        for source in feature['properties']['data'].keys():
            src = condensed['sources'][source]
            members = src.get('members', [0])
            member = feature['properties']['data'][source][0]
            n = len(check_times(src))
            def gen_member(member):
                return [generate(list(condensed['indices'].keys())[i], n) if isinstance(member[i], list) else None for i in range(len(member))]
            feature['properties']['data'][source] = [gen_member(member) for i in range(len(members))]
    # make sure it's the same for both file formats
    random.seed(0)
    for feature in uncommented['features']:
        for source in feature['properties']['data'].keys():
            src = uncommented['sources'][source]
            n = len(check_times(src))
            members = src.get('members', None)
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


def test_size(fct=None, name=''):
    if fct is not None:
        fct(condensed)
        fct(uncommented)
    randomize_wx()
    suffix = '' if 0 == len(name) else f'_{name}'
    save(condensed, FILE_CONDENSED.replace('.geojson', f'{suffix}.geojson'))
    save(uncommented, FILE_UNCOMMENTED.replace('.geojson', f'{suffix}.geojson'))
    print(summarize(f'condensed {name}', condensed))
    print(summarize(f'uncommmented {name}', uncommented))
    validate(condensed, SCHEMA_BASE)
    validate(uncommented, SCHEMA_BASE)
    validate(condensed, SCHEMA_FWI)
    validate(uncommented, SCHEMA_FWI)



def make_complete(data):
    # try to figure out how much overhead there would be with an actual set of data
    MEMBERS = [str(x) for x in range(40)] + ["control"]
    # just use dump and load to make a deep copy
    NUM_POINTS = 20
    random.seed(0)
    data['sources']['iefs']['members'] = MEMBERS
    pt = json.loads(json.dumps(data['features'][0]))
    def random_pt():
        p = json.loads(json.dumps(pt))
        p['geometry']['coordinates'] = generate_coord()
        return p
    data['features'] = [random_pt() for i in range(NUM_POINTS)]


def make_minimal(data):
    # figure out overhead for really minimal dataset
    data['features'] = [data['features'][0]]
    d = data['features'][0]['properties']['data']
    s = list(d.keys())[0]
    data['features'][0]['properties']['data'] = {s: d[s]}
    data['sources'] = {s: data['sources'][s]}


test_size()
test_size(make_complete, 'complete')
test_size(make_minimal, 'minimal')
