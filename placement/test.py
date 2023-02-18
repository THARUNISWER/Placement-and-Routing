from solver import Solver
from visualizer import Visualizer
from problem import Problem

# Define a problem
problem = Problem(rectangles=[
    [1, 10, 3],  # Format: [width, height] as list. Default rotatable: False
    (3, 4, 2),  # Format: (width, height) as tuple. Default rotatable: False
    {"width": 25, "height": 6, "rotatable": False, "id": 1},  # Or can be defined as dict.
    {"width": 7, "height": 8, "rotatable": True, "id": 4},
[9, 10, 5],
[11, 12, 6],
[13, 14, 7],
[15, 16, 8],
[17, 18, 9],
[19, 20, 10],
])
print("problem:", problem)

# Find a solution
print("\n=== Solving without width/height constraints ===")
solution = Solver().solve(problem=problem)
print("solution:", solution)

# Visualization (to floorplan.png)
Visualizer().visualize(solution=solution, path="../figs/floorplan.png")

# [Other Usages]
# We can also give a solution width (and/or height) limit, as well as progress bar and random seed
print("\n=== Solving with width/height constraints ===")
solution = Solver().solve(problem=problem, seed=1111)
print("solution:", solution)
Visualizer().visualize(solution=solution, path="../figs/floorplan_limit.png")
