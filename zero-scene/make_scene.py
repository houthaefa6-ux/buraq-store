#!/usr/bin/env python3
"""
مشهد: كراكتر الصفر مختبئ خلف الحائط، متوتر وخائف — بخلفية شفافة.

الاستخدام:
    python3 make_scene.py [zero.png] [zero_hiding.png]

يحتاج فقط مكتبة Pillow:  pip install pillow
"""
import random
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageChops

SRC = sys.argv[1] if len(sys.argv) > 1 else "zero.png"
OUT = sys.argv[2] if len(sys.argv) > 2 else "zero_hiding.png"

W, H = 1500, 1500          # حجم الصورة النهائية
SS = 2                     # مضاعفة الدقة ثم التصغير لحواف ناعمة
WALL_RIGHT = 600           # حافة الحائط اليمنى (الصفر يطلّ من خلفها)
WALL_SIDE = 46             # سماكة الحائط (الوجه الجانبي)
CHAR_POS = (40, 150)       # موضع الكراكتر
CHAR_TILT = -7             # ميلان بسيط كأنه ينكمش خلف الحائط
random.seed(7)


def clean_alpha(img, cutoff=70):
    """إزالة الهالة شبه الشفافة حول الكراكتر."""
    r, g, b, a = img.split()
    a = a.point(lambda v: 0 if v < cutoff else v)
    return Image.merge("RGBA", (r, g, b, a))


def brick_wall(w, h):
    """حائط طوب كرتوني بوجه أمامي ووجه جانبي وحافة علوية مكسّرة."""
    s = SS
    wall = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(wall)
    front_w = (w - WALL_SIDE) * s
    bw, bh, gap = 150 * s, 62 * s, 7 * s
    mortar = (226, 214, 200, 255)
    tones = [(196, 84, 52), (208, 96, 60), (184, 74, 46), (214, 108, 70), (190, 88, 58)]

    d.rectangle([0, 0, front_w, h * s], fill=mortar)
    row = 0
    for y in range(0, h * s, bh + gap):
        off = -(bw // 2) if row % 2 else 0
        for x in range(off, front_w, bw + gap):
            x0, x1 = max(x, 0), min(x + bw, front_w)
            if x1 - x0 < 8 * s:
                continue
            c = random.choice(tones)
            d.rounded_rectangle([x0, y, x1, y + bh], radius=7 * s, fill=c + (255,))
            # لمعة علوية وظل سفلي لكل طوبة
            d.line([x0 + 8 * s, y + 6 * s, x1 - 8 * s, y + 6 * s],
                   fill=tuple(min(255, v + 34) for v in c) + (255,), width=3 * s)
            d.line([x0 + 8 * s, y + bh - 5 * s, x1 - 8 * s, y + bh - 5 * s],
                   fill=tuple(int(v * .78) for v in c) + (255,), width=3 * s)
        row += 1

    # الوجه الجانبي (أغمق) يعطي الحائط عمقاً
    d.rectangle([front_w, 0, w * s, h * s], fill=(120, 52, 36, 255))
    for y in range(0, h * s, bh + gap):
        d.rectangle([front_w, y + bh, w * s, y + bh + gap], fill=(150, 130, 116, 255))
    d.line([front_w, 0, front_w, h * s], fill=(92, 38, 26, 255), width=4 * s)

    # حافة علوية متدرجة (طوب ناقص) بدل قصّة مستقيمة
    cut = ImageDraw.Draw(wall)
    step = bh + gap
    for i, (x_from, rows) in enumerate([(0, 2), (150, 1)]):
        cut.rectangle([x_from * s if i else 0, 0,
                       (150 if i == 0 else 330) * s, rows * step - gap], fill=(0, 0, 0, 0))
    return wall.resize((w, h), Image.LANCZOS)


def sweat_drop(d, x, y, size):
    s = size
    d.polygon([(x, y - s * 1.5), (x - s * .75, y), (x + s * .75, y)], fill=(120, 205, 255, 255))
    d.ellipse([x - s * .78, y - s * .55, x + s * .78, y + s], fill=(120, 205, 255, 255))
    d.ellipse([x - s * .4, y - s * .1, x - s * .05, y + s * .35], fill=(235, 250, 255, 255))


def shake_lines(d, cx, cy, r, a0, a1, n=3, color=(255, 120, 20, 255)):
    """أقواس ارتجاف حول الكراكتر."""
    for i in range(n):
        rr = r + i * 26 * SS
        d.arc([cx - rr, cy - rr, cx + rr, cy + rr], a0 + i * 3, a1 - i * 3,
              fill=color, width=9 * SS)


# ---------- بناء المشهد ----------
scene = Image.new("RGBA", (W, H), (0, 0, 0, 0))

# 1) الكراكتر
zero = clean_alpha(Image.open(SRC).convert("RGBA"))
zero = zero.rotate(CHAR_TILT, resample=Image.BICUBIC, expand=True)
scene.alpha_composite(zero, CHAR_POS)

# 2) ظل الحائط الساقط على الكراكتر (فقط فوق جسمه، فتبقى الخلفية شفافة)
shadow = Image.new("L", (W, H), 0)
ImageDraw.Draw(shadow).rectangle([WALL_RIGHT - 10, 0, WALL_RIGHT + 85, H], fill=120)
shadow = shadow.filter(ImageFilter.GaussianBlur(28))
shadow = ImageChops.multiply(shadow, scene.getchannel("A"))
scene.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 30)] * 3, shadow)))

# 3) الحائط فوق الكراكتر
wall = brick_wall(WALL_RIGHT, H - 60)
scene.alpha_composite(wall, (0, 60))

# 4) يد الصفر ممسكة بحافة الحائط (مقصوصة من الصورة الأصلية)
src = clean_alpha(Image.open(SRC).convert("RGBA"))
hand = src.crop((85, 285, 296, 468)).rotate(40, resample=Image.BICUBIC, expand=True)
hand = hand.resize((int(hand.width * .85), int(hand.height * .85)), Image.LANCZOS)
hx, hy = WALL_RIGHT - WALL_SIDE - 150, 560
hs = Image.new("RGBA", (W, H), (0, 0, 0, 0))
hs.paste((40, 15, 10, 110), (hx + 8, hy + 14), hand.getchannel("A"))
hs = hs.filter(ImageFilter.GaussianBlur(9))
hs.putalpha(ImageChops.multiply(hs.getchannel("A"), scene.getchannel("A")))
scene.alpha_composite(hs)
scene.alpha_composite(hand, (hx, hy))

# 5) مؤثرات التوتر: عرق + خطوط ارتجاف
fx = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
d = ImageDraw.Draw(fx)
for x, y, s in [(1085, 215, 26), (1160, 330, 19), (1010, 140, 17), (700, 200, 20)]:
    sweat_drop(d, x * SS, y * SS, s * SS)
shake_lines(d, 800 * SS, 800 * SS, 520 * SS, -30, 12)
shake_lines(d, 800 * SS, 800 * SS, 520 * SS, 40, 72, n=2)
scene.alpha_composite(fx.resize((W, H), Image.LANCZOS))

scene.save(OUT)
print(f"تم الحفظ: {OUT}  ({W}x{H}, خلفية شفافة)")
