#!/usr/bin/env python
# _bg_res.py — 백그라운드 작업 "프로세스 트리(부모+모든 자식)"만 PID로 격리해
#   CPU·RAM을 측정한다. 시스템 전체가 아니라 그 작업이 실제로 쓴 값만 집계.
#   (개발 워크플로우 도구, 빌드 제외.)
#
# 사용: python _bg_res.py <metafile>
#   metafile 형식: "<root_pid> <start_epoch>"  (백그라운드 던질 때 기록)
# 출력: 현재시각·경과 + 트리 프로세스 수 + CPU(정규화·합산) + RAM(트리 전용)
import sys, time, datetime
try:
    sys.stdout.reconfigure(encoding='utf-8')   # cp949 콘솔서 ▓░·한글 인코딩 크래시 방지
except Exception:
    pass
try:
    import psutil
except ImportError:
    print("[리소스] psutil 없음"); sys.exit(0)


def bar(pct, n=10):
    pct = min(max(pct, 0.0), 100.0)
    f = int(round(pct / 100 * n))
    return '▓' * f + '░' * (n - f)


meta = sys.argv[1] if len(sys.argv) > 1 else '_bgtask.meta'
try:
    raw = open(meta).read().split()
    root_pid = int(raw[0])
    start = float(raw[1]) if len(raw) > 1 else None
except Exception as e:
    print(f"[리소스] 메타파일 없음/손상 ({e})"); sys.exit(0)

now = datetime.datetime.now()
elapsed = (time.time() - start) if start else None
el_s = f"{int(elapsed // 60)}분 {int(elapsed % 60)}초" if elapsed is not None else "?"

try:
    root = psutil.Process(root_pid)
    tree = [root] + root.children(recursive=True)
except Exception:
    tree = []

if not tree:
    print(f"[리소스] 작업 트리 종료됨 · 현재 {now:%H:%M:%S} · 경과 {el_s}")
    sys.exit(0)

# CPU%는 2회 샘플 차이라 prime 후 잠깐 대기해야 정확
for p in tree:
    try: p.cpu_percent()
    except Exception: pass
time.sleep(0.8)

cpu = 0.0; rss = 0; alive = 0
for p in tree:
    try:
        cpu += p.cpu_percent()
        rss += p.memory_info().rss
        alive += 1
    except Exception:
        pass

ncpu = psutil.cpu_count() or 1
cpu_norm = cpu / ncpu   # 전체 코어 대비 0~100% 정규화
print(f"[현재] {now:%H:%M:%S}   경과 {el_s}")
print(f"[트리] 프로세스 {alive}개 (root PID {root_pid} + 자식 전체)")
print(f"[CPU]  {bar(cpu_norm)} {cpu_norm:.0f}%  (합산 {cpu:.0f}% / {ncpu}코어)")
print(f"[RAM]  {rss/1e9:.2f} GB  (이 작업 트리 전용)")
