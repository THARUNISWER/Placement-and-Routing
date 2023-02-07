from solver import Solver
from visualizer import Visualizer
from problem import Problem
import graphviz
import re


# function to extract modules from graph file(.gv)
def convert(src):
    str_src = str(src)
    label_re = re.compile(r'label="([0-9]+)_([A-Z]+[0-9]+) <([0-9]+),([0-9]+)>')
    lst = label_re.findall(str_src)
    input_lst = []
    for l in lst:
        temp_dict = {}
        temp_dict["id"] = int(l[0])
        temp_dict["type"] = l[1]
        temp_dict["start_time"] = int(l[2])
        temp_dict["end_time"] = int(l[3])
        input_lst.append(temp_dict)
    return input_lst


# function to pass the problem for simulated annealing to get the floorplan
def pass_problem(problem, cur_time):
    # Find a solution
    print("\n=== Solving without width/height constraints ===")
    print(prev_modules)
    solution = Solver().solve(problem=problem)
    for obj in solution.floorplan.positions:
        i = next((i for i, item in enumerate(new_modules) if item["id"] == obj["id"]), None)
        if i is not None:
            new_modules[i]["x"] = obj["x"]
            new_modules[i]["y"] = obj["y"]

    print("solution:", solution)

    # Visualization (to floorplan.png)
    Visualizer().visualize(solution=solution, path="./figs/test/floorplan" + str(cur_time) + ".png")

    # [Other Usages]
    # We can also give a solution width (and/or height) limit, as well as progress bar and random seed
    # print("\n=== Solving with width/height constraints ===")
    # solution = Solver().solve(problem=problem, seed=1111)
    # print("solution:", solution)
    # Visualizer().visualize(solution=solution, path="./figs/test/floorplan_limit" + str(cur_time) +  ".png")


mapped_component = {"M1": {"width": 2, "height": 2}, "D1": {"width": 2, "height": 2},
                    "D2": {"width":3, "height": 2}, "M2": {"width":3, "height": 2},
                    "D3": {"width": 3, "height": 3}, "I1": {"width":1, "height": 1},
                    "I2": {"width":1, "height": 1}, "I3": {"width":1, "height": 1},
                    "I4": {"width":1, "height": 1}, "I5": {"width":1, "height": 1},
                    "Storage": {"width": 2, "height": 1}}

graph = graphviz.Source.from_file('./input_files/In_Vitro HLS Output/In-Vitro[Dot].gv')


# list to store input graph
input_lst = convert(graph)

# example input
# input_lst = [{"id": 13, "type": "M1", "start_time": 2, "end_time": 7}, {"id": 14, "type": "M1", "start_time": 4, "end_time":9},
#               {"id": 16, "type": "M2", "start_time": 7, "end_time": 10}, {"id": 17, "type": "M2", "start_time": 8, "end_time":11},
#               {"id": 18, "type": "M2", "start_time": 2, "end_time": 5}, {"id": 15, "type": "M1", "start_time": 5, "end_time":10}]

sorted_lst = sorted(input_lst, key=lambda i: i['start_time'])
last_start_time = sorted_lst[len(input_lst)-1]["start_time"]

cur_time = input_lst[0]["start_time"]
new_modules = []
prev_modules = []

# handles various timestamps in the problem
for x in sorted_lst:
    if cur_time == x["start_time"]:
        temp_dict = {"id": x["id"]}
        temp_dict.update(mapped_component[x["type"]])
        temp_dict["start_time"] = x["start_time"]
        temp_dict["end_time"] = x["end_time"]
        new_modules.append(temp_dict)
    else:
        if len(prev_modules) > 0:
            new_modules += prev_modules
        #print(new_modules)
        rectangles = list(dict((k, x[k]) for k in ('id', 'width', 'height')) for x in new_modules)
        problem = Problem(rectangles=rectangles)
        pass_problem(problem, cur_time)
        prev_modules = new_modules
        new_modules = []
        cur_time = x["start_time"]
        temp_dict = {"id": x["id"]}
        temp_dict.update(mapped_component[x["type"]])
        temp_dict["start_time"] = x["start_time"]
        temp_dict["end_time"] = x["end_time"]
        new_modules.append(temp_dict)
        expired_modules = []
        for l in prev_modules:
            if l["end_time"] <= cur_time:
                expired_modules.append(l)
        prev_modules = [i for i in prev_modules if i not in expired_modules]

# last timestamp
for l in prev_modules:
    if l["end_time"] <= cur_time:
        prev_modules.remove(l)
if len(prev_modules) > 0:
    new_modules += prev_modules
rectangles = list(dict((k, x[k]) for k in ('id', 'width', 'height')) for x in new_modules)
problem = Problem(rectangles=rectangles)
pass_problem(problem, cur_time)







