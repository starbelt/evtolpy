# Mission Segment Energy Consumption

This document explains the equations used to calculate **energy consumption** across different mission segments in the aircraft model.

---

## General Kinematic Relations

Energy consumption calculations often require **velocity**, **displacement**, and **acceleration** values for each mission segment.  
These are derived from fundamental kinematic relations:

$$
v_f^2 = v_0^2 + 2ad
$$

$$
d = \tfrac{1}{2}(v_0 + v_f) \, t
$$

where:

* $v_0$ = initial velocity  
* $v_f$ = final velocity  
* $a$   = acceleration  
* $d$   = displacement  
* $t$   = segment duration 

These relations are applied differently depending on the type of maneuver.

---

## Case 1: Constant Acceleration in One Axis

For mission segments involving **motion in only one direction** (e.g., horizontal taxi with no climb):

$$
a = \frac{v_f^2 - v_0^2}{2d}
$$

$$
d = v_{\text{avg}} \cdot t
$$

### Example Implementation (Python)

```python
# displacement
d_h_m = v_avg_h * t

# final velocity (assuming start from rest)
v_f_h = (2 * d_h_m) / t

# acceleration
a_h = (v_f_h**2 - v0_h**2) / (2 * d_h_m)

