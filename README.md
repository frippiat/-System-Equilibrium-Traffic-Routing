# System Equilibrium Traffic Routing

## Collaborators: Warre Veys, Ward Vandebroecke

## Context in which the project has been done:
 This project was created for the Bachelor's Thesis in the Bachelor of Science in Engineering (Computer Science Engineering), under the supervision of Kenneth Stoop and prof. dr. ir. Mario Pickavet.

## General overview

The project titled "Beating the Nash Equilibrium in Traffic" investigates traffic congestion in Belgium and seeks alternative route planning solutions. The focus is on comparing two routing strategies: **user equilibrium**, where drivers select routes based solely on personal travel time, and **system equilibrium**, which aims to coordinate routes to minimize overall travel time for all users.

Key components include:

1. **Data Collection**: Utilizing static traffic data and current route-planning applications (like Waze and Google Maps) to inform models.
2. **Mathematical Modeling**: Developing mathematical formulations to describe traffic flow and implement the routing strategies, addressing the limitations of existing methods that overlook system-wide effects.
3. **Implementation**: The project is implemented in Python using optimization tools like Gurobi to solve complex linear optimization problems efficiently.
4. **Visualization and Testing**: The results and impacts of proposed routing strategies are visualized and tested for real-world applicability, with a focus on how imposed routes can enhance traffic flow despite not being the fastest for individual drivers.

Ultimately, the project aims to demonstrate how coordinated route guidance can alleviate traffic congestion, highlighting the importance of collective user behavior in traffic systems.
