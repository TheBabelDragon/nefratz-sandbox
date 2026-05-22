# -*- coding: utf-8 -*-
"""
NEFRATZ SANDBOX v15
Pythonista iPhone Optimized
"""

import ui
import random
import math
import time
from scene import *
from collections import deque

# ======================================================
# CONFIG
# ======================================================

MAX_ATOMS=220
MAX_PARTICLES=120

CELL=90

BOND_DIST=95

ATOM_DRAG=.97
CENTER_PULL=.0014
ORBIT_FORCE=.025

FIELD_VORTEX=0
FIELD_GRAVITY=1
FIELD_TURB=2
FIELD_WAVE=3

HEBREW={
"A":"א","B":"ב","C":"ג","D":"ד",
"E":"ה","F":"ו","G":"ז","H":"ח",
"I":"ט","J":"י","K":"כ","L":"ל",
"M":"מ","N":"נ","O":"ס","P":"ע",
"Q":"פ","R":"צ","S":"ק","T":"ר",
"U":"ש","V":"ת","W":"א","X":"ב",
"Y":"ג","Z":"ד"
}

CHARS=list(
set(
HEBREW.values()
)
)

# ======================================================
# ORGANISM
# ======================================================

class Organism:

    def __init__(self):

        self.energy=.9
        self.mood=.7
        self.mode="RESONANCE"

    def feed(self):

        self.energy=min(
            1,
            self.energy+.08
        )

        self.mood=min(
            1,
            self.mood+.05
        )

    def update(self):

        self.energy-=.001
        self.mood-=.0003

        self.energy=max(
            .1,
            self.energy
        )

        if self.energy<.35:
            self.mode="DREAMING"
        else:
            self.mode="RESONANCE"

# ======================================================
# ATOM
# ======================================================

class Atom:

    def __init__(
        self,
        char,
        x,
        y
    ):

        self.char=char

        self.x=x
        self.y=y

        self.vx=random.uniform(-1,1)
        self.vy=random.uniform(-1,1)

        self.energy=1

        self.pinned=False

    def update(
        self,
        cx,
        cy,
        field,
        t
    ):

        if self.pinned:
            return

        dx=cx-self.x
        dy=cy-self.y

        d=math.sqrt(
            dx*dx+
            dy*dy
        )+.001

        nx=dx/d
        ny=dy/d

        self.vx+=(
            nx*d*
            CENTER_PULL
        )

        self.vy+=(
            ny*d*
            CENTER_PULL
        )

        self.vx+=(
            -ny*
            ORBIT_FORCE
        )

        self.vy+=(
            nx*
            ORBIT_FORCE
        )

        # ----------------------
        # field modes
        # ----------------------

        if field==FIELD_VORTEX:

            self.vx+=(
                -.08*ny
            )

            self.vy+=(
                .08*nx
            )

        elif field==FIELD_GRAVITY:

            self.vy+=.04

        elif field==FIELD_TURB:

            self.vx+=random.uniform(
                -.4,
                .4
            )

            self.vy+=random.uniform(
                -.4,
                .4
            )

        elif field==FIELD_WAVE:

            self.vy+=math.sin(
                t+
                self.x*.02
            )*.25

        self.vx*=ATOM_DRAG
        self.vy*=ATOM_DRAG

        self.x+=self.vx
        self.y+=self.vy

# ======================================================
# SPATIAL HASH
# ======================================================

class Spatial:

    def __init__(self):

        self.grid={}

    def build(
        self,
        atoms
    ):

        self.grid={}

        for a in atoms:

            gx=int(
                a.x/CELL
            )

            gy=int(
                a.y/CELL
            )

            k=(gx,gy)

            self.grid.setdefault(
                k,
                []
            ).append(a)

    def neighbors(
        self,
        a
    ):

        gx=int(
            a.x/CELL
        )

        gy=int(
            a.y/CELL
        )

        for oy in(
            -1,0,1
        ):
            for ox in(
                -1,0,1
            ):

                k=(
                    gx+ox,
                    gy+oy
                )

                if k in self.grid:

                    for n in self.grid[k]:

                        if n!=a:
                            yield n

# ======================================================
# REWRITE ENGINE
# ======================================================

