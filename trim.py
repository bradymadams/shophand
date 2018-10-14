from math import *
import jinja2

CASING_SIDE_W = 5.25
CASING_HEAD_W = 5.5
APRON_W = 5.5

BLOCK_W = CASING_SIDE_W
BLOCK_H = 11.
STOOL_T = 1.125
JAMB_T = 11./16.

CROWN_D = 2.125 # Depth of crown moulding (used to determine extra material required for miter returns)

BEAD_T = 0.5

REVEAL = 0.25   # Reveal left by casing on jamb
CROWN_HANG = 1.5
BEAD_HANG = 0.5
STOOL_HANG = 0.5

IGNORE_JAMBS = True

class Part(object):
    def __init__(self, length, count=1, rough=None):
        self.length = length
        self.count = count
        self.rough = rough if rough else self.length

    def __str__(self):
        return f'{self.count} @ {self.rough} ({self.length})'

class PartsList(object):
    def __init__(self, **kwargs):
        self.parts = {}
        for k in kwargs.keys():
            if kwargs[k]:
                self.parts[k] = [kwargs[k]]

    def __str__(self):
        s = ''
        for p in self.parts.keys():
            s += f'{p}\n'
            for t in self.parts[p]:
                s+= f'\t{t}\n'
        return s
    
    def __iadd__(self, other):
        for k in other.parts.keys():
            newp = []
            for p in other.parts[k]:
                newp.append(Part(p.length, p.count, p.rough))
            if k in self.parts.keys():
                self.parts[k].extend(newp)
            else:
                self.parts[k] = newp
        return self

class Opening(object):
    def __init__(self, name, width, height, use_crown=True, has_jambs=False):
        self.name = name
        self.width = width
        self.height = height
        self.use_crown = use_crown
        self.has_jambs = has_jambs

    def __str__(self):
        return f'----- {self.name} -----\n{self.parts()}\n'

    def _extra_thickness_from_jambs(self):
        return JAMB_T if not self.has_jambs else 0.

    def _distance_across_casing(self):
        return self.width + 2 * (CASING_SIDE_W + REVEAL - self._extra_thickness_from_jambs())

    def crown(self):
        if not self.use_crown:
            return None
        L = self._distance_across_casing() + 2 * CROWN_HANG
        Lrough = L + 2 * CROWN_D
        return Part(L, rough=Lrough)

    def head(self):
        return Part(self._distance_across_casing())

    def bead(self):
        return Part(self._distance_across_casing() + 2 * BEAD_HANG)

    def side(self):
        raise NotImplementedError()

    def stool(self):
        return None # No stool by default - override if needed

    def apron(self):
        return None # No apron by default - override if needed

    def block(self):
        return None # No blocking by default - override if needed

    def jamb_top(self):
        return Part(self.width)

    def jamb_side(self):
        raise NotImplementedError()

    def parts(self):
        jt = None if IGNORE_JAMBS else self.jamb_top()
        js = None if IGNORE_JAMBS else self.jamb_side()
        return PartsList(
            jamb_top=jt,
            jamb_side=js,
            crown=self.crown(),
            head=self.head(),
            bead=self.bead(),
            side=self.side(),
            stool=self.stool(),
            apron=self.apron(),
            block=self.block())

class Window(Opening):
    def side(self):
        return Part(self.height - STOOL_T - self._extra_thickness_from_jambs() + REVEAL, 2)

    def stool(self):
        return Part(self._distance_across_casing() + 2 * STOOL_HANG)

    def apron(self):
        return Part(self._distance_across_casing())

    def jamb_side(self):
        return Part(self.height - JAMB_T - STOOL_T, 2)

class DoubleWindow(Window):
    def __init__(self, name, width, height, div, use_crown=True):
        super().__init__(name, width, height, use_crown)
        self.div = div
    
    def side(self):
        p = super().side()
        p.count = 3
        return p
    
    def jamb_top(self):
        return Part((self.width - self.div) / 2, 2)
    
    def jamb_side(self):
        p = super().jamb_side()
        p.count = 4
        return p

