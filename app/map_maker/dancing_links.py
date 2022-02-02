#!/usr/bin/env python
#
# Copyright 2008 Sebastian Raaphorst.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""An implementation of Donald Knuth's Dancing Links implementation:

http://lanl.arxiv.org/pdf/cs/0011047

By Sebastian Raaphorst, 2008.

Thanks to the following people for their testing efforts:
   * Winfried Plappert"""


class DLX:
    """The DLX data structure and relevant operations."""

    # These pertain to column types.
    # Primary columns must be covered.
    # Secondary columns can be covered at most once.
    PRIMARY = 0
    SECONDARY = 1

    def __init__(self, columns, rows=None, rowNames=None):
        """Initialize the DLX problem with the specified columns and row data,
        if provided. Column data must be a list of pairs of the form
        (columnname, 0/1) where 0 represents a primary column (i.e. one that
        must be covered) and 1 represents a secondary column (i.e. one that is
        not essential to cover)."""

        # Create directional objects for the problem.
        # We need column headers equal to the number of columns, and one
        # more for the problem header.
        self.nodect = len(columns) + 1
        self.up = list(range(self.nodect))
        self.down = list(range(self.nodect))
        self.left = [0] * self.nodect
        self.right = list(range(self.nodect))
        self.C = list(range(self.nodect))
        self.S = [0] * self.nodect

        # Remember to add one column name for the header; here we use None.
        self.N = [colname for (colname, _) in columns] + [None]

        # Now perform the L-R linking of columns, which requires special
        # processing to ensure that only PRIMARY columns are linked
        # together. We will link only L pointers and then use them to
        # link R pointers.
        prev = self.nodect - 1
        cur = 0
        for (_, columntype) in columns:
            if columntype == DLX.PRIMARY:
                self.left[cur] = prev
                prev = cur
            else:
                self.left[cur] = cur
            cur += 1
        self.left[self.nodect - 1] = prev

        # Now process the R nodes.
        prev = self.nodect - 1
        cur = self.left[prev]
        while cur != self.nodect - 1:
            self.right[cur] = prev
            prev = cur
            cur = self.left[cur]
        self.right[self.nodect - 1] = prev

        # Store the header index.
        self.header = len(columns)

        # Store the solution variable.
        self.partialsolution = []

        # If there are any rows, append them.
        if rows:
            self.appendRows(rows, rowNames)

    def appendRows(self, rows, rowNames=None):
        """Append the rows to the matrix. The row information should be provided
        as a list with each entry corresponding to a row, with row information
        stored as a list of column indices where the 1s appear.

        Returns a list containing row identifiers, which are the indices of the
        first nodes appearing in the row."""

        rowIdentifiers = []
        if rowNames is None:
            rowNames = [None] * len(rows)
        for i in range(len(rows)):
            rowIdentifiers.append(self.appendRow(rows[i], rowNames[i]))
        return rowIdentifiers

    def appendRow(self, row, rowName=None):
        """Given a set of row indices (e.g. column coordinates), append the
        necessary entries to the DLX matrix.

        Returns a row identifier, which is the index of the first node
        appearing in the row."""

        first = self.nodect
        prev = self.nodect
        for index in row:
            # Append data to all lists for the node representing this row.
            self.up.append(self.up[index])
            self.down.append(index)
            self.down[self.up[index]] = self.nodect
            self.up[index] = self.nodect
            self.S[index] += 1
            self.C.append(index)

            self.right.append(self.nodect)
            self.left.append(prev)
            self.right[self.nodect] = self.right[prev]

            self.right[prev] = self.nodect
            self.left[self.right[self.nodect]] = self.nodect

            self.N.append(rowName)
            self.prev = self.nodect
            self.nodect += 1
        return first

    def useRow(self, rowindex):
        """Given a row index, as returned by appendRows or appendRow, use this
        in the partial solution.

        ***NOTE:***
        To unuse rows, unuseRow() must be called with the appropriate rows in
        reverse order that calls were made to useRow(). For example, if we had:
             useRow(7)
             useRow(92)
             useRow(14)
        To undo this and restore the DLX matrix to its original form, we would
        need to perform:
             unuseRow(14)
             unuseRow(92)
             unuseRow(7)
        Failure to comply will result in unexpected behaviour.

        This can be used to force certain rows into the final solution, i.e. by
        executing the appropriate useRow calls prior to solving.

        This should NEVER be called during solving; failure to comply may result
        in unpredictable behaviour."""

        # Add the row to the solution.
        self.partialsolution.append(rowindex)

        # Cover all columns in the row.
        i = rowindex
        while 1:
            self._cover(self.C[i])
            i = self.right[i]
            if i == rowindex:
                break

    def unuseRow(self, rowindex):
        """Given a row index, as returned by appendRows or appendRow, if
        useRow() was called to use this row, now unuse it.

        ***NOTE:***
        To unuse rows, unuseRow() must be called with the appropriate rows in
        reverse order that calls were made to useRow(). For example, if we had:
             useRow(7)
             useRow(92)
             useRow(14)
        To undo this and restore the DLX matrix to its original form, we would
        need to perform:
             unuseRow(14)
             unuseRow(92)
             unuseRow(7)
        Failure to comply will result in an AssertionError being raised.
        
        This should NEVER be called during solving, but only prior to and after;
        calling while solving will likely result in AssertionErrors as well."""

        # This is so important that we force it.
        assert(self.partialsolution.pop() == rowindex)

        # Uncover all columns in the row.
        i = self.left[rowindex]
        while 1:
            self._uncover(self.C[i])
            i = self.left[i]
            if i == self.left[rowindex]:
                break

    # *** PROVIDED COLUMN SELECTORS ***
    def leftmostColumnSelector(self, _):
        """Select the leftmost available column to cover.

        Note that the userdata (second parameter) is ignored."""

        return self.right[self.header]

    def smallestColumnSelector(self, _):
        """Select the column with the fewest rows covering it, i.e. minimize
        the branching factor.

        Note that the userdata (second parameter) is ignored."""

        smallest = self.right[self.header]
        j = self.right[self.right[self.header]]
        while j != self.header:
            if self.S[j] < self.S[smallest]:
                smallest = j
            j = self.right[j]
        return smallest

    def getRowList(self, row):
        """Get a list of the column names corresponding to the row."""

        names = []
        i = row
        while True:
            names.append(self.N[self.C[i]])
            i = self.right[i]
            if i == row:
                break
        return names

    def printSolution(self, solution):
        """A convenience function, which simply writes out each of the chosen
        rows in the covering as a list of column names."""
        print("solution")
        print(solution)
        for i in solution:
            print(i)
            print(self.getRowList(i))

    def solve(self,
              columnselector=smallestColumnSelector,
              columnselectoruserdata=None):
        """Solve the DLX problem.

        The function accepts two parameters, as follows:

        1. Function: columnselector(DLX, columnselectoruserdata)
        The columnselector function, given the header, and the partial solution
        (stored as a list of rows, with entries being the first DLXEntry in each
        row), should choose a column to process next. If header is returned,
        then it is assumed that no column can be selected and the problem
        backtracks. Default value is smallestColumnSelector.

        2. column selector userdata
        Data to be passed to the supplied column selector as a second parameter.
        Default value is None.

        It yields solutions to the DLX instance, serving as a generator. Thus,
        to process all solutions, one should execute:

        for solution in DLXinstance.solve():
           process solution here

        This call initializes and populated a DLXStatistics object, which may
        be accessed as self.statistics."""

        self.statistics = DLXStatistics()
        for sol in self._solve(0, columnselector, columnselectoruserdata, self.statistics):
            yield sol

    def _solve(self, depth, columnselector, columnselectoruserdata, statistics):
        """This is an internal function and should not be called directly."""

        # result = None

        # Check to see if we have a complete solution.
        if self.right[self.header] == self.header:
            # Make a copy so that it is preserved.
            yield self.partialsolution[:]
            return

        # Make sure that the statistics are capable of holding the necessary information.
        if len(statistics.nodes) <= depth:
            statistics.nodes += [0] * (depth - len(statistics.nodes) + 1)
        if len(statistics.updates) <= depth:
            statistics.updates += [0] * (depth - len(statistics.updates) + 1)

        # Choose a column object.
        c = columnselector(self, columnselectoruserdata)
        if c == self.header or self.S[c] == 0:
            return

        # Cover the column.
        statistics.updates[depth] += self._cover(c)

        # Extend the solution by trying each possible row in the column.
        r = self.down[c]
        while r != c:
            self.partialsolution.append(r)
            statistics.nodes[depth] += 1

            # Now cover the columns that are handled by the inclusion of this row.
            j = self.right[r]
            while j != r:
                self._cover(self.C[j])
                j = self.right[j]

            # Recursively search.
            for sol in self._solve(depth+1, columnselector, columnselectoruserdata, statistics):
                yield sol

            # Reverse the operation.
            self.partialsolution.pop()

            # We are no longer using this row right now, so uncover.
            j = self.left[r]
            while j != r:
                self._uncover(self.C[j])
                j = self.left[j]

            # If the result was not None, then terminate prematurely.
            # if result is not None:
                # break

            # Try the next row.
            r = self.down[r]

        self._uncover(c)
        return

    def _cover(self, c):
        """This is an internal function and should not be called directly."""
        updates = 1

        # Remove this column from the header.
        self.left[self.right[c]] = self.left[c]
        self.right[self.left[c]] = self.right[c]

        # Iterate over the rows covered by this column.
        # Stop when we reach the header.
        i = self.down[c]
        while i != c:
            # Remove this row from the problem.
            j = self.right[i]
            while j != i:
                self.up[self.down[j]] = self.up[j]
                self.down[self.up[j]] = self.down[j]
                self.S[self.C[j]] -= 1
                j = self.right[j]
                updates += 1
            i = self.down[i]

        return updates

    def _uncover(self, c):
        """This is an internal function and should not be called directly."""

        # Reverse the operations done in _cover.
        i = self.up[c]
        while i != c:
            j = self.left[i]
            while j != i:
                self.S[self.C[j]] += 1
                self.down[self.up[j]] = j
                self.up[self.down[j]] = j
                j = self.left[j]
            i = self.up[i]

        # Readd the column to the header.
        self.right[self.left[c]] = c
        self.left[self.right[c]] = c


class DLXStatistics:
    """Statistics collected from a run of solving a DLX problem.

    This object has two lists, nodes and updates, as fields.

    Nodes represents the number of nodes visited at each depth of the
    search tree.

    Updates represents the number of link updates performed at each
    depth of the search tree."""
    __slots__ = ['nodes', 'updates']

    def __init__(self):
        """__init__(self)

        Create a new empty statistical object."""

        self.nodes = []
        self.updates = []

# Testing code.
if __name__ == '__main__':
    columns = [('a', DLX.PRIMARY), ('b', DLX.PRIMARY), ('c', DLX.PRIMARY), ('d', DLX.SECONDARY), ('e', DLX.PRIMARY)]
    d = DLX(columns)
    rows = [[1, 2, 4],
            [0, 1, 3],
            [0],
            [0, 1, 2, 3, 4]]
    rowNames = ['row%i' % i for i in range(len(rows))]
    r = d.appendRows(rows, rowNames)
    for sol in d.solve():
        print("Solution:")
        for i in sol:
            print(i)
            print(d.N[i])
        # d.printSolution(sol)
        # create_solution_grid(d, sol)
