from app.map_maker.utilities import random_choice

class HeaderCell:
    __slots__ = ['name', 'size', 'primary', 'row_idx']

    def __init__(self, name, primary=True):
        self.name = name
        self.size: int = 0
        self.primary: bool = primary
        self.row_idx = []

class RainAlgorithmX:
    def __init__(self, column_headers: list, row_headers: list, rows: list, 
                 pos: tuple = (0, 0), seed: int = 0):
        # Only used for random choices
        self.pos = pos
        self.seed = seed

        self.column_headers = [HeaderCell(*c) for c in column_headers]
        self.primary_column_headers = []
        for header in self.column_headers:
            if header.primary:
                self.primary_column_headers.append(header)
            else:
                break
        self.row_headers = row_headers
        self.rows = rows
        self.uncovered_columns = {y for y in range(len(self.column_headers))}
        self.uncovered_primary_columns = {y for y in range(len(self.primary_column_headers))}
        self.uncovered_rows = {x for x in range(len(self.row_headers))}

        self.solution_rows = []
        self.covered_rows = []
        self.bad_solutions = {} # Key: Depth int, Value: Set

        # Set size
        for column_idx, column_header in enumerate(self.column_headers):
            for row_idx, row in enumerate(self.rows):
                if column_idx in row:
                    column_header.size += 1
                    column_header.row_idx.append(row_idx)

    def get_solution(self):
        return sorted([self.row_headers[row_idx] for row_idx in self.solution_rows])

    def choose_column(self) -> int:
        """
        Finds the column with the minimum size.
        Returns it's index
        """
        minimum_column_index = 0
        min_size = 99999
        for idx, col in enumerate(self.primary_column_headers):
            if idx in self.uncovered_primary_columns and col.size < min_size:
                minimum_column_index = idx
                min_size = col.size
        return minimum_column_index, min_size

    def solve(self) -> bool:
        counter = 0
        while self.uncovered_primary_columns and counter < 99999:
            counter += 1
            output = self.process()
            if not output:
                # No valid solutions at all
                return False
        if counter >= 99999:
            print("Infinite Loop detected!")
        return True

    def revert(self):
        # No solutions at this level
        depth = len(self.solution_rows)
        if depth in self.bad_solutions:
            self.bad_solutions[depth].clear()
        if self.solution_rows:
            bad_row = self.solution_rows.pop()
            covered_rows = self.covered_rows.pop()
            self.uncover(bad_row, covered_rows)
            if depth - 1 not in self.bad_solutions:
                self.bad_solutions[depth - 1] = set()
            self.bad_solutions[depth - 1].add(bad_row)
            # print("Uncover")
            # print(covered_rows)
            # print(self.uncovered_columns)
            # print(self.uncovered_rows)
            # print([c.size for c in self.column_headers])
            return True
        else:
            return False  # No valid solutions at all

    def process(self):
        # print("Process")
        # Choose a column
        column_idx, min_size = self.choose_column()
        # print("Column Choice", column_idx, min_size)

        if min_size == 0:
            return self.revert()

        # Choose a row that has a 1 in the column
        bad_rows = self.bad_solutions.get(len(self.solution_rows), set())
        possible_rows = [idx for idx, row in enumerate(self.rows) if 
                         idx in self.uncovered_rows and 
                         idx not in bad_rows and 
                         column_idx in row]
        # print("Possible Rows", possible_rows)
        if not possible_rows:
            return self.revert()
        row_idx = random_choice(possible_rows, self.pos, self.seed)
        # print("Row choice", row_idx)

        # Include row in solution
        self.solution_rows.append(row_idx)

        covered_rows = self.cover(row_idx)
        self.covered_rows.append(covered_rows)
        # print("Cover")
        # print(self.uncovered_columns)
        # print(self.uncovered_rows)
        # print([c.size for c in self.column_headers])

        return True

    def cover(self, row_idx) -> list:
        # For each column where the row has a 1
        row = self.rows[row_idx]
        covered_rows = []
        for column_idx in row:
            # For each row where this column has a 1
            for ridx in self.column_headers[column_idx].row_idx:
                if ridx in self.uncovered_rows:
                    other_row = self.rows[ridx]
                    # cover the row
                    self.uncovered_rows.discard(ridx)
                    covered_rows.append(ridx)
                    for cidx in other_row:
                        self.column_headers[cidx].size -= 1
            # cover the column
            self.uncovered_columns.discard(column_idx)
            if self.column_headers[column_idx].primary:
                self.uncovered_primary_columns.discard(column_idx)
        return covered_rows

    def uncover(self, row_idx, covered_rows):
        # Add it back
        # For each column where the row has a 1
        row = self.rows[row_idx]
        for column_idx in row:
            # uncover the column
            self.uncovered_columns.add(column_idx)
            if self.column_headers[column_idx].primary:
                self.uncovered_primary_columns.add(column_idx)

        # For each row to uncover
        for ridx in covered_rows:
            # uncover the row
            self.uncovered_rows.add(ridx)
            for cidx in self.rows[ridx]:
                self.column_headers[cidx].size += 1
# Testing code.
if __name__ == '__main__':
    import cProfile
    pr = cProfile.Profile()

    def test1():
        columns = [('a', True), ('b', True), ('c', True), ('d', False), ('e', True)]
        rows = [[1, 2, 4],
                [0, 1, 3],
                [0],
                [0, 1, 2, 3, 4]]
        row_names = ['row%i' % i for i in range(len(rows))]
        return columns, row_names, rows

    def test2():
        columns = [('a', True), ('b', True), ('c', True), ('d', True), ('e', True), ('f', True), ('g', True)]
        rows = [[2, 4, 5],
                [0, 3, 6],
                [1, 2, 5],
                [0, 3],
                [1, 6],
                [3, 4, 6]]
        row_names = ['row%i' % i for i in range(len(rows))]
        return columns, row_names, rows

    def test3():
        columns = [('a', True), ('b', True), ('c', True), ('d', True), ('e', True), ('f', True), ('g', True)]
        rows = [[0, 3, 6],
                [0, 3],
                [3, 4, 6],
                [2, 4, 5],
                [1, 2, 5, 6],
                [1, 6],
                [0, 3, 4]]
        row_names = ['row%i' % i for i in range(len(rows))]
        return columns, row_names, rows

    columns, row_names, rows = test3()
    pr.enable()
    for seed in range(10):
        print("Seed: %d" % seed)
        d = RainAlgorithmX(columns, row_names, rows, seed=seed)
        output = d.solve()
        if output:
            print(d.get_solution())
        else:
            print("No valid solution")
    pr.disable()
    pr.print_stats(sort='time')