class Rewrite:

    def __init__(self):

        self.atoms=[]
        self.history=deque(
            maxlen=6
        )

    def build(
        self,
        text,
        w,
        h
    ):

        heb="".join(
            HEBREW.get(
                c.upper(),
                ""
            )
            for c in text
            if c.isalpha()
        )

        if not heb:
            heb="אבגד"

        self.history.appendleft(
            heb
        )

        self.atoms=[]

        cx=w*.5
        cy=h*.5

        radius=min(
            w,
            h
        )*.3

        golden=2.399963

        total=max(
            len(heb),
            1
        )

        for i,ch in enumerate(
            heb[:MAX_ATOMS]
        ):

            theta=i*golden

            r=radius*math.sqrt(
                (i+1)/total
            )

            x=(
                cx+
                math.cos(theta)*r
            )

            y=(
                cy+
                math.sin(theta)*r
            )

            self.atoms.append(
                Atom(
                    ch,
                    x,
                    y
                )
            )

# ======================================================
# SCENE
# ======================================================

class SandboxScene(Scene):

    def setup(self):

        self.background_color='black'

        self.org=Organism()

        self.rewrite=Rewrite()

        self.spatial=Spatial()

        self.field=FIELD_VORTEX

        self.time_counter=0

        self.drag_atom=None

        self.touch_x=None
        self.touch_y=None

        self.zoom=1.0
        self.pan_x=0
        self.pan_y=0

        self.fps=60

        self.frame_count=0
        self.last_fps=time.time()

        self.rewrite.build(
            "TheBabelDragon",
            self.size.w,
            self.size.h
        )

    # ===================================
    # TOUCH
    # ===================================

    def touch_began(
        self,
        touch
    ):

        x=touch.location.x
        y=touch.location.y

        self.touch_x=x
        self.touch_y=y

        closest=None
        best=999999

        for a in self.rewrite.atoms:

            d2=(
                (a.x-x)**2+
                (a.y-y)**2
            )

            if d2<best:

                best=d2
                closest=a

        if best<1600:
            self.drag_atom=closest

    def touch_moved(
        self,
        touch
    ):

        x=touch.location.x
        y=touch.location.y

        self.touch_x=x
        self.touch_y=y

        if self.drag_atom:

            self.drag_atom.x=x
            self.drag_atom.y=y

            self.drag_atom.vx=0
            self.drag_atom.vy=0

    def touch_ended(
        self,
        touch
    ):

        self.drag_atom=None

    # ===================================
    # SANDBOX ACTIONS
    # ===================================

    def explode(self):

        cx=self.size.w*.5
        cy=self.size.h*.5

        for a in self.rewrite.atoms:

            dx=a.x-cx
            dy=a.y-cy

            d=math.sqrt(
                dx*dx+
                dy*dy
            )+.001

            a.vx+=dx/d*8
            a.vy+=dy/d*8

    def freeze(self):

        for a in self.rewrite.atoms:

            a.vx=0
            a.vy=0

    def mutate(self):

        for a in self.rewrite.atoms:

            if random.random()<.2:

                a.char=random.choice(
                    CHARS
                )

    def clear_atoms(self):

        self.rewrite.atoms=[]

    def spawn(self):

        cx=self.size.w*.5
        cy=self.size.h*.5

        for i in range(30):

            self.rewrite.atoms.append(

                Atom(

                    random.choice(
                        CHARS
                    ),

                    cx+
                    random.uniform(
                        -50,
                        50
                    ),

                    cy+
                    random.uniform(
                        -50,
                        50
                    )

                )
            )

    # ===================================
    # UPDATE
    # ===================================

    def update(self):

        self.time_counter+=.05

        self.org.update()

        cx=self.size.w*.5
        cy=self.size.h*.5

        if self.touch_x:

            cx=.95*cx+.05*self.touch_x
            cy=.95*cy+.05*self.touch_y

        atoms=self.rewrite.atoms

        self.spatial.build(
            atoms
        )

        for a in atoms:

            a.update(
                cx,
                cy,
                self.field,
                self.time_counter
            )

            a.x=max(
                0,
                min(
                    self.size.w,
                    a.x
                )
            )

            a.y=max(
                0,
                min(
                    self.size.h,
                    a.y
                )
            )

        # FPS

        self.frame_count+=1

        now=time.time()

        if now-self.last_fps>1:

            self.fps=self.frame_count
            self.frame_count=0
            self.last_fps=now

    # ===================================
    # DRAW
    # ===================================

    def draw(self):

        mood=self.org.mood

        background(
            .02,
            0,
            .05
        )

        atoms=self.rewrite.atoms

        # -------------------
        # bonds
        # -------------------

        stroke_weight(1)

        bond_count=0

        for a in atoms:

            for b in self.spatial.neighbors(a):

                d=math.sqrt(
                    (b.x-a.x)**2+
                    (b.y-a.y)**2
                )

                if d<BOND_DIST:

                    bond_count+=1

                    alpha=(
                        1-
                        d/BOND_DIST
                    )*.4

                    stroke(
                        .4+
                        mood*.6,
                        .8,
                        1,
                        alpha
                    )

                    line(
                        a.x,
                        a.y,
                        b.x,
                        b.y
                    )

        # -------------------
        # atoms
        # -------------------

        for a in atoms:

            size=14

            glow=size*2

            fill(
                .4,
                .5,
                1,
                .12
            )

            ellipse(
                a.x-glow/2,
                a.y-glow/2,
                glow,
                glow
            )

            fill(
                1,
                .4,
                .9
            )

            ellipse(
                a.x-size/2,
                a.y-size/2,
                size,
                size
            )

            tint(
                1,
                1,
                1
            )

            text(
                a.char,
                x=a.x,
                y=a.y,
                font_size=11
            )

        # -------------------
        # history
        # -------------------

        tint(
            .7,
            .9,
            1
        )

        y=self.size.h-35

        for h in self.rewrite.history:

            text(
                h[:30],
                x=self.size.w*.5,
                y=y,
                font_size=10,
                alignment=5
            )

            y-=18

        # -------------------
        # stats
        # -------------------

        tint(
            1,
            1,
            1
        )

        stats=f"""
Atoms:{len(atoms)}
Bonds:{bond_count}
FPS:{self.fps}
Mode:{self.org.mode}
Energy:{self.org.energy:.2f}
Field:{self.field}
"""

        text(
            stats,
            x=15,
            y=120,
            font_size=10,
            alignment=6
        )

