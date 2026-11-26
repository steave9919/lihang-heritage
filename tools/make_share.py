# -*- coding: utf-8 -*-
"""生成微信分享素材：二维码、竖版海报、内容长图。"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageChops
import qrcode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'share')
ASSETS = os.path.join(ROOT, 'assets')
os.makedirs(OUT, exist_ok=True)

# 绑定正式域名后，改这里与 SHORT_URL 重新运行即可刷新二维码与海报
URL = 'https://steave9919.github.io/lihang-heritage/'
SHORT_URL = 'steave9919.github.io/lihang-heritage/'

INK = (11, 16, 21)
INK2 = (18, 26, 34)
GOLD = (184, 154, 99)
PAPER = (238, 234, 225)
MUTED = (150, 152, 150)
DIM = (108, 114, 116)
LINE = (58, 66, 72)
WHITE = (255, 255, 255)

FB = 'C:/Windows/Fonts/msyhbd.ttc'
FS = 'C:/Windows/Fonts/msyh.ttc'
FSONG = 'C:/Windows/Fonts/simsun.ttc'
FAR = 'C:/Windows/Fonts/arial.ttf'


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(d, text, fnt, maxw):
    """按像素宽度逐字断行。"""
    lines, cur = [], ''
    for ch in text:
        if ch == '\n':
            lines.append(cur)
            cur = ''
            continue
        trial = cur + ch
        if d.textlength(trial, font=fnt) > maxw and cur:
            lines.append(cur)
            cur = ch
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def para(d, text, x, y, fnt, fill, maxw, lh):
    for ln in wrap(d, text, fnt, maxw):
        d.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return y


def right_text(d, xy, text, font, fill):
    x, y = xy
    w = d.textlength(text, font=font)
    d.text((x - w, y), text, font=font, fill=fill)


def line(d, x1, y1, x2, y2, fill=LINE, width=1):
    d.line([(x1, y1), (x2, y2)], fill=fill, width=width)


def base_canvas(w, h, watermark=True):
    c = Image.new('RGB', (w, h), INK)
    d = ImageDraw.Draw(c)
    # 极淡竖线纹理
    for x in range(0, w, 96):
        line(d, x, 0, x, h, (17, 24, 30), 1)
    if watermark:
        layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.text((int(w * .60), int(h * .06)), '相',
                font=font(FSONG, int(w * .62)), fill=(184, 154, 99, 14))
        c = Image.alpha_composite(c.convert('RGBA'), layer).convert('RGB')
        d = ImageDraw.Draw(c)
    return c, d


def portrait_layer(w, h, left_fade=210, bottom_fade=190, alpha=210, bright=.82):
    src = Image.open(os.path.join(ASSETS, 'lihang-portrait.webp')).convert('RGB')
    scale = max(w / src.width, h / src.height)
    nw, nh = int(src.width * scale), int(src.height * scale)
    src = src.resize((nw, nh), Image.LANCZOS)
    left = max(0, (nw - w) // 2)
    src = src.crop((left, 0, left + w, min(h, nh)))
    if src.height < h:
        pad = Image.new('RGB', (w, h), INK)
        pad.paste(src, (0, 0))
        src = pad
    src = ImageEnhance.Brightness(src).enhance(bright).convert('RGBA')

    mask = Image.new('L', (w, h), 255)
    md = ImageDraw.Draw(mask)
    for x in range(min(left_fade, w)):
        md.line([(x, 0), (x, h)], fill=int(255 * x / left_fade))
    if bottom_fade:
        bm = Image.new('L', (w, h), 255)
        bd = ImageDraw.Draw(bm)
        for i in range(min(bottom_fade, h)):
            y = h - bottom_fade + i
            bd.line([(0, y), (w, y)], fill=int(255 * (bottom_fade - i) / bottom_fade))
        mask = ImageChops.multiply(mask, bm)
    mask = mask.point(lambda v: int(v * alpha / 255))
    src.putalpha(mask)
    return src


def place_portrait(c, pl, x, y):
    """把带 alpha 的人像正确混合到画布上。"""
    layer = Image.new('RGBA', c.size, (0, 0, 0, 0))
    layer.paste(pl, (x, y))
    return Image.alpha_composite(c.convert('RGBA'), layer).convert('RGB')


def make_qr(size=250):
    qr = qrcode.QRCode(version=None,
                       error_correction=qrcode.constants.ERROR_CORRECT_H,
                       box_size=10, border=4)
    qr.add_data(URL)
    qr.make(fit=True)
    im = qr.make_image(fill_color=INK, back_color=WHITE).convert('RGB')
    im.save(os.path.join(OUT, 'qrcode.png'))
    return im.resize((size, size), Image.LANCZOS)


def paste_qr(canvas, qr, x, y):
    pad = 12
    d = ImageDraw.Draw(canvas)
    d.rectangle([x - pad, y - pad, x + qr.width + pad, y + qr.height + pad],
                fill=WHITE, outline=GOLD, width=1)
    canvas.paste(qr, (x, y))


def head_block(c, d, w, compact=False):
    """共用头图区，返回结束 y。"""
    top = 96 if not compact else 80
    line(d, 80, top, w - 80, top, LINE)
    d.text((80, top + 18), 'LI HANG HERITAGE', font=font(FAR, 20), fill=GOLD)
    right_text(d, (w - 80, top + 18), '河北 · 邯郸 · 肥乡', font=font(FS, 20), fill=MUTED)

    y = top + 90
    big = 76 if not compact else 70
    d.text((80, y), '一座因宰相', font=font(FSONG, big), fill=PAPER)
    d.text((80, y + big + 16), '得名的村庄', font=font(FSONG, big), fill=GOLD)
    y2 = y + (big + 16) * 2 + 16
    line(d, 80, y2, 300, y2, GOLD, 2)
    d.text((80, y2 + 22), '北宋名相李沆故里 · 南相公庄', font=font(FS, 27), fill=(198, 196, 188))
    return y2 + 76


def quote_block(d, x, y, width=410):
    d.text((x, y), '民国《肥乡县志》', font=font(FS, 21), fill=GOLD)
    y += 46
    for t in ['「南相公庄为', '李文靖公故里」']:
        d.text((x, y), t, font=font(FSONG, 38), fill=PAPER)
        y += 52
    return y


def footer_block(c, d, w, y, qr):
    line(d, 80, y, w - 80, y, LINE)
    y += 46
    paste_qr(c, qr, 80, y)
    tx = 80 + qr.width + 80
    d.text((tx, y + 8), '长按识别二维码', font=font(FB, 34), fill=PAPER)
    d.text((tx, y + 62), '浏览李沆故里数字馆', font=font(FS, 25), fill=GOLD)
    d.text((tx, y + 128), '若微信内打不开，请点右上角 ···', font=font(FS, 20), fill=MUTED)
    d.text((tx, y + 162), '选择「在浏览器中打开」', font=font(FS, 20), fill=MUTED)
    return y + qr.width + 60


# ---------------------------------------------------------------- 海报
def poster(qr):
    W, H = 1080, 1760
    c, d = base_canvas(W, H)
    c = place_portrait(c, portrait_layer(690, 920, left_fade=230, bottom_fade=220, alpha=225),
                       W - 690, 150)
    d = ImageDraw.Draw(c)

    head_block(c, d, W)
    quote_block(d, 80, 570)

    y = 1120
    line(d, 80, y, W - 80, y, LINE)
    y += 48
    facts = [('947—1004', '李沆生卒'), ('圣相', '史称 · 光明正大'), ('从祀孔庙', '宋仁宗时')]
    for i, (num, cap) in enumerate(facts):
        x = 80 + i * 333
        d.text((x, y), num, font=font(FAR if i == 0 else FB, 40 if i == 0 else 38), fill=GOLD)
        d.text((x, y + 56), cap, font=font(FS, 20), fill=MUTED)
    y += 130

    y = footer_block(c, d, W, y, qr)
    line(d, 80, y, W - 80, y, LINE)
    d.text((80, y + 24), SHORT_URL, font=font(FAR, 19), fill=DIM)
    right_text(d, (W - 80, y + 24), '千年一村 · 以文献立馆', font=font(FS, 20), fill=DIM)

    p = os.path.join(OUT, 'wechat-poster.jpg')
    c.save(p, 'JPEG', quality=88, optimize=True, progressive=True)
    return p


# ---------------------------------------------------------------- 内容长图
SECTIONS = [
    ('01', '村名由来',
     '隋唐时期，此地名叫河凤乡。北宋年间，村中李氏家族几代为官，李沆官至同中书门下平章事；'
     '古称宰相为「相公」，村庄由此更名相公庄，又按方位分为南、北相公庄。'
     '民国二十九年《肥乡县志》卷三十七明载：「南相公庄为李文靖公故里」。'
     '一个地名，把一千年的政治史留在了华北平原上。'),
    ('02', '李沆其人',
     '李沆（947—1004），字太初，洺州肥乡人。太平兴国五年（980）进士，'
     '曾任太子宾客，为宋真宗之师；咸平初以户部侍郎、参知政事拜同中书门下平章事，监修国史。'
     '卒谥「文靖」，赠太尉、中书令，史称「圣相」，配享真宗庙庭，宋仁宗时从祀孔子庙庭。'),
    ('03', '圣相之治',
     '为相主张清静无为、务行故事，尤注意戒除人主骄奢之心。'
     '不用浮薄新进喜事之人；真宗夜遣使持手诏欲立刘氏为贵妃，沆引烛焚诏，'
     '附奏曰「但道臣沆以为不可」，其议遂寝。史称其为相「光明正大」，'
     '政治遗产不在兴作，而在克制。'),
    ('04', '以文献立馆',
     '村中新落成的故居文化馆，让「故里」有了可步入的现场；而李沆当年的宅邸与墓葬，'
     '村中并无原生遗存，杨亿所撰《李沆墓志铭》记其归葬洛阳贤相乡。'
     '实体馆陈列其形，本数字馆存其文献：据《宋史·李沆传》、李沆墓志铭、'
     '王禹偁《小畜集》所载李炳墓志、民国《肥乡县志》立站，逐条标注版本与出处，'
     '不以后世建置混同宋代原址遗存。'),
]


def longimage(qr):
    W, H = 1080, 3400
    c, d = base_canvas(W, H)
    c = place_portrait(c, portrait_layer(620, 760, left_fade=210, bottom_fade=190, alpha=215),
                       W - 620, 200)
    d = ImageDraw.Draw(c)

    head_block(c, d, W, compact=True)
    quote_block(d, 80, 520, width=430)

    y = 880
    line(d, 80, y, W - 80, y, GOLD, 1)
    y += 46

    for num, title, body in SECTIONS:
        d.text((80, y), num, font=font(FAR, 26), fill=GOLD)
        d.text((150, y - 8), title, font=font(FB, 38), fill=PAPER)
        line(d, 80, y + 56, W - 80, y + 56, LINE)
        y = para(d, body, 80, y + 92, font(FS, 29), (198, 196, 188), W - 160, 50)
        y += 78

    y = footer_block(c, d, W, y + 10, qr)
    line(d, 80, y, W - 80, y, LINE)
    d.text((80, y + 24), SHORT_URL, font=font(FAR, 19), fill=DIM)
    right_text(d, (W - 80, y + 24), '圣相故里 · 南相公庄', font=font(FS, 20), fill=DIM)

    final_h = min(H, y + 90)
    c = c.crop((0, 0, W, final_h))
    p = os.path.join(OUT, 'wechat-long.jpg')
    c.save(p, 'JPEG', quality=87, optimize=True, progressive=True)
    return p, final_h


if __name__ == '__main__':
    qr = make_qr(250)
    print('qrcode.png       ', os.path.getsize(os.path.join(OUT, 'qrcode.png')), 'B')
    p1 = poster(qr)
    print('wechat-poster.jpg', os.path.getsize(p1), 'B')
    p2, h = longimage(qr)
    print('wechat-long.jpg  ', os.path.getsize(p2), 'B', 'H=', h)
