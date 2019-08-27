def get_next_name(name, names):
    if name not in names:
        return name
    else:
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
