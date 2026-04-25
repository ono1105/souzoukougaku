"""
点群パズル 3D版 — 対称性の素因数分解
依存: pip install pygame PyOpenGL PyOpenGL_accelerate numpy
実行: python point_group_puzzle_3d.py

操作:
  マウスドラッグ : 視点回転
  マウスホイール : ズーム
  Z             : Undo
  R             : Reset
  ESC           : 終了
"""

import sys, math
import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

# ══════════════════════════════════════════════
# 1. 群の生成元・商写像の定義
# ══════════════════════════════════════════════

def Rz(deg):
    r = math.radians(deg); c,s = math.cos(r),math.sin(r)
    return np.array([[c,-s,0],[s,c,0],[0,0,1]])

def Rx(deg):
    r = math.radians(deg); c,s = math.cos(r),math.sin(r)
    return np.array([[1,0,0],[0,c,-s],[0,s,c]])

def Ry(deg):
    r = math.radians(deg); c,s = math.cos(r),math.sin(r)
    return np.array([[c,0,s],[0,1,0],[-s,0,c]])

INV  = -np.eye(3)                        # 反転
MXY  = np.diag([1.,1.,-1.])             # z=0 鏡映
MXZ  = np.diag([1.,-1.,1.])             # y=0 鏡映
MYZ  = np.diag([-1.,1.,1.])             # x=0 鏡映

def generate_group(gens, max_order=200):
    """生成元リストから群の全元（3x3行列）を生成"""
    elems = [np.eye(3)]
    queue = list(gens)
    while queue:
        g = queue.pop(0)
        is_new = True
        for e in elems:
            if np.allclose(g, e, atol=1e-6):
                is_new = False; break
        if is_new:
            elems.append(g)
            for e in elems:
                for prod in [g @ e, e @ g]:
                    already = any(np.allclose(prod, x, atol=1e-6) for x in elems+queue)
                    if not already:
                        queue.append(prod)
        if len(elems) > max_order:
            break
    return elems

def orbit(group_elems, seed):
    """種点に群を作用させて一般位置を生成（重複除去）"""
    pts = []
    for g in group_elems:
        p = g @ seed
        if not any(np.allclose(p, q, atol=1e-4) for q in pts):
            pts.append(p)
    return pts

# 各点群の定義
_DEFS = {
    "C1":  {"gens": [],                              "nsubs":[]},
    "Ci":  {"gens": [INV],                           "nsubs":["C1"]},
    "C2":  {"gens": [Rz(180)],                       "nsubs":["C1"]},
    "C3":  {"gens": [Rz(120)],                       "nsubs":["C1"]},
    "C4":  {"gens": [Rz(90)],                        "nsubs":["C2","C1"]},
    "C6":  {"gens": [Rz(60)],                        "nsubs":["C3","C2","C1"]},
    "C2h": {"gens": [Rz(180), MXY],                 "nsubs":["C2","Ci","C1"]},
    "C2v": {"gens": [Rz(180), MXZ],                 "nsubs":["C2","C1"]},
    "C3v": {"gens": [Rz(120), MXZ],                 "nsubs":["C3","C1"]},
    "C4v": {"gens": [Rz(90),  MXZ],                 "nsubs":["C4","C2v","C2","C1"]},
    "C6v": {"gens": [Rz(60),  MXZ],                 "nsubs":["C6","C3v","C2v","C3","C2","C1"]},
    "D2":  {"gens": [Rz(180), Rx(180)],             "nsubs":["C2","C1"]},
    "D3":  {"gens": [Rz(120), Rx(180)],             "nsubs":["C3","C1"]},
    "D4":  {"gens": [Rz(90),  Rx(180)],             "nsubs":["D2","C4","C2","C1"]},
    "D6":  {"gens": [Rz(60),  Rx(180)],             "nsubs":["D3","D2","C6","C3","C2","C1"]},
    "T":   {"gens": [Rz(120)@Rx(120), Rz(180)],    "nsubs":["D2","C3","C2","C1"]},
    "Td":  {"gens": [Rz(120)@Rx(120), MXZ],        "nsubs":["T","D2","C3","C2","C1"]},
    "O":   {"gens": [Rz(90), Rx(90)],              "nsubs":["T","D4","D3","D2","C4","C3","C2","C1"]},
    "Oh":  {"gens": [Rz(90), Rx(90), INV],         "nsubs":["O","Td","T","D4","D2","C4","C3","C2","Ci","C1"]},
}

