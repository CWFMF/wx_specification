import json

class WxEncoder(json.JSONEncoder):
    NOINDENT_ENCODER = json.JSONEncoder()
    def __init__(self, *args, **kwargs):
        kwargs['indent'] = '    '
        super().__init__(*args, **kwargs)
    def encode(self, o, cur_indent=''):
        sub_indent = cur_indent + self.indent
        # Horribly inefficient, but just want it to work for now
        unindented = WxEncoder.NOINDENT_ENCODER.encode(o)
        if 80 >= len(unindented):
            return sub_indent + unindented
        if isinstance(o, list):
            return '[\n' + sub_indent + (',\n' + sub_indent).join([self.encode(p, sub_indent).lstrip(' ') for p in o]) + '\n' + cur_indent + ']'
        elif isinstance(o, dict):
            return ('{\n' + sub_indent
                    + (',\n' + sub_indent).join([(self.encode(k, sub_indent).lstrip(' ') + ': ' + self.encode(v, sub_indent).lstrip(' ')) for k, v in o.items()])
                    + '\n' + cur_indent + '}')
        return super().encode(o)


def read(filename):
    with open(filename) as file:
        return json.load(file)


def save(data, filename):
    with open(filename, 'w') as file:
        file.write(WxEncoder().encode(data) + '\n')

