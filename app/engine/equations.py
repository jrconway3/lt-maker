import re, functools

from app.data.database import DB

class Parser():
    def __init__(self):
        self.equations = {}
        for equation in DB.equations:
            self.equations[equation.nid] = self.tokenize(equation.expression)
        
        self.replacement_dict = self.create_replacement_dict()

        for nid, expression in self.equations.items():
            self.fix(nid, expression, self.replacement_dict)

        # Now add these equations as local functions
        for nid in self.equations.keys():
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