LABELS = {
    "C1":"C1","Ci":"Ci","C2":"C2","C3":"C3","C4":"C4","C6":"C6",
    "C2h":"C2h","C2v":"C2v","C3v":"C3v","C4v":"C4v","C6v":"C6v",
    "D2":"D2","D3":"D3","D4":"D4","D6":"D6",
    "T":"T","Td":"Td","O":"O","Oh":"Oh",
}
DESCS = {
    "C1":"Identity only","Ci":"Inversion","C2":"2-fold rotation",
    "C3":"3-fold rotation","C4":"4-fold rotation","C6":"6-fold rotation",
    "C2h":"C2 + horiz mirror","C2v":"C2 + vert mirrors",
    "C3v":"C3 + vert mirrors","C4v":"C4 + vert mirrors","C6v":"C6 + vert mirrors",
    "D2":"Three 2-fold axes","D3":"D3 axes","D4":"D4 axes","D6":"D6 axes",
    "T":"Tetrahedral rotations","Td":"Full tetrahedral",
    "O":"Cubic rotations","Oh":"Full cubic (order 48)",
}

# 種点：一般位置になるよう対称軸上を避ける
SEED = np.array([0.6, 0.7, 0.8])
SEED /= np.linalg.norm(SEED)

print("Generating groups...", end=" ", flush=True)
GROUPS = {}
for k, d in _DEFS.items():
    elems = generate_group(d["gens"])
    pts   = orbit(elems, SEED)
    GROUPS[k] = {"elems": elems, "pts": pts,
                 "nsubs": d["nsubs"],
                 "label": LABELS[k], "desc": DESCS[k]}
print("done.")

# ══════════════════════════════════════════════
# 2. 商写像：剰余類の計算
# ══════════════════════════════════════════════

def coset_decompose(G_elems, N_elems):
    """G の N による左剰余類に分割。各剰余類はリストのリスト（行列インデックス）"""
    used = [False]*len(G_elems)
    cosets = []
    for i, g in enumerate(G_elems):
        if used[i]: continue
        coset = []
        for j, h in enumerate(G_elems):
            if used[j]: continue
            # n = g^{-1} h が N に属するか
            g_inv = np.linalg.inv(g)
            n = g_inv @ h
            if any(np.allclose(n, ne, atol=1e-5) for ne in N_elems):
                coset.append(j); used[j] = True
        cosets.append(coset)
    return cosets  # len = |G|/|N|

def quotient_map(G_elems, N_elems, pts):
    """各点（G元のインデックス）→商群の代表元インデックスを返す"""
    cosets = coset_decompose(G_elems, N_elems)
    pt_to_coset = {}
    for ci, coset in enumerate(cosets):
        for idx in coset:
            pt_to_coset[idx] = ci
    # pts[i] は G_elems[i] @ seed に対応
    # ただし pts の順序と G_elems の対応を作る
    return cosets  # cosets[i] = i番目の剰余類に属するG元インデックス

def compute_merge_assignment(src_key, tgt_key):
    """
    src群の各点が tgt群（正規部分群による商）のどの点に合体するか返す。
    戻り値: assignment[i] = j  (src点i → tgt点j)
    """
    G = GROUPS[src_key]
    N = GROUPS[tgt_key]
    cosets = coset_decompose(G["elems"], N["elems"])
    src_pts = G["pts"]
    tgt_pts = N["pts"]

    # 各 src_pt を G元と対応付け
    assignment = []
    for i, sp in enumerate(src_pts):
        # sp = G_elems[?] @ SEED → どのG元か特定
        g_idx = None
        for gi, ge in enumerate(G["elems"]):
            if np.allclose(ge @ SEED, sp, atol=1e-4):
                g_idx = gi; break
        # g_idx が属する剰余類を探す
        coset_id = None
        for ci, coset in enumerate(cosets):
            if g_idx in coset:
                coset_id = ci; break
        # 剰余類の代表元 G_elems[coset[0]] @ SEED を tgt_pts で探す
        rep = G["elems"][cosets[coset_id][0]] @ SEED
        rep /= np.linalg.norm(rep)
        best, bd = 0, 1e9
        for j, tp in enumerate(tgt_pts):
            d = np.linalg.norm(rep - tp)
            if d < bd: bd, best = d, j
        assignment.append(best)
    return assignment

