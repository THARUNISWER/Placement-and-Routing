from solver import Solver
from visualizer import Visualizer
from problem import Problem
import graphviz
import re
from floorplan import Floorplan
from solution import Solution
from sequence_pair import SequencePair


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
def pass_problem(problem_new, prev_modules, cur_time):
    # Find a solution

    print("\n=== Solving without width/height constraints ===")
    print("current time: ", cur_time)
    print("prev_modules: ", prev_modules)
    print("new_modules: ", problem_new.rectangles)

    #finding best placement for new modules using simulated annealing method -> sub problem 1
    if len(problem_new.rectangles) == 1:
        sequence_pair_new = SequencePair(pair=(list(range(1)), list(range(1))))
        temp_dict = {}
        positions_new=[]
        temp_dict['id'] = problem_new.rectangles[0]['id']
        temp_dict['x'] = 0
        temp_dict['y'] = 0
        temp_dict['width'] = problem_new.rectangles[0]['width']
        temp_dict['height'] = problem_new.rectangles[0]['height']
        positions_new.append(temp_dict)
        bounding_box_new=[]
        bounding_box_new.append(problem_new.rectangles[0]['width'])
        bounding_box_new.append(problem_new.rectangles[0]['height'])
        area_new = bounding_box_new[0] * bounding_box_new[1]
        floorplan_new = Floorplan(positions = positions_new, bounding_box = bounding_box_new, area = area_new)
        solution_new = Solution(sequence_pair=sequence_pair_new, floorplan=floorplan_new)
    else:
        solution_new = Solver().solve(problem=problem_new)

    #   finding relative displacements between all prev_modules wrt to the module that is
    # present in the lower left corner
    # calculating positions data structure of common modules ("positions_common") using relative displacements -> sub problem 2
    prev_modules = sorted(prev_modules, key=lambda i: (i['x'], i['y']))
    positions_common = []
    bounding_box_common = []
    flag=0
    for l in prev_modules:
        temp_dict={}
        temp_dict["id"]= l["id"]
        if flag==0:
            temp_dict["x"]= 0
            temp_dict["y"]= 0
            first_x= l["x"]
            first_y= l["y"]
            flag=1
        else:
            temp_dict["x"]= l["x"] - first_x
            temp_dict["y"]= l["y"] - first_y
        temp_dict["width"]= l["width"]
        temp_dict["height"]= l["height"]
        positions_common.append(temp_dict)

    #default final values if there are no prev_modules i.e common modules
    #the position_final and bounding_box_final will solely depend on new modules
    positions_final = solution_new.floorplan.positions
    bounding_box_final = []
    bounding_box_final.append(solution_new.floorplan.bounding_box[0])
    bounding_box_final.append(solution_new.floorplan.bounding_box[1])
    area_final = bounding_box_final[0] * bounding_box_final[1]
    if len(prev_modules)>0:
        # to find width of the grid containing common modules,
        # we have to find the module with maximum ('x' + 'width') value i.e right most module
        # so sort prev_module acc to i['x']+i['width'] parameter
        prev_modules = sorted(prev_modules, key=lambda i: (i['x']+i['width']))
        bounding_box_common.append(prev_modules[len(prev_modules) - 1]['x'] + prev_modules[len(prev_modules) - 1]['width'])

        # to find height of the grid containing common modules,
        # we have to find the module with maximum ('y' + 'height') value i.e top most module
        # so sort prev_module acc to i['y']+i['height'] parameter
        prev_modules = sorted(prev_modules, key=lambda i: (i['y'] + i['height']))
        bounding_box_common.append(prev_modules[len(prev_modules)-1]['y'] + prev_modules[len(prev_modules) - 1]['height'])

        # now, we are having 2 grids one that contains all new modules and the other containing common modules and we have to combine them
        # there are 4 possible ways in which we can place 2 grids, they are:
        # 1. dont rotate both grids
        # 2, 3. rotate one of the grids
        # 4. rotate both the grids
        # choose the formation that gives min area
        min_area = min( (solution_new.floorplan.bounding_box[0]+bounding_box_common[0])*max(solution_new.floorplan.bounding_box[1],bounding_box_common[1]),
                        (solution_new.floorplan.bounding_box[0]+bounding_box_common[1])*max(solution_new.floorplan.bounding_box[1],bounding_box_common[0]),
                        (solution_new.floorplan.bounding_box[1]+bounding_box_common[0])*max(solution_new.floorplan.bounding_box[0],bounding_box_common[1]),
                        (solution_new.floorplan.bounding_box[1]+bounding_box_common[1])*max(solution_new.floorplan.bounding_box[0],bounding_box_common[0]))

        #updating the positions of modules and the bounding_box of the grid according to the formation that gave the min area
        if min_area == (solution_new.floorplan.bounding_box[0]+bounding_box_common[1])*max(solution_new.floorplan.bounding_box[1],bounding_box_common[0]):
            for obj in positions_common:
                obj['x'], obj['y'] = obj['y'], obj['x']
            bounding_box_common[0], bounding_box_common[1] = bounding_box_common[1], bounding_box_common[0]
        elif min_area == (solution_new.floorplan.bounding_box[1]+bounding_box_common[0])*max(solution_new.floorplan.bounding_box[0],bounding_box_common[1]):
            for obj in solution_new.floorplan.positions:
                obj['x'], obj['y'] = obj['y'], obj['x']
            solution_new.floorplan.bounding_box[0], solution_new.floorplan.bounding_box[1] = solution_new.floorplan.bounding_box[1], solution_new.floorplan.bounding_box[0]
        elif min_area == (solution_new.floorplan.bounding_box[1]+bounding_box_common[1])*max(solution_new.floorplan.bounding_box[0],bounding_box_common[0]):
            for obj in positions_common:
                obj['x'], obj['y'] = obj['y'], obj['x']
            for obj in solution_new.floorplan.positions:
                obj['x'], obj['y'] = obj['y'], obj['x']
            bounding_box_common[0], bounding_box_common[1] = bounding_box_common[1], bounding_box_common[0]
            solution_new.floorplan.bounding_box[0], solution_new.floorplan.bounding_box[1] = solution_new.floorplan.bounding_box[1], solution_new.floorplan.bounding_box[0]

        for obj in positions_common:
            obj['x']+= solution_new.floorplan.bounding_box[0]

        positions_final= solution_new.floorplan.positions + positions_common
        bounding_box_final[0] = solution_new.floorplan.bounding_box[0] + bounding_box_common[0]
        bounding_box_final[1] = max(solution_new.floorplan.bounding_box[1], bounding_box_common[1])
        area_final = bounding_box_final[0] * bounding_box_final[1]

    floorplan_final = Floorplan(positions = positions_final, bounding_box = bounding_box_final, area = area_final)
    sequence_pair_final = SequencePair(pair=(list(range(len(positions_final))), list(range(len(positions_final))) ))
    solution_final = Solution(sequence_pair= sequence_pair_final, floorplan= floorplan_final)

    for obj in solution_final.floorplan.positions:
        i = next((i for i, item in enumerate(new_modules) if item["id"] == obj["id"]), None)
        if i is not None:
            new_modules[i]["x"] = obj["x"]
            new_modules[i]["y"] = obj["y"]

    print("solution:", solution_final)

    # Visualization (to floorplan.png)
    Visualizer().visualize(solution=solution_final, path="./figs/test/floorplan" + str(cur_time) + ".png")


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
        # problem_new contains the new rectangles that are not present in previous timestamp
        rectangles_new= list(dict((k, x[k]) for k in ('id', 'width', 'height')) for x in new_modules)
        print("rectangles_new: " ,rectangles_new)
        problem_new= Problem(rectangles=rectangles_new)
        if len(prev_modules) > 0:
            new_modules += prev_modules

        # rectangles = list(dict((k, x[k]) for k in ('id', 'width', 'height')) for x in new_modules)
        # problem = Problem(rectangles=rectangles)
        pass_problem(problem_new, prev_modules, cur_time)
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
rectangles_new= list(dict((k, x[k]) for k in ('id', 'width', 'height')) for x in new_modules)
print(rectangles_new)
problem_new= Problem(rectangles=rectangles_new)
for l in prev_modules:
    if l["end_time"] <= cur_time:
        prev_modules.remove(l)
if len(prev_modules) > 0:
    new_modules += prev_modules
rectangles = list(dict((k, x[k]) for k in ('id', 'width', 'height')) for x in new_modules)
problem = Problem(rectangles=rectangles)
pass_problem(problem_new, prev_modules, cur_time)







