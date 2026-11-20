"""Hand calculations for rigidity and strength (reproduced in the article appendix).

Loads are deliberately harsh: 2 N (about 200 g-force) on the tracer knob, 1 N at mid-span of the pole arm.
E is for PLA printed with layers along the bending stress (3.5 GPa) and for the worst direction (2.0 GPa).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cad"))
import params as P  # noqa: E402

E_GOOD, E_BAD = 3500.0, 2000.0        # MPa
SIG_Y = 50.0                          # MPa, PLA tensile yield (printed, conservative)
rows = {}

# tracer arm: cantilever from the front face of block A to the knob axis
Lc = P.L - P.X_BLOCK1
b, h = P.ARM_W, P.ARM_T
Iz_vert = b * h ** 3 / 12             # bending from a vertical load (thin direction)
Iy_side = h * b ** 3 / 12             # bending from a sideways load
F = 2.0
for tag, E in (("3.5 GPa", E_GOOD), ("2.0 GPa", E_BAD)):
    rows[f"tracer arm vertical sag, {tag}"] = F * Lc ** 3 / (3 * E * Iz_vert)
    rows[f"tracer arm sideways deflection, {tag}"] = F * Lc ** 3 / (3 * E * Iy_side)
rows["tracer arm bending stress (MPa)"] = F * Lc * (h / 2) / Iz_vert
rows["tracer arm stress margin"] = SIG_Y / rows["tracer arm bending stress (MPa)"]

# slotted section at the pivot slot (weakest cross-section of the arm)
slot_w = P.M3_CLEAR + 0.2
net_I = (b * h ** 3 - slot_w * h ** 3) / 12
M_slot = F * (P.L - 0.0)               # worst case: knob load acting 100 mm from the slot
rows["tracer arm stress at the slot (MPa)"] = M_slot * (h / 2) / net_I
rows["slot stress margin"] = SIG_Y / rows["tracer arm stress at the slot (MPa)"]

# pole arm, simply supported
Lp = P.R_POLE
bp, hp = 13.0, P.POLE_T
Ip = bp * hp ** 3 / 12
Fp = 1.0
rows["pole arm vertical deflection mid-span, 3.5 GPa (mm)"] = Fp * Lp ** 3 / (48 * E_GOOD * Ip)
rows["pole arm bending stress (MPa)"] = (Fp * Lp / 4) * (hp / 2) / Ip
rows["pole arm Euler buckling load in plane (N)"] = 3.14159 ** 2 * E_BAD * (hp * bp ** 3 / 12) / Lp ** 2

# wheel axle: M3 steel bolt, simply supported across the two plates, wheel load 0.7 N at mid
La = P.X_BLOCK0 - (P.X_REAR_FACE - P.C_T)
Ia = 3.14159 * 3.0 ** 4 / 64
rows["axle deflection at 0.7 N (mm)"] = 0.7 * La ** 3 / (48 * 200000.0 * Ia)

# bearing seat: hoop stress if the printed pocket really ends up with 0.05 mm radial interference
ri, ro = 5.0, 5.0 + 1.6                 # wall around the pocket in the wheel rim (about 1.6 mm minimum)
dr = 0.05
rows["pocket hoop stress at 0.05 mm interference (MPa)"] = E_BAD * dr / ri * (ro ** 2 + ri ** 2) / (ro ** 2 - ri ** 2) / 2

out = {k: round(v, 4) for k, v in rows.items()}
os.makedirs(os.path.join(HERE, "..", "docs", "article", "figures"), exist_ok=True)
with open(os.path.join(HERE, "..", "docs", "article", "figures", "structure.json"), "w") as f:
    json.dump(out, f, indent=1)
for k, v in out.items():
    print(f"{k:58s}{v:>12}")
