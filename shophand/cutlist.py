import math

class Cut(object):
    def __init__(self, opening, name, length):
        self.opening = opening
        self.name = name
        self.length = length

    def __str__(self):
        return f'{self.opening.name} {self.name} @ {self.length}'

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

class CutListMaker(object):
    def __init__(self, board_length, kerf=0.125, join=False):
        self.board_length = board_length
        self.kerf = kerf
        self.join = join

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
                        cuts.append(Cut(c.opening, f'{name} {i+1}/{nc}', clen))
                    del cuts[j]
                    j -= 1
                else:
                    raise Exception(f'Cut length greater than board length {c.length + self.kerf} > {self.board_length}')
            j += 1

        ncuts = len(cuts)
        cut_made = [False] * ncuts

        board = cl.new_board(self.board_length)

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
                board = cl.new_board(self.board_length)
            else:
                cut_made[next_cut_i] = True
                board.cuts.append(next_cut)

        return cl
