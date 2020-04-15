import re, functools

from app import utilities
from app.data.database import DB

class Parser():
    def __init__(self):
        self.equations = {}
        for equation in DB.equations.values():
            self.equations[equation.nid] = self.tokenize(equation.expression)
        
        self.replacement_dict = self.create_replacement_dict()

        for nid in list(self.equations.keys()):
            expression = self.equations[nid]
            self.fix(nid, expression, self.replacement_dict)

        # Now add these equations as local functions
        for nid in self.equations.keys():
            if not nid.startswith('__'):
                setattr(self, nid.lower(), functools.partial(self.equations[nid], self.equations))

    def tokenize(self, s: str) -> str:
        return re.split('([^a-zA-Z_])', s)

    def create_replacement_dict(self):
        dic = {}
        for stat in DB.stats:
            dic[stat.nid] = ("unit.stats['%s']" % stat.nid)
        for nid in self.equations.keys():
            dic[nid] = ("equations['%s'](equations, unit, item, dist)" % nid)
        dic['WEIGHT'] = '(item.weight if item and item.weight else 0)'
        dic['DIST'] = 'dist'
        return dic

    def fix(self, lhs, rhs, dic):
        rhs = [dic.get(n, n) for n in rhs]
        rhs = ''.join(rhs)
        rhs = 'int(%s)' % rhs
        exec("def %s(equations, unit, item=None, dist=0): return %s" % (lhs, rhs), self.equations)

    def get(self, lhs, unit, item=None, dist=0):
        return self.equations[lhs](self.equations, unit, item, dist)

    def get_expression(self, expr, unit):
        # For one time use
        expr = self.tokenize(expr)
        expr = [self.replacement_dict.get(n, n) for n in expr]
        expr = ''.join(expr)
        expr = 'int(%s)' % expr
        return eval(expr)

    def get_range(self, item, unit) -> list:
        # Calc min range
        if utilities.is_int(item.min_range):
            min_range = int(item.min_range)
        else:
            min_range = self.get(item.min_range, unit, item)
        # Calc max range
        if utilities.is_int(item.max_range):
            max_range = int(item.max_range)
        else:
            max_range = self.get(item.max_range, unit, item)
        max_range += item.longshot.value if item.longshot else 0
        return list(range(min_range, max_range + 1))
