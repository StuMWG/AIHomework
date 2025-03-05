import networkx as nx
from collections import deque
import heapq
import time
import csv
import math

# Reads the text file containing city connections and returns an adjacency graph
def connections(file_path):
    graph = nx.Graph()
    with open(file_path, 'r') as file:
        for line in file:
            cities = line.strip().split()
            if len(cities) == 2:  
                city1 = cities[0].replace('_', ' ').lower()
                city2 = cities[1].replace('_', ' ').lower()
                graph.add_edge(city1, city2)
    return graph

# Reads the CSV file containing city coordinates and returns a dictionary
def coordinates(csv_file):
    coordinates = {}
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            city = row[0].strip().replace('_', ' ').lower()
            lat, lon = float(row[1]), float(row[2])
            coordinates[city] = (lat, lon)
    return coordinates

 # Calculates the distance between coordinates
def distance(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    return math.sqrt(dlat**2 + dlon**2)

# Calculates the total distance used for heristic functions
def totalDistance(path, coordinates):
    return sum(distance(coordinates[path[i]], coordinates[path[i+1]]) for i in range(len(path) - 1))

# interface for distinguishing functions that use coordinates and those that do not
def runSearch(function, name, graph, start, destination, coordinates):
    path, runtime = function(graph, start, destination, coordinates) if name in ["Best-First Search", "A* Search"] else function(graph, start, destination)
    distance = totalDistance(path, coordinates) if path else None
    return path, distance, runtime

# Dictonarey that stores runtimes
runtimes = {}

# uses FIFO queue to visit all nodes at the current depth then moves to the next depth, continuing until it finds the goal
def bfs(graph, start, goal):
    # Breadth-First Search
    startTime = time.perf_counter()
    queue = deque([(start, [start])])
    visited = set()

    while queue:
        # pops the first node from the queue
        node, path = queue.popleft()
        if node == goal:
            runtime = (time.perf_counter() - startTime)
            runtimes["BFS"] = runtime
            return path, runtime

        if node not in visited:
            # adds nodes visited into the set
            visited.add(node)
            # moves all neighbors of node onto the queue
            for neighbor in graph.neighbors(node):
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))

    runtime = (time.perf_counter() - startTime)
    runtimes["BFS"] = runtime
    return None, runtime

# uses recursion to explore as far as possible along each branch before backtracking until it reaches the goal
def dfs(graph, start, goal, path=None, visited=None, startTime=None):
    # Depth-First Search
    if path is None:
        path = [start]
    if visited is None:
        visited = set()
    if startTime is None:
        startTime = time.perf_counter()

    if start == goal:
        runtime = (time.perf_counter() - startTime)
        runtimes["DFS"] = runtime
        return path, runtime

    visited.add(start)
    # recursively visits all neighbor nodes
    for neighbor in graph.neighbors(start):
        if neighbor not in visited:
            newPath, _ = dfs(graph, neighbor, goal, path + [neighbor], visited, startTime)
            if newPath:
                runtime = (time.perf_counter() - startTime)
                runtimes["DFS"] = runtime
                return newPath, runtime

    runtime = (time.perf_counter() - startTime)
    runtimes["DFS"] = runtime
    return None, runtime

# uses repeated calls of dls with an incremented depth limit until the goal is found
def iddfs(graph, start, goal, maxDepth=50):
    # Iterative Deepening
    startTime = time.perf_counter()

    # depth-limited search
    def dls(node, goal, depth, path, visited):
        if depth == 0 and node == goal:
            return path
        if depth > 0:
            visited.add(node)
            for neighbor in graph.neighbors(node):
                if neighbor not in visited:
                    # recursively add all neighbor nodes to path, one branch at a time
                    newPath = dls(neighbor, goal, depth - 1, path + [neighbor], visited)
                    if newPath:
                        return newPath
        return None

    # iterates through depth levels
    for depth in range(maxDepth):
        visited = set()
        result = dls(start, goal, depth, [start], visited)
        if result:
            runtime = (time.perf_counter() - startTime)
            runtimes["ID-DFS"] = runtime
            return result, runtime

    runtime = (time.perf_counter() - startTime)
    runtimes["ID-DFS"] = runtime
    return None, runtime