# ======================================================
# RESPONSIVE UI
# ======================================================

root=ui.View()
root.background_color='black'

screen_w,screen_h=ui.get_screen_size()

root.frame=(0,0,screen_w,screen_h)

TOP=0
BOTTOM_BAR=140

# --------------------------
# Scene
# --------------------------

sceneview=SceneView(
    frame=(
        0,
        TOP,
        screen_w,
        screen_h-BOTTOM_BAR
    )
)

scene=SandboxScene()
sceneview.scene=scene

root.add_subview(sceneview)

# --------------------------
# Input
# --------------------------

input_y=screen_h-130

tf=ui.TextField(
    frame=(
        10,
        input_y,
        screen_w-120,
        40
    )
)

tf.background_color="#111111"
tf.text_color='black'
tf.placeholder='rewrite text'

root.add_subview(tf)

# --------------------------
# Rewrite button
# --------------------------

def rewrite(sender):

    txt=tf.text.strip()

    if txt:

        scene.rewrite.build(
            txt,
            sceneview.width,
            sceneview.height
        )

        scene.org.feed()

        tf.text=''

rewrite_btn=ui.Button(
    frame=(
        screen_w-100,
        input_y,
        90,
        40
    )
)

rewrite_btn.title='Rewrite'
rewrite_btn.background_color='#AA0033'
rewrite_btn.action=rewrite

root.add_subview(rewrite_btn)

# --------------------------
# Tool buttons
# --------------------------

buttons=[

("Boom",scene.explode),
("Freeze",scene.freeze),
("Spawn",scene.spawn),
("Mutate",scene.mutate)

]

button_y=screen_h-75

padding=8

button_w=(
    screen_w-
    padding*(len(buttons)+1)
)/len(buttons)

for i,(title,fn) in enumerate(buttons):

    b=ui.Button()

    b.frame=(

        padding+i*(button_w+padding),

        button_y,

        button_w,

        42
    )

    b.title=title
    b.background_color='#333366'

    b.action=lambda sender,f=fn:f()

    root.add_subview(b)

# --------------------------
# launch
# --------------------------

root.present(
    'fullscreen',
    hide_title_bar=True
)
