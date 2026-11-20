"""Rebuild every STEP/STL file, then run the assembly checks.

Run from the repo root:  python3 -I cad/build.py [--quick]
"""
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "parts"))

PARTS = ["wheel", "carriage_a", "carriage_b", "carriage_c", "dial",
         "tracer_arm", "pole_arm", "pole_weight", "check_rule", "coupon"]

for name in PARTS:
    print(f"--- {name}")
    runpy.run_path(os.path.join(HERE, "parts", name + ".py"), run_name="__main__")

print("--- assembly")
runpy.run_path(os.path.join(HERE, "assembly.py"), run_name="__main__")
