import functools
import re

def get_next_name(name, names):
    if name not in names:
        return name
    else:
        # Remove the (1) when generating additional names
        name = re.sub(r' \(\d+\)$', '', name)
        counter = 1
        while True:
            test_name = name + (' (%s)' % counter)
            if test_name not in names:
                return test_name
            counter += 1

def get_next_int(name, names):
    if name not in names:
        return name
    else:
        counter = 1
        while True:
            test_name = str(counter)
            if test_name not in names:
                return test_name
            counter += 1

def get_next_generic_nid(name: str, names):
    if name not in names:
        return name
    elif is_int(name):
        counter = int(name) + 1
        while True:
            test_name = str(counter)
            if test_name not in names:
                return test_name
            counter += 1
    else:
        return get_next_name(name, names)

def find_last_number(s: str):
    last_number = re.findall(r'\d+$', s)
    if last_number:
        return int(last_number[-1])
    return None

def get_prefix(s: str):
    last_number = re.findall(r'\d+', s)
    if last_number:
        idx = re.search(r'\d+', s).span(0)[0]
        return s[:idx]
    else:
        idx = s.index('.')
        return s[:idx]

def intify(s: str) -> list:
    vals = s.split(',')
    return [int(i) for i in vals]

def skill_parser(s: str) -> list:
    if s is not None:
        each_skill = [each.split(',') for each in s.split(';')]
        split_line = [[int(s_l[0]), s_l[1]] for s_l in each_skill]
        return split_line
    else:
        return []

def is_int(s: str) -> bool:
    try:
        int(s)
        return True
    except ValueError:
        return False
    except TypeError:
        return False

def is_float(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False
    except TypeError:
        return False

def camel_case(s: str) -> str:
    return functools.reduce(lambda a, b: a + ((b.upper() == b and (a and a[-1].upper() != a[-1])) and (' ' + b) or b), s, '')

def camel_to_snake(name: str) -> str:
    """
    https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
    """
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()    

if __name__ == '__main__':
    print(camel_to_snake("Direction"))
    print(camel_to_snake("EntityID"))
    print(camel_to_snake("Node1"))
    print(camel_to_snake("OverworldNodeNid"))
