"""Single source of truth for every dimension (mm).  Imported by all parts, the assembly and the sim.

ASSEMBLY FRAME (used by every part script)
    origin  : elbow pivot axis, on the paper (z = 0)
    +X      : along the tracer arm, toward the tracer point
    +Y      : left of the tracer arm (the wheel side).  The pole arm lies on the -Y side.
    +Z      : up from the paper
"""
import math

# ---- Measuring geometry (the maths lives here) ------------------------------------------
L = 100.0                         # elbow pivot axis -> tracer axis
WHEEL_CIRC = 100.0                # wheel rolling circumference: 1 rev = L*C = 100 cm^2
WHEEL_D = WHEEL_CIRC / math.pi    # 31.831 mm rolling diameter (tops of the knurl ridges)
WHEEL_R = WHEEL_D / 2
R_POLE = 160.0                    # pole arm, pivot axis to pivot axis
WHEEL_B = 26.0                    # wheel lateral offset (+Y).  Drops out of the maths.
WHEEL_A = -22.0                   # wheel axial position from the elbow (x).  Enters only the pole-inside constant.

# ---- Heights ----------------------------------------------------------------------------
Z_ARM = 20.0                      # centreline of the tracer arm above the paper
Z_WHEEL = WHEEL_R                 # wheel axle height (rim touches the paper at z = 0)
Z_POLE_ARM = 31.0                 # underside of both pole-arm ends (bearing bottom face)

# ---- Drum and vernier -------------------------------------------------------------------
DRUM_D = 27.0
DRUM_DIVS = 50                    # 2 cm^2 each
VERNIER_DIVS = 10                 # 10 vernier divs span 9 drum divs -> 0.2 cm^2 resolution

# ---- Hardware ---------------------------------------------------------------------------
BEARING_OD, BEARING_ID, BEARING_W = 10.0, 3.0, 4.0     # 623ZZ
BALL_D = 6.0
M3_CLEAR = 3.4
M3_NUT_AF, M3_NUT_H = 5.8, 2.6
M3_HEAD_D, M3_HEAD_H = 5.5, 3.0

# ---- Tolerances (tune with the coupon print) --------------------------------------------
bearing_fit = 0.10                # added to bearing OD for the press-fit bore
arm_clearance = 0.25              # per side, tracer arm in carriage channel
nut_clear = 0.20
standoff_d = 5.0                  # touches the inner race only (never the shield / outer race)

# ---- Arms -------------------------------------------------------------------------------
ARM_W, ARM_T = 12.0, 8.0          # tracer arm: 12 wide (in the paper plane), 8 thick
POLE_W, POLE_T = 12.0, 6.0

# ---- Geneva counter (10:1: one wheel revolution = one dial step of 36 degrees) ----------
GEN_N = 10
GEN_PIN_A = 6.0                   # crank (pin) radius on the wheel
GEN_C = GEN_PIN_A / math.sin(math.pi / GEN_N)          # centre distance 19.416
GEN_PIN_D = 2.4
GEN_SLOT_W = 2.9
GEN_LOCK_R = 5.0                  # lock disc radius on the wheel
GEN_TIP_R = 19.0                  # dial lobe tip radius
GEN_T = 3.0                       # dial thickness

# ---- Check rule -------------------------------------------------------------------------
CHECK_AREA_CM2 = 100.0
CHECK_R = math.sqrt(CHECK_AREA_CM2 * 100.0 / math.pi)   # 56.419 mm

# ---- Printing / material ---------------------------------------------------------------
RHO_PLA = 1.24e-3                 # g/mm^3 solid
INFILL_EFF = 0.45                 # effective solid fraction (3 walls + 25 % gyroid), rough
GEN_RELIEF_DEG = 75.0             # sector removed from the lock disc so the lobe tips can pass (sweep-verified)

# ---- Carriage layout (assembly frame; derived from the wheel layout in cad/parts/wheel.py) -------------
WHEEL_X_FRONT = WHEEL_A + 10.0            # drum end of the wheel      (-12.0)
WHEEL_X_REAR = WHEEL_A - 16.2             # crank plate end            (-38.2)
STANDOFF_FRONT_H = 0.6                    # front standoff ring height (gap wheel <-> plate)
X_FRONT_FACE = WHEEL_X_FRONT + STANDOFF_FRONT_H     # wheel-facing face of plate B   (-11.4)
B_T = 5.0                                 # plate B thickness
X_BLOCK0 = X_FRONT_FACE + B_T             # block A mating face            (-6.4)
X_BLOCK1 = 18.0                           # block A front face = index edge of the L scale
X_REAR_FACE = WHEEL_X_REAR - 0.6          # wheel-facing face of plate C   (-38.8)
C_T = 4.0
BLOCK_Y0, BLOCK_Y1 = -12.0, 13.25
BLOCK_Z0, BLOCK_Z1 = 10.75, 29.25
CH_W = ARM_W + 2 * arm_clearance          # 12.5
CH_H = ARM_T + 2 * arm_clearance          # 8.5
POST_Y = 50.5                             # plate C posts (outside the wheel and the dial)
POST_Z = (7.0, 33.0)
B_Y1 = 55.0                               # plate B outer edge
BALLAST_Y0, BALLAST_Y1 = 55.5, 69.5
DIAL_Z = Z_WHEEL + GEN_C                  # dial axis height (35.33)
DIAL_X0 = WHEEL_A - 13.7                  # dial plane  x in [DIAL_X0, DIAL_X0 + GEN_T]
BLOCK_SCREWS = [(-9.25, 13.25), (-9.25, 26.75), (9.75, 13.25), (9.75, 26.75)]   # (y, z) A<->B screws
CLAMP_X = 9.0                             # clamp screw station in block A
GEN_PHASE_DEG = 72.0              # wheel pose: pin has just left the slot when the drum reads 0 (dial completes its step as the drum wraps)
