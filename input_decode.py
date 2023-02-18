from placement.solver import Solver
from combined_visualizer import Visualizer
import routing.shortest_path_algo as rs
from placement.problem import Problem
import graphviz
import re
from placement.floorplan import Floorplan
from placement.solution import Solution
from placement.sequence_pair import SequencePair
import copy
import os
import shutil

# map to define size of components
mapped_component = {"M1": {"width": 2, "height": 2}, "D1": {"width": 2, "height": 2},
                    "D2": {"width":3, "height": 2}, "M2": {"width":3, "height": 2},
                    "D3": {"width": 3, "height": 3}, "I1": {"width":1, "height": 1},
                    "I2": {"width":1, "height": 1}, "I3": {"width":1, "height": 1},
                    "I4": {"width":1, "height": 1}, "I5": {"width":1, "height": 1},
                    "Storage": {"width": 2, "height": 1}}

# updating mapped component to accommodate for routing
mapped_component = {key:{"width" : val["width"]+4, "height" : val["height"] + 4} for key,val in mapped_component.items()}

graph = graphviz.Source.from_file('input_files\In_Vitro HLS Output\In-Vitro[Dot].gv')


# function to extract modules and routes from graph file(.gv)
def convert(src):
    str_src = str(src)
    label_re = re.compile(r'label="([0-9]+)_([A-Z]+[0-9]+) <([0-9]+),([0-9]+)>"')
    pl_lst = label_re.findall(str_src)
    label_re = re.compile(r'([0-9]+) -> ([0-9]+)')
    ro_lst = label_re.findall(str_src)
    input_pl_lst = []
    for l in pl_lst:
        temp_dict = {}
        temp_dict["id"] = int(l[0])
        temp_dict["type"] = l[1]
        temp_dict["start_time"] = int(l[2])
        temp_dict["end_time"] = int(l[3])
        input_pl_lst.append(temp_dict)

    input_ro_lst = []
    for l in ro_lst:
        temp_dict = {}
        temp_dict["start_module"] = int(l[0])
        temp_dict["end_module"] = int(l[1])
        time_module = next((item for item in input_pl_lst if item["id"] == temp_dict["start_module"]), None)
        temp_dict["time"] = time_module["end_time"]
        input_ro_lst.append(temp_dict)
    return input_pl_lst, input_ro_lst


# function to reduce the modules to its original size
def update(solution_final):
    for rectangle in solution_final.floorplan.positions:
        rectangle['x'] += 2
        rectangle['y'] += 2
        rectangle['height'] -= 4
        rectangle['width'] -= 4


# functon to inflate the module to new size to allow space for routing
def rem_update(solution_final):
    for rectangle in solution_final.floorplan.positions:
        rectangle['x'] -= 2
        rectangle['y'] -= 2
        rectangle['height'] += 4
        rectangle['width'] += 4


# function to pass the problem for simulated annealing to get the floorplan
def pass_problem(problem_new, common_modules, cur_time):
    # Find a solution

    print("\n=== Solving without width/height constraints ===")
    print("current time: ", cur_time)
    print("common_modules: ", common_modules)
    print("new_modules: ", problem_new.rectangles)

    # sub_problem-1: simulated annealing for new modules
    solution_new = Solver().solve(problem=problem_new)

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
        common_floorplan = Floorplan(positions=common_modules, bounding_box=bounding_box_common)
        new_floorplan = solution_new.floorplan
        solution_final = optimize(common_floorplan, new_floorplan)
    else:
        solution_final = solution_new

    return solution_final


# function to optimize the set up of floorplan of common modules with the new modules
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


# function to make a 2-D array representing our current placement of modules
def draw_routing_grid(solution_final, length, width):
    grid = [[0 for i in range(length)] for j in range(width)]
    for rectangles in solution_final.floorplan.positions:
        for x in range(rectangles['x']-1, rectangles['x']+rectangles['width']+1):
            for y in range(rectangles['y']-1, rectangles['y']+rectangles['height']+1):
                grid[x][y] = rectangles['id']
    return grid