# uses a priority queue to visit the node with the smallest distance to the goal
def bestFirstSearch(graph, start, goal, coordinates):
    # Best First Search using distance as a heuristic.
    startTime = time.perf_counter()
    queue = [(distance(coordinates[start], coordinates[goal]), start, [start])]
    visited = set()

    while queue:
        _, node, path = heapq.heappop(queue) # pops the node with the smallest distance
        if node == goal:
            runtime = (time.perf_counter() - startTime)
            runtimes["Best-First"] = runtime
            return path, runtime

        # skip if already visited
        if node in visited:
            continue # goes to next iteration of the loop

        visited.add(node)
        for neighbor in graph.neighbors(node):
            if neighbor not in visited:
                heapq.heappush(queue, (distance(coordinates[neighbor], coordinates[goal]), neighbor, path + [neighbor]))

    runtime = (time.perf_counter() - startTime)
    runtimes["Best-First"] = runtime
    return None, runtime

# uses a priority queue to visit the node with the smallest estimated cost to goal
def aStarSearch(graph, start, goal, coordinates):
    # A* Search using distance as heuristic
    startTime = time.perf_counter()
    priorityQueue = [(0, start, [start])]
    visitedNodes = set()
    gCost = {start: 0}  # Stores the known cost to reach each visited node

    while priorityQueue:
        _, node, path = heapq.heappop(priorityQueue)
        
        if node == goal:
            runtime = time.perf_counter() - startTime
            runtimes["A*"] = runtime
            return path, runtime

        if node in visitedNodes:
            continue  

        visitedNodes.add(node)
        
        for neighbor in graph.neighbors(node):
            travelCost = gCost[node] + distance(coordinates[node], coordinates[neighbor])
            if neighbor not in gCost or travelCost < gCost[neighbor]:
                gCost[neighbor] = travelCost
                # f(n) = g(n) + h(n)
                estimatedTotalCost = travelCost + distance(coordinates[neighbor], coordinates[goal])
                heapq.heappush(priorityQueue, (estimatedTotalCost, neighbor, path + [neighbor]))

    runtime = time.perf_counter() - startTime
    runtimes["A*"] = runtime
    return None, runtime

# Load Data
file_path = "Adjacencies.txt"
csv_file = "coordinates.csv"
graph = connections(file_path)
coordinates = coordinates(csv_file)

# User Input
start = input("Enter your starting city: ").strip().lower()
destination = input("Enter your destination city: ").strip().lower()

algorithms = {
    "1": ("Breadth-First Search", bfs),
    "2": ("Depth-First Search", dfs),
    "3": ("ID-DFS Search", iddfs),
    "4": ("Best-First Search", bestFirstSearch),
    "5": ("A* Search", aStarSearch)
}

# Display algorithm options
print("\nChoose a search algorithm:")
for key, (name, _) in algorithms.items():
    print(f"{key}. {name}")

choice1 = input("Enter the number of the algorithm you want to use: ").strip()
name1, function1 = algorithms[choice1]
path1, distance1, runtime1 = runSearch(function1, name1, graph, start, destination, coordinates)

# initial path
if path1:
    print(f"\n{name1} Path: {' -> '.join(path1)}")
    print(f"Total Distance: {distance1:.2f} km")
    print(f"Time Taken: {runtime1:.6f} seconds")

# Run comparison
compare = input("\nWould you like to compare another algorithm? (y/n): ").strip().lower()
if compare == 'y':
    print("\nChoose another search algorithm:")
    for key, (name, _) in algorithms.items():
        print(f"{key}. {name}")

    choice2 = input("Enter the number of another algorithm to compare: ").strip()
    name2, function2 = algorithms[choice2]
    path2, distance2, runtime2 = runSearch(function2, name2, graph, start, destination, coordinates)

    # Display comparison
    if path2:
        print(f"\nComparison Results:")
        print(f"{name1} Path: {' -> '.join(path1)}")
        print(f"{name2} Path: {' -> '.join(path2)}")
        print(f"{name1} Distance: {distance1:.2f} km")
        print(f"{name2} Distance: {distance2:.2f} km")
        print(f"{name1} Time: {runtime1:.6f} seconds")
        print(f"{name2} Time: {runtime2:.6f} seconds")
    else:
        print(f"\n{name2}: No path found.")