import random

# this is probably unneccesary, but want to make fake weather that looks 'reasonable'


def from_previous(n, fct):
    if n < 1:
        raise RuntimeError('Requested empty data array')
    v = [fct()]
    while n > len(v):
        v.append(fct(v[-1]))
    return v


def from_previous_normal(n, mu, sigma, low=None, high=None, precision=1):
    def fct(x=mu):
        # this is getting stupid and complicated, but want to keep things near
        # initial value, so average current and initial
        v = random.normalvariate((x + mu) / 2, sigma)
        if low is not None:
            v = max(low, v)
        if high is not None:
            v = min(high, v)
        return round(v, precision)
    return from_previous(n, fct)


def generate_int(n, initial, sigma, low=None, high=None):
    return [int(x) for x in from_previous_normal(n, initial, sigma, low, high)]


def generate_temp(n, initial=20, sigma=2):
    return from_previous_normal(n, initial, sigma)


def generate_rh(n, initial=50, sigma=5):
    return generate_int(n, initial, sigma, 0, 100)


def generate_ws(n, initial=20, sigma=5):
    return from_previous_normal(n, initial, sigma, 0, 100)


def generate_wd(n, initial=270, sigma=30):
    return [(int(x) % 360) for x in from_previous_normal(n, initial, sigma)]


def generate_prec(n, initial=0, sigma=10):
    return [0.25 * x for x in generate_int(n, initial, sigma, 0)]

GENERATORS = {
    'temp': generate_temp,
    'rh': generate_rh,
    'ws': generate_ws,
    'wd': generate_wd,
    'prec': generate_prec
}


def generate(k, n):
    return GENERATORS[k](n)