# function to find out the routes between modules for routing
def route(solution_final, sorted_ro_lst, time):
    length = solution_final.floorplan.bounding_box[1] + 10
    width = solution_final.floorplan.bounding_box[0] + 10
    pl_grid = draw_routing_grid(solution_final, length=length, width=width)
    cur_time_routing = [item for item in sorted_ro_lst if item["time"] == time]
    fin_lst = solution_final.floorplan.positions
    folder_path = "figs\\test\\time" + str(time)
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    os.mkdir(folder_path)
    for obj in cur_time_routing:
        start_module = next((item for item in fin_lst if item["id"] == obj["start_module"]), None)
        end_module = next((item for item in fin_lst if item["id"] == obj["end_module"]), None)
        start = (start_module['x'], start_module['y'] - 1)
        end = (end_module['x'] - 1, end_module['y'])
        pl_grid[start[0]][start[1]] = 0
        pl_grid[end[0]][end[1]] = 0
        path = rs.find_path(start, end, pl_grid)
        file_path = "figs\\test\\time" + str(time) + "\\routeplan_" + str(start_module["id"]) + "_" + str(end_module["id"]) +".png"
        Visualizer().visualize(solution=solution_final, routing_pos=path, path=file_path)


def main():
    # list to store input graph
    input_pl_lst, input_ro_lst = convert(graph)

    # example input
    # input_pl_lst = [{"id": 13, "type": "I1", "start_time": 2, "end_time": 7}, {"id": 18, "type": "I1", "start_time": 2, "end_time": 7}]
    sorted_pl_lst = sorted(input_pl_lst, key=lambda i: i['start_time'])
    sorted_ro_lst = sorted(input_ro_lst, key=lambda i: i['time'])

    cur_time = input_pl_lst[0]["start_time"]
    new_modules = []
    common_modules = []

    # handles various timestamps in the problem
    for x in sorted_pl_lst:
        if cur_time == x["start_time"]:
            temp_dict = {"id": x["id"]}
            temp_dict.update(mapped_component[x["type"]])
            temp_dict["start_time"] = x["start_time"]
            temp_dict["end_time"] = x["end_time"]
            new_modules.append(temp_dict)
        else:
            problem_new = Problem(rectangles=new_modules)
            if len(common_modules) > 0:
                new_modules += common_modules

            # placement
            solution_final = pass_problem(problem_new, common_modules, cur_time)
            update(solution_final)
            print("solution:", solution_final)
            Visualizer().visualize(solution=solution_final, path="figs\\test\\floorplan" + str(cur_time) + ".png")

            # routing
            route(solution_final, sorted_ro_lst, cur_time)
            rem_update(solution_final)
            common_modules = solution_final.floorplan.positions
            new_modules = []
            cur_time = x["start_time"]
            temp_dict = {"id": x["id"]}
            temp_dict.update(mapped_component[x["type"]])
            temp_dict["start_time"] = x["start_time"]
            temp_dict["end_time"] = x["end_time"]
            new_modules.append(temp_dict)
            expired_modules = []
            for l in common_modules:
                if l["end_time"] < cur_time:
                    expired_modules.append(l)
            common_modules = [i for i in common_modules if i not in expired_modules]

    # last timestamp
    problem_new = Problem(rectangles=new_modules)
    for x in common_modules:
        if x["end_time"] <= cur_time:
            common_modules.remove(x)
    if len(common_modules) > 0:
        new_modules += common_modules
    solution_final = pass_problem(problem_new, common_modules, cur_time)
    update(solution_final)
    print("solution:", solution_final)
    Visualizer().visualize(solution=solution_final, path=".placement/figs/test/floorplan" + str(cur_time) + ".png")
    route(solution_final, sorted_ro_lst, cur_time)


if __name__ == "__main__":
    main()

# problems:
# problem1: can route only for consecutive timestamps
# problem2: relative positions but absolute grid
# problem3: where to begin? where to end?
