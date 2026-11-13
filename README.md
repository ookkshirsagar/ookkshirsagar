<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/header.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/header-light.svg">
    <img src="assets/header.svg" width="100%" alt="Omkar Kshirsagar, robotics systems engineer, dexterous manipulation"/>
  </picture>
</p>

<p align="center">
  <b>Robotics engineer building manipulation systems end to end:<br/>perception, grasp and motion planning, control, and simulation in NVIDIA Isaac Sim.</b>
</p>

<p align="center">
  <a href="mailto:ookkshirsagar@gmail.com"><img src="https://img.shields.io/badge/Email-ookkshirsagar%40gmail.com-EA4335?logo=gmail&logoColor=white" alt="Email"/></a>
  <a href="https://www.linkedin.com/in/ookkshirsagar/"><img src="https://img.shields.io/badge/LinkedIn-ookkshirsagar-0A66C2?logo=linkedin&logoColor=white" alt="LinkedIn"/></a>
  <a href="https://orcid.org/0009-0006-1997-5838"><img src="https://img.shields.io/badge/ORCID-0009--0006--1997--5838-A6CE39?logo=orcid&logoColor=white" alt="ORCID"/></a>
</p>

### About

I work across the full manipulation stack with ROS 2, MoveIt 2, MoveIt Task Constructor and NVIDIA Isaac Sim. My focus is dexterous manipulation and sim-to-real, and every project reports measured results rather than a demo alone. I am currently working on reinforcement learning for in-hand manipulation with fingertip tactile sensing. Based in Heilbronn, Germany.

### Featured projects

<table>
  <tr>
    <td width="50%" valign="top">
      <a href="https://github.com/ookkshirsagar/openarm-vision-kitting"><img src="assets/projects/openarm-vision-kitting.gif" width="100%" alt="OpenArm 2.0 kitting parts found by a camera in Isaac Sim"/></a>
      <h4><a href="https://github.com/ookkshirsagar/openarm-vision-kitting">Vision-guided kitting · OpenArm 2.0</a></h4>
      RGB-D part detection, MoveIt Task Constructor pick and place, NVIDIA Isaac Sim.<br/>
      <b>8 / 8 kits · 24 / 24 parts · 4 mm placement error</b><br/>
      <sub>ROS 2 · MoveIt 2 · MTC · Isaac Sim · Python</sub>
    </td>
    <td width="50%" valign="top">
      <a href="https://github.com/ookkshirsagar/moveit-mtc-pick-and-place"><img src="assets/projects/moveit-mtc-pick-and-place.gif" width="100%" alt="UR5e with an Inspire RH56DFX hand stacking cubes in Isaac Sim"/></a>
      <h4><a href="https://github.com/ookkshirsagar/moveit-mtc-pick-and-place">Dexterous pick and place · UR5e + RH56DFX</a></h4>
      End-to-end MTC task with a contact-aware hand closure; stacks cubes squarely, on mock hardware or in Isaac Sim.<br/>
      <b>50 / 50 random picks and places · 5 / 5 three-cube stacks · 1.2 s planning</b><br/>
      <sub>ROS 2 · MoveIt Task Constructor · ros2_control · C++</sub>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <a href="https://github.com/ookkshirsagar/urdf-mesh-optimizer"><img src="assets/projects/urdf-mesh-optimizer.jpg" width="100%" alt="CAD export reduced to a visual mesh and a collision mesh"/></a>
      <h4><a href="https://github.com/ookkshirsagar/urdf-mesh-optimizer">urdf-mesh-optimizer</a></h4>
      Turns heavy CAD exports into real-time visual and collision meshes for a whole URDF in one command, with Hausdorff error reports and a MoveIt check for CI.<br/>
      <b>370k → 1.5k collision triangles (−99.6 %) · 0.75 mm RMS deviation</b><br/>
      <sub>Python · Open3D · URDF · pip package</sub>
    </td>
    <td width="50%" valign="top">
      <a href="https://github.com/ookkshirsagar/rh56dfx_description"><img src="assets/projects/rh56dfx_description.gif" width="100%" alt="Inspire RH56DFX hand cycling through grasp poses"/></a>
      <h4><a href="https://github.com/ookkshirsagar/rh56dfx_description">rh56dfx_description</a></h4>
      ROS 2 description package for the Inspire RH56DFX hand, ready for MoveIt, RViz and ros2_control.<br/>
      <b>Left and right hands · 6 actuators driving mimic-joint fingers</b><br/>
      <sub>ROS 2 · URDF / xacro · ros2_control</sub>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <a href="https://github.com/ookkshirsagar/Wrist_Rehabilitation"><img src="assets/projects/wrist-rehabilitation.png" width="100%" alt="Therapist and patient rigs linked over MQTT"/></a>
      <h4><a href="https://github.com/ookkshirsagar/Wrist_Rehabilitation">Wrist rehabilitation robot</a></h4>
      Teleoperated therapy: the therapist's motion is mirrored to the patient's actuator in real time, with force feedback and safety-limited control.<br/>
      <b>83° / 81° flexion–extension range · limits checked every control cycle</b><br/>
      <sub>Python · Dynamixel · MQTT · control</sub>
    </td>
    <td width="50%" valign="top">
      <a href="https://github.com/ookkshirsagar/Autonomous-Object-Detection-Robot-using-EIT"><img src="assets/projects/hidden-hunter-eit.jpg" width="100%" alt="Custom ESP32-S2 EIT measurement board"/></a>
      <h4><a href="https://github.com/ookkshirsagar/Autonomous-Object-Detection-Robot-using-EIT">Hidden Hunter · buried-object detection</a></h4>
      Ground robot that maps buried objects with electrical impedance tomography, using a custom ESP32-S2 measurement board.<br/>
      <b>Buried objects detected up to 50 mm deep</b><br/>
      <sub>Raspberry Pi · ESP32 · PCB design · MQTT</sub>
    </td>
  </tr>
</table>

<p align="center"><sub>In progress: <a href="https://github.com/ookkshirsagar/dg5f-tactile-inhand-rl"><b>dg5f-tactile-inhand-rl</b></a>, which asks whether touch helps: in-hand rotation with the Tesollo DG-5F-S in Isaac Lab, PPO with and without fingertip tactile sensing.</sub></p>

### Toolbox

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/skills.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/skills-light.svg">
    <img src="assets/skills.svg" width="100%" alt="Skills as a ROS 2 node graph: perception, grasp planning, motion planning, execution, simulation, learning, systems"/>
  </picture>
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/footer.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/footer-light.svg">
    <img src="assets/footer.svg" width="100%" alt="Dual-arm cooperative manipulation"/>
  </picture>
</p>
