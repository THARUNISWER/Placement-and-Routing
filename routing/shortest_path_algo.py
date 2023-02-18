import queue
import math


class Grid:
    def __init__(self, start, goal, scene):
        self._start = start
        self._goal = goal
        self._width = len(scene[0])
        self._height = len(scene)
        self._scene = scene

    def solve(self):
        frontier = queue.PriorityQueue()
        frontier.put((0, self._start))
        came_from = {}
        cost_so_far = {}
        came_from[self._start] = None
        cost_so_far[self._start] = 0

        if not self.not_in_obstacle(self._start) or not self.not_in_obstacle(self._goal):
            return None

        if not self.in_bounds(self._start):
            print("START BOUND")
            return None
        if not self.in_bounds(self._goal):
            print("GOAL BOUNDS")
            print(self._start)
            print(self._goal)
            print(self._width)
            print(self._height)
            return None

        while not frontier.empty():
            _, current_position = frontier.get()

            if current_position == self._goal:
                return self.back_track_moves(came_from)

            for next_position in self.neighbors(current_position):
                new_cost = cost_so_far[current_position] + \
                    self.euclidean_distance(current_position, next_position)

                if next_position not in cost_so_far or new_cost < cost_so_far[next_position]:
                    cost_so_far[next_position] = new_cost
                    priority = new_cost + \
                        self.euclidean_distance(self._goal, next_position)
                    frontier.put((priority, next_position))
                    came_from[next_position] = current_position

        return None

    def neighbors(self, location):
        (x, y) = location
        results = [(x+1, y), (x, y-1),
                   (x-1, y), (x, y+1)]

        if (x + y) % 2 == 0:
            results.reverse()

        results = filter(self.in_bounds, results)
        results = filter(self.not_in_obstacle, results)
        return results

    def in_bounds(self, location):
        (x, y) = location
        return 0 <= x < self._height and 0 <= y < self._width

    def not_in_obstacle(self, location):
        (x, y) = location
        if self._scene[x][y]:
            return False
        return True

    def euclidean_distance(self, location1, location2):
        (x1, y1) = location1
        (x2, y2) = location2
        return math.sqrt(((x1-x2)**2)+((y1-y2)**2))

    def back_track_moves(self, visited):
        current = self._goal
        start = self._start
        path = []

        while current != start:
            path.append(current)
            current = visited[current]

        path.append(self._start)
        path.reverse()
        return path.copy()

    def print_board(self):
        for row in self._scene:
            row = ["." if x is False else x for x in row]
            row = ["X" if x is True else x for x in row]
            print(row)
        print()


def find_path(start, goal, scene):
    sc = []
    for row in scene:
        sc.append([])
        for num in row:
            if num == 0:
                sc[-1].append(False)
            else:
                sc[-1].append(True)
    grid = Grid(start, goal, sc)
    path = grid.solve()
    return path