# ══════════════════════════════════════════════
# 3. アニメーション軌跡の判定
# ══════════════════════════════════════════════

def classify_operation(src_pt, tgt_pt, G_elems, N_elems):
    """
    src→tgt の合体がどの種類の操作か判定。
    戻り値: "rotation" | "reflection" | "inversion" | "identity"
    """
    if np.allclose(src_pt, tgt_pt, atol=1e-4):
        return "identity"
    # 反転: tgt ≈ -src
    if np.allclose(src_pt + tgt_pt, 0, atol=0.1):
        return "inversion"
    # 鏡映: |src|=|tgt|, src+tgt の方向が鏡映面の法線と垂直
    # 簡易判定: 行列式-1の元で結ばれるか
    for g in G_elems:
        if abs(np.linalg.det(g) + 1) < 0.1:  # 鏡映・反映回転
            if np.allclose(g @ src_pt, tgt_pt, atol=0.1):
                return "reflection"
    return "rotation"

def arc_path(p0, p1, t, op_type):
    """op_type に応じた軌跡上の点を返す (t: 0→1)"""
    ease = t*t*(3-2*t)  # smoothstep
    if op_type == "identity":
        return p0.copy()
    elif op_type in ("inversion", "reflection"):
        # 直線補間（3D空間内の直線）
        return (1-ease)*p0 + ease*p1
    else:
        # SLERP（球面測地線 = 回転軸まわりの円弧）
        p0n = p0/np.linalg.norm(p0)
        p1n = p1/np.linalg.norm(p1)
        dot = float(np.clip(np.dot(p0n,p1n),-1,1))
        if dot < 0: p1n=-p1n; dot=-dot
        omega = math.acos(min(dot,0.9999))
        if omega < 1e-6: return p0.copy()
        s = math.sin(omega)
        return (math.sin((1-ease)*omega)*p0n + math.sin(ease*omega)*p1n)/s

# ══════════════════════════════════════════════
# 4. OpenGL 描画
# ══════════════════════════════════════════════

_quad = None
def get_quad():
    global _quad
    if _quad is None: _quad = gluNewQuadric()
    return _quad

ATOM_COLORS = [
    (0.3,0.6,1.0),(0.3,0.9,0.5),(1.0,0.85,0.2),(0.7,0.3,1.0),
    (1.0,0.35,0.35),(1.0,0.55,0.2),(0.2,0.85,0.85),(0.85,0.85,0.3),
]

def draw_sphere_at(pos, r, color):
    glPushMatrix()
    glTranslatef(*[float(x) for x in pos])
    glColor4f(*color, 1.0)
    gluSphere(get_quad(), r, 16, 16)
    glColor4f(*color, 0.12)
    gluSphere(get_quad(), r*1.7, 8, 8)
    glPopMatrix()

def draw_trail(p0, p1, op_type, color, steps=30):
    """合体軌跡を細い線で描画"""
    glLineWidth(1.5)
    glColor4f(*color, 0.5)
    glBegin(GL_LINE_STRIP)
    for i in range(steps+1):
        p = arc_path(p0, p1, i/steps, op_type)
        glVertex3f(*[float(x) for x in p])
    glEnd()

def draw_axes(length=1.25):
    glLineWidth(1.2)
    glBegin(GL_LINES)
    glColor3f(0.5,0.1,0.1); glVertex3f(-length,0,0); glVertex3f(length,0,0)
    glColor3f(0.1,0.5,0.1); glVertex3f(0,-length,0); glVertex3f(0,length,0)
    glColor3f(0.1,0.1,0.5); glVertex3f(0,0,-length); glVertex3f(0,0,length)
    glEnd()

def draw_wire_sphere(r=1.0, segs=24, lats=6):
    glColor4f(0.15,0.25,0.4,0.3)
    glLineWidth(0.5)
    for i in range(lats):
        lat = math.pi*(-0.5+i/lats); z=r*math.sin(lat); rc=r*math.cos(lat)
        glBegin(GL_LINE_LOOP)
        for j in range(segs):
            a=2*math.pi*j/segs; glVertex3f(rc*math.cos(a),rc*math.sin(a),z)
        glEnd()
    for i in range(6):
        lon=math.pi*i/6
        glBegin(GL_LINE_LOOP)
        for j in range(segs):
            a=2*math.pi*j/segs
            glVertex3f(r*math.cos(lon)*math.cos(a),r*math.sin(lon)*math.cos(a),r*math.sin(a))
        glEnd()

