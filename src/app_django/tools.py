
import math


# ############################################################################ #

_S = 1
_M = _S * 60
_H = _M * 60
_d = _H * 24
_m = _d * 30
_y = _m * 12


def split_seconds(s):
    """
    list(zip(
        'y m d H M S f'.split(' '),
        split_seconds(
            12*30*24*60*60 + 30*24*60*60 + 24*60*60 + 60*60 + 60 + 10 + 0.5
        )
    ))
    [('y', 1), ('m', 1), ('d', 1), ('H', 1), ('M', 1), ('S', 10), ('f', 0.5)]

    list(zip(
        'y m d H M S f'.split(' '),
        split_seconds(time.time())
    ))
    [('y', 50), ('m', 1), ('d', 5), ('H', 17), ('M', 3), ('S', 1), ('f', 0.854)]
    2019-50 = 1969

    """
    # https://pythonworld.ru/moduli/modul-math.html
    assert s > 0, 'not support negative value'

    remainder = s
    result = []
    for _divider in (_y, _m, _d, _H, _M, _S):
        result.append(
            math.floor(remainder / _divider)
        )
        remainder = remainder - (result[-1] * _divider)
    #
    result.append(remainder)
    return result


def print_seconds(s, format='%dd %Hh %Mm '):
    """
         format='%y %m %d %H %M %S %f'
    """
    if s < 0:
        format = '- ' + format
        s = s * -1
    #

    keys = 'y m d H M S f'.split(' ')
    if s == 0:
        vars = {k: 0 for k in keys}
    else:
        vars = dict(zip(keys, split_seconds(s)))
    #

    if '%y' not in format:
        vars['m'] += int(vars['y'] * math.floor(_y/_m))
    #
    if '%m' not in format:
        vars['d'] += int(vars['m'] * math.floor(_m/_d))
    #
    if '%d' not in format:
        vars['H'] += int(vars['d'] * math.floor(_d/_H))
    #
    if '%H' not in format:
        vars['M'] += int(vars['H'] * math.floor(_H/_M))
    #
    if '%M' not in format:
        vars['S'] += int(vars['M'] * math.floor(_M/_S))
    #

    for k in keys:
        format = format.replace('%{}'.format(k), '{%s}' % k)
    #
    return format.format(**vars)


# ############################################################################ #

