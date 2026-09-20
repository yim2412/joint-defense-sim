# -*- coding: utf-8 -*-
import cProfile, pstats, io as _io, sys, time, os
sys.path.insert(0, r"C:/Users/준/Desktop/국방시스템공학")
os.chdir(r"C:/Users/준/Desktop/국방시스템공학")
from engine_combat import run_v7_simulation

cfg = dict(enemy_fleet_mode='preset', enemy_fleet_preset='랴오닝 항모전단',
           weather='맑음 (주간)', sim_seed=7)
t0=time.time(); pr=cProfile.Profile(); pr.enable()
r=run_v7_simulation(cfg)
pr.disable(); el=time.time()-t0
s=_io.StringIO(); ps=pstats.Stats(pr,stream=s).sort_stats('cumulative')
ps.print_stats(20)
print('단발 1회 wall-time: %.2fs · sim_time %.0fs' % (el, r.get('sim_time',0)))
print(s.getvalue()[:3000])
