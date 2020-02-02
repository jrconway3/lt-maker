from dataclasses import dataclass

from app.data.data import data, Prefab
from app import utilities

@dataclass
class Equation(Prefab):
    nid: str = None
    expression: str = None

class EquationCatalog(data):
    def import_data(self, fn):
        with open(fn) as fp:
            lines = [line.strip() for line in fp.readlines() if not line.startswith('#')]

        for line in lines:
            if '=' not in line:
                print('%s is not a valid equation' % line)
                continue
            lhs, rhs = line.split('=')
            lhs, rhs = lhs.strip(), rhs.strip()
            equation = Equation(lhs, rhs)
            self.append(equation)

    def add_new_default(self, db):
        new_row_nid = utilities.get_next_name('EQUATION', self.keys())
        new_equation = Equation(new_row_nid, "0")
        self.append(new_equation)
