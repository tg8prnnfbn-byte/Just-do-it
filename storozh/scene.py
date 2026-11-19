"""«Правила для нічного сторожа» — 3D-сцена в Blender (bpy), Cycles, 9:16, 30 fps, 6 кадрів (36 с).

    ~/bpy-venv/bin/python storozh/scene.py --save storozh/out/storozh.blend
    ~/bpy-venv/bin/python storozh/scene.py --render 0 180 storozh/out/frames/    # діапазон кадрів
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
FPS = 30
RES = (720, 1280)          # рендер, потім апскейл до 1080x1920
SHOTS = [("s1_exterior", 0, 180), ("s2_rules", 180, 360), ("s3_swing", 360, 570),
         ("s4_speaker", 570, 720), ("s5_window", 720, 870), ("s6_hide", 870, 1080)]
R = random.Random(7)


# ---------- утиліти ----------
def mat(name, color, rough=0.8, emit=None, emit_k=0.0, noise=0.0, noise_scale=6.0, color2=None, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if noise > 0:                                   # мальована фактура: шум змішує два відтінки
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = noise_scale
        tex.inputs["Detail"].default_value = 6
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        c2 = color2 or tuple(c * (1 - noise) for c in color)
        ramp.color_ramp.elements[0].color = (*c2, 1)
        ramp.color_ramp.elements[1].color = (*color, 1)
        nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = (*color, 1)
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1)
        bsdf.inputs["Emission Strength"].default_value = emit_k
    return m


def obj_add(fn, name, mat_=None, bevel=0.0, **kw):
    fn(**kw)
    o = bpy.context.active_object
    o.name = name
    if mat_:
        o.data.materials.append(mat_)
    if bevel:
        b = o.modifiers.new("bevel", "BEVEL")
        b.width = bevel
        b.segments = 2
    return o


def box(name, loc, size, m, bevel=0.02):
    o = obj_add(bpy.ops.mesh.primitive_cube_add, name, m, bevel, size=1, location=loc)
    o.scale = size
    return o


def cyl(name, loc, r, depth, m, rot=(0, 0, 0), verts=16, r2=None, fill="NGON"):
    if r2 is not None:
        o = obj_add(bpy.ops.mesh.primitive_cone_add, name, m, 0, vertices=verts, radius1=r, radius2=r2, depth=depth,
                    location=loc, rotation=rot, end_fill_type=fill)
    else:
        o = obj_add(bpy.ops.mesh.primitive_cylinder_add, name, m, 0, vertices=verts, radius=r, depth=depth, location=loc,
                    rotation=rot)
    return o


def sphere(name, loc, r, m, sub=2):
    o = obj_add(bpy.ops.mesh.primitive_ico_sphere_add, name, m, 0, subdivisions=sub, radius=r, location=loc)
    bpy.ops.object.shade_smooth()
    return o


def point_light(name, loc, energy, color, radius=0.15):
    ld = bpy.data.lights.new(name, "POINT")
    ld.energy, ld.color, ld.shadow_soft_size = energy, color, radius
    o = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    return o


def key(o, path, frame, value=None, index=-1):
    if value is not None:
        setattr(o, path, value)
    o.keyframe_insert(path, frame=frame, index=index)


# ---------- світ ----------
def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 0, SHOTS[-1][2] - 1
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 16
    sc.cycles.adaptive_threshold = 0.04
    sc.render.use_persistent_data = True
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.render.image_settings.file_format = "PNG"
    sc.view_settings.look = "AgX - Medium High Contrast"
    world = bpy.data.worlds.new("night")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.03, 0.045, 0.1, 1)
    bg.inputs["Strength"].default_value = 1.2

    moon = bpy.data.lights.new("moon", "SUN")
    moon.energy, moon.color, moon.angle = 1.1, (0.55, 0.65, 1.0), math.radians(2)
    mo = bpy.data.objects.new("moon", moon)
    sc.collection.objects.link(mo)
    mo.rotation_euler = (math.radians(55), 0, math.radians(-35))

    # матеріали
    M = dict(
        grass=mat("grass", (0.05, 0.07, 0.04), 0.95, noise=0.6, noise_scale=3, color2=(0.09, 0.06, 0.03)),
        asphalt=mat("asphalt", (0.09, 0.09, 0.1), 0.85, noise=0.4, noise_scale=12),
        wall=mat("wall", (0.62, 0.52, 0.32), 0.9, noise=0.35, noise_scale=4),
        roof=mat("roof", (0.18, 0.12, 0.1), 0.8, noise=0.3),
        frame=mat("frame", (0.85, 0.85, 0.8), 0.6),
        dark_win=mat("dark_win", (0.02, 0.025, 0.04), 0.1, metal=0.2),
        lit_win=mat("lit_win", (1, 0.75, 0.4), 0.5, emit=(1, 0.7, 0.35), emit_k=4.0),
        lit_win2=mat("lit_win2", (1, 0.85, 0.6), 0.5, emit=(1, 0.8, 0.55), emit_k=2.5),
        red=mat("red", (0.55, 0.06, 0.05), 0.5, noise=0.2),
        blue=mat("blue", (0.08, 0.2, 0.45), 0.5, noise=0.2),
        yellow=mat("yellow", (0.75, 0.55, 0.05), 0.5, noise=0.2),
        metal=mat("metal", (0.25, 0.26, 0.28), 0.45, metal=0.7),
        wood=mat("wood", (0.35, 0.2, 0.1), 0.8, noise=0.4, noise_scale=20),
        sand=mat("sand", (0.55, 0.45, 0.28), 0.95, noise=0.4, noise_scale=25),
        fence=mat("fence", (0.12, 0.25, 0.16), 0.6),
        trunk=mat("trunk", (0.12, 0.08, 0.06), 0.9),
        leaves=mat("leaves", (0.45, 0.2, 0.05), 0.85, noise=0.5, noise_scale=5, color2=(0.25, 0.08, 0.03)),
        lamp_glass=mat("lamp_glass", (1, 0.8, 0.5), 0.3, emit=(1, 0.72, 0.4), emit_k=12),
        horn=mat("horn", (0.42, 0.3, 0.16), 0.5, metal=0.5, noise=0.4, noise_scale=8),
        jacket=mat("jacket", (0.1, 0.15, 0.1), 0.8, noise=0.2),
        skin=mat("skin", (0.65, 0.45, 0.35), 0.6),
        cap=mat("cap", (0.06, 0.06, 0.07), 0.7),
        kid=mat("kid", (0.015, 0.015, 0.02), 0.9),
        eye=mat("eye", (1, 1, 0.9), 0.4, emit=(1, 0.95, 0.8), emit_k=0.0),
        paper=None,
    )
    pm = bpy.data.materials.new("paper")
    pm.use_nodes = True
    it = pm.node_tree.nodes.new("ShaderNodeTexImage")
    it.image = bpy.data.images.load(str(HERE / "tex" / "rules.png"))
    pm.node_tree.links.new(it.outputs["Color"], pm.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    pm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
    M["paper"] = pm

    # земля, майданчик
    g = obj_add(bpy.ops.mesh.primitive_plane_add, "ground", M["grass"], size=120)
    box("pad", (0, 0, 0.02), (16, 12, 0.04), M["asphalt"], 0.0)
    # будівля дитсадка (2 поверхи)
    box("building", (0, 14, 3.6), (26, 9, 7.2), M["wall"], 0.05)
    box("roof", (0, 14, 7.35), (26.6, 9.6, 0.3), M["roof"])
    lit_upper = None
    for fl, z in enumerate((1.6, 5.0)):
        for i in range(9):
            x = -11 + i * 2.75
            lit = (fl == 1 and i == 6)
            m_ = M["lit_win"] if lit else (M["lit_win2"] if (fl == 0 and i == 1) else M["dark_win"])
            box(f"winframe_{fl}_{i}", (x, 9.49, z), (1.6, 0.03, 2.0), M["frame"], 0.0)
            w = box(f"win_{fl}_{i}", (x, 9.46, z), (1.4, 0.03, 1.8), m_, 0.0)
            box(f"winbar_{fl}_{i}", (x, 9.43, z), (0.07, 0.03, 1.8), M["frame"], 0.0)
            box(f"winbarh_{fl}_{i}", (x, 9.43, z + 0.3), (1.4, 0.03, 0.06), M["frame"], 0.0)
            if lit:
                lit_upper = w
    box("door", (8.5, 9.45, 1.1), (1.6, 0.1, 2.3), M["wood"])
    point_light("win_glow", (5.5, 8.6, 5.0), 60, (1, 0.7, 0.4), 0.6)
    point_light("win_glow2", (-8.25, 8.6, 1.6), 25, (1, 0.8, 0.6), 0.6)
    # паркан
    for i in range(-24, 25):
        cyl(f"fence_f_{i}", (i * 0.5, -9, 0.7), 0.025, 1.4, M["fence"], verts=6)
    box("fence_rail_top", (0, -9, 1.3), (24, 0.05, 0.05), M["fence"], 0)
    box("fence_rail_low", (0, -9, 0.3), (24, 0.05, 0.05), M["fence"], 0)
    box("gate_gap", (0, -9, 0.7), (2.2, 0.2, 1.6), M["grass"], 0)   # прохід (заслонимо стовпчиками воріт)
    for x in (-1.2, 1.2):
        cyl(f"gate_post_{x}", (x, -9, 0.9), 0.07, 1.8, M["metal"], verts=8)
    bpy.data.objects.remove(bpy.data.objects["gate_gap"])
    # пісочниця
    for dx, dy, sx, sy in ((0, 1.4, 3, 0.15), (0, -1.4, 3, 0.15), (1.45, 0, 0.15, 2.8), (-1.45, 0, 0.15, 2.8)):
        box(f"sbox_{dx}_{dy}", (-4 + dx, 2 + dy, 0.18), (sx, sy, 0.3), M["wood"])
    box("sand", (-4, 2, 0.12), (2.8, 2.7, 0.16), M["sand"], 0.0)
    # гірка
    for x in (-0.4, 0.4):
        cyl(f"slide_leg_{x}", (-6.5 + x, -3, 0.9), 0.04, 1.8, M["metal"], verts=8)
    box("slide_top", (-6.5, -3, 1.8), (1.0, 1.0, 0.08), M["red"])
    s = box("slide", (-6.5, -4.4, 0.95), (0.7, 2.4, 0.05), M["yellow"])
    s.rotation_euler = (math.radians(-38), 0, 0)
    box("slide_roof", (-6.5, -3, 2.6), (1.2, 1.2, 0.08), M["blue"])
    for i in range(5):
        box(f"ladder_{i}", (-6.5, -2.45, 0.35 + i * 0.35), (0.8, 0.05, 0.04), M["metal"], 0)
    # гойдалка
    for x in (2.2, 5.0):
        for dy in (-0.5, 0.5):
            leg = cyl(f"sw_leg_{x}_{dy}", (x, 1.5 + dy * 0.6, 1.2), 0.05, 2.5, M["metal"], verts=8)
            leg.rotation_euler = (math.radians(14 * (1 if dy > 0 else -1)), 0, 0)
    cyl("sw_bar", (3.6, 1.5, 2.4), 0.05, 3.0, M["metal"], rot=(0, math.radians(90), 0), verts=8)
    pivot = bpy.data.objects.new("swing_pivot", None)
    sc.collection.objects.link(pivot)
    pivot.location = (3.6, 1.5, 2.38)
    for dx in (-0.3, 0.3):
        c = cyl(f"chain_{dx}", (3.6 + dx, 1.5, 1.6), 0.012, 1.55, M["metal"], verts=6)
        c.parent = pivot
        c.location = (dx, 0, -0.78)
    seat = box("seat", (0, 0, 0), (0.75, 0.3, 0.05), M["wood"])
    seat.parent = pivot
    seat.location = (0, 0, -1.58)
    # лавка
    box("bench", (-1.5, 6.5, 0.45), (2.0, 0.45, 0.06), M["wood"])
    for x in (-2.3, -0.7):
        box(f"bench_leg_{x}", (x, 6.5, 0.22), (0.06, 0.4, 0.44), M["metal"], 0)
    # ліхтарі
    lamps = []
    for i, (x, y) in enumerate(((-7, -2), (7, 4))):
        cyl(f"lamp_pole_{i}", (x, y, 2.2), 0.06, 4.4, M["metal"], verts=8)
        box(f"lamp_arm_{i}", (x + 0.35, y, 4.35), (0.75, 0.06, 0.06), M["metal"], 0)
        cyl(f"lamp_head_{i}", (x + 0.7, y, 4.2), 0.22, 0.18, M["metal"], r2=0.05, verts=12)
        sphere(f"lamp_bulb_{i}", (x + 0.7, y, 4.08), 0.09, M["lamp_glass"], 1)
        lamps.append(point_light(f"lamp_{i}", (x + 0.7, y, 4.0), 700, (1, 0.72, 0.42), 0.12))
    # гучномовець-«дзвін» на стовпі
    cyl("spk_pole", (6, -5, 3.0), 0.07, 6.0, M["wood"], verts=8)
    horn = cyl("horn", (6.2, -5.45, 5.6), 0.45, 0.9, M["horn"], rot=(math.radians(-80), 0, math.radians(25)), verts=24, r2=0.08, fill="NOTHING")
    sol = horn.modifiers.new("solid", "SOLIDIFY")
    sol.thickness = 0.03
    box("spk_bracket", (6.15, -5.05, 5.6), (0.3, 0.08, 0.08), M["metal"], 0)
    point_light("spk_light", (7.6, -6.2, 6.4), 120, (1, 0.75, 0.5), 0.3)
    # дерева
    for i in range(14):
        x, y = R.choice([R.uniform(-30, -10), R.uniform(10, 30)]), R.uniform(-15, 25)
        if abs(x) < 10 and abs(y) < 10:
            continue
        h = R.uniform(3, 6)
        cyl(f"trunk_{i}", (x, y, h / 2), 0.15, h, M["trunk"], verts=8)
        for k in range(3):
            sphere(f"crown_{i}_{k}", (x + R.uniform(-0.8, 0.8), y + R.uniform(-0.8, 0.8), h + R.uniform(-0.3, 0.8)),
                   R.uniform(1.0, 1.8), M["leaves"], 1)
    # будка сторожа (окремий набір далеко збоку)
    BX = 60
    box("booth_floor", (BX, 0, 0), (4, 4, 0.1), M["wood"], 0)
    box("booth_wall_b", (BX, 2, 1.5), (4, 0.1, 3), M["wall"], 0)
    box("booth_wall_l", (BX - 2, 0, 1.5), (0.1, 4, 3), M["wall"], 0)
    box("booth_wall_r", (BX + 2, 0, 1.5), (0.1, 4, 3), M["wall"], 0)
    box("booth_window", (BX + 0.6, 1.94, 1.7), (1.4, 0.04, 1.0), M["dark_win"], 0)
    box("desk", (BX, 1.2, 0.75), (1.8, 0.9, 0.06), M["wood"])
    for dx in (-0.8, 0.8):
        box(f"desk_leg_{dx}", (BX + dx, 1.2, 0.37), (0.06, 0.8, 0.74), M["wood"], 0)
    paper = obj_add(bpy.ops.mesh.primitive_plane_add, "rules", M["paper"], size=1, location=(BX - 0.1, 1.1, 0.785))
    paper.scale = (0.21, 0.29, 1)
    paper.rotation_euler = (0, 0, math.radians(-8))
    cyl("mug", (BX + 0.55, 1.3, 0.84), 0.05, 0.12, M["red"], verts=16)
    cyl("desk_lamp_base", (BX + 0.6, 1.45, 0.8), 0.08, 0.03, M["metal"], verts=16)
    cyl("desk_lamp_shade", (BX + 0.45, 1.3, 1.15), 0.14, 0.16, M["blue"], r2=0.04, rot=(0, math.radians(30), 0), verts=16)
    point_light("desk_light", (BX + 0.35, 1.25, 1.05), 18, (1, 0.8, 0.55), 0.05)
    box("flashlight", (BX - 0.6, 1.35, 0.8), (0.25, 0.05, 0.05), M["metal"], 0)

    # сторож (видно ззаду)
    def watchman(loc):
        b = cyl("w_body", (loc[0], loc[1], 1.0), 0.32, 1.2, M["jacket"], verts=16)
        bv = b.modifiers.new("bevel", "BEVEL"); bv.width = 0.12; bv.segments = 3
        sphere("w_head", (loc[0], loc[1], 1.78), 0.2, M["skin"])
        cyl("w_cap", (loc[0], loc[1], 1.93), 0.21, 0.12, M["cap"], verts=16)
        for dx in (-0.12, 0.12):
            cyl(f"w_leg_{dx}", (loc[0] + dx, loc[1], 0.22), 0.1, 0.45, M["cap"], verts=8)
        arm = cyl("w_arm", (loc[0] + 0.33, loc[1] + 0.25, 1.15), 0.06, 0.6, M["jacket"], rot=(math.radians(70), 0, 0), verts=8)
        torch = cyl("w_torch", (loc[0] + 0.33, loc[1] + 0.55, 1.22), 0.04, 0.22, M["metal"], rot=(math.radians(80), 0, 0), verts=8)
        sd = bpy.data.lights.new("torch", "SPOT")
        sd.energy, sd.spot_size, sd.spot_blend, sd.color = 900, math.radians(28), 0.4, (1, 0.92, 0.75)
        so = bpy.data.objects.new("torch", sd)
        sc.collection.objects.link(so)
        so.location = (loc[0] + 0.33, loc[1] + 0.7, 1.22)
        so.rotation_euler = (math.radians(95), 0, 0)
        return so

    torch = watchman((0.6, -7.2))
    # діти-силуети з очима (з'являються в кадрі 6)
    kids = []
    for i, (x, y) in enumerate(((-3, 1), (-1.4, 2.6), (0.4, 1.8), (2.0, 3.2), (3.5, 1.2), (-4.6, 3.8), (1.2, 4.6))):
        k = cyl(f"kid_{i}", (x, y, 0.5), 0.17, 0.85, M["kid"], verts=12)
        kb = k.modifiers.new("bevel", "BEVEL"); kb.width = 0.08; kb.segments = 3
        h = sphere(f"kid_head_{i}", (x, y, 1.08), 0.17, M["kid"])
        for dx in (-0.06, 0.06):
            e = sphere(f"kid_eye_{i}_{dx}", (x + dx, y - 0.16, 1.11), 0.025, M["eye"], 1)
            kids.append(e)
        kids += [k, h]
    # дитина у вікні другого поверху
    wk = box("win_kid", (5.5, 9.41, 4.5), (0.36, 0.01, 0.7), M["kid"], 0.0)
    sh_ = sphere("win_kid_sh", (5.5, 9.41, 4.83), 0.25, M["kid"])
    sh_.scale = (1.0, 0.04, 0.45)
    wkh = cyl("win_kid_head", (5.5, 9.41, 5.12), 0.2, 0.01, M["kid"], rot=(math.radians(90), 0, 0), verts=20)
    return sc, M, lamps, pivot, torch, kids, (wk, wkh, sh_), lit_upper


# ---------- анімація й камери ----------
def camera(name, lens=32):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_fit = "VERTICAL"
    o = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(o)
    return o


def aim(cam, target):
    d = Vector(target) - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def cam_path(cam, keys):
    """keys: [(frame, loc, target)] — плавно (Безьє) між ключами."""
    for f, loc, tgt in keys:
        cam.location = loc
        aim(cam, tgt)
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)


def animate(sc, M, lamps, pivot, torch, kids, win_kid, lit_upper):
    eye_mat = M["eye"]
    eye_in = eye_mat.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    # гойдалка гойдається сама (згасаюча амплітуда, далі знов розгойдується)
    for f in range(0, 1080, 12):
        a = math.radians(24 * math.sin(f / 30 * 2 * math.pi / 2.4))
        pivot.rotation_euler = (a, 0, 0)
        pivot.keyframe_insert("rotation_euler", frame=f)
    # мерехтіння ліхтаря №0 і повне згасання в кадрі 6
    L0 = lamps[0]
    for f in range(0, 1080, 2):
        e = 700
        if 400 < f < 470 and (f // 6) % 3 == 0:
            e = 40
        if f >= 960:
            e = 0 if f < 1040 else 0
        if 950 <= f < 960 and f % 4 < 2:
            e = 30
        L0.data.energy = e
        L0.data.keyframe_insert("energy", frame=f)
    # діти: приховані до кадру 6, з'являються після згасання ліхтаря, очі спалахують
    for o in kids:
        o.hide_render = True
        o.keyframe_insert("hide_render", frame=0)
        o.hide_render = False
        o.keyframe_insert("hide_render", frame=965)
    eye_in.default_value = 0.0
    eye_in.keyframe_insert("default_value", frame=965)
    eye_in.default_value = 18.0
    eye_in.keyframe_insert("default_value", frame=985)
    # дитина у вікні: з'являється на середині кадру 5
    for o in win_kid:
        o.hide_render = True
        o.keyframe_insert("hide_render", frame=0)
        o.hide_render = False
        o.keyframe_insert("hide_render", frame=800)
    # ліхтарик сторожа вимикається разом з ліхтарем
    torch.data.keyframe_insert("energy", frame=950)
    torch.data.energy = 0
    torch.data.keyframe_insert("energy", frame=958)

    cams = []
    c1 = camera("cam_s1", 30)                                    # 1: загальний, повільний наїзд крізь ворота
    cam_path(c1, [(0, (0.0, -16.0, 1.7), (0.5, 6, 2.2)), (179, (0.0, -10.2, 1.6), (0.5, 6, 2.6))])
    c2 = camera("cam_s2", 40)                                    # 2: аркуш з правилами, наїзд зверху
    cam_path(c2, [(180, (59.75, 0.35, 1.55), (59.9, 1.1, 0.78)), (359, (59.85, 0.75, 1.15), (59.9, 1.1, 0.78))])
    c3 = camera("cam_s3", 28)                                    # 3: кран донизу до гойдалки
    cam_path(c3, [(360, (8.5, -6.0, 8.0), (3.6, 1.5, 1.0)), (569, (5.8, -2.2, 1.4), (3.6, 1.5, 1.0))])
    c4 = camera("cam_s4", 50)                                    # 4: гучномовець, повільна орбіта, глибина різкості
    c4.data.dof.use_dof = True
    c4.data.dof.focus_distance = 3.4
    c4.data.dof.aperture_fstop = 2.0
    cam_path(c4, [(570, (9.0, -5.0, 5.0), (6.1, -5.4, 5.5)), (645, (8.4, -7.6, 4.8), (6.1, -5.4, 5.5)),
                  (719, (6.6, -8.8, 4.9), (6.1, -5.4, 5.5))])
    c5 = camera("cam_s5", 35)                                    # 5: наїзд на освітлене вікно другого поверху
    cam_path(c5, [(720, (4.0, -3.0, 2.2), (5.5, 9.5, 5.0)), (869, (5.2, 4.0, 4.0), (5.5, 9.5, 5.0))])
    c6 = camera("cam_s6", 30)                                    # 6: з-за плеча сторожа на майданчик
    cam_path(c6, [(870, (1.55, -9.5, 2.0), (-0.4, 2.5, 0.9)), (1079, (1.35, -8.7, 1.92), (-0.4, 2.5, 0.9))])
    cams = [c1, c2, c3, c4, c5, c6]
    for (name, f0, f1), c in zip(SHOTS, cams):
        mk = sc.timeline_markers.new(name, frame=f0)
        mk.camera = c
    sc.camera = c1


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    sc, M, lamps, pivot, torch, kids, win_kid, lit_upper = build()
    animate(sc, M, lamps, pivot, torch, kids, win_kid, lit_upper)
    if "--save" in args:
        bpy.ops.wm.save_as_mainfile(filepath=str(Path(args[args.index("--save") + 1]).resolve()))
    if "--still" in args:                                        # окремі кадри для перевірки
        out = Path(args[args.index("--still") + 2]).resolve()
        out.mkdir(parents=True, exist_ok=True)
        for f in [int(x) for x in args[args.index("--still") + 1].split(",")]:
            sc.frame_set(f)
            sc.render.filepath = str(out / f"still_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
    if "--render" in args:
        i = args.index("--render")
        f0, f1, out = int(args[i + 1]), int(args[i + 2]), Path(args[i + 3]).resolve()
        out.mkdir(parents=True, exist_ok=True)
        sc.frame_start, sc.frame_end = f0, f1
        sc.render.filepath = str(out) + "/f_"
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
