
def displacement(prev_modules, floorplan):
    if len(prev_modules) == 0:
        return True
    prev_modules = sorted(prev_modules, key=lambda i: i['id'])
    flag = 0
    vec = []
    floorplan_modules = []
    for obj in prev_modules:
        if flag == 0:
            flag = 1
            ini_obj = obj
        else:
            vec_x = ini_obj["x"] - obj["x"]
            vec_y = ini_obj["y"] - obj["y"]
            vec.append({"vec_x": vec_x, "vec_y": vec_y})
    for obj in floorplan.positions:
        i = next((i for i, item in enumerate(prev_modules) if item["id"] == obj["id"]), None)
        if i is not None:
            floorplan_modules.append(obj)
    floorplan_modules = sorted(floorplan_modules, key=lambda i: i['id'])
    fvec = []
    for obj in floorplan_modules:
        if flag == 0:
            flag = 1
            ini_obj = obj
        else:
            vec_x = ini_obj["x"] - obj["x"]
            vec_y = ini_obj["y"] - obj["y"]
            fvec.append({"vec_x": vec_x, "vec_y": vec_y})
    if fvec == vec:
        print("HI")
        print(fvec)
        return True
    return False
