#!/usr/bin/env python3
"""12 рухів камери в ретро-нуарі «Нью-Йорк 1950-х» (1080x1920, 30 fps).

Мініатюрний 2.5D-рушій: мальовані текстури фасадів/вулиці/тротуарів натягуються на площини в перспективі
(PIL PERSPECTIVE, міпмапи, туман за глибиною), персонаж, ліхтарі й машини — спрайти, повернуті до камери,
з відображеннями на мокрому асфальті. Камера: позиція, поворот (yaw), нахил (pitch), крен (roll), фокус.

    python3 noir/cam3d.py noir/out/video_silent.mp4 [--stills 1,5] [--only 3]
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

import man
import tex

HERE = Path(__file__).resolve().parent
OW, OH, FPS = 1080, 1920, 30
NEAR = 0.08
FOG_C = (150, 120, 130)
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
Z0, Z1 = -70.0, 130.0                 # межі вулиці
STREET_X, WALK_X, FAC_X = 6.0, 9.5, 9.5


# ---------- текстури з міпмапами ----------
class Tex:
    def __init__(self, img):
        self.levels = [img.convert("RGBA")]
        while min(self.levels[-1].size) > 64:
            w, h = self.levels[-1].size
            self.levels.append(self.levels[-1].resize((max(1, w // 2), max(1, h // 2)), Image.BOX))

    @property
    def size(self):
        return self.levels[0].size


def build_world():
    L = Z1 - Z0
    W = {}
    W["fac_l"] = Tex(tex.facade(L, 42, seed=1))
    W["fac_r"] = Tex(tex.facade(L, 42, seed=2))
    W["street"] = Tex(tex.street(2 * STREET_X, L))
    W["walk"] = Tex(tex.sidewalk(WALK_X - STREET_X, L))
    W["sky"] = Tex(tex.sky())
    W["lamp"] = tex.lamp()
    W["taxi_f"], W["taxi_s"] = tex.car("taxi", "front"), tex.car("taxi", "side")
    W["sedan_f"], W["sedan_s"] = tex.car("sedan", "front"), tex.car("sedan", "side")
    return W


# ---------- камера ----------
class Cam:
    def __init__(self, x, y, z, yaw=0.0, pitch=0.0, roll=0.0, f=1000.0):
        self.x, self.y, self.z, self.yaw, self.pitch, self.roll, self.f = x, y, z, yaw, pitch, roll, f
        self.cy_, self.sy_ = math.cos(yaw), math.sin(yaw)
        self.cp, self.sp = math.cos(pitch), math.sin(pitch)

    def to_cam(self, p):
        dx, dy, dz = p[0] - self.x, p[1] - self.y, p[2] - self.z
        x1 = self.cy_ * dx - self.sy_ * dz
        z1 = self.sy_ * dx + self.cy_ * dz
        y2 = self.cp * dy - self.sp * z1
        z2 = self.sp * dy + self.cp * z1
        return x1, y2, z2

    def proj(self, p):
        x, y, z = self.to_cam(p)
        return OW / 2 + self.f * x / z, OH / 2 - self.f * y / z, z


def look_at(x, y, z, tx, ty, tz, roll=0.0, f=1000.0):
    yaw = math.atan2(tx - x, tz - z)
    pitch = math.atan2(ty - y, math.hypot(tx - x, tz - z))
    return Cam(x, y, z, yaw, pitch, roll, f)


# ---------- перспективна площина ----------
def persp_coeffs(dst, src):
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float))


def draw_quad(frame, cam, corners, texobj, src, fog_k=0.0):
    """corners: 4 світові точки (TL, TR, BR, BL); src: 4 точки текстури (рівень 0)."""
    pts = [cam.proj(c) for c in corners]
    if min(p[2] for p in pts) < NEAR:
        return False
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, y0 = max(0, int(min(xs))), max(0, int(min(ys)))
    x1, y1 = min(OW, int(max(xs)) + 1), min(OH, int(max(ys)) + 1)
    if x1 <= x0 or y1 <= y0:
        return True
    # вибір рівня міпмапи за співвідношенням розмірів
    src_w = math.hypot(src[1][0] - src[0][0], src[1][1] - src[0][1]) + 1e-6
    dst_w = max(math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]), math.hypot(pts[2][0] - pts[3][0], pts[2][1] - pts[3][1]))
    src_h = math.hypot(src[3][0] - src[0][0], src[3][1] - src[0][1]) + 1e-6
    dst_h = max(math.hypot(pts[3][0] - pts[0][0], pts[3][1] - pts[0][1]), math.hypot(pts[2][0] - pts[1][0], pts[2][1] - pts[1][1]))
    ratio = min(dst_w / src_w, dst_h / src_h)
    lvl = 0
    while ratio < 0.5 and lvl < len(texobj.levels) - 1:
        ratio *= 2
        lvl += 1
    sc = 0.5 ** lvl
    img = texobj.levels[lvl]
    dst = [(p[0] - x0, p[1] - y0) for p in pts]
    try:
        co = persp_coeffs(dst, [(u * sc, v * sc) for u, v in src])
    except np.linalg.LinAlgError:
        return True
    patch = img.transform((x1 - x0, y1 - y0), Image.PERSPECTIVE, tuple(co), resample=Image.BILINEAR)
    m = Image.new("L", patch.size, 0)
    ImageDraw.Draw(m).polygon(dst, fill=255)
    a = np.minimum(np.asarray(patch.getchannel("A")), np.asarray(m))
    if fog_k > 0.01:
        rgb = Image.blend(patch.convert("RGB"), Image.new("RGB", patch.size, FOG_C), min(0.85, fog_k))
        patch = rgb.convert("RGBA")
    patch.putalpha(Image.fromarray(a))
    frame.alpha_composite(patch, (x0, y0))
    return True


def fog(depth):
    return 1 - math.exp(-max(0.0, depth - 15) / 90)


def strip_list(W):
    """Площини світу, нарізані на смуги вздовж вулиці (для правильного порядку й обрізання біля камери)."""
    L = Z1 - Z0
    out = []
    n = 40
    for i in range(n):
        za, zb = Z0 + L * i / n, Z0 + L * (i + 1) / n
        ua, ub = (za - Z0) * tex.PPM, (zb - Z0) * tex.PPM
        fw, fh = W["fac_l"].size
        out.append(("ground", "street", [(-STREET_X, 0, zb), (STREET_X, 0, zb), (STREET_X, 0, za), (-STREET_X, 0, za)],
                    [(0, ub), (W["street"].size[0], ub), (W["street"].size[0], ua), (0, ua)]))
        sw = W["walk"].size[0]
        out.append(("ground", "walk", [(-WALK_X, 0.15, zb), (-STREET_X, 0.15, zb), (-STREET_X, 0.15, za), (-WALK_X, 0.15, za)],
                    [(sw, ub), (0, ub), (0, ua), (sw, ua)]))
        out.append(("ground", "walk", [(STREET_X, 0.15, zb), (WALK_X, 0.15, zb), (WALK_X, 0.15, za), (STREET_X, 0.15, za)],
                    [(0, ub), (sw, ub), (sw, ua), (0, ua)]))
        hm = fh / tex.PPM
        out.append(("wall", "fac_l", [(-FAC_X, hm, za), (-FAC_X, hm, zb), (-FAC_X, 0, zb), (-FAC_X, 0, za)],
                    [(ua, 0), (ub, 0), (ub, fh), (ua, fh)]))
        ra, rb = (Z1 - za) * tex.PPM, (Z1 - zb) * tex.PPM
        out.append(("wall", "fac_r", [(FAC_X, hm, zb), (FAC_X, hm, za), (FAC_X, 0, za), (FAC_X, 0, zb)],
                    [(rb, 0), (ra, 0), (ra, fh), (rb, fh)]))
    sw, sh = W["sky"].size
    out.append(("sky", "sky", [(-170, 330, Z1 + 40), (170, 330, Z1 + 40), (170, 0, Z1 + 40), (-170, 0, Z1 + 40)],
                [(0, 0), (sw, 0), (sw, sh), (0, sh)]))
    out.append(("sky", "sky", [(170, 330, Z0 - 40), (-170, 330, Z0 - 40), (-170, 0, Z0 - 40), (170, 0, Z0 - 40)],
                [(0, 0), (sw, 0), (sw, sh), (0, sh)]))
    return out


def split_draw(frame, cam, W, kind, name, corners, src, depth=0):
    """Малює смугу; якщо частина за камерою — ділить уздовж і відкидає невидимі шматки."""
    zs = [cam.to_cam(c)[2] for c in corners]
    if max(zs) < NEAR:
        return
    if min(zs) >= NEAR:
        d = sum(zs) / 4
        draw_quad(frame, cam, corners, W[name], src, fog_k=0 if kind == "sky" else fog(d))
        return
    if depth > 5:
        return
    # ділимо навпіл по довшій стороні (0-1 / 3-2 або 0-3 / 1-2)
    def mid(a, b):
        return tuple((x + y) / 2 for x, y in zip(a, b))
    c0, c1, c2, c3 = corners
    s0, s1, s2, s3 = src
    if kind == "wall":
        m01, m32 = mid(c0, c1), mid(c3, c2)
        t01, t32 = mid(s0, s1), mid(s3, s2)
        split_draw(frame, cam, W, kind, name, [c0, m01, m32, c3], [s0, t01, t32, s3], depth + 1)
        split_draw(frame, cam, W, kind, name, [m01, c1, c2, m32], [t01, s1, s2, t32], depth + 1)
    else:
        m03, m12 = mid(c0, c3), mid(c1, c2)
        t03, t12 = mid(s0, s3), mid(s1, s2)
        split_draw(frame, cam, W, kind, name, [c0, c1, m12, m03], [s0, s1, t12, t03], depth + 1)
        split_draw(frame, cam, W, kind, name, [m03, m12, c2, c3], [t03, t12, s2, s3], depth + 1)


# ---------- спрайти ----------
@lru_cache(maxsize=256)
def reflected(key, img_id):
    img = SPRITES[key]
    r = img.transpose(Image.FLIP_TOP_BOTTOM)
    a = np.asarray(r.getchannel("A")).astype(np.float32)
    grad = np.linspace(0.42, 0.0, r.height)[:, None]
    r.putalpha(Image.fromarray((a * grad).astype(np.uint8)))
    return r.filter(ImageFilter.GaussianBlur(3))


SPRITES = {}


def put_sprite(frame, cam, img, key, x, z, height_m, reflect=True, flip=False):
    base = cam.proj((x, 0, z))
    top = cam.proj((x, height_m, z))
    if base[2] < NEAR or top[2] < NEAR:
        return
    h = math.hypot(top[0] - base[0], top[1] - base[1])
    if h < 3:
        return
    w = h * img.width / img.height
    if w > OW * 3 or h > OH * 3:
        return
    k = key + ("f" if flip else "")
    if k not in SPRITES:
        SPRITES[k] = img.transpose(Image.FLIP_LEFT_RIGHT) if flip else img
    src = SPRITES[k]
    ang = math.degrees(math.atan2(top[0] - base[0], base[1] - top[1]))
    sz = (max(1, int(w)), max(1, int(h)))
    spr = src.resize(sz, Image.BILINEAR)
    fk = fog(base[2])
    if fk > 0.02:
        rgb = Image.blend(spr.convert("RGB"), Image.new("RGB", sz, FOG_C), min(0.8, fk))
        rgb.putalpha(spr.getchannel("A"))
        spr = rgb
    if reflect:
        r = reflected(k, id(src)).resize(sz, Image.BILINEAR)
        if abs(ang) > 0.5:
            r = r.rotate(-ang, expand=True, resample=Image.BILINEAR)
        frame.alpha_composite(r, (int(base[0] - r.width / 2), int(base[1])))
    if abs(ang) > 0.5:
        spr = spr.rotate(-ang, expand=True, resample=Image.BILINEAR)
        frame.alpha_composite(spr, (int((base[0] + top[0]) / 2 - spr.width / 2), int((base[1] + top[1]) / 2 - spr.height / 2)))
    else:
        frame.alpha_composite(spr, (int(base[0] - w / 2), int(base[1] - h)))


def man_view(cam, mx, mz, facing):
    """Ракурс героя: кут між напрямком, куди він дивиться, і напрямком на камеру."""
    to_cam = math.atan2(cam.x - mx, cam.z - mz)
    rel = (math.degrees(to_cam - facing) + 540) % 360 - 180      # 0 = камера попереду
    a = abs(rel)
    view = "front" if a < 25 else "front34" if a < 65 else "side" if a < 115 else "back34" if a < 155 else "back"
    flip = rel > 0                                               # профіль дивиться в бік руху
    return view, flip


# ---------- сцена ----------
LAMPS = [(sx * 6.4, z) for z in range(-60, 125, 14) for sx in (-1, 1)]
CARS = [("taxi", -3.0, 26.0, "street"), ("sedan", 3.2, 48.0, "street"), ("taxi", -4.6, 70.0, "parked"),
        ("sedan", -4.6, -14.0, "parked"), ("taxi", 4.6, 6.0, "parked"), ("taxi", -2.8, -40, "street")]


def render(W, cam, man_state, extra=None):
    frame = Image.new("RGBA", (OW, OH), (60, 54, 70, 255))
    items = strip_list(W)
    sky = [it for it in items if it[0] == "sky"]
    ground = [it for it in items if it[0] == "ground"]
    walls = [it for it in items if it[0] == "wall"]
    for it in sky:
        split_draw(frame, cam, W, *it)

    def depth(corners):
        return max(cam.to_cam(c)[2] for c in corners)
    for it in sorted(ground, key=lambda it: -depth(it[2])):
        split_draw(frame, cam, W, *it)
    # спрайти + стіни разом, від дальніх до ближніх
    objs = []
    for it in walls:
        objs.append((sum(cam.to_cam(c)[2] for c in it[2]) / 4, "wall", it))
    for i, (lx, lz) in enumerate(LAMPS):
        objs.append((cam.to_cam((lx, 2, lz))[2], "lamp", (lx, lz)))
    for i, (kind, cx_, cz, mode) in enumerate(CARS):
        objs.append((cam.to_cam((cx_, 1, cz))[2], "car", (kind, cx_, cz, mode)))
    mx, mz, facing, phase = man_state
    objs.append((cam.to_cam((mx, 1, mz))[2], "man", None))
    for dpt, kind, it in sorted(objs, key=lambda o: -o[0]):
        if dpt < NEAR:
            continue
        if kind == "wall":
            split_draw(frame, cam, W, *it)
        elif kind == "lamp":
            put_sprite(frame, cam, W["lamp"], "lamp", it[0], it[1], 4.4)
        elif kind == "car":
            k, cx_, cz, mode = it
            ang = abs((math.degrees(math.atan2(cam.x - cx_, cam.z - cz)) + 540) % 360 - 180)
            side = 50 < ang < 130
            img = W[f"{k}_{'s' if side else 'f'}"]
            put_sprite(frame, cam, img, f"{k}_{'s' if side else 'f'}", cx_, cz, 1.55 if not side else 1.5)
        else:
            view, flip = man_view(cam, mx, mz, facing)
            spr = man.sprite(view, phase)
            put_sprite(frame, cam, spr, f"man_{view}_{phase}", mx, mz, 1.85, flip=flip)
    if extra:
        extra(frame, cam)
    out = frame.convert("RGB")
    if cam.roll:
        big = out.rotate(math.degrees(cam.roll), resample=Image.BICUBIC, expand=False)
        z = 1 + abs(math.sin(cam.roll)) * 1.2
        w, h = int(OW / z), int(OH / z)
        out = big.crop(((OW - w) // 2, (OH - h) // 2, (OW + w) // 2, (OH + h) // 2)).resize((OW, OH), Image.BICUBIC)
    return out


# ---------- дощ, кольорокорекція, підписи ----------
RNG = np.random.default_rng(9)
DROPS = RNG.uniform(0, 1, (420, 3))


def rain(img, t, speed=1.0):
    d = ImageDraw.Draw(img, "RGBA")
    for x0, y0, k in DROPS:
        y = ((y0 + t * (1.6 + k) * speed) % 1.0) * (OH + 200) - 100
        x = x0 * OW + y * 0.08
        ln = 30 + 50 * k
        d.line((x, y, x + ln * 0.08, y + ln), fill=(220, 220, 240, int(60 + 60 * k)), width=2)
    return img


_YY, _XX = np.mgrid[0:OH, 0:OW].astype(np.float32)
_VIG = np.clip(1.06 - 0.28 * (((_XX - OW / 2) / (OW / 2)) ** 2 + ((_YY - OH / 2) / (OH / 2)) ** 2) ** 1.3, 0.6, 1)
GRAIN = [RNG.normal(0, 6, (OH // 2, OW // 2)).astype(np.float32) for _ in range(6)]


def grade(img, t):
    a = np.asarray(img).astype(np.float32) / 255
    lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    a = a * ((lum + 0.18 * (lum - lum ** 2) * (lum - 0.5) * 4) / np.maximum(lum, 1e-4))[..., None]
    sh, hi = np.clip(1 - lum * 2, 0, 1)[..., None], np.clip(lum * 2 - 1, 0, 1)[..., None]
    a += sh * np.array([-0.01, 0.0, 0.04]) + hi * np.array([0.05, 0.02, -0.03])
    small = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((OW // 8, OH // 8), Image.BILINEAR)
    b = np.asarray(small.filter(ImageFilter.GaussianBlur(5)).resize((OW, OH), Image.BILINEAR)).astype(np.float32) / 255
    a += np.clip(b - 0.6, 0, 1) * 0.7
    a *= _VIG[..., None]
    g = np.asarray(Image.fromarray(GRAIN[int(t * FPS) % 6]).resize((OW, OH)))[..., None] / 255
    a += g
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def tag(img, text, sub=None, big=False):
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(BOLD, 74 if not big else 92)
    tw = d.textlength(text, font=f)
    x, y = (OW - tw) / 2, OH - 330
    d.rounded_rectangle((x - 34, y - 18, x + tw + 34, y + 96), radius=18, fill=(255, 214, 40), outline=(14, 12, 16), width=6)
    d.text((x, y), text, font=f, fill=(14, 12, 16))
    if sub:
        f2 = ImageFont.truetype(BOLD, 40)
        sw = d.textlength(sub, font=f2)
        d.text(((OW - sw) / 2, y - 76), sub, font=f2, fill=(255, 240, 200), stroke_width=4, stroke_fill=(14, 12, 16))


def title(img, k):
    d = ImageDraw.Draw(img, "RGBA")
    f = ImageFont.truetype(BOLD, 96)
    f2 = ImageFont.truetype(BOLD, 46)
    a = int(255 * k)
    t1, t2 = "12 Camera Moves", "Retro Noir · 1950s New York"
    w1, w2 = d.textlength(t1, font=f), d.textlength(t2, font=f2)
    d.rounded_rectangle(((OW - w1) / 2 - 40, 210, (OW + w1) / 2 + 40, 350), radius=16, fill=(14, 12, 16, a))
    d.text(((OW - w1) / 2, 230), t1, font=f, fill=(250, 246, 236, a))
    d.rounded_rectangle(((OW - w2) / 2 - 30, 370, (OW + w2) / 2 + 30, 450), radius=14, fill=(255, 214, 40, a),
                        outline=(14, 12, 16, a), width=5)
    d.text(((OW - w2) / 2, 382), t2, font=f2, fill=(14, 12, 16, a))


# ---------- 12 рухів ----------
DUR = 3.3
SPEED = 1.15                       # м/с, герой іде назустріч (−z)
FACING = math.pi                   # дивиться в −z


def man_at(t, z0=22.0, x=1.2, walking=True):
    z = z0 - (SPEED * t if walking else 0)
    phase = int((SPEED * t / 1.5 * 8)) % 8 if walking else -1
    return x, z, FACING, phase


def orbit(mx, mz, r, ang_deg, h, ty=1.3, roll=0.0, f=1000.0):
    a = math.radians(ang_deg)                    # 0 = попереду героя (з боку −z)
    cx, cz = mx + r * math.sin(a), mz - r * math.cos(a)
    return look_at(cx, h, cz, mx, ty, mz, roll, f)


def ease(u):
    return u * u * (3 - 2 * u)


def shot_cam(i, u, t):
    """i — номер руху, u — 0..1 у межах кадру, t — час кадру. Повертає (камера, стан героя, підпис)."""
    st = man_at(t)
    mx, mz = st[0], st[1]
    if i == 0:   # BackwardOrbit: камера відступає й облітає героя
        return orbit(mx, mz, 3.5 + 3 * ease(u), -10 + 75 * ease(u), 1.7), st, "/BackwardOrbit"
    if i == 1:   # PendulumSwing: за плечем, маятник з креном
        sw = math.sin(u * 2 * math.pi)
        return orbit(mx, mz, 3.0, 180 + 28 * sw, 1.9, roll=math.radians(7 * sw)), st, "/PendulumSwing"
    if i == 2:   # FPV: швидкий проліт уздовж вулиці повз героя з нахилом
        z = mz + 16 - 30 * ease(u)
        x = 3.5 * math.sin(u * math.pi) - 1
        cam = Cam(x, 2.2 - 0.9 * u, z, yaw=math.pi + 0.25 * math.cos(u * math.pi), pitch=-0.06,
                  roll=math.radians(-12 * math.sin(u * math.pi * 1.5)), f=820)
        return cam, st, "/FPV"
    if i == 3:   # DollyIn
        return orbit(mx, mz, 9 - 6.5 * ease(u), 0, 1.65, ty=1.45), st, "/DollyIn"
    if i == 4:   # Static
        mz0 = man_at(i * DUR)[1]                     # камера нерухома відносно початку кадру
        return look_at(-1.3, 1.55, mz0 - 6.5, 1.2, 1.3, mz0, 0, 1000), st, "/Static"
    if i == 5:   # DollyOut
        return orbit(mx, mz, 2.5 + 9 * ease(u), 8, 1.65 + 1.2 * u, ty=1.4), st, "/DollyOut"
    if i == 6:   # LowArcAround: низько, знизу вгору, дуга навколо
        return orbit(mx, mz, 2.4, -50 + 120 * ease(u), 0.35, ty=1.25, f=900), st, "/LowArcAround"
    if i == 7:   # Close-up
        return orbit(mx, mz, 1.35 - 0.25 * u, 6, 1.72, ty=1.66, f=1150), st, "/Close-up"
    if i == 8:   # Crane: підйом з нахилом донизу
        h = 1.5 + 9 * ease(u)
        return orbit(mx, mz, 4.5 + 2 * u, 150, h, ty=1.0), st, "/Crane"
    if i == 9:   # Ground-Skim: над самою мокрою бруківкою
        z = mz - 22 + 14 * ease(u)
        return Cam(0.3, 0.16, z, yaw=math.radians(3), pitch=math.radians(2.5), f=900), st, "/Ground-Skim"
    if i == 10:  # Tilt: від решітки таксі вгору до хмарочосів
        p = math.radians(-24 + 62 * ease(u))
        return Cam(4.6, 0.9, 1.3, yaw=math.radians(-2), pitch=p, f=900), man_at(t, z0=26), "/Tilt"
    # SnapZoom: різкий наїзд оптикою
    k = 0 if u < 0.35 else ease(min(1, (u - 0.35) / 0.12))
    f = 900 + 2100 * k
    return look_at(-1.8, 1.65, mz - 10, mx, 1.6, mz, 0, f), st, "/SnapZoom"


TITLE = 2.0
TOTAL = 12 * DUR


def frame_at(W, t):
    i = min(11, int(t // DUR))
    u = (t - i * DUR) / DUR
    cam, st, label = shot_cam(i, u, t)
    extra = None
    img = render(W, cam, st, extra)
    rain(img, t, speed=1.6 if i in (2, 9) else 1.0)
    if i == 11 and 0.35 < u < 0.5:                           # розмиття руху під час снеп-зуму
        img = Image.blend(img, img.resize((OW // 3, OH // 3)).resize((OW, OH)).filter(ImageFilter.GaussianBlur(4)), 0.5)
    img = grade(img, t)
    tag(img, label, sub=f"{i + 1:02d} / 12")
    if t < TITLE:
        title(img, min(1, (TITLE - t) / 0.5))
    if u < 4 / FPS and i > 0:                                # коротке затемнення на стиках
        img = Image.blend(img, Image.new("RGB", img.size, (10, 8, 12)), 0.5 * (1 - u * FPS / 4))
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--stills", default="")
    ap.add_argument("--only", type=int, default=-1)
    a = ap.parse_args()
    W = build_world()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if a.stills:
        for s in a.stills.split(","):
            frame_at(W, float(s)).save(out.parent / f"still_{float(s):05.2f}.png")
        return
    t0, t1 = (0, TOTAL) if a.only < 0 else (a.only * DUR, (a.only + 1) * DUR)
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
                             f"{OW}x{OH}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                             "-crf", "20", "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    n0, n1 = int(t0 * FPS), int(t1 * FPS)
    for k in range(n0, n1):
        proc.stdin.write(frame_at(W, k / FPS).tobytes())
        if k % 60 == 0:
            print(f"  {k}/{n1}", flush=True)
    proc.stdin.close()
    proc.wait()
    json.dump({"dur": DUR, "total": TOTAL, "moves": 12}, open(out.parent / "timing.json", "w"))
    print("Готово:", out)


if __name__ == "__main__":
    main()
