import math
import jinja2

import shophand

CASING_SIDE_W = 5.125
CASING_HEAD_W = 5.5
CASING_T = 11. / 16.
APRON_W = 5.5

BLOCK_W = CASING_SIDE_W
BLOCK_H = 11.
STOOL_T = 1.125
JAMB_T = 11./16.

CROWN_D = 2. + 1./16. # Depth of crown moulding (used to determine extra material required for miter returns)

BEAD_T = 0.5

REVEAL = 0.25   # Reveal left by casing on jamb
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
        L = self._distance_across_casing() + 2 * (CROWN_D - CASING_T)
        Lrough = L + 2 * CROWN_D + 0.5 # Adding a little extra for kerfs for miter return cuts
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
        Door('Back Bed Closet East', 28.125, 80., has_jambs=True),
        Door('Back Bed Closet West', 28.125, 80., has_jambs=True),
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
        inches = round(12. * (feet - math.floor(feet)))
        feet = math.floor(feet)
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
                        c.append( shophand.cutlist.Cut(o, k, math.ceil(p.rough) + 1.) )

    clmkr = shophand.cutlist.CutListMaker(16. * 12.)

    cl_side = clmkr.make('Head Casing', cuts['head'])
    cl_head = clmkr.make('Side Casing', cuts['side'])
    cl_apron = clmkr.make('Apron', cuts['apron'])
    cl_block = clmkr.make('Block', cuts['block'])

    clmkr = shophand.cutlist.CutListMaker(10. * 12.)

    cl_stool = clmkr.make('Stool', cuts['stool'])

    clmkr = shophand.cutlist.CutListMaker(8. * 12., join=True)
    
    cl_crown = clmkr.make('Crown', cuts['crown'])

    clmkr = shophand.cutlist.CutListMaker(8. * 12., join=True)

    cl_bead = clmkr.make('Bead', cuts['bead'])

    with open('cutlist.template.html', 'r') as f:
        htmlt = f.read()

    template = jinja2.Template(htmlt)
    html = template.render(cutlists=( cl_head, cl_side, cl_apron, cl_block, cl_stool, cl_crown, cl_bead ))

    with open('cutlist.html', 'w') as f:
        f.write(html)

if __name__ == '__main__':
    house()

