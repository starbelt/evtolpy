**Written by First Last**  
Other contributors: Khoa Nguyen

# Mission Segment Energy Consumption

This document explains the equations used to calculate energy consumption across different mission segments in the aircraft model.

## Table of Contents

* [General Workflow for Calculating Average Electric Power (kW)](#general-workflow-for-calculating-average-electric-power-kw)  

* [Reference Equations](#reference-equations)

  - [General Kinematic Relations](#general-kinematic-relations)     

  - [Aerodynamics Drag Modeling](#aerodynamics-drag-modeling)

* [Average Shaft Power Calculation](#average-shaft-power-calculation)

  | Main Mission                                                            | Reserve Mission                                                                      |
  |-------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
  | [Segment A: Depart Taxi](#segment-a-depart-taxi)                        | [Segment B': Reserve Hover Climb](#segment-b-reserve-hover-climb)                    |
  | [Segment B: Hover Climb](#segment-b-hover-climb)                        | [Segment C': Reserve Transition Climb](#segment-c-reserve-transition-climb)          |
  | [Segment C: Transition Climb](#segment-c-transition-climb)              | [Segment E': Reserve Acceleration Climb](#segment-e-reserve-acceleration-climb)      |
  | [Segment D: Depart Procedures](#segment-d-depart-procedures)            | [Segment F': Reserve Cruise](#segment-f-reserve-cruise)                              |
  | [Segment E: Accelerate Climb](#segment-e-accelerate-climb)              | [Segment G': Reserve Deceleration Descend](#segment-g-reserve-deceleration-descend)  |
  | [Segment F: Cruise](#segment-f-cruise)                                  | [Segment I': Reserve Transition Descend](#segment-i-reserve-transition-descend)      |
  | [Segment G: Decelerate Descend](#segment-g-decelerate-descend)          | [Segment J': Reserve Hover Descend](#segment-j-reserve-hover-descend)                |
  | [Segment H: Arrive Procedures](#segment-h-arrive-procedures)            |                                                                                      |
  | [Segment I: Transition Descend](#segment-i-transition-descend)          |                                                                                      |
  | [Segment J: Hover Descend](#segment-j-hover-descend)                    |                                                                                      |
  | [Segment K: Arrive Taxi](#segment-k-arrive-taxi)                        |                                                                                      |


Note: The above mission profile is adapted from [Uber Elevate's *UberAir Vehicle Requirements and Mission*](../../references/summary-mission-and-requirements.pdf)

---
---
## General Workflow for Calculating Average Electric Power (kW)  

**Step 1: Calculate Average Shaft Power (kW)**  
* Based on aerodynamic and propulsion requirements.  
* Note: Different calculation will be implemented for each mission segment.
* General equation:

$$
P_{shaft,avg} = \frac{F_h \cdot v_h + F_v \cdot v_v}{\eta_{rotor} \cdot W_{KW}}
$$  

**Step 2: Calculate Average Electric Power (kW)**    
* Including the efficiency of the electric power unit $\eta_{epu}$ (*power.epu_effic*).   
* General equation (*applied for all energy segments calculation*):  

$$
P_{elec, avg} = \frac{P_{shaft, avg}}{\eta_{epu}}
$$

**Step 3: Calculate Energy Consumption (kWh)**    
* By integrating electric power over the mission segment duration.  
* General equation (*applied for all energy segments calculation*):  

$$
E = \frac{P_{elec, avg} \cdot t}{S_{HR}}
$$  

where $S_{HR}$ is the seconds-to-hour conversion factor.

---
---
## Reference Equations

### General Kinematic Relations

Energy consumption calculations often require **velocity**, **displacement**, and **acceleration** values for each mission segment. These are derived from the fundamental kinematic equations:

$$
v_f^2 = v_i^2 + 2ad
$$

$$
v_f = v_i + at
$$

$$
d = v_it + \frac{1}{2}at^2
$$

$$
d = \frac{1}{2}(v_i + v_f)t = v_{avg}t
$$

where:

* $v_i$     = initial velocity (m/s)
* $v_f$     = final velocity (m/s)
* $v_{avg}$ = average velocity (m/s)
* $a$       = acceleration ($m^2$/s)
* $d$       = displacement (m)
* $t$       = segment duration (s)

These relations are applied differently depending on the type of maneuver (e.g., takeoff, climb, cruise, descent, hover), which is one of the reasons that leads to different average shaft power calculations for each segment.

---
### Aerodynamics Drag Modeling

**Description:**  
* Drag modeling is a key component of the **average shaft power calculation** for each mission segment.  
* The total aerodynamic drag is computed as a combination of **induced drag** (due to lift generation) and **parasite drag** (profile drag from aircraft components).  
* Drag coefficients account for contributions from the **fuselage, horizontal tail, vertical tail, landing gear**, and optionally **wing airfoil** and **stopped rotor** effects for cruise conditions.  

**Total Parasite Drag Coefficient**  
* The total parasite drag coefficient $C_{D0,total}$ is computed as the sum of available components:  

$$
C_{D0,total} = C_{D0,fuselage} + C_{D0,horiz\_tail} + C_{D0,vert\_tail} + C_{D0,landing\_gear}
$$  

* For cruise segments (F and F'), additional contributions are included:  

$$
C_{D0,cruise} = C_{D0,total} + C_{D0,wing\_airfoil\_cruise} + C_{D0,stopped\_rotor}
$$  

**Induced Drag**  
* Induced drag is calculated based on lift:  

$$
D_i = \frac{L^2}{q \cdot S \cdot \pi \cdot AR \cdot e}
$$  

where:  
  * $L$ = aerodynamic lift  
  * $q = 0.5 \cdot \rho \cdot V^2$ = dynamic pressure  
  * $S$ = wing planform area  
  * $AR$ = wing aspect ratio  
  * $e$ = span efficiency factor  

**Parasite Drag**  
* Parasite drag force is computed using the total parasite drag coefficient:  

$$
D_p = q \cdot S \cdot C_{D0}
$$  

**Total Drag Force** 
* The total drag force is the sum of induced and parasite drag, including empirical correction factorss for trim and protuberances:  

$$
D_{total} = (D_i + D_p) \cdot \text{Trim drag factor} \cdot \text{Excrescence and protuberance factor}
$$  

**Application in Shaft Power Calculation**  
* For each mission segment, the total drag $D_{total}$ is used to compute the **horizontal force component** in the shaft power formula:  

$$
F_h = D_{total} + m \cdot a_h
$$  

* Vertical force components and accelerations are combined for segments with climb or descent to compute the total shaft power:  

$$
P_{shaft,avg} = \frac{F_h \cdot v_h + F_v \cdot v_v}{\eta_{rotor} \cdot W_{KW}}
$$  

This modular approach allows segment-specific drag modeling while accounting for lift-induced effects, parasite drag from multiple components, and special cruise adjustments for stopped rotors or wing airfoil contributions.

---
---
## Average Shaft Power Calculation

### Segment A: Depart Taxi

**Description:**  
* Calculations for the **Depart Taxi** segment consider **horizontal motion only**. 
* Drag effects are neglected, and the aircraft starts from rest, accelerating to a final horizontal velocity. 
* Average shaft power is then calculated based on MTOM, horizontal acceleration, and average horizontal velocity.  
   
**Displacement, Acceleration, and Final Velocity**   
* Let:  
  * $v_i$ = 0 = initial horizontal velocity  
  * $v_{avg}$ = average horizontal velocity (*mission.depart_taxi_avg_h_m_p_s*)  
  * $t$ = duration of taxi segment (*mission.depart_taxi_s*)  

* The horizontal displacement $d_h$ and acceleration $a_h$ are:

$$
d_h = v_{avg} \cdot t
$$

$$
v_f = \frac{2 d_h}{t}
$$

$$
a_h = \frac{v_f^2}{2 d_h}
$$  
  
**Average Shaft Power (kW)**   
* Using aircraft mass $m$ (*aircraft.max_takeoff_mass_kg*) and rotor efficiency $\eta_{rotor}$ (*propulsion.rotor_effic*):  

$$
P_{shaft, avg} = \frac{m \cdot a_h \cdot v_{avg}}{\eta_{rotor} \cdot W_{KW}}
$$  

where $W_{KW}$ is the unit conversion factor to kW.

```python
def _calc_depart_taxi_avg_shaft_power_kw(self):
  if self.mission != None:
    d_h_m = self.mission.depart_taxi_avg_h_m_p_s*self.mission.depart_taxi_s
    vf_h_m_p_s = (2.0*d_h_m)/self.mission.depart_taxi_s
    a_h_m_p_s2 = vf_h_m_p_s**2.0/(2.0*d_h_m)
    return \
      (self.max_takeoff_mass_kg*a_h_m_p_s2*\
      self.mission.depart_taxi_avg_h_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
  else:
    return None
```

---
### Segment B: Hover Climb  
**Description:**   
* Calculations for the **Hover Climb** segment consider **vertical motion only**.  
* Drag effects are neglected, and the aircraft starts from rest, accelerating upward to a final vertical velocity.  
* The total shaft power consists of two components:  
  1. Hover Power: the induced power required to support the aircraft’s weight when aerodynamic lift from the wings is negligible.  
  2. Climb Power: the additional power required to accelerate the aircraft vertically.  
* Physically, the hover power represents the induced power required to support partial or full aircraft weight during hover or transition, when the wings do not yet generate sufficient lift. 

**Displacement, Acceleration, and Final Velocity**   
* Let:  
  * $v_i$ = 0 = initial vertical velocity  
  * $v_{avg}$ = average vertical velocity (*mission.hover_climb_avg_v_m_p_s*)  
  * $t$ = duration of hover climb segment (*mission.hover_climb_s*)    

* The vertical displacement $d_v$ and acceleration $a_v$ are:  

$$
d_v = v_{avg} \cdot t
$$

$$
v_f = \frac{2 d_v}{t}
$$

$$
a_v = \frac{v_f^2}{2 d_v}
$$   

**Hover Power (W)**  
* The induced velocity in hover, based on propeller momentum theory, is:  

$$
v_{i,hover} = \sqrt{\frac{m \cdot g}{2 \cdot \rho \cdot A}}
$$  

where:  
  * $m$ = aircraft mass (*aircraft.max_takeoff_mass_kg*)  
  * $g$ = gravitational acceleration (*environ.g_m_p_s2*)  
  * $\rho$ = air density (*environ.air_density_sea_lvl_kg_p_m3*)  
  * $A$ = total rotor disk area (*propulsion.disk_area_m2*)  

The induced hover power is then:  

$$
P_{hover} = m \cdot g \cdot v_{i,hover}
$$  

**Average Shaft Power (kW)**   
* The total shaft power is the sum of hover power and climb power, divided by rotor efficiency:  

$$
P_{shaft,avg} = \frac{P_{hover} + m \cdot a_v \cdot v_{avg}}{\eta_{rotor} \cdot W_{KW}}
$$  

where $W_{KW}$ is the unit conversion factor to kW, and $\eta_{rotor}$ = rotor efficiency (*propulsion.rotor_effic*).  

```python
def _calc_hover_climb_avg_shaft_power_kw(self):
  if self.mission != None and self.propulsion != None:
      
      # vertical kinematics (upward positive)
      d_v_m = self.mission.hover_climb_avg_v_m_p_s*self.mission.hover_climb_s
      vf_v_m_p_s = (2.0*d_v_m)/self.mission.hover_climb_s
      a_v_m_p_s2 = vf_v_m_p_s**2.0/(2.0*d_v_m)
  
      # induced velocity in hover (prop thrust momentum theory)
      v_i_hover = math.sqrt((self.max_takeoff_mass_kg*self.environ.g_m_p_s2)/\
                            (2.0*self.environ.air_density_sea_lvl_kg_p_m3*self.propulsion.disk_area_m2))

      # induced power (hover)
      P_hover_W = (self.max_takeoff_mass_kg*self.environ.g_m_p_s2)*v_i_hover

      return \
        (P_hover_W+self.max_takeoff_mass_kg*a_v_m_p_s2*\
          self.mission.hover_climb_avg_v_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
  else:
      return None
```

---
### Segment C: Transition Climb  

**Description:**  
* Calculations for the **Transition Climb** segment include both **horizontal and vertical motion**.  
* Aerodynamic lift, induced drag, parasite drag, weight, hover-induced power, and climb forces are all considered.  
* Horizontal velocity starts from rest and accelerates to a final velocity based on the average horizontal velocity.  
* Vertical velocity is assumed **constant** throughout the segment (no vertical acceleration).  
* The total shaft power includes both **aerodynamic power** and **hover-induced power**, representing the thrust required to support any portion of aircraft weight not yet carried by aerodynamic lift.  
* Physically, the hover-induced power term represents the induced power required to supplement lift when wings are not yet producing full aerodynamic support during the transition from hover to forward flight.  
   
**Displacement, Acceleration, and Velocity Components**  
* Let:  
  * $v_{i,h}$ = 0 = initial horizontal velocity  
  * $v_{avg,h}$ = average horizontal velocity (*mission.trans_climb_avg_h_m_p_s*)  
  * $v_{f,h}$ = final horizontal velocity  
  * $v_v$ = vertical velocity (*mission.trans_climb_v_m_p_s*)  
  * $t$ = duration of transition climb segment (*mission.trans_climb_s*)  

* Horizontal displacement $d_h$ and acceleration $a_h$:

$$
d_h = v_{avg,h} \cdot t
$$

$$
v_{f,h} = 2 \cdot v_{avg,h} - v_{i,h}
$$

$$
a_h = \frac{v_{f,h}^2 - v_{i,h}^2}{2 \cdot d_h}
$$  

* Vertical acceleration $a_v$ = 0 (constant vertical velocity)  

**Hover-Induced Power (W)**  
* When aerodynamic lift does not fully balance the aircraft’s weight, additional thrust is required.  
  The thrust deficit is defined as:  

$$
T_{req} = (Weight - Lift) + m \cdot a_v
$$  

* If $T_{req} > 0$, the induced velocity and induced hover power are calculated using propeller momentum theory:  

$$
v_{i,hover} = \sqrt{\frac{T_{req}}{2 \cdot \rho \cdot A}}
$$  

$$
P_{hover} = T_{req} \cdot v_{i,hover}
$$  

**Average Shaft Power (kW)**  
* Horizontal and vertical forces:  

$$
F_h = D_{total} + m \cdot a_h
$$

$$
F_v = m \cdot a_v
$$

* Shaft power:  

$$
P_{shaft, avg} = \frac{P_{hover} + F_h \cdot v_{avg,h} + F_v \cdot v_v}{\eta_{rotor} \cdot W_{KW}}
$$  

where $W_{KW}$ is the unit conversion factor to kW, aircraft mass $m$ (*aircraft.max_takeoff_mass_kg*), $\eta_{rotor}$ = rotor efficiency (*propulsion.rotor_effic*), $\rho$ = air density (*environ.air_density_sea_lvl_kg_p_m3*), and $A$ = rotor disk area (*propulsion.disk_area_m2*).  

```python
def _calc_trans_climb_avg_shaft_power_kw(self):
  if self.mission != None and self.propulsion != None and self.environ != None:
    q = 0.5*self.environ.air_density_sea_lvl_kg_p_m3*self.mission.trans_climb_avg_h_m_p_s**2.0
    theta = math.atan2(self.mission.trans_climb_v_m_p_s, self.mission.trans_climb_avg_h_m_p_s)

    weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
    lift_n = weight_n*math.cos(theta)
    vehicle_cl = lift_n/(q*self.wing_area_m2)

    # induced drag
    di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
    # parasite drag
    cd0 = self._calc_total_drag_coef()
    if cd0 == None:
      return None
    dp_n = q*self.wing_area_m2*cd0
    # total drag
    total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor

    # horizontal acceleration
    v0_h_m_p_s = 0.0
    vf_h_m_p_s = 2.0*self.mission.trans_climb_avg_h_m_p_s
    d_h_m = self.mission.trans_climb_avg_h_m_p_s*self.mission.trans_climb_s
    a_h_m_p_s2 = (vf_h_m_p_s**2.0-v0_h_m_p_s**2.0)/(2.0*d_h_m)
      
    # vertical component (constant velocity, no acceleration)
    a_v_m_p_s2 = 0.0

    # force components 
    force_h_n = total_drag_n+self.max_takeoff_mass_kg*a_h_m_p_s2
    force_v_n = self.max_takeoff_mass_kg*a_v_m_p_s2

    # induced velocity & power based on thrust deficit
    T_req_n = max(0.0, (weight_n - lift_n) + self.max_takeoff_mass_kg*a_v_m_p_s2)
    if T_req_n > 0.0:
      v_i_hover = math.sqrt(T_req_n/(2.0*self.environ.air_density_sea_lvl_kg_p_m3*self.propulsion.disk_area_m2))
    else:
      v_i_hover = 0.0

    # hover-induced power for unsupported weight only (no efficiency here yet)
    P_hover_W = T_req_n*v_i_hover

    # total shaft power (apply rotor efficiency once)
    return (P_hover_W+force_h_n*self.mission.trans_climb_avg_h_m_p_s+\
            force_v_n*self.mission.trans_climb_v_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
  else:
    return None
```

---
### Segment D: Depart Procedures  

**Description:**  
* Calculations for the **Depart Procedures** segment consider **horizontal motion only**.  
* Horizontal velocity is assumed **constant**.  
* Vertical motion is neglected.
* Aerodynamic lift, induced drag, parasite drag, and horizontal drag are included.  
* Average shaft power is then calculated based on horizontal forces and rotor efficiency.  

**Displacement, Acceleration, and Velocity Components**  
* Let:  
  * $v_h$ = horizontal velocity (*mission.depart_proc_h_m_p_s*)  
  * $t$ = duration of depart procedures segment (*mission.depart_proc_s*)  

* Horizontal motion: constant velocity, so no acceleration ($a_h = 0$).   
  
**Average Shaft Power (kW)**  
* Horizontal force:  

$$
F_h = D_{total}
$$  

* Shaft power:  

$$
P_{shaft, avg} = \frac{F_h \cdot v_h}{\eta_{rotor} \cdot W_{KW}}
$$  

where $W_{KW}$ is the unit conversion factor to kW, and $\eta_{rotor}$ = rotor efficiency (*propulsion.rotor_effic*).  

```python
def _calc_depart_proc_avg_shaft_power_kw(self):
  if self.mission != None and self.propulsion != None and self.environ != None:
    q = 0.5*self.environ.air_density_sea_lvl_kg_p_m3*self.mission.depart_proc_h_m_p_s**2.0
    weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
    lift_n = weight_n
    
    # induced drag
    di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
    # parasite drag
    cd0 = self._calc_total_drag_coef()
    if cd0 == None:
      return None
    dp_n = q*self.wing_area_m2*cd0
    # total drag
    total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor

    # force components 
    force_h_n = total_drag_n

    return (force_h_n*self.mission.depart_proc_h_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
  else:
    return None
```

---
### Segment E: Accelerate Climb  

**Description:**  
* Calculations for the **Accelerate Climb** segment include **horizontal and vertical motion**.  
* Aerodynamic lift, induced drag, parasite drag, weight, and horizontal/vertical accelerations are included.  
* Horizontal velocity starts from the final velocity of the previous segment and accelerates further.  
* Vertical velocity starts from zero and accelerates to the final vertical velocity (*mission.accel_climb_v_m_p_s*).  
* Average shaft power is then calculated based on horizontal and vertical forces and rotor efficiency.   
  
**Displacement, Acceleration, and Velocity Components**  
* Let:  
  * $v_{i,h}$ = initial horizontal velocity = final horizontal velocity of previous segment (*mission.depart_proc_h_m_p_s*)
  * $v_{avg,h}$ = average horizontal velocity (*mission.accel_climb_avg_h_m_p_s*)  
  * $v_{f,h}$ = final horizontal velocity  
  * $v_{i,v}$ = 0 = initial vertical velocity  
  * $v_{f,v}$ = final vertical velocity (*mission.accel_climb_v_m_p_s*)  
  * $t$ = duration of accelerate climb segment (*mission.accel_climb_s*)  
  
* Horizontal displacement $d_h$ and acceleration $a_h$:

$$
d_h = v_{avg,h} \cdot t
$$

$$
v_{f,h} = 2 \cdot v_{avg,h} - v_{i,h}
$$

$$
a_h = \frac{v_{f,h}^2 - v_{i,h}^2}{2 \cdot d_h}
$$  

* Vertical displacement $d_v$ and acceleration $a_v$:

$$
d_v = \frac{1}{2}(v_{i,v} + v_{f,v}) \cdot t
$$

$$
a_v = \frac{v_{f,v}^2 - v_{i,v}^2}{2 \cdot d_v}
$$  

**Average Shaft Power (kW)**  
* Horizontal and vertical forces:

$$
F_h = D_{total} + m \cdot a_h
$$

$$
F_v = (Weight - Lift) + m \cdot a_v
$$

* Shaft power:

$$
P_{shaft, avg} = \frac{F_h \cdot v_{avg,h} + F_v \cdot \frac{v_{i,v} + v_{f,v}}{2}}{\eta_{rotor} \cdot W_{KW}}
$$   

where $W_{KW}$ is the unit conversion factor to kW, aircraft mass $m$ (*aircraft.max_takeoff_mass_kg*), and $\eta_{rotor}$ = rotor efficiency (*propulsion.rotor_effic*).  

```python
def _calc_accel_climb_avg_shaft_power_kw(self):
  if self.mission != None and self.propulsion != None and self.environ != None:
    q = 0.5*self.environ.air_density_sea_lvl_kg_p_m3*self.mission.accel_climb_avg_h_m_p_s**2.0
    theta = math.atan2(self.mission.accel_climb_v_m_p_s, self.mission.accel_climb_avg_h_m_p_s)

    weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
    lift_n = weight_n*math.cos(theta)
    vehicle_cl = lift_n/(q*self.wing_area_m2)

    # induced drag
    di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
    # parasite drag
    cd0 = self._calc_total_drag_coef()
    if cd0 == None:
      return None
    dp_n = q*self.wing_area_m2*cd0
    # total drag
    total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor

    # horizontal accelerations
    v0_h_m_p_s = self.mission.depart_proc_h_m_p_s
    vf_h_m_p_s = 2.0*self.mission.accel_climb_avg_h_m_p_s-v0_h_m_p_s
    d_h_m = self.mission.accel_climb_avg_h_m_p_s*self.mission.accel_climb_s
    a_h_m_p_s2 = (vf_h_m_p_s**2.0-v0_h_m_p_s**2.0)/(2.0*d_h_m)

    # vertical accelerations
    v0_v_m_p_s = 0.0
    vf_v_m_p_s = self.mission.accel_climb_v_m_p_s
    d_v_m = 0.5*(v0_v_m_p_s+vf_v_m_p_s)*self.mission.accel_climb_s
    a_v_m_p_s2 = (vf_v_m_p_s**2.0-v0_v_m_p_s**2.0)/(2.0*d_v_m)

    # force components
    force_h_n = total_drag_n+self.max_takeoff_mass_kg*a_h_m_p_s2
    force_v_n = (weight_n-lift_n)+self.max_takeoff_mass_kg*a_v_m_p_s2

    return (force_h_n*self.mission.accel_climb_avg_h_m_p_s+force_v_n*(0.5*(v0_v_m_p_s+vf_v_m_p_s)))/(self.propulsion.rotor_effic*W_P_KW)
  else:
    return None
```

---
### Segment F: Cruise  

**Description:**  
* Calculations for the **Cruise** segment consider **horizontal motion only**.  
* Horizontal velocity is assumed **constant**.  
* Vertical motion is neglected.  
* Aerodynamic lift, induced drag, parasite drag, and horizontal drag are included.  
* Average shaft power is then calculated based on horizontal forces and rotor efficiency.  

**Displacement, Acceleration, and Velocity Components**  
* Let:  
  * $v_h$ = horizontal velocity (*mission.cruise_h_m_p_s*)  
  * $t$ = duration of cruise segment (*mission.cruise_s*)  

* Horizontal motion: constant velocity, so no acceleration ($a_h = 0$).  

**Average Shaft Power (kW)**  
* Horizontal force:  

$$
F_h = D_{total}
$$  

* Shaft power:  

$$
P_{shaft, avg} = \frac{F_h \cdot v_h}{\eta_{rotor} \cdot W_{KW}}
$$  

where $W_{KW}$ is the unit conversion factor to kW, and $\eta_{rotor}$ = rotor efficiency (*propulsion.rotor_effic*).  

```python
def _calc_cruise_avg_shaft_power_kw(self):
  if self.mission != None and self.propulsion != None and self.environ != None:
    q = 0.5*self.environ.air_density_max_alt_kg_p_m3*self.mission.cruise_h_m_p_s**2.0
    weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
    lift_n = weight_n
    
    # induced drag
    di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
    # parasite drag
    cd0 = self._calc_total_drag_coef()
    if cd0 == None:
      return None
    if self.wing_airfoil_cd_at_cruise_cl != None and self.stopped_rotor_cd0 != None:
      cd0_cruise = cd0+self.wing_airfoil_cd_at_cruise_cl+self.stopped_rotor_cd0
    else:
      cd0_cruise = cd0
    dp_n = q*self.wing_area_m2*cd0_cruise
    # total drag
    total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor

    return (total_drag_n*self.mission.cruise_h_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
  else:
    return None
```

---
### Segment G: Decelerate Descend  

**Description:**  
* Calculations for the **Decelerate Descend** segment include **horizontal and vertical motion**.  
* Aerodynamic lift, induced drag, parasite drag, weight, and horizontal deceleration are included. Additionally, vertical thrust assist and spoiler drag are applied automatically when needed. 
* Horizontal velocity starts from cruise velocity and decelerates to a final horizontal velocity.  
* Vertical velocity starts from 0 and accelerates downwards to *mission.decel_descend_v_m_p_s*.  
* Average shaft power is then calculated based on horizontal and vertical forces, rotor efficiency, and includes adjustments for vertical thrust deficit and spoiler drag.  

**Displacement, Acceleration, and Velocity Components**  
* Let:  
  * $v_{i,h}$ = initial horizontal velocity (*mission.cruise_h_m_p_s*)  
  * $v_{avg,h}$ = average horizontal velocity (*mission.decel_descend_avg_h_m_p_s*)  
  * $v_{i,v}$ = 0 = initial vertical velocity 
  * $v_{f,v}$ = vertical velocity (*mission.decel_descend_v_m_p_s*)  
  * $t$ = duration of decelerate descend segment (*mission.decel_descend_s*)  

* Horizontal displacement $d_h$ and acceleration $a_h$:

$$
d_h = v_{avg,h} \cdot t
$$

$$
v_{f,h} = 2 \cdot v_{avg,h} - v_{i,h}
$$

$$
a_h = \frac{v_{f,h}^2 - v_{i,h}^2}{2 \cdot d_h}
$$  

* Vertical displacement $d_v$ and acceleration $a_v$:

$$
d_v = \frac{v_{f,v}}{2} \cdot t
$$

$$
a_v = \frac{v_{f,v}^2 - v_{i,v}^2}{2 \cdot d_v}
$$  

* Note: vertical acceleration is **downwards**, so it is subtracted in the force calculation.  

**Average Shaft Power (kW)**  
* Horizontal and vertical forces:  

$$
F_h = D_{total} + m \cdot a_h
$$

$$
F_v = (Weight - Lift) - m \cdot a_v
$$

* Shaft power (baseline):  

$$
P_{shaft, avg} = \frac{F_h \cdot v_{avg,h} + F_v \cdot \frac{v_{i,v} + v_{f,v}}{2}}{\eta_{rotor} \cdot W_{KW}}
$$  

**Special Automatic Adjustments:**  

**1.  Vertical thrust assist:** If vertical acceleration requires more thrust than gravity provides, add additional shaft power:  

$$
P_{thrust, assist} = \frac{(m \cdot a_v - (Weight - Lift)) \cdot \frac{v_{i,v} + v_{f,v}}{2}}{\eta_{rotor} \cdot W_{KW}}, \quad \text{if } m \cdot a_v > (Weight - Lift)
$$  

**2. Spoiler drag:** If total shaft power is negative, add equivalent spoiler drag to increase horizontal force:  

$$
F_{h,new} = F_h + F_{spoiler}, \quad P_{shaft,new} = \frac{F_{h,new} \cdot v_{avg,h} + F_v \cdot \frac{v_{i,v} + v_{f,v}}{2}}{\eta_{rotor} \cdot W_{KW}}
$$  

where $W_{KW}$ is the unit conversion factor to kW, aircraft mass $m$ (*aircraft.max_takeoff_mass_kg*), and $\eta_{rotor}$ = rotor efficiency (*propulsion.rotor_effic*).  

```python
def _calc_decel_descend_avg_shaft_power_kw(self):
  if self.mission != None and self.propulsion != None and self.environ != None:     
    q = 0.5*self.environ.air_density_sea_lvl_kg_p_m3*self.mission.decel_descend_avg_h_m_p_s**2.0
    theta = math.atan2(self.mission.decel_descend_v_m_p_s, self.mission.decel_descend_avg_h_m_p_s)

    weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
    lift_n = weight_n*math.cos(theta)
    vehicle_cl = lift_n/(q*self.wing_area_m2)

    # induced drag
    di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
    # parasite drag
    cd0 = self._calc_total_drag_coef()
    if cd0 == None:
      return None
    dp_n = q*self.wing_area_m2*cd0
    # total drag
    total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor

    # horizontal accelerations
    v0_h_m_p_s = self.mission.cruise_h_m_p_s
    vf_h_m_p_s = 2.0*self.mission.decel_descend_avg_h_m_p_s-v0_h_m_p_s
    d_h_m = self.mission.decel_descend_avg_h_m_p_s*self.mission.decel_descend_s
    a_h_m_p_s2 = (vf_h_m_p_s**2.0-v0_h_m_p_s**2.0)/(2.0*d_h_m) 

    # vertical accelerations
    v0_v_m_p_s = 0.0
    vf_v_m_p_s = self.mission.decel_descend_v_m_p_s
    d_v_m = 0.5*(v0_v_m_p_s+vf_v_m_p_s)*self.mission.decel_descend_s
    a_v_m_p_s2 = (vf_v_m_p_s**2.0-v0_v_m_p_s**2.0)/(2.0*d_v_m)

    # force components
    force_h_n = total_drag_n+self.max_takeoff_mass_kg*a_h_m_p_s2
    force_v_n = (weight_n-lift_n)-self.max_takeoff_mass_kg*a_v_m_p_s2 # physical: downward, speeding up

    # compute shaft power baseline
    shaft_power_kw = (force_h_n*self.mission.decel_descend_avg_h_m_p_s+force_v_n*(0.5*(v0_v_m_p_s+vf_v_m_p_s)))/(self.propulsion.rotor_effic*W_P_KW)

    # check vertical deficit: if gravity cannot provide enough, add vertical thrust assist shaft power
    vertical_deficit_n = self.max_takeoff_mass_kg*a_v_m_p_s2-(weight_n-lift_n)
    shaft_power_deficit_kw = 0.0
    if vertical_deficit_n > 0.0:
      shaft_power_deficit_kw = (vertical_deficit_n*(0.5*(v0_v_m_p_s+vf_v_m_p_s)))/(self.propulsion.rotor_effic*W_P_KW)

    # total shaft power (baseline + vertical assist)
    shaft_power_kw += shaft_power_deficit_kw

    # check for negative power to add spoiler drag
    if shaft_power_kw < 0.0:
      # required additional horizontal force to neutralize negative power
      required_extra_force_n = -force_h_n
      # compute equivalent delta Cd
      delta_cd_spoiler = required_extra_force_n/(q*self.wing_area_m2)
      if delta_cd_spoiler < 0.0:
        delta_cd_spoiler = 0.0
      # recompute with spoilers
      dp_spoiler_n = q*self.wing_area_m2*delta_cd_spoiler
      total_drag_n = (di_n+dp_n+dp_spoiler_n)*self.trim_drag_factor*self.excres_protub_factor
      force_h_n = total_drag_n+self.max_takeoff_mass_kg*a_h_m_p_s2

      # total shaft power (with spoiler drag and vertical assist)
      shaft_power_kw = (force_h_n*self.mission.decel_descend_avg_h_m_p_s+force_v_n*(0.5*(v0_v_m_p_s+vf_v_m_p_s)))/(self.propulsion.rotor_effic*W_P_KW) + shaft_power_deficit_kw

    return shaft_power_kw
  else:
    return None
```

---
### Segment H: Arrive Procedures  

**Description:**  
* Calculations for the **Arrive Procedures** segment consider **horizontal motion only**.  
* Horizontal velocity is assumed **constant**.  
* Vertical motion is neglected.  
* Aerodynamic lift, induced drag, parasite drag, and horizontal drag are included.  
* Average shaft power is then calculated based on horizontal forces and rotor efficiency.  

**Displacement, Acceleration, and Velocity Components**  
* Let:  
  * $v_h$ = horizontal velocity (*mission.arrive_proc_h_m_p_s*)  
  * $t$ = duration of arrive procedures segment (*mission.arrive_proc_s*)  

* Horizontal motion: constant velocity, so no acceleration ($a_h = 0$).   

**Average Shaft Power (kW)**  
* Horizontal force:  

$$
F_h = D_{total}
$$  

* Shaft power:  

$$
P_{shaft, avg} = \frac{F_h \cdot v_h}{\eta_{rotor} \cdot W_{KW}}
$$  

where $W_{KW}$ is the unit conversion factor to kW, and $\eta_{rotor}$ = rotor efficiency (*propulsion.rotor_effic*).  

```python
def _calc_arrive_proc_avg_shaft_power_kw(self):
  if self.mission != None and self.propulsion != None and self.environ != None:
    q = 0.5*self.environ.air_density_sea_lvl_kg_p_m3*self.mission.arrive_proc_h_m_p_s**2.0
    weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
    # horizontal component
    lift_n = weight_n
    # induced drag
    di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
    # parasite drag
    cd0 = self._calc_total_drag_coef()
    if cd0 == None:
      return None
    dp_n = q*self.wing_area_m2*cd0
    # total drag
    total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor

    # force components
    force_h_n = total_drag_n

    return (force_h_n*self.mission.arrive_proc_h_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
  else:
    return None
```

---
### Segment I: Transition Descend  

**Description:**  
* Calculations for the **Transition Descend** segment include **horizontal and vertical motion**.  
* Aerodynamic lift, induced drag, parasite drag, weight, descent forces, and hover-induced power are included.  
* Additional automatic corrections include **spoiler drag** if power becomes negative.  
* Horizontal velocity starts from an estimated initial value and decelerates to zero.  
* Vertical velocity transitions from the previous descend rate (*mission.decel_descend_v_m_p_s*) to the final descent velocity (*mission.trans_descend_v_m_p_s*).  
* The total shaft power includes **aerodynamic power**, **hover-induced assist power**, and automatic spoiler drag compensation.  
* Physically, the hover-induced term represents induced power required to provide thrust when aerodynamic lift and gravity are insufficient to balance vertical forces during the transition phase.  

**Displacement, Acceleration, and Velocity Components**  
* Let:  
  * $v_{i,h}$ = initial horizontal velocity  
  * $v_{f,h}$ = 0 = final horizontal velocity  
  * $v_{i,v}$ = initial vertical velocity (*mission.decel_descend_v_m_p_s*)  
  * $v_{f,v}$ = final vertical velocity (*mission.trans_descend_v_m_p_s*)  
  * $v_{avg,h}$ = average horizontal velocity (*mission.trans_descend_avg_h_m_p_s*)  
  * $t$ = duration of transition descend segment (*mission.trans_descend_s*)  

* Horizontal displacement $d_h$, initial velocity $v_{i,h}$, and acceleration $a_h$:

$$
v_{i,h} = 2 \cdot v_{avg,h} - v_{f,h}
$$

$$
d_h = v_{avg,h} \cdot t
$$

$$
a_h = \frac{v_{f,h}^2 - v_{i,h}^2}{2 \cdot d_h}
$$  

* Vertical displacement $d_v$ and acceleration $a_v$:

$$
d_v = \frac{|v_{i,v}| + |v_{f,v}|}{2} \cdot t
$$

$$
a_v = \frac{v_{f,v}^2 - v_{i,v}^2}{2 \cdot d_v}
$$  

**Hover-Induced Power (W)**  
* When aerodynamic lift and gravity together are insufficient to balance vertical forces, additional thrust is required.  
  The thrust deficit is defined as:  

$$
T_{req} = (Weight - Lift) + m \cdot a_v
$$  

* If $T_{req} > 0$, the induced velocity and corresponding induced power are calculated using propeller momentum theory:  

$$
v_{i,hover} = \sqrt{\frac{T_{req}}{2 \cdot \rho \cdot A}}
$$  

$$
P_{hover} = T_{req} \cdot v_{i,hover}
$$  

**Average Shaft Power (kW)**  
* Horizontal and vertical forces:  

$$
F_h = D_{total} + m \cdot a_h
$$

$$
F_v = m \cdot a_v
$$

* Shaft power (baseline):  

$$
P_{shaft, avg} = \frac{P_{hover} + F_h \cdot v_{avg,h} + F_v \cdot \frac{v_{i,v} + v_{f,v}}{2}}{\eta_{rotor} \cdot W_{KW}}
$$  

**Special Automatic Adjustments - Spoiler drag**  

* If total shaft power is negative, spoiler drag is applied to dissipate excess energy and bring power back to nonnegative levels:  

$$
F_{h,new} = F_h + F_{spoiler}, \quad P_{shaft,new} = \frac{P_{hover} + F_{h,new} \cdot v_{avg,h} + F_v \cdot \frac{v_{i,v} + v_{f,v}}{2}}{\eta_{rotor} \cdot W_{KW}}
$$  

where $W_{KW}$ is the unit conversion factor to kW, aircraft mass $m$ (*aircraft.max_takeoff_mass_kg*), $\eta_{rotor}$ = rotor efficiency (*propulsion.rotor_effic*), $\rho$ = air density (*environ.air_density_sea_lvl_kg_p_m3*), and $A$ = rotor disk area (*propulsion.disk_area_m2*).   

```python
def _calc_trans_descend_avg_shaft_power_kw(self):
  if self.mission != None and self.propulsion != None and self.environ != None:
    q = 0.5*self.environ.air_density_sea_lvl_kg_p_m3*self.mission.trans_descend_avg_h_m_p_s**2.0
    theta = math.atan2(self.mission.trans_descend_v_m_p_s, self.mission.trans_descend_avg_h_m_p_s)

    weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
    lift_n = weight_n*math.cos(theta)
    vehicle_cl = lift_n/(q*self.wing_area_m2)

    # induced drag
    di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
    # parasite drag
    cd0 = self._calc_total_drag_coef()
    if cd0 == None:
      return None
    dp_n = q*self.wing_area_m2*cd0
    # total drag
    total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor

    # horizontal acceleration (vehicle decelerates to stop)
    v0_h_m_p_s = 2.0*self.mission.trans_descend_avg_h_m_p_s
    vf_h_m_p_s = 0.0
    d_h_m = self.mission.trans_descend_avg_h_m_p_s*self.mission.trans_descend_s
    a_h_m_p_s2 = (vf_h_m_p_s**2.0 - v0_h_m_p_s**2.0)/(2.0*d_h_m)

    # vertical acceleration
    v0_v_m_p_s = self.mission.decel_descend_v_m_p_s
    vf_v_m_p_s = self.mission.trans_descend_v_m_p_s
    d_v_m = 0.5*(abs(v0_v_m_p_s)+abs(vf_v_m_p_s))*self.mission.trans_descend_s
    a_v_m_p_s2 = (vf_v_m_p_s**2.0 - v0_v_m_p_s**2.0)/(2.0*d_v_m)

    # force components
    force_h_n = total_drag_n+self.max_takeoff_mass_kg*a_h_m_p_s2
    force_v_n = self.max_takeoff_mass_kg*a_v_m_p_s2

    # compute thrust deficit if gravity + lift are insufficient
    T_req_n = max(0.0, (weight_n - lift_n) + self.max_takeoff_mass_kg*a_v_m_p_s2)
    if T_req_n > 0.0:
      v_i_hover = math.sqrt(T_req_n/(2.0*self.environ.air_density_sea_lvl_kg_p_m3*self.propulsion.disk_area_m2))
    else:
      v_i_hover = 0.0

    # hover-induced (assist) power for unsupported weight only
    P_hover_W = T_req_n*v_i_hover

    # baseline shaft power (sum of aerodynamic and vertical terms)
    shaft_power_kw = (P_hover_W+force_h_n*self.mission.trans_descend_avg_h_m_p_s+\
                      force_v_n*(0.5*(v0_v_m_p_s+vf_v_m_p_s)))/(self.propulsion.rotor_effic*W_P_KW)

    # check for negative power → apply spoiler drag to dissipate excess
    if shaft_power_kw < 0.0:
      required_extra_force_n = -force_h_n
      delta_cd_spoiler = required_extra_force_n/(q*self.wing_area_m2)
      if delta_cd_spoiler < 0.0:
        delta_cd_spoiler = 0.0
      dp_spoiler_n = q*self.wing_area_m2*delta_cd_spoiler
      total_drag_n = (di_n+dp_n+dp_spoiler_n)*self.trim_drag_factor*self.excres_protub_factor
      force_h_n = total_drag_n+self.max_takeoff_mass_kg*a_h_m_p_s2

      # recompute total shaft power with spoiler drag
      shaft_power_kw = (P_hover_W+force_h_n*self.mission.trans_descend_avg_h_m_p_s+\
                        force_v_n*(0.5*(v0_v_m_p_s+vf_v_m_p_s)))/(self.propulsion.rotor_effic*W_P_KW)

    return shaft_power_kw
  else:
    return None
```

---
### Segment J: Hover Descend  

**Description:**  
* Calculations for the **Hover Descend** segment consider **vertical motion only**.  
* Drag effects are neglected.  
* The aircraft starts with an initial downward velocity and decelerates to a stop at the end of the segment.  
* The total shaft power consists of two components:  
  1. Hover Power: the induced power required to balance the aircraft’s weight during descent.  
  2. Vertical Power: the additional (or reduced) power due to vertical acceleration.  
* Physically, the hover power represents the induced power required to maintain lift and support weight during vertical descent, while the acceleration term accounts for deceleration as the vehicle approaches landing zone. 
  
**Displacement, Acceleration, and Velocity Components**  
* Let:  
  * $v_{i,v}$ = initial vertical velocity
  * $v_{f,v}$ = 0 = final vertical velocity  
  * $v_{avg,v}$ = average vertical velocity (*mission.hover_descend_avg_v_m_p_s*)  
  * $t$ = duration of hover descend segment (*mission.hover_descend_s*)  

* Vertical displacement $d_v$, initial velocity $v_{i,v}$, and acceleration $a_v$:

$$
v_{i,v} = 2 \cdot v_{avg,v} - v_{f,v}
$$

$$
d_v = v_{avg,v} \cdot t
$$

$$
a_v = \frac{v_{f,v}^2 - v_{i,v}^2}{2 \cdot d_v}
$$  

**Hover Power (W)**  
* The induced velocity in hover, from propeller momentum theory, is:  

$$
v_{i,hover} = \sqrt{\frac{m \cdot g}{2 \cdot \rho \cdot A}}
$$  

where:  
  * $m$ = aircraft mass (*aircraft.max_takeoff_mass_kg*)  
  * $g$ = gravitational acceleration (*environ.g_m_p_s2*)  
  * $\rho$ = air density (*environ.air_density_sea_lvl_kg_p_m3*)  
  * $A$ = total rotor disk area (*propulsion.disk_area_m2*)  

The induced hover power is then:  

$$
P_{hover} = m \cdot g \cdot v_{i,hover}
$$  

**Average Shaft Power (kW)**  
* The total shaft power (hover and vertical components) is:  

$$
P_{shaft,avg} = \frac{P_{hover} + (m \cdot a_v) \cdot v_{avg,v}}{\eta_{rotor} \cdot W_{KW}}
$$  

where $W_{KW}$ is the unit conversion factor to kW, and $\eta_{rotor}$ = rotor efficiency (*propulsion.rotor_effic*).  

```python
def _calc_hover_descend_avg_shaft_power_kw(self):
  if self.mission != None and self.propulsion != None and self.environ != None:
      
      # vertical kinematics (upward positive)
      v0_v_m_p_s = 2.0*self.mission.hover_descend_avg_v_m_p_s
      vf_v_m_p_s = 0.0
      d_v_m = self.mission.hover_descend_avg_v_m_p_s*self.mission.hover_descend_s
      a_v_m_p_s2 = (vf_v_m_p_s**2.0 - v0_v_m_p_s**2.0) / (2.0*d_v_m)

      # vertical thrust required (upward positive)
      force_v_n =  (self.max_takeoff_mass_kg*a_v_m_p_s2)

      # induced velocity in hover (prop thrust momentum theory)
      v_i_hover = math.sqrt((self.max_takeoff_mass_kg*self.environ.g_m_p_s2)/\
                            (2.0*self.environ.air_density_sea_lvl_kg_p_m3*self.propulsion.disk_area_m2))

      # induced hover power
      P_hover_W = (self.max_takeoff_mass_kg*self.environ.g_m_p_s2)*v_i_hover

      # total shaft power (hover & vertical component)
      return \
        (P_hover_W + force_v_n * self.mission.hover_descend_avg_v_m_p_s) / \
          (self.propulsion.rotor_effic * W_P_KW)
  else:
      return None
```

---
### Segment K: Arrive Taxi  

**Description:**    
* Calculations for the **Arrive Taxi** segment consider **horizontal motion only**.  
* Drag effects are neglected.  
* Horizontal velocity increases from zero to a final velocity.
* Average shaft power is then calculated based on MTOM, horizontal acceleration, and average horizontal velocity.  

**Displacement, Acceleration, and Velocity Components**  
* Let:  
  * $v_{i,h}$ = 0 = initial horizontal velocity  
  * $v_{f,h}$ = final horizontal velocity  
  * $v_{avg,h}$ = average horizontal velocity (*mission.arrive_taxi_avg_h_m_p_s*)  
  * $t$ = duration of arrive taxi segment (*mission.arrive_taxi_s*)  

* Horizontal displacement $d_h$ and acceleration $a_h$:

$$
v_{f,h} = 2 \cdot v_{avg,h} - v_{i,h}
$$

$$
d_h = v_{avg,h} \cdot t
$$

$$
a_h = \frac{v_{f,h}^2 - v_{i,h}^2}{2 \cdot d_h}
$$  

**Average Shaft Power (kW)**  
* Horizontal force:  

$$
F_h = m \cdot a_h
$$

* Shaft power:  

$$
P_{shaft, avg} = \frac{F_h \cdot v_{avg,h}}{\eta_{rotor} \cdot W_{KW}}
$$  

where $W_{KW}$ is the unit conversion factor to kW, aircraft mass $m$ (*aircraft.max_takeoff_mass_kg*), and $\eta_{rotor}$ = rotor efficiency (*propulsion.rotor_effic*).  

```python
def _calc_arrive_taxi_avg_shaft_power_kw(self):
  if self.mission != None and self.propulsion != None and self.environ != None:
    # horizontal accelerations
    v0_h_m_p_s = 0.0
    vf_h_m_p_s = 2.0*self.mission.arrive_taxi_avg_h_m_p_s
    d_h_m = self.mission.arrive_taxi_avg_h_m_p_s*self.mission.arrive_taxi_s
    a_h_m_p_s2 = (vf_h_m_p_s**2.0-v0_h_m_p_s**2.0)/(2.0*d_h_m)
    
    # horizontal force 
    force_h_n = self.max_takeoff_mass_kg*a_h_m_p_s2

    return (force_h_n*self.mission.arrive_taxi_avg_h_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
  else:
    return None
```

---
### Segment B': Reserve Hover Climb
**Description:**  
* Calculations for the **Reserve Hover Climb** segment consider **vertical motion only**.  
* Drag effects are neglected, and the aircraft starts from rest, accelerating upward to a final vertical velocity.  
* The total shaft power consists of two components:  
  1. Hover Power: the induced power required to support the aircraft’s weight when aerodynamic lift from the wings is negligible.  
  2. Climb Power: the additional power required to accelerate the aircraft vertically during the reserve hover climb phase.  
* Physically, the hover power represents the induced power required to support partial or full aircraft weight during hover or transition, when the wings do not yet generate sufficient lift. 

**Displacement, Acceleration, and Final Velocity**  
* Let:  
  * $v_i$ = 0 = initial vertical velocity  
  * $v_{avg}$ = average vertical velocity (*mission.reserve_hover_climb_avg_v_m_p_s*)  
  * $t$ = duration of reserve hover climb segment (*mission.reserve_hover_climb_s*)  

* Vertical displacement $d_v$ and final velocity $v_f$:  

$$
d_v = v_{avg} \cdot t
$$

$$
v_f = 2 \cdot v_{avg}
$$

$$
a_v = \frac{v_f^2}{2 \cdot d_v}
$$  

**Hover Power (W)**  
* The induced velocity in hover, based on propeller momentum theory, is:  

$$
v_{i,hover} = \sqrt{\frac{m \cdot g}{2 \cdot \rho \cdot A}}
$$  

where:  
  * $m$ = aircraft mass (*aircraft.max_takeoff_mass_kg*)  
  * $g$ = gravitational acceleration (*environ.g_m_p_s2*)  
  * $\rho$ = air density (*environ.air_density_sea_lvl_kg_p_m3*)  
  * $A$ = total rotor disk area (*propulsion.disk_area_m2*)  

The induced hover power is then:  

$$
P_{hover} = m \cdot g \cdot v_{i,hover}
$$  

**Average Shaft Power (kW)**  
* The total shaft power is the sum of hover power and climb power, divided by rotor efficiency:  

$$
P_{shaft,avg} = \frac{P_{hover} + m \cdot a_v \cdot v_{avg}}{\eta_{rotor} \cdot W_{KW}}
$$  

where $W_{KW}$ is the unit conversion factor to kW, and $\eta_{rotor}$ = rotor efficiency (*propulsion.rotor_effic*).  

```python
def _calc_reserve_hover_climb_avg_shaft_power_kw(self):
  if self.mission != None and self.propulsion != None:
      
      # vertical kinematics (upward positive)
      d_v_m = self.mission.reserve_hover_climb_avg_v_m_p_s*self.mission.reserve_hover_climb_s
      vf_v_m_p_s = (2.0*d_v_m)/self.mission.reserve_hover_climb_s
      a_v_m_p_s2 = vf_v_m_p_s**2.0/(2.0*d_v_m)
      
      # induced velocity in hover (prop thrust momentum theory)
      v_i_hover = math.sqrt((self.max_takeoff_mass_kg*self.environ.g_m_p_s2)/\
                            (2.0*self.environ.air_density_sea_lvl_kg_p_m3*self.propulsion.disk_area_m2))
      
      # induced power (hover)
      P_hover_W = (self.max_takeoff_mass_kg*self.environ.g_m_p_s2)*v_i_hover
      
      return \
        (P_hover_W+self.max_takeoff_mass_kg*a_v_m_p_s2*\
          self.mission.reserve_hover_climb_avg_v_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
  else:
      return None
```

---
### Segment C': Reserve Transition Climb  

**Description:**  
* Calculations for the **Reserve Transition Climb** segment include both **horizontal and vertical motion**.  
* Aerodynamic lift, induced drag, parasite drag, weight, hover-induced power, and climb forces are all considered.  
* Horizontal velocity starts from rest and accelerates to a final velocity based on the average horizontal velocity.  
* Vertical velocity is assumed **constant** throughout the segment (no vertical acceleration).  
* The total shaft power includes both **aerodynamic power** and **hover-induced power**, representing the thrust required to support any portion of aircraft weight not yet carried by aerodynamic lift.  
* Physically, the hover-induced power term represents the induced power required to supplement lift when wings are not yet producing full aerodynamic support during the transition from hover to forward flight in reserve operations.  

**Displacement, Acceleration, and Velocity Components**  
* Let:  
  * $v_{i,h}$ = 0 = initial horizontal velocity  
  * $v_{avg,h}$ = average horizontal velocity (*mission.reserve_trans_climb_avg_h_m_p_s*)  
  * $v_{f,h}$ = final horizontal velocity  
  * $v_{v}$ = vertical velocity (*mission.reserve_trans_climb_v_m_p_s*)  
  * $t$ = duration of reserve transition climb segment (*mission.reserve_trans_climb_s*)  

* Horizontal displacement $d_h$ and acceleration $a_h$:  

$$
d_h = v_{avg,h} \cdot t
$$

$$
v_{f,h} = 2 \cdot v_{avg,h} - v_{i,h}
$$

$$
a_h = \frac{v_{f,h}^2 - v_{i,h}^2}{2 \cdot d_h}
$$  

* Vertical acceleration $a_v$ = 0 (constant vertical velocity)  

**Hover-Induced Power (W)**  
* When aerodynamic lift does not fully balance the aircraft’s weight, additional thrust is required.  
  The thrust deficit is defined as:  

$$
T_{req} = (Weight - Lift) + m \cdot a_v
$$  

* If $T_{req} > 0$, the induced velocity and induced hover power are calculated using propeller momentum theory:  

$$
v_{i,hover} = \sqrt{\frac{T_{req}}{2 \cdot \rho \cdot A}}
$$  

$$
P_{hover} = T_{req} \cdot v_{i,hover}
$$  

**Average Shaft Power (kW)**  
* Horizontal and vertical forces:  

$$
F_h = D_{total} + m \cdot a_h
$$

$$
F_v = m \cdot a_v
$$  

* Shaft power:  

$$
P_{shaft, avg} = \frac{P_{hover} + F_h \cdot v_{avg,h} + F_v \cdot v_v}{\eta_{rotor} \cdot W_{KW}}
$$  

where $W_{KW}$ is the unit conversion factor to kW, aircraft mass $m$ (*aircraft.max_takeoff_mass_kg*), $\eta_{rotor}$ = rotor efficiency (*propulsion.rotor_effic*), $\rho$ = air density (*environ.air_density_sea_lvl_kg_p_m3*), and $A$ = rotor disk area (*propulsion.disk_area_m2*). 

```python
def _calc_reserve_trans_climb_avg_shaft_power_kw(self):
  if self.mission != None and self.propulsion != None and self.environ != None:
    q = 0.5*self.environ.air_density_sea_lvl_kg_p_m3*self.mission.reserve_trans_climb_avg_h_m_p_s**2.0
    theta = math.atan2(self.mission.reserve_trans_climb_v_m_p_s, self.mission.reserve_trans_climb_avg_h_m_p_s)

    weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
    lift_n = weight_n*math.cos(theta)
    vehicle_cl = lift_n/(q*self.wing_area_m2)

    # induced drag
    di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
    # parasite drag
    cd0 = self._calc_total_drag_coef()
    if cd0 == None:
      return None
    dp_n = q*self.wing_area_m2*cd0
    # total drag
    total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor

    # horizontal acceleration
    v0_h_m_p_s = 0.0
    vf_h_m_p_s = 2.0*self.mission.reserve_trans_climb_avg_h_m_p_s
    d_h_m = self.mission.reserve_trans_climb_avg_h_m_p_s*self.mission.reserve_trans_climb_s
    a_h_m_p_s2 = (vf_h_m_p_s**2.0 - v0_h_m_p_s**2.0)/(2.0*d_h_m)

    # vertical component (constant velocity, no acceleration)
    a_v_m_p_s2 = 0.0

    # force components
    force_h_n = total_drag_n+self.max_takeoff_mass_kg*a_h_m_p_s2
    force_v_n = self.max_takeoff_mass_kg*a_v_m_p_s2

    # induced velocity & power based on thrust deficit
    T_req_n = max(0.0, (weight_n - lift_n) + self.max_takeoff_mass_kg*a_v_m_p_s2)
    if T_req_n > 0.0:
      v_i_hover = math.sqrt(T_req_n/(2.0*self.environ.air_density_sea_lvl_kg_p_m3*self.propulsion.disk_area_m2))
    else:
      v_i_hover = 0.0

    # hover-induced power for unsupported weight only (no efficiency here yet)
    P_hover_W = T_req_n*v_i_hover

    # total shaft power (apply rotor efficiency once)
    return (P_hover_W+force_h_n*self.mission.reserve_trans_climb_avg_h_m_p_s+\
            force_v_n*self.mission.reserve_trans_climb_v_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
  else:
    return None
```

---
### Segment E': Reserve Acceleration Climb  

**Description:**  
* Calculations for the **Reserve Acceleration Climb** segment include **horizontal and vertical motion**.  
* Aerodynamic lift, induced drag, parasite drag, weight, and horizontal/vertical accelerations are included.  
* Horizontal velocity starts from the final velocity of the previous segment and accelerates further.  
* Vertical velocity is constant throughout the segment (no vertical acceleration).  
* Average shaft power is then calculated based on horizontal and vertical forces with rotor efficiency.  

**Displacement, Acceleration, and Velocity Components**  
* Let:  
  * $v_{i,h}$ = initial horizontal velocity  
  * $v_{avg,h}^{previous}$ = average horizontal velocity of the previous segment (*mission.reserve_trans_climb_avg_h_m_p_s*)
  * $v_{avg,h}$ = average horizontal velocity (*mission.reserve_accel_climb_avg_h_m_p_s*)  
  * $v_{f,h}$ = final horizontal velocity  
  * $v_v$ = vertical velocity (*mission.reserve_accel_climb_v_m_p_s*)  
  * $t$ = duration of reserve acceleration climb segment (*mission.reserve_accel_climb_s*)  

* Horizontal displacement $d_h$ and acceleration $a_h$:  

$$
d_h = v_{avg,h} \cdot t
$$

$$
v_{i,h} = 2 \cdot v_{avg,h}^{previous} - v_{i,h}
$$

$$
v_{f,h} = 2 \cdot v_{avg,h} - v_{i,h}
$$

$$
a_h = \frac{v_{f,h}^2 - v_{i,h}^2}{2 \cdot d_h}
$$  

* Vertical acceleration $a_v$ = 0 (constant vertical velocity)  

**Average Shaft Power (kW)**  
* Horizontal and vertical forces:  

$$
F_h = D_{total} + m \cdot a_h
$$

$$
F_v = (Weight - Lift) + m \cdot a_v
$$  

* Shaft power:  

$$
P_{shaft, avg} = \frac{F_h \cdot v_{avg,h} + F_v \cdot v_v}{\eta_{rotor} \cdot W_{KW}}
$$  

where $W_{KW}$ is the unit conversion factor to kW, aircraft mass $m$ (*aircraft.max_takeoff_mass_kg*), and $\eta_{rotor}$ = rotor efficiency (*propulsion.rotor_effic*).  

```python
def _calc_reserve_accel_climb_avg_shaft_power_kw(self):
  if self.mission != None and self.propulsion != None and self.environ != None:
    q = 0.5*self.environ.air_density_sea_lvl_kg_p_m3*self.mission.reserve_accel_climb_avg_h_m_p_s**2.0
    theta = math.atan2(self.mission.reserve_accel_climb_v_m_p_s, self.mission.reserve_accel_climb_avg_h_m_p_s)

    weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
    lift_n = weight_n*math.cos(theta)
    vehicle_cl = lift_n/(q*self.wing_area_m2)

    # induced drag
    di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
    # parasite drag
    cd0 = self._calc_total_drag_coef()
    if cd0 == None:
      return None
    dp_n = q*self.wing_area_m2*cd0
    # total drag
    total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor
    
    # horizontal accelerations
    v0_h_m_p_s = 2.0*self.mission.reserve_trans_climb_avg_h_m_p_s
    vf_h_m_p_s = 2.0*self.mission.reserve_accel_climb_avg_h_m_p_s-v0_h_m_p_s
    d_h_m = self.mission.reserve_accel_climb_avg_h_m_p_s*self.mission.reserve_accel_climb_s
    a_h_m_p_s2 = (vf_h_m_p_s**2.0 - v0_h_m_p_s**2.0)/(2.0*d_h_m)

    # vertical component (constant velocity, no acceleration)
    a_v_m_p_s2 = 0.0

    # force components
    force_h_n = total_drag_n+self.max_takeoff_mass_kg*a_h_m_p_s2
    force_v_n = (weight_n-lift_n)+self.max_takeoff_mass_kg*a_v_m_p_s2
    return (force_h_n*self.mission.reserve_accel_climb_avg_h_m_p_s+force_v_n*self.mission.reserve_accel_climb_v_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
  else:
    return None
```

---
### Segment F': Reserve Cruise  

**Description:**  
* Calculations for the **Reserve Cruise** segment consider **horizontal motion only**.  
* Horizontal velocity is assumed **constant**.  
* Vertical motion is neglected.  
* Aerodynamic lift, induced drag, parasite drag, and horizontal drag are included.  
* Average shaft power is then calculated based on horizontal forces and rotor efficiency.  

**Displacement, Acceleration, and Velocity Components**  
* Let:  
  * $v_h$ = horizontal velocity (*mission.reserve_cruise_h_m_p_s*)  
  * $t$ = duration of cruise segment (*mission.reserve_cruise_s*)  

* Horizontal motion: constant velocity, so no acceleration ($a_h = 0$).  

**Average Shaft Power (kW)**  
* Horizontal force:  

$$
F_h = D_{total}
$$  

* Shaft power:  

$$
P_{shaft, avg} = \frac{F_h \cdot v_h}{\eta_{rotor} \cdot W_{KW}}
$$  

where $W_{KW}$ is the unit conversion factor to kW, and $\eta_{rotor}$ = rotor efficiency (*propulsion.rotor_effic*).  

```python
def _calc_reserve_cruise_avg_shaft_power_kw(self):
  if self.mission != None and self.propulsion != None and self.environ != None:
    q = 0.5*self.environ.air_density_max_alt_kg_p_m3*self.mission.reserve_cruise_h_m_p_s**2.0
    weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
    lift_n = weight_n
    
    # induced drag
    di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
    # parasite drag
    cd0 = self._calc_total_drag_coef()
    if cd0 == None:
      return None
    if self.wing_airfoil_cd_at_cruise_cl != None and self.stopped_rotor_cd0 != None:
      cd0_cruise = cd0+self.wing_airfoil_cd_at_cruise_cl+self.stopped_rotor_cd0
    else:
      cd0_cruise = cd0
    dp_n = q*self.wing_area_m2*cd0_cruise
    # total drag
    total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor

    return (total_drag_n*self.mission.reserve_cruise_h_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
  else:
    return None
```

---
### Segment G: Reserve Decelerate Descend  

**Description:**  
* Calculations for the **Reserve Decelerate Descend** segment include **horizontal and vertical motion**.  
* Aerodynamic lift, induced drag, parasite drag, weight, and horizontal deceleration are included. Additionally, vertical thrust assist and spoiler drag are applied automatically when needed. 
* Horizontal velocity starts from previous segment's velocity and decelerates to a final horizontal velocity. 
* Vertical velocity starts from 0 and accelerates downwards to this segment's final velocity.  
* Average shaft power is then calculated based on horizontal and vertical forces, rotor efficiency, and includes adjustments for vertical thrust deficit and spoiler drag.  

**Displacement, Acceleration, and Velocity Components**  
* Let:  
  * $v_{i,h}$ = initial horizontal velocity = previous segment final velocity (*mission.cruise_h_m_p_s*)  
  * $v_{avg,h}$ = average horizontal velocity (*mission.reserve_decel_descend_avg_h_m_p_s*)  
  * $v_{i,v}$ = 0 = initial vertical velocity 
  * $v_{f,v}$ = vertical velocity (*mission.reserve_decel_descend_v_m_p_s*)  
  * $t$ = duration of decelerate descend segment (*mission.reserve_decel_descend_s*)  

* Horizontal displacement $d_h$ and acceleration $a_h$:

$$
d_h = v_{avg,h} \cdot t
$$

$$
v_{f,h} = 2 \cdot v_{avg,h} - v_{i,h}
$$

$$
a_h = \frac{v_{f,h}^2 - v_{i,h}^2}{2 \cdot d_h}
$$  

* Vertical displacement $d_v$ and acceleration $a_v$:

$$
d_v = \frac{v_{f,v}}{2} \cdot t
$$

$$
a_v = \frac{v_{f,v}^2 - v_{i,v}^2}{2 \cdot d_v}
$$  

* Note: vertical acceleration is **downwards**, so it is subtracted in the force calculation.  

**Average Shaft Power (kW)**  
* Horizontal and vertical forces:  

$$
F_h = D_{total} + m \cdot a_h
$$

$$
F_v = (Weight - Lift) - m \cdot a_v
$$

* Shaft power (baseline):  

$$
P_{shaft, avg} = \frac{F_h \cdot v_{avg,h} + F_v \cdot \frac{v_{i,v} + v_{f,v}}{2}}{\eta_{rotor} \cdot W_{KW}}
$$  

**Special Automatic Adjustments:**  

**1.  Vertical thrust assist:** If vertical acceleration requires more thrust than gravity provides, add additional shaft power:  

$$
P_{thrust, assist} = \frac{(m \cdot a_v - (Weight - Lift)) \cdot \frac{v_{i,v} + v_{f,v}}{2}}{\eta_{rotor} \cdot W_{KW}}, \quad \text{if } m \cdot a_v > (Weight - Lift)
$$  

**2. Spoiler drag:** If total shaft power is negative, add equivalent spoiler drag to increase horizontal force:  

$$
F_{h,new} = F_h + F_{spoiler}, \quad P_{shaft,new} = \frac{F_{h,new} \cdot v_{avg,h} + F_v \cdot \frac{v_{i,v} + v_{f,v}}{2}}{\eta_{rotor} \cdot W_{KW}}
$$  

where $W_{KW}$ is the unit conversion factor to kW, aircraft mass $m$ (*aircraft.max_takeoff_mass_kg*), and $\eta_{rotor}$ = rotor efficiency (*propulsion.rotor_effic*).  

```python
def _calc_reserve_decel_descend_avg_shaft_power_kw(self):
  if self.mission != None and self.propulsion != None and self.environ != None:
    q = 0.5*self.environ.air_density_sea_lvl_kg_p_m3*self.mission.reserve_decel_descend_avg_h_m_p_s**2.0
    theta = math.atan2(self.mission.reserve_decel_descend_v_m_p_s, self.mission.reserve_decel_descend_avg_h_m_p_s)

    weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
    lift_n = weight_n*math.cos(theta)
    vehicle_cl = lift_n/(q*self.wing_area_m2)

    # induced drag
    di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
    # parasite drag
    cd0 = self._calc_total_drag_coef()
    if cd0 == None:
      return None
    dp_n = q*self.wing_area_m2*cd0
    # total drag
    total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor

    # horizontal accelerations
    v0_h_m_p_s = self.mission.reserve_cruise_h_m_p_s
    vf_h_m_p_s = 2.0*self.mission.reserve_decel_descend_avg_h_m_p_s-v0_h_m_p_s
    d_h_m = self.mission.reserve_decel_descend_avg_h_m_p_s*self.mission.reserve_decel_descend_s
    a_h_m_p_s2 = (vf_h_m_p_s**2.0-v0_h_m_p_s**2.0)/(2.0*d_h_m)

    # vertical acceleration 
    v0_v_m_p_s = 0.0
    vf_v_m_p_s = self.mission.reserve_decel_descend_v_m_p_s
    d_v_m = 0.5*(v0_v_m_p_s+vf_v_m_p_s)*self.mission.reserve_decel_descend_s
    a_v_m_p_s2 = (vf_v_m_p_s**2.0-v0_v_m_p_s**2.0)/(2.0*d_v_m)

    # force components
    force_h_n = total_drag_n+self.max_takeoff_mass_kg*a_h_m_p_s2
    force_v_n = (weight_n-lift_n)-self.max_takeoff_mass_kg*a_v_m_p_s2 # physical: downward, speeding up

    # compute shaft power baseline
    shaft_power_kw = (force_h_n*self.mission.reserve_decel_descend_avg_h_m_p_s+force_v_n*(0.5*(v0_v_m_p_s+vf_v_m_p_s)))/(self.propulsion.rotor_effic*W_P_KW)
    
    # check vertical deficit: if gravity cannot provide enough, add vertical thrust assist shaft power
    vertical_deficit_n = self.max_takeoff_mass_kg*a_v_m_p_s2-(weight_n-lift_n)
    shaft_power_deficit_kw = 0.0
    if vertical_deficit_n > 0.0:
      # convert deficit to power explicitly
      shaft_power_deficit_kw = (vertical_deficit_n*(0.5*(v0_v_m_p_s+vf_v_m_p_s)))/(self.propulsion.rotor_effic*W_P_KW)
    
    # total shaft power (baseline + vertical assist)
    shaft_power_kw += shaft_power_deficit_kw

    # check for negative power to add spoiler drag
    if shaft_power_kw < 0.0:
      # required additional horizontal force to neutralize negative power
      required_extra_force_n = -force_h_n
      # compute equivalent delta Cd
      delta_cd_spoiler = required_extra_force_n/(q*self.wing_area_m2)
      if delta_cd_spoiler < 0.0:
        delta_cd_spoiler = 0.0
      # recompute with spoilers
      dp_spoiler_n = q*self.wing_area_m2*delta_cd_spoiler
      total_drag_n = (di_n+dp_n+dp_spoiler_n)*self.trim_drag_factor*self.excres_protub_factor
      force_h_n = total_drag_n+self.max_takeoff_mass_kg*a_h_m_p_s2
    
      # total shaft power
      shaft_power_kw = (force_h_n*self.mission.reserve_decel_descend_avg_h_m_p_s+force_v_n*(0.5*(v0_v_m_p_s+vf_v_m_p_s)))/(self.propulsion.rotor_effic*W_P_KW) + shaft_power_deficit_kw

    return shaft_power_kw
  else:
    return None
```

---
### Segment I: Reserve Transition Descend  

**Description:**  
* Calculations for the **Reserve Transition Descend** segment include **horizontal and vertical motion**.  
* Aerodynamic lift, induced drag, parasite drag, weight, descent forces, and hover-induced power are included.  
* Additional automatic corrections include **spoiler drag** if power becomes negative.  
* Horizontal velocity starts from an estimated initial value and decelerates to zero.  
* Vertical velocity transitions from the previous descend velocity (*mission.reserve_decel_descend_v_m_p_s*) to the final vertical descent rate (*mission.reserve_trans_descend_v_m_p_s*).  
* The total shaft power includes **aerodynamic power**, **hover-induced assist power**, and automatic spoiler drag compensation.  
* Physically, the hover-induced term represents induced power required to provide thrust when aerodynamic lift and gravity are insufficient to balance vertical forces during the transition phase.  

**Displacement, Acceleration, and Velocity Components**  
* Let:  
  * $v_{i,h}$ = initial horizontal velocity  
  * $v_{avg,h}^{previous}$ = previous segment's average horizontal velocity (*mission.reserve_decel_descend_avg_h_m_p_s*)  
  * $v_{i,h}^{previous}$ = initial horizontal velocity of the previous segment (*mission.reserve_cruise_h_m_p_s*)
  * $v_{f,h}$ = 0 = final horizontal velocity  
  * $v_{i,v}$ = initial vertical velocity (*mission.reserve_decel_descend_v_m_p_s*)  
  * $v_{f,v}$ = final vertical velocity (*mission.reserve_trans_descend_v_m_p_s*)  
  * $v_{avg,h}$ = average horizontal velocity (*mission.reserve_trans_descend_avg_h_m_p_s*)  
  * $t$ = duration of transition descend segment (*mission.reserve_trans_descend_s*)  

* Horizontal displacement $d_h$, initial velocity $v_{i,h}$, and acceleration $a_h$:

$$
v_{i,h} = v_{f,h}^{previous} = 2 \cdot v_{avg,h}^{previous} - v_{i,h}^{previous}
$$

$$
d_h = v_{avg,h} \cdot t
$$

$$
a_h = \frac{v_{f,h}^2 - v_{i,h}^2}{2 \cdot d_h}
$$  

* Vertical displacement $d_v$ and acceleration $a_v$:

$$
d_v = \frac{v_{i,v} + v_{f,v}}{2} \cdot t
$$

$$
a_v = \frac{v_{f,v}^2 - v_{i,v}^2}{2 \cdot d_v}
$$  

**Hover-Induced Power (W)**  
* When aerodynamic lift and gravity together are insufficient to balance vertical forces, additional thrust is required.  
  The thrust deficit is defined as:  

$$
T_{req} = (Weight - Lift) + m \cdot a_v
$$  

* If $T_{req} > 0$, the induced velocity and corresponding induced power are calculated using propeller momentum theory:  

$$
v_{i,hover} = \sqrt{\frac{T_{req}}{2 \cdot \rho \cdot A}}
$$  

$$
P_{hover} = T_{req} \cdot v_{i,hover}
$$  

**Average Shaft Power (kW)**  
* Horizontal and vertical forces:  

$$
F_h = D_{total} + m \cdot a_h
$$

$$
F_v = m \cdot a_v
$$

* Shaft power (baseline):  

$$
P_{shaft, avg} = \frac{P_{hover} + F_h \cdot v_{avg,h} + F_v \cdot \frac{v_{i,v} + v_{f,v}}{2}}{\eta_{rotor} \cdot W_{KW}}
$$  

**Special Automatic Adjustment — Spoiler Drag:**  
* If total shaft power is negative, spoiler drag is applied to increase horizontal drag and dissipate excess energy:  

$$
F_{h,new} = F_h + F_{spoiler}, \quad P_{shaft,new} = \frac{P_{hover} + F_{h,new} \cdot v_{avg,h} + F_v \cdot \frac{v_{i,v} + v_{f,v}}{2}}{\eta_{rotor} \cdot W_{KW}}
$$  

where $W_{KW}$ is the unit conversion factor to kW, aircraft mass $m$ (*aircraft.max_takeoff_mass_kg*), $\eta_{rotor}$ = rotor efficiency (*propulsion.rotor_effic*), $\rho$ = air density (*environ.air_density_sea_lvl_kg_p_m3*), and $A$ = rotor disk area (*propulsion.disk_area_m2*). 

```python
def _calc_reserve_trans_descend_avg_shaft_power_kw(self):
  if self.mission != None and self.propulsion != None and self.environ != None:    
    q = 0.5*self.environ.air_density_sea_lvl_kg_p_m3*self.mission.reserve_trans_descend_avg_h_m_p_s**2.0
    theta = math.atan2(self.mission.reserve_trans_descend_v_m_p_s, self.mission.reserve_trans_descend_avg_h_m_p_s)

    weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
    lift_n = weight_n*math.cos(theta)
    vehicle_cl = lift_n/(q*self.wing_area_m2)

    # induced drag
    di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
    # parasite drag
    cd0 = self._calc_total_drag_coef()
    if cd0 == None:
      return None
    dp_n = q*self.wing_area_m2*cd0
    # total drag
    total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor

    # horizontal accelerations
    v0_h_m_p_s = 2.0*self.mission.reserve_decel_descend_avg_h_m_p_s-self.mission.reserve_cruise_h_m_p_s
    vf_h_m_p_s = 0.0
    d_h_m = self.mission.reserve_trans_descend_avg_h_m_p_s*self.mission.reserve_trans_descend_s
    a_h_m_p_s2 = (vf_h_m_p_s**2.0-v0_h_m_p_s**2.0)/(2.0*d_h_m)

    # vertical acceleration 
    v0_v_m_p_s = self.mission.reserve_decel_descend_v_m_p_s
    vf_v_m_p_s = self.mission.reserve_trans_descend_v_m_p_s
    d_v_m = 0.5*(v0_v_m_p_s+vf_v_m_p_s)*self.mission.reserve_trans_descend_s
    a_v_m_p_s2 = (vf_v_m_p_s**2.0-v0_v_m_p_s**2.0)/(2.0*d_v_m)

    # force components
    force_h_n = total_drag_n+self.max_takeoff_mass_kg*a_h_m_p_s2
    # exclude (weight - lift) here; handled via thrust-deficit induced power
    force_v_n = self.max_takeoff_mass_kg*a_v_m_p_s2

    # compute thrust deficit if gravity + lift are insufficient
    T_req_n = max(0.0, (weight_n - lift_n) + self.max_takeoff_mass_kg*a_v_m_p_s2)
    if T_req_n > 0.0:
      v_i_hover = math.sqrt(T_req_n/(2.0*self.environ.air_density_sea_lvl_kg_p_m3*self.propulsion.disk_area_m2))
    else:
      v_i_hover = 0.0

    # hover-induced (assist) power for unsupported weight only (no efficiency here yet)
    P_hover_W = T_req_n*v_i_hover

    # baseline shaft power (sum of aerodynamic and vertical terms)
    shaft_power_kw = (P_hover_W+force_h_n*self.mission.reserve_trans_descend_avg_h_m_p_s+\
                      force_v_n*(0.5*(v0_v_m_p_s+vf_v_m_p_s)))/(self.propulsion.rotor_effic*W_P_KW)
    
    # check for negative power to add spoiler drag
    if shaft_power_kw < 0.0:
      # required additional horizontal force to neutralize negative power
      required_extra_force_n = -force_h_n
      # compute equivalent delta Cd
      delta_cd_spoiler = required_extra_force_n/(q*self.wing_area_m2)
      if delta_cd_spoiler < 0.0:
        delta_cd_spoiler = 0.0
      # recompute with spoilers
      dp_spoiler_n = q*self.wing_area_m2*delta_cd_spoiler
      total_drag_n = (di_n+dp_n+dp_spoiler_n)*self.trim_drag_factor*self.excres_protub_factor
      force_h_n = total_drag_n+self.max_takeoff_mass_kg*a_h_m_p_s2
    
      # total shaft power
      shaft_power_kw = (P_hover_W+force_h_n*self.mission.reserve_trans_descend_avg_h_m_p_s+\
                        force_v_n*(0.5*(v0_v_m_p_s+vf_v_m_p_s)))/(self.propulsion.rotor_effic*W_P_KW)

    return shaft_power_kw
  else:
    return None
```

---
### Segment J: Reserve Hover Descend  

**Description:**  
* Calculations for the **Reserve Hover Descend** segment consider **vertical motion only**.  
* Drag effects are neglected.  
* The aircraft begins with a downward velocity and decelerates to rest at the end of the descent.  
* The total shaft power consists of two components:  
  1. Hover Power: the induced power required to balance the aircraft’s weight during reserve descent.  
  2. Vertical Power: the additional (or reduced) power due to vertical acceleration.  
* Physically, the hover power represents the induced power required to maintain lift and support the aircraft’s weight during vertical reserve descent, while the acceleration term accounts for the reduction in descent rate as the aircraft slows to a hover.  
  
**Displacement, Acceleration, and Velocity Components**  
* Let:  
  * $v_{i,v}$ = initial vertical velocity
  * $v_{f,v}$ = 0 = final vertical velocity  
  * $v_{avg,v}$ = average vertical velocity (*mission.reserve_hover_descend_avg_v_m_p_s*)  
  * $t$ = duration of hover descend segment (*mission.reserve_hover_descend_s*)  

* Vertical displacement $d_v$, initial velocity $v_{i,v}$, and acceleration $a_v$:

$$
v_{i,v} = 2 \cdot v_{avg,v} - v_{f,v}
$$

$$
d_v = v_{avg,v} \cdot t
$$

$$
a_v = \frac{v_{f,v}^2 - v_{i,v}^2}{2 \cdot d_v}
$$  

**Hover Power (W)**  
* The induced velocity in hover, from propeller momentum theory, is:  

$$
v_{i,hover} = \sqrt{\frac{m \cdot g}{2 \cdot \rho \cdot A}}
$$  

where:  
  * $m$ = aircraft mass (*aircraft.max_takeoff_mass_kg*)  
  * $g$ = gravitational acceleration (*environ.g_m_p_s2*)  
  * $\rho$ = air density (*environ.air_density_sea_lvl_kg_p_m3*)  
  * $A$ = total rotor disk area (*propulsion.disk_area_m2*)  

The induced hover power is then:  

$$
P_{hover} = m \cdot g \cdot v_{i,hover}
$$  

**Average Shaft Power (kW)**  
* The total shaft power (hover and vertical components) is:  

$$
P_{shaft,avg} = \frac{P_{hover} + (m \cdot a_v) \cdot v_{avg,v}}{\eta_{rotor} \cdot W_{KW}}
$$  

where $W_{KW}$ is the unit conversion factor to kW, and $\eta_{rotor}$ = rotor efficiency (*propulsion.rotor_effic*).  

```python
def _calc_reserve_hover_descend_avg_shaft_power_kw(self):
  if self.mission != None and self.propulsion != None and self.environ != None:
      
      # vertical kinematics (upward positive)
      v0_v_m_p_s = 2.0*self.mission.reserve_hover_descend_avg_v_m_p_s
      vf_v_m_p_s = 0.0
      d_v_m = self.mission.reserve_hover_descend_avg_v_m_p_s*self.mission.reserve_hover_descend_s
      a_v_m_p_s2 = (vf_v_m_p_s**2.0 - v0_v_m_p_s**2.0) / (2.0*d_v_m)

      # additional power due to acceleration
      force_v_n =  (self.max_takeoff_mass_kg*a_v_m_p_s2)

      # induced velocity in hover (prop thrust momentum theory)
      v_i_hover = math.sqrt((self.max_takeoff_mass_kg*self.environ.g_m_p_s2)/\
                            (2.0*self.environ.air_density_sea_lvl_kg_p_m3*self.propulsion.disk_area_m2))

      # induced hover power
      P_hover_W = (self.max_takeoff_mass_kg*self.environ.g_m_p_s2)*v_i_hover

      # total shaft power (hover & vertical component)
      return \
        (P_hover_W + force_v_n * self.mission.reserve_hover_descend_avg_v_m_p_s) / \
          (self.propulsion.rotor_effic * W_P_KW)
  else:
      return None
```