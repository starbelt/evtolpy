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
* Average velocity is provided and used to compute displacement, acceleration, and final velocity. 
* The average shaft power is then calculated using MTOM, acceleration, and average velocity.  
   

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
* 
* 
*   
  

**Displacement, Acceleration, and Final Velocity**    
  
  
**Average Shaft Power (kW)**    

```python


```

