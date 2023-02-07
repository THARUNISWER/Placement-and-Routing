

def displacement(prev_modules, floorplan):
    prev_modules = sorted(prev_modules, key=lambda i: i['id'])
    prev_obj = prev_modules[0]
    for obj in prev_modules:
        vec_x = prev_obj["x"] - obj["x"]