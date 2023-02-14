from solver import Solver
from visualizer import Visualizer
from problem import Problem
import graphviz
import re
from floorplan import Floorplan
from solution import Solution
from sequence_pair import SequencePair
import copy


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
def pass_problem(problem_new, common_modules, cur_time):
    # Find a solution

    print("\n=== Solving without width/height constraints ===")
    print("current time: ", cur_time)
    print("common_modules: ", common_modules)
    print("new_modules: ", problem_new.rectangles)

    # sub_problem-1: simulated annealing for new modules
    solution_new = Solver().solve(problem=problem_new)
    print(solution_new)

    # moving the whole system of common modules(common_modules) to origin
    bounding_box_common = []
    if len(common_modules) > 0:
        bottom_x = min(common_modules, key=lambda p: (p['x']))
        bottom_y = min(common_modules, key=lambda p: (p['y']))
        first_x = bottom_x['x']
        first_y = bottom_y['y']
        for obj in common_modules:
            obj['y'] -= first_y
            obj['x'] -= first_x
    # merging both placements
    if len(common_modules) > 0:
        # width of the grid containing common modules
        rightmost = max(common_modules, key=lambda i: (i['x']+i['width']))
        bounding_box_common.append(rightmost['x'] + rightmost['width'])

        # height of the grid containing common modules
        rightmost = max(common_modules, key=lambda i: (i['y'] + i['height']))
        bounding_box_common.append(rightmost['y'] + rightmost['height'])
        common_floorplan = Floorplan(positions = common_modules, bounding_box=bounding_box_common)
        print(common_floorplan)
        new_floorplan = solution_new.floorplan
        solution_final = optimize(common_floorplan, new_floorplan)
    else:
        solution_final = solution_new

    for obj in solution_final.floorplan.positions:
        i = next((i for i, item in enumerate(new_modules) if item["id"] == obj["id"]), None)
        if i is not None:
            new_modules[i]["x"] = obj["x"]
            new_modules[i]["y"] = obj["y"]

    print("solution:", solution_final)

    # Visualization (to floorplan.png)
    Visualizer().visualize(solution=solution_final, path="./figs/test/floorplan" + str(cur_time) + ".png")


def optimize(common_floorplan, new_floorplan):
    shift_right = common_floorplan.bounding_box[0]
    shift_up = common_floorplan.bounding_box[1]
    possible_floorplans = []
    # Case 1:
    new_floorplan1 = copy.deepcopy(new_floorplan)
    for obj in new_floorplan1.positions:
        obj["x"] += shift_right
    fin_width = new_floorplan1.bounding_box[0] + common_floorplan.bounding_box[0]
    fin_height = max(new_floorplan1.bounding_box[1], common_floorplan.bounding_box[1])
    fin_bounding_box = [fin_width, fin_height]
    possible_floorplans.append(Floorplan(common_floorplan.positions + new_floorplan1.positions, fin_bounding_box))

    # Case 2:
    new_floorplan2 = copy.deepcopy(new_floorplan)
    for obj in new_floorplan2.positions:
        obj["y"] += shift_up
    fin_width = max(new_floorplan2.bounding_box[0], common_floorplan.bounding_box[0])
    fin_height = new_floorplan2.bounding_box[1] + common_floorplan.bounding_box[1]
    fin_bounding_box = [fin_width, fin_height]
    possible_floorplans.append(Floorplan(common_floorplan.positions + new_floorplan2.positions, fin_bounding_box))

    # Case 3:
    new_floorplan3 = copy.deepcopy(new_floorplan)
    new_floorplan3.bounding_box[0], new_floorplan3.bounding_box[1] = new_floorplan3.bounding_box[1], \
                                                                     new_floorplan3.bounding_box[0]
    for obj in new_floorplan3.positions:
        obj["width"], obj["height"] = obj["height"], obj["width"]
        obj["x"], obj["y"] = obj["y"], obj["x"]
        obj["x"] += shift_right
    fin_width = new_floorplan3.bounding_box[0] + common_floorplan.bounding_box[0]
    fin_height = max(new_floorplan3.bounding_box[1], common_floorplan.bounding_box[1])
    fin_bounding_box = [fin_width, fin_height]
    possible_floorplans.append(Floorplan(common_floorplan.positions + new_floorplan3.positions, fin_bounding_box))

    # Case 4:
    new_floorplan4 = copy.deepcopy(new_floorplan)
    new_floorplan4.bounding_box[0], new_floorplan4.bounding_box[1] = new_floorplan4.bounding_box[1], \
                                                                     new_floorplan4.bounding_box[0]
    for obj in new_floorplan4.positions:
        obj["width"], obj["height"] = obj["height"], obj["width"]
        obj["x"], obj["y"] = obj["y"], obj["x"]
        obj["y"] += shift_up
    fin_width = max(new_floorplan4.bounding_box[0], common_floorplan.bounding_box[0])
    fin_height = new_floorplan4.bounding_box[1] + common_floorplan.bounding_box[1]
    fin_bounding_box = [fin_width, fin_height]
    possible_floorplans.append(Floorplan(common_floorplan.positions + new_floorplan4.positions, fin_bounding_box))

    fin_floorplan = min(possible_floorplans, key=lambda f: f.area)
    return Solution(sequence_pair=SequencePair(pair=([], [])), floorplan=fin_floorplan)


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
# input_lst = [{"id": 13, "type": "I1", "start_time": 2, "end_time": 7}]

sorted_lst = sorted(input_lst, key=lambda i: i['start_time'])
last_start_time = sorted_lst[len(input_lst)-1]["start_time"]

cur_time = input_lst[0]["start_time"]
new_modules = []
common_modules = []

# handles various timestamps in the problem
for x in sorted_lst:
    if cur_time == x["start_time"]:
        temp_dict = {"id": x["id"]}
        temp_dict.update(mapped_component[x["type"]])
        temp_dict["start_time"] = x["start_time"]
        temp_dict["end_time"] = x["end_time"]
        new_modules.append(temp_dict)
    else:
        # problem_new contains the new rectangles that are not present in previous timestamp
        rectangles_new= list(dict((k, x[k]) for k in ('id', 'width', 'height')) for x in new_modules)
        print("rectangles_new: " ,rectangles_new)
        problem_new= Problem(rectangles=rectangles_new)
        if len(common_modules) > 0:
            new_modules += common_modules

        # rectangles = list(dict((k, x[k]) for k in ('id', 'width', 'height')) for x in new_modules)
        # problem = Problem(rectangles=rectangles)
        pass_problem(problem_new, common_modules, cur_time)
        common_modules = new_modules
        new_modules = []
        cur_time = x["start_time"]
        temp_dict = {"id": x["id"]}
        temp_dict.update(mapped_component[x["type"]])
        temp_dict["start_time"] = x["start_time"]
        temp_dict["end_time"] = x["end_time"]
        new_modules.append(temp_dict)
        expired_modules = []
        for l in common_modules:
            if l["end_time"] <= cur_time:
                expired_modules.append(l)
        common_modules = [i for i in common_modules if i not in expired_modules]

# last timestamp
rectangles_new= list(dict((k, x[k]) for k in ('id', 'width', 'height')) for x in new_modules)
print(rectangles_new)
problem_new = Problem(rectangles=rectangles_new)
for l in common_modules:
    if l["end_time"] <= cur_time:
        common_modules.remove(l)
if len(common_modules) > 0:
    new_modules += common_modules
rectangles = list(dict((k, x[k]) for k in ('id', 'width', 'height')) for x in new_modules)
problem = Problem(rectangles=rectangles)
pass_problem(problem_new, common_modules, cur_time)







