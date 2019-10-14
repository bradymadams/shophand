import math
import sys

class Cut(object):
    def __init__(self, where, name, length):
        self.where = where
        self.name = name
        self.length = length

    def __str__(self):
        return f'{self.where.name} {self.name} @ {self.length}'

class Board(object):
    def __init__(self, length, kerf):
        self.length = length
        self.kerf = kerf
        self.cuts = []

    @property
    def excess(self):
        return self.length - sum([c.length for c in self.cuts]) - self.kerf * len(self.cuts)

class CutList(object):
    def __init__(self, name, kerf):
        self.name = name
        self.kerf = kerf
        self.boards = []

    def new_board(self, length):
        self.boards.append(Board(length, self.kerf))
        return self.boards[-1]

    @property
    def max_length(self):
        return max([b.length for b in self.boards])

class CutListMaker(object):
    def __init__(self, board_length, kerf=0.125, join=False, off_cuts=None):
        self.board_length = board_length
        self.kerf = kerf
        self.join = join
        self.off_cuts = off_cuts if off_cuts else []

    def _get_next_shortest_board(self, cl, shortest_remaining_cut):
        blength = None
        i = 0
        itake = None
        for oc in self.off_cuts:
            if oc > shortest_remaining_cut:
                if blength is None or oc < blength:
                    blength = oc
                    itake = i
            i += 1

        if blength:
            del self.off_cuts[itake]
            return cl.new_board(blength)

        return cl.new_board(self.board_length) # make a new fresh board


    def make(self, name, cuts):
        cl = CutList(name, self.kerf)

        j = 0
        for c in list(cuts):
            if (c.length + self.kerf) > self.board_length:
                if self.join:
                    # Split into multiple cuts
                    nc = int(math.ceil((c.length + self.kerf) / self.board_length))
                    name = c.name
                    length = c.length
                    for i in range(nc):
                        clen = length if length < self.board_length else self.board_length - self.kerf
                        length -= clen
                        cuts.append(Cut(c.where, f'{name} {i+1}/{nc}', clen))
                    del cuts[j]
                    j -= 1
                else:
                    raise Exception(f'Cut length greater than board length {c.length + self.kerf} > {self.board_length}')
            j += 1

        shortest_remaining_cut = min([c.length for c in cuts])

        ncuts = len(cuts)
        cut_made = [False] * ncuts

        board = self._get_next_shortest_board(cl, shortest_remaining_cut)

        while not all(cut_made):
            next_cut = None
            next_cut_i = -1
            for i in range(ncuts):
                if cut_made[i]:
                    continue
                if (cuts[i].length + self.kerf) <= board.excess:
                    if next_cut is None or cuts[i].length > next_cut.length:
                        next_cut = cuts[i]
                        next_cut_i = i
            if next_cut is None:
                board = self._get_next_shortest_board(cl, shortest_remaining_cut)
            else:
                cut_made[next_cut_i] = True
                board.cuts.append(next_cut)
                shortest_remaining_cut = sys.float_info.max
                for i in range(len(cuts)):
                    if not cut_made[i] and cuts[i].length < shortest_remaining_cut:
                        shortest_remaining_cut = cuts[i].length

        return cl
