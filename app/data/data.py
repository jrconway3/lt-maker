class data(object):
    """
    Only accepts data points that have nid attribute
    Generally behaves as a list first and a dictionary second
    """

    def __init__(self, vals=None):
        if vals:
            self._list = vals
            self._dict = {val.nid: val for val in vals}
        else:
            self._list = []
            self._dict = {}

    def values(self):
        return self._list

    def keys(self):
        return [val.nid for val in self._list]

    def items(self):
        return [(val.nid, val) for val in self._list]

    def get(self, key, fallback=None):
        return self._dict.get(key, fallback)

    def update_nid(self, val, nid):
        for k, v in self._dict.items():
            if v == val:
                del self._dict[k]
                val.nid = nid
                self._dict[nid] = val
                break

    def change_key(self, old_key, new_key):
        old_value = self._dict[old_key]
        del self._dict[old_key]
        old_value.nid = new_key
        self._dict[new_key] = old_value

    def append(self, val):
        if val.nid not in self._dict:
            self._list.append(val)
            self._dict[val.nid] = val
        # else:
        #     raise KeyError("%s already present in data" % val.nid)

    def delete(self, val):
        # Fails silently
        if val.nid in self._dict:
            self._list.remove(val)
            del self._dict[val.nid]

    def remove_key(self, key):
        val = self._dict[key]
        self._list.remove(val)
        del self._dict[key]

    def pop(self, idx=None):
        if idx is None:
            idx = len(self._list) - 1
        r = self._list.pop(idx)
        del self._dict[r.nid]

    def insert(self, idx, val):
        self._list.insert(idx, val)
        self._dict[val.nid] = val

    def clear(self):
        self._list = []
        self._dict = {}

    def index(self, nid):
        for idx, val in enumerate(self._list):
            if val.nid == nid:
                return idx
        raise ValueError

    # Saving functions
    def save(self):
        return self._list  # Needs to save off a copy!

    def restore(self, vals):
        self.clear()
        for val in vals:
            self.append(val)

    # Magic Methods
    def __repr__(self):
        return repr(self._list)

    def __len__(self):
        return len(self._list)

    def __getitem__(self, idx):
        return self._list[idx]

    def __iter__(self):
        return iter(self._list)

class serial_obj(object):
    def serialize(self):
        s_dict = {}
        for attr in self.__dict__.items():
            name, value = attr
            value = self.serialize_attr(name, value)
            s_dict[name] = value
        return s_dict

    def serialize_attr(self, name, value):
        if isinstance(value, data):
            value = value.save()
        else:  # int, str, float, list, dict
            value = value
        return value

    @classmethod
    def deserialize(cls, s_dict):
        self = cls.__new__(cls)
        for name, value in s_dict.items():
            setattr(self, name, self.deserialize_attr(name, value))
        return self

    def deserialize_attr(self, name,value):
        if isinstance(value, data):
            value = value.restore()
        else:
            value = value
        return value
