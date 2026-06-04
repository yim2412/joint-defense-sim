# 홈 배경 합성: NASA ISS 한반도 야경 + 미사일 방어 작전 오버레이
# 결과물: assets/images/home_bg.jpg (런처 홈 배경)
#
# 원본(공개도메인, NASA Earth Observatory / ISS Expedition 38):
#   https://assets.science.nasa.gov/dynamicimage/assets/science/esd/eo/images/imagerecords/83000/83182/ISS038-E-038300_lrg.jpg
# 재생성 시: 위 URL을 assets/images/_korea_night_iss.jpg 로 받은 뒤 이 스크립트 실행.
import os
import urllib.request
from PIL import Image, ImageDraw, ImageEnhance

_SRC = 'assets/images/_korea_night_iss.jpg'
_URL = ('https://assets.science.nasa.gov/dynamicimage/assets/science/esd/eo/'
        'images/imagerecords/83000/83182/ISS038-E-038300_lrg.jpg')
if not os.path.exists(_SRC):
    urllib.request.urlretrieve(_URL, _SRC)

src = Image.open(_SRC).convert('RGB')
W, H = src.size
src = src.crop((0, 95, W, H))            # 상단 ISS 구조물 제거
W, H = src.size
src = ImageEnhance.Brightness(src).enhance(0.82)
base = src.convert('RGBA')
ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))


def bezier(p0, p1, p2, n=90):
    out = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        out.append((x, y))
    return out


def glow_curve(p0, p2, lift, color, core=3, glow=15):
    mid = ((p0[0] + p2[0]) / 2, (p0[1] + p2[1]) / 2 - lift)
    pts = bezier(p0, mid, p2)
    r, g, b = color
    for w, a in ((glow, 38), (glow * 0.55, 75), (core, 235)):
        layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(layer).line(pts, fill=(r, g, b, a), width=max(1, int(w)), joint='curve')
        ov.alpha_composite(layer)


def marker(x, y, color, rad=7):
    r, g, b = color
    for rr, a in ((rad * 2.4, 45), (rad * 1.5, 105), (rad, 235)):
        layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(layer).ellipse((x - rr, y - rr, x + rr, y + rr), fill=(r, g, b, a))
        ov.alpha_composite(layer)


THREAT = (255, 80, 55)
INTCPT = (60, 210, 255)
HIT = (255, 225, 120)

# 위협 탄도탄 (북측 → 남측, 완만한 포물선)
glow_curve((345, 175), (475, 460), 135, THREAT)
glow_curve((415, 160), (565, 430), 145, THREAT)
glow_curve((325, 205), (300, 480), 80, THREAT)
# 요격 (동해상 이지스 → 교차점)
glow_curve((905, 330), (560, 245), 120, INTCPT)
glow_curve((890, 378), (470, 330), 110, INTCPT)
# 마커
for p in ((345, 175), (415, 160), (325, 205)):
    marker(*p, THREAT, 6)
for p in ((905, 330), (890, 378)):
    marker(*p, INTCPT, 7)
for p in ((560, 245), (470, 330)):
    marker(*p, HIT, 8)

# 좌측 비네트 (사이드바 경계 자연스럽게)
vg = Image.new('RGBA', (W, H), (0, 0, 0, 0))
vd = ImageDraw.Draw(vg)
for x in range(W):
    a = int(150 * (1 - x / 520)) if x < 520 else 0
    vd.line([(x, 0), (x, H)], fill=(4, 9, 18, max(0, a)))
ov.alpha_composite(vg)
# 하단 비네트
hg = Image.new('RGBA', (W, H), (0, 0, 0, 0))
hd = ImageDraw.Draw(hg)
for y in range(H):
    a = int(120 * ((y - (H - 260)) / 260)) if y > H - 260 else 0
    hd.line([(0, y), (W, y)], fill=(4, 9, 18, max(0, a)))
ov.alpha_composite(hg)

out = Image.alpha_composite(base, ov).convert('RGB')
out.save('assets/images/home_bg.jpg', quality=88)
print('saved', out.size)
