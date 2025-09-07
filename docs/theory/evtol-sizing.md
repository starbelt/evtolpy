# Mission Segment Energy Consumption

This document explains the equations used to calculate **energy consumption** across different mission segments in the aircraft model.
* [Segment A: Depart Taxi](#segment-a-depart-taxi)
* [Segment B: Hover Climb](#segment-b-hover-climb)
* [Segment C: Transition Climb](#segment-c-transition-climb)
* [Segment D: Depart Procedures](#segment-d-depart-procedures)
* [Segment E: Accelerate Climb](#segment-e-accelerate-climb)
* [Segment F: Cruise](#segment-f-cruise)
* [Segment G: Decelerate Descend](#segment-g-decelerate-descend)
* [Segment H: Arrive Procedures](#segment-h-arrive-procedures)
* [Segment I: Transition Descend](#segment-i-transition-descend)
* [Segment J: Hover Descend](#segment-j-hover-descend)
* [Segment K: Arrive Taxi](#segment-k-arrive-taxi)
* [Segment B': Reserve Hover Climb](#segment-b-reserve-hover-climb)
* [Segment C': Reserve Transition Climb](#segment-c-reserve-transition-climb)
* [Segment E': Reserve Acceleration Climb](#segment-e-reserve-acceleration-climb)
* [Segment F': Reserve Cruise](#segment-f-reserve-cruise)
* [Segment G': Reserve Deceleration Descend](#segment-g-reserve-deceleration-descend)
* [Segment I': Reserve Transition Descend](#segment-i-reserve-transition-descend)
* [Segment J': Reserve Hover Descend](#segment-j-reserve-hover-descend)

---
## General Kinematic Relations

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
## General Workflow for Calculating Average Electric Power (kW)  

**Step 1: Calculate Average Shaft Power (kW)**  
* Based on aerodynamic and propulsion requirements.  
* Note: Different calculation will be implemented for each mission segment.

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
## Segment A: Depart Taxi

**Description:**  
* Calculations for the **Depart Taxi** segment consider **horizontal motion only**. 
* Drag effects are neglected, and the aircraft starts from rest, accelerating to a final horizontal velocity. 
* Average horizontal velocity is provided and used to compute displacement, acceleration, and final velocity. 
* The average shaft power is then calculated using MTOM, horizontal acceleration, and average horizontal velocity.  
   
**Displacement, Acceleration, and Final Velocity**   
* Let:  
  * $v_i = 0$ = initial horizontal velocity  
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
## Segment B: Hover Climb  
**Description:**   
* Calculations for the **Hover Climb** segment consider **vertical motion only**.
* Drag effects are neglected, and the aircraft starts from rest, accelerating to a final vertical velocity.
* Average vertical velocity is provided and used to compute displacement, acceleration, and final velocity.
* The average shaft power is then calculated using MTOM, gravity, vertical acceleration, and average vertical velocity.  
   
**Displacement, Acceleration, and Final Velocity**   
* Let:  
  * $v_i = 0$ = initial vertical velocity  
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
   
**Average Shaft Power (kW)**   
* Using aircraft mass $m$ (*aircraft.max_takeoff_mass_kg*), gravitational acceleration $g$ (*environ.g_m_p_s2*), and rotor efficiency $\eta_{rotor}$ (*propulsion.rotor_effic*):  

$$
P_{shaft, avg} = \frac{m \cdot (g + a_v) \cdot v_{avg}}{\eta_{rotor} \cdot W_{KW}}
$$    

where $W_{KW}$ is the unit conversion factor to kW.

```python
def _calc_hover_climb_avg_shaft_power_kw(self):
if self.mission != None and self.propulsion != None:
    d_v_m = self.mission.hover_climb_avg_v_m_p_s*self.mission.hover_climb_s
    vf_v_m_p_s = (2.0*d_v_m)/self.mission.hover_climb_s
    a_v_m_p_s2 = vf_v_m_p_s**2.0/(2.0*d_v_m)
    return \
    (self.max_takeoff_mass_kg*(self.environ.g_m_p_s2+a_v_m_p_s2)*\
    self.mission.hover_climb_avg_v_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
else:
    return None
```

---
## Segment C: Transition Climb  

**Description:**  
* Calculations for the **Transition Climb** segment include both **horizontal and vertical motion**.  
* Aerodynamic lift, induced drag, parasite drag, weight, and climb forces are included.  
* Horizontal velocity starts from zero and accelerates to a final horizontal velocity. Average horizontal velocity is used to compute displacement, acceleration, and final velocity.  
* Vertical velocity is considered **constant** (no vertical acceleration).  
* The average shaft power is calculated using horizontal and vertical forces, MTOM, and rotor efficiency.  
   
**Displacement, Acceleration, and Velocity Components**  
* Let:  
  * $v_{i,h} = 0$ = initial horizontal velocity  
  * $v_{avg,h}$ = average horizontal velocity (*mission.trans_climb_avg_h_m_p_s*)  
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
  
**Average Shaft Power (kW)**  
* Horizontal and vertical forces:  

$$
F_h = Drag_{total} + m \cdot a_h
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
def _calc_trans_climb_avg_shaft_power_kw(self):
if self.mission != None and self.propulsion != None and self.environ != None:
    q = 0.5*self.environ.air_density_sea_lvl_kg_p_m3*self.mission.trans_climb_avg_h_m_p_s**2.0
    weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
    vehicle_cl = weight_n/(q*self.wing_area_m2)
    lift_n = q*self.wing_area_m2*vehicle_cl

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
    force_v_n = (weight_n-lift_n)+self.max_takeoff_mass_kg*a_v_m_p_s2

    return (force_h_n*self.mission.trans_climb_avg_h_m_p_s+force_v_n*self.mission.trans_climb_v_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
else:
    return None
```

---
## Segment D: Depart Procedures  

**Description:**  
* Calculations for the **Depart Procedures** segment consider **horizontal motion only**.  
* Horizontal velocity is assumed **constant**.  
* Vertical motion is neglected.
* Aerodynamic lift, induced drag, parasite drag, and horizontal drag are included.  
* The average shaft power is calculated using horizontal forces and rotor efficiency.  

**Displacement, Acceleration, and Velocity Components**  
* Let:  
  * $v_h = horizontal velocity (*mission.depart_proc_h_m_p_s*)  
  * $t$ = duration of depart procedures segment (*mission.depart_proc_s*)  

* Horizontal motion: constant velocity, so no acceleration ($a_h = 0$).   
  
**Average Shaft Power (kW)**  
* Horizontal force:  

$$
F_h = Drag_{total}
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