# ══════════════════════════════════════════════
# 5. 2D オーバーレイ
# ══════════════════════════════════════════════

class Overlay:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.surf = pygame.Surface((w,h), pygame.SRCALPHA)
        self.f_lg = pygame.font.SysFont("Arial", 30, bold=True)
        self.f_md = pygame.font.SysFont("Arial", 19)
        self.f_sm = pygame.font.SysFont("Arial", 14)
        self.tex  = glGenTextures(1)
        self.rects: dict = {}

    def _btn(self, key, text, x, y, w, h,
             col=(55,110,190), selected=False, active=True):
        a = 195 if active else 60
        c = (50,155,95) if selected else col
        pygame.draw.rect(self.surf,(*c,a),(x,y,w,h),border_radius=7)
        if selected:
            pygame.draw.rect(self.surf,(100,230,130,210),(x,y,w,h),2,border_radius=7)
        fc = (255,255,255) if active else (100,110,130)
        lbl = self.f_sm.render(text, True, fc)
        self.surf.blit(lbl,(x+w//2-lbl.get_width()//2, y+h//2-lbl.get_height()//2))
        self.rects[key] = pygame.Rect(x,y,w,h)

    def draw(self, st, puzzles, pidx):
        self.surf.fill((0,0,0,0)); self.rects.clear()
        W,H = self.w, self.h
        gd = GROUPS[st["group"]]

        lbl = self.f_lg.render(gd["label"], True, (100,185,255))
        self.surf.blit(lbl,(W//2-lbl.get_width()//2,8))
        dsc = self.f_sm.render(gd["desc"], True, (85,105,135))
        self.surf.blit(dsc,(W//2-dsc.get_width()//2,44))
        order_lbl = self.f_sm.render(f"order: {len(gd['elems'])}", True, (70,90,120))
        self.surf.blit(order_lbl,(W//2-order_lbl.get_width()//2,62))

        self._btn("mode_free",   "Free",   10, 8,70,26, selected=(st["mode"]=="free"))
        self._btn("mode_puzzle", "Puzzle", 88, 8,80,26, selected=(st["mode"]=="puzzle"))

        if st["mode"]=="free":
            t=self.f_sm.render("Group:",True,(85,105,135)); self.surf.blit(t,(10,42))
            for i,gk in enumerate(GROUPS):
                self._btn(f"grp_{gk}",GROUPS[gk]["label"],
                          10,62+i*27,100,23,selected=(gk==st["group"]))
        else:
            t=self.f_sm.render("Puzzles:",True,(85,105,135)); self.surf.blit(t,(10,42))
            for i,p in enumerate(puzzles):
                self._btn(f"puz_{i}",p[2],10,62+i*30,165,25,selected=(i==pidx))
            tl=self.f_md.render("Goal: "+GROUPS[st["ptgt"]]["label"],True,(255,220,60))
            self.surf.blit(tl,(10,H-95))
            hist=" > ".join([GROUPS[g]["label"] for g in st["hist"]]+[gd["label"]])
            hl=self.f_sm.render(hist[-60:],True,(65,80,105)); self.surf.blit(hl,(10,H-68))

        ns = gd["nsubs"]
        if ns:
            t=self.f_sm.render("Divide by:",True,(85,105,135)); self.surf.blit(t,(W-175,58))
            for i,nk in enumerate(ns):
                ratio = len(gd["elems"])//len(GROUPS[nk]["elems"])
                self._btn(f"mrg_{nk}",f"/ {GROUPS[nk]['label']}  (x{ratio})",
                          W-175,80+i*40,165,32,active=not st["anim"])
        else:
            fl=self.f_md.render("C1 reached!",True,(80,230,130))
            self.surf.blit(fl,(W-175,88))

        self._btn("undo", "Undo (Z)",W-175,H-50,82,26)
        self._btn("reset","Reset (R)",W-88, H-50,78,26)

        if st["msg"] and st["msg_t"]>0:
            ml=self.f_md.render(st["msg"],True,(80,230,130))
            ms=pygame.Surface((ml.get_width()+20,ml.get_height()+10),pygame.SRCALPHA)
            ms.fill((0,0,0,170)); ms.blit(ml,(10,5))
            self.surf.blit(ms,(W//2-ms.get_width()//2,H-140))
        if st.get("solved"):
            cl=self.f_lg.render("CLEAR!",True,(80,230,130))
            self.surf.blit(cl,(W//2-cl.get_width()//2,H//2-16))

        hint=self.f_sm.render("Drag:rotate  Wheel:zoom  Z:Undo  R:Reset  ESC:quit",True,(42,52,72))
        self.surf.blit(hint,(W//2-hint.get_width()//2,H-18))

        raw=pygame.image.tostring(self.surf,"RGBA",False)
        glBindTexture(GL_TEXTURE_2D,self.tex)
        glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,W,H,0,GL_RGBA,GL_UNSIGNED_BYTE,raw)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR)

    def render_gl(self):
        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
        glOrtho(0,self.w,self.h,0,-1,1)
        glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D); glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
        glBindTexture(GL_TEXTURE_2D,self.tex)
        glColor4f(1,1,1,1)
        glBegin(GL_QUADS)
        glTexCoord2f(0,0); glVertex2f(0,0)
        glTexCoord2f(1,0); glVertex2f(self.w,0)
        glTexCoord2f(1,1); glVertex2f(self.w,self.h)
        glTexCoord2f(0,1); glVertex2f(0,self.h)
        glEnd()
        glDisable(GL_TEXTURE_2D); glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION); glPopMatrix()
        glMatrixMode(GL_MODELVIEW);  glPopMatrix()

    def hit(self, key, pos):
        r=self.rects.get(key)
        return r.collidepoint(pos) if r else False

# ══════════════════════════════════════════════
# 6. メイン
# ══════════════════════════════════════════════

def main():
    SW,SH = 1000,700
    pygame.init()
    pygame.display.set_mode((SW,SH),DOUBLEBUF|OPENGL)
    pygame.display.set_caption("Point Group Puzzle 3D")
    clock = pygame.time.Clock()

    glViewport(0,0,SW,SH)
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(45,SW/SH,0.1,100)
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST); glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_LIGHTING); glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0,GL_POSITION,[3,5,5,1])
    glLightfv(GL_LIGHT0,GL_DIFFUSE, [1,1,1,1])
    glLightfv(GL_LIGHT0,GL_AMBIENT, [0.3,0.3,0.3,1])
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK,GL_AMBIENT_AND_DIFFUSE)

    ov = Overlay(SW,SH)

    PUZZLES=[
        ("C4","C1","C4->C1"),
        ("C6","C1","C6->C1"),
        ("D4","C1","D4->C1"),
        ("C4v","C2","C4v->C2"),
        ("D6","C3","D6->C3"),
        ("Oh","O","Oh->O"),
        ("Oh","C1","Oh->C1 (hard)"),
    ]
    pidx=0

    st={
        "mode":"free","group":"C4",
        "hist":[],"ptgt":"C1","pstart":"C4",
        "anim":False,"anim_t":0.0,
        "anim_data":[],   # [(src_pt, tgt_pt, op_type, color)]
        "pending":"",
        "solved":False,"msg":"","msg_t":0.0,
        "rx":20.0,"ry":30.0,"zoom":4.5,
        "drag":False,"lm":(0,0),
    }
    ADUR=0.7

    def start_merge(nk):
        if st["anim"]: return
        G=GROUPS[st["group"]]; N=GROUPS[nk]
        assignment = compute_merge_assignment(st["group"], nk)
        src_pts = G["pts"]; tgt_pts = N["pts"]
        data=[]
        for i,sp in enumerate(src_pts):
            tp = tgt_pts[assignment[i]]
            op = classify_operation(sp, tp, G["elems"], N["elems"])
            data.append((sp.copy(), tp.copy(), op, ATOM_COLORS[i%len(ATOM_COLORS)]))
        st["anim_data"]=data; st["pending"]=nk
        st["anim"]=True; st["anim_t"]=0.0

    def finish_merge():
        st["hist"].append(st["group"])
        st["group"]=st["pending"]; st["anim"]=False
        if st["mode"]=="puzzle" and st["group"]==st["ptgt"]:
            st["solved"]=True; st["msg"]="CLEAR! Well done!"; st["msg_t"]=5.0

    def set_puzzle(i):
        nonlocal pidx; pidx=i; p=PUZZLES[i]
        st.update({"mode":"puzzle","group":p[0],"pstart":p[0],"ptgt":p[1],
                   "hist":[],"solved":False,"anim":False,
                   "msg":f"Goal: {GROUPS[p[1]]['label']}  Good luck!","msg_t":3.0})

    running=True
    while running:
        dt=clock.tick(60)/1000.0
        if st["msg_t"]>0: st["msg_t"]-=dt

        for ev in pygame.event.get():
            if ev.type==QUIT: running=False
            if ev.type==KEYDOWN:
                if ev.key==K_ESCAPE: running=False
                if ev.key==K_z and not st["anim"] and st["hist"]:
                    st["group"]=st["hist"].pop(); st["solved"]=False
                if ev.key==K_r:
                    if st["mode"]=="puzzle": st["group"]=st["pstart"]
                    st["hist"].clear(); st["solved"]=False; st["anim"]=False

            if ev.type==MOUSEBUTTONDOWN and ev.button==1:
                pos=ev.pos; consumed=False
                for key,action in [
                    ("mode_free",  lambda: st.update({"mode":"free","hist":[],"anim":False})),
                    ("mode_puzzle",lambda: set_puzzle(pidx)),
                    ("undo",       lambda: (st["hist"] and not st["anim"] and
                                   [st.update({"group":st["hist"].pop(),"solved":False})])),
                    ("reset",      lambda: [
                                   st.update({"group":st["pstart"]}) if st["mode"]=="puzzle" else None,
                                   st["hist"].clear(), st.update({"solved":False,"anim":False})]),
                ]:
                    if ov.hit(key,pos): action(); consumed=True; break
                if not consumed:
                    for gk in GROUPS:
                        if ov.hit(f"grp_{gk}",pos):
                            st.update({"group":gk,"hist":[],"anim":False}); consumed=True; break
                if not consumed:
                    for nk in GROUPS[st["group"]]["nsubs"]:
                        if ov.hit(f"mrg_{nk}",pos):
                            start_merge(nk); consumed=True; break
                if not consumed:
                    for i in range(len(PUZZLES)):
                        if ov.hit(f"puz_{i}",pos):
                            set_puzzle(i); consumed=True; break
                if not consumed:
                    st["drag"]=True; st["lm"]=pos

            if ev.type==MOUSEBUTTONUP and ev.button==1: st["drag"]=False
            if ev.type==MOUSEMOTION and st["drag"]:
                dx=ev.pos[0]-st["lm"][0]; dy=ev.pos[1]-st["lm"][1]
                st["ry"]+=dx*0.5; st["rx"]+=dy*0.5; st["lm"]=ev.pos
            if ev.type==MOUSEBUTTONDOWN and ev.button==4: st["zoom"]=max(2.0,st["zoom"]-0.25)
            if ev.type==MOUSEBUTTONDOWN and ev.button==5: st["zoom"]=min(10.0,st["zoom"]+0.25)

        if st["anim"]:
            st["anim_t"]+=dt
            if st["anim_t"]>=ADUR: finish_merge()

        # ── 描画 ──
        glClearColor(0.04,0.04,0.10,1)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0,0,-st["zoom"])
        glRotatef(st["rx"],1,0,0)
        glRotatef(st["ry"],0,1,0)

        glDisable(GL_LIGHTING)
        draw_axes(); draw_wire_sphere()
        glEnable(GL_LIGHTING)

        if st["anim"]:
            prog=min(1.0,st["anim_t"]/ADUR)
            glDisable(GL_LIGHTING)
            for sp,tp,op,col in st["anim_data"]:
                draw_trail(sp,tp,op,col)
            glEnable(GL_LIGHTING)
            for sp,tp,op,col in st["anim_data"]:
                pos=arc_path(sp,tp,prog,op)
                draw_sphere_at(pos,0.07,col)
        else:
            for i,p in enumerate(GROUPS[st["group"]]["pts"]):
                draw_sphere_at(p,0.07,ATOM_COLORS[i%len(ATOM_COLORS)])

        glDisable(GL_LIGHTING)
        ov.draw(st,PUZZLES,pidx)
        ov.render_gl()
        glEnable(GL_LIGHTING)

        pygame.display.flip()

    pygame.quit(); sys.exit()

if __name__=="__main__":
    main()