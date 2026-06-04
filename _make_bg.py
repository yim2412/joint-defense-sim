# 홈 배경: KF-21 보라매 편대 비행 사진을 밝게/시네마틱 처리
# 결과물: assets/images/home_bg.jpg  (런처 홈 배경, 빌드 포함)
# 소스: src_kf21_source.jpg (프로젝트 루트, 빌드 제외)
#   원본(Wikimedia Commons, KAI): "KF-21 prototype 003 and 004 during flight testing.jpg"
#   https://commons.wikimedia.org/wiki/Special:FilePath/KF-21%20prototype%20003%20and%20004%20during%20flight%20testing.jpg
from PIL import Image, ImageDraw, ImageEnhance

src = Image.open('src_kf21_source.jpg').convert('RGB')
W, H = src.size
src = ImageEnhance.Brightness(src).enhance(1.35)   # 원본보다 한층 더 밝게
src = ImageEnhance.Color(src).enhance(0.98)
base = src.convert('RGBA')
ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(ov)

# 좌측 비네트 (사이드바 경계만 살짝)
lim = int(W * 0.32)
for x in range(lim):
    a = int(85 * (1 - x / lim))
    d.line([(x, 0), (x, H)], fill=(4, 9, 18, max(0, a)))
# 하단 비네트 (버튼 가독성만 살짝)
top = int(H * 0.62)
for y in range(top, H):
    a = int(95 * ((y - top) / (H - top)))
    d.line([(0, y), (W, y)], fill=(4, 9, 18, max(0, a)))

out = Image.alpha_composite(base, ov).convert('RGB')
out.save('assets/images/home_bg.jpg', quality=90)
print('saved', out.size)