class Door(Opening):
    def side(self):
        return Part(self.height - STOOL_T - self._extra_thickness_from_jambs() + REVEAL - BLOCK_H, 2)
    
    def jamb_side(self):
        return Part(self.height - JAMB_T, 2)
    
    def block(self):
        return Part(BLOCK_H, 2)

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
                    nc = int(ceil((c.length + self.kerf) / self.board_length))
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

def house():
    ops = (
        Door('Front Door', 32.25, 80., has_jambs=True),
        Window('Living Room Front Window', 95., 52., has_jambs=True),
        Window('Living Room Picture Window', 57., 52., has_jambs=True),
        #Window('Downstairs Bathroom Window', 32., 26.),
        Door('Downstairs Bathroom Door', 30.25, 79.75, has_jambs=True),
        Door('Guest Bed Door', 30., 79.75, has_jambs=True),
        Door('Guest Bed Closet', 44.5, 70.5, has_jambs=True),
        Window('Kitchen Window South-East', 36., 38., has_jambs=True),
        Window('Kitchen Window South-West', 32., 38., has_jambs=True),
        Window('Kitchen Window West', 38., 51.5, has_jambs=True),
        Door('Kitchen Patio Door (future)', 80., 80.),
        Door('Back Door In', 31, 78.5, has_jambs=True),
        Door('Back Bed Door Out', 30.5, 79.5, has_jambs=True),
        Door('Back Bed Door In', 30.5, 79.5, has_jambs=True),
        Door('Back Bed Closet East', 30.5, 80.),
        Door('Back Bed Closet West', 30.5, 80.),
        Window('Back Bed Window West', 27., 41.25),
        Window('Back Bed Window North', 27., 41.25),
        Door('Stairwell Door (hall side)', 32., 80.25, has_jambs=True),
        Door('Side Door In', 32.25, 80.25, has_jambs=True),
        Window('Upstairs West Window', 36.25, 46.),
        DoubleWindow('Upstairs East Windows', 54., 45.5, 5.5),
        Door('Upstairs Closet Door', 48., 75.),
        Door('Upstairs Bathroom Door Out', 34., 81., use_crown=False),
        Door('Upstairs Bathroom Door In', 34., 81., use_crown=False),
        Window('Upstairs Bathroom Window', 32.25, 46.),
    )

    master = PartsList()
    for o in ops:
        master += o.parts()
        
    #print(master)

    totals = {}
    for k, pt in master.parts.items():
        total = 0.
        for p in pt:
            total += (p.rough * p.count)
        totals[k] = total

    for k, t in totals.items():
        feet = t / 12.
        inches = round(12. * (feet - floor(feet)))
        feet = floor(feet)
        print(f'{k}: {feet}\' {inches}"')

    # Create lists of unique cuts
    cuts = {'crown':[], 'head':[], 'bead':[], 'side':[], 'stool':[], 'apron':[], 'block':[]}

    for o in ops:
        parts = o.parts()
        for k, c in cuts.items():
            if k in parts.parts.keys():
                kparts = parts.parts[k]
                for p in kparts:
                    for i in range(p.count):
                        c.append( Cut(o, k, ceil(p.rough) + 1.) )

    clmkr = CutListMaker(16. * 12.)

    cl_side = clmkr.make('Head Casing', cuts['head'])
    cl_head = clmkr.make('Side Casing', cuts['side'])
    cl_apron = clmkr.make('Apron', cuts['apron'])
    cl_block = clmkr.make('Block', cuts['block'])

    clmkr = CutListMaker(10. * 12.)

    cl_stool = clmkr.make('Stool', cuts['stool'])

    clmkr = CutListMaker(8. * 12., join=True)
    
    cl_crown = clmkr.make('Crown', cuts['crown'])

    clmkr = CutListMaker(8. * 12., join=True)

    cl_bead = clmkr.make('Bead', cuts['bead'])

    with open('cutlist.template.html', 'r') as f:
        htmlt = f.read()

    template = jinja2.Template(htmlt)
    html = template.render(cutlists=( cl_head, cl_side, cl_apron, cl_block, cl_stool, cl_crown, cl_bead ))

    with open('cutlist.html', 'w') as f:
        f.write(html)

if __name__ == '__main__':
    house()

