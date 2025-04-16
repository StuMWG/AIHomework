import random
from scipy.special import softmax

# Defining data
facilitators = [
    "Lock", "Glen", "Banks", "Richards", "Shaw", 
    "Singer", "Uther", "Tyler", "Numen", "Zeldin"
]

time_hour = {
    "10 AM": 10,
    "11 AM": 11,
    "12 PM": 12,
    "1 PM":  13,
    "2 PM":  14,
    "3 PM":  15
}

rooms = {
    "Slater 003": 45,
    "Roman 216": 30,
    "Loft 206": 75,
    "Roman 201": 50,
    "Loft 310": 108,
    "Beach 201": 60,
    "Beach 301": 75,
    "Frank 119": 60
}

# Define activities as dictionaries of expected enrollment, preferred facilitators, and other facilitators.
activities = {
    "SLA100A": {
        "expected": 50,
        "preferred": ["Glen", "Lock", "Banks", "Zeldin"],
        "other":     ["Numen", "Richards"]
    },
    "SLA100B": {
        "expected": 50,
        "preferred": ["Glen", "Lock", "Banks", "Zeldin"],
        "other":     ["Numen", "Richards"]
    },
    "SLA191A": {
        "expected": 50,
        "preferred": ["Glen", "Lock", "Banks", "Zeldin"],
        "other":     ["Numen", "Richards"]
    },
    "SLA191B": {
        "expected": 50,
        "preferred": ["Glen", "Lock", "Banks", "Zeldin"],
        "other":     ["Numen", "Richards"]
    },
    "SLA201": {
        "expected": 50,
        "preferred": ["Glen", "Banks", "Zeldin", "Shaw"],
        "other":     ["Numen", "Richards", "Singer"]
    },
    "SLA291": {
        "expected": 50,
        "preferred": ["Lock", "Banks", "Zeldin", "Singer"],
        "other":     ["Numen", "Richards", "Shaw", "Tyler"]
    },
    "SLA303": {
        "expected": 60,
        "preferred": ["Glen", "Zeldin", "Banks"],
        "other":     ["Numen", "Singer", "Shaw"]
    },
    "SLA304": {
        "expected": 25,
        "preferred": ["Glen", "Banks", "Tyler"],
        "other":     ["Numen", "Singer", "Shaw", "Richards", "Uther", "Zeldin"]
    },
    "SLA394": {
        "expected": 20,
        "preferred": ["Tyler", "Singer"],
        "other":     ["Richards", "Zeldin"]
    },
    "SLA449": {
        "expected": 60,
        "preferred": ["Tyler", "Singer", "Shaw"],
        "other":     ["Zeldin", "Uther"]
    },
    "SLA451": {
        "expected": 100,
        "preferred": ["Tyler", "Singer", "Shaw"],
        "other":     ["Zeldin", "Uther", "Richards", "Banks"]
    }
}

activities_list = list(activities.keys())

# Functions for random generation
def random_assignment():
    # Return a random time, room, and facilitator tuple.
    time = random.choice(list(time_hour.keys()))
    room = random.choice(list(rooms.keys()))
    facilitator = random.choice(facilitators)
    return (time, room, facilitator)

def random_schedule():
    # Create a schedule as a list of time, room, and facilitator
    schedule = []
    for _ in activities_list:
        schedule.append(random_assignment())
    return schedule

# Fitness Function
def fitness(schedule):
    # Given a schedule, compute the total fitness using the scoring rules.
    total_fitness = 0.0

    assignments = {}
    for i, activity in enumerate(activities_list):
        assignments[activity] = schedule[i]
        
    time_room_count = {}
    facilitator_total_count = {f: 0 for f in facilitators}
    facilitator_per_timeslot = {f: {} for f in facilitators}

    for activity in activities_list:
        (time, room, facilitator) = assignments[activity]
        
        # time-room combos:
        time_room_count.setdefault((time, room), 0)
        time_room_count[(time, room)] += 1
        
        # facilitator counts:
        facilitator_total_count[facilitator] += 1
        facilitator_per_timeslot[facilitator].setdefault(time, 0)
        facilitator_per_timeslot[facilitator][time] += 1

    # per-activity scores
    for activity in activities_list:
        (time, room, facilitator) = assignments[activity]
        info = activities[activity]
        score = 0.0

        # Overlap in same room/time
        if time_room_count[(time, room)] > 1:
            # -0.5 for same time and in same room
            score -= 0.5

        # Room capacity
        capacity = rooms[room]
        expected = info["expected"]
        if capacity < expected:
            score -= 0.5  # too small
        else:
            # check if too big
            if capacity > 6 * expected:
                score -= 0.4
            elif capacity > 3 * expected:
                score -= 0.2
            else:
                score += 0.3  # right size

        # Facilitator match
        if facilitator in info["preferred"]:
            score += 0.5
        elif facilitator in info["other"]:
            score += 0.2
        else:
            score -= 0.1

        # Facilitator load
        count_this_slot = facilitator_per_timeslot[facilitator][time]
        if count_this_slot == 1:
            score += 0.2
        else:
            score -= 0.2

        # if facilitator is scheduled for more than 4 total
        total_for_facilitator = facilitator_total_count[facilitator]
        if total_for_facilitator > 4:
            score -= 0.5

        # if facilitator is scheduled to oversee less than 2 total
        if facilitator != "Tyler":
            if total_for_facilitator <= 2:
                score -= 0.4
        else:
            # Case for Tyler
            pass

        total_fitness += score

    # Time difference function
    def hour_diff(a, b):
        return abs(time_hour[a] - time_hour[b])
    
    tA_101, _, _ = assignments["SLA100A"]
    tB_101, _, _ = assignments["SLA100B"]
    diff101 = hour_diff(tA_101, tB_101)
    if diff101 > 4:
        total_fitness += 0.5
    if diff101 == 0:
        total_fitness -= 0.5

    tA_191, _, _ = assignments["SLA191A"]
    tB_191, _, _ = assignments["SLA191B"]
    diff191 = hour_diff(tA_191, tB_191)
    if diff191 > 4:
        total_fitness += 0.5
    if diff191 == 0:
        total_fitness -= 0.5

    # Handling case for 101 and 191 consecutive time slots
    def check_101_191(act101, act191):
        nonlocal total_fitness
        t1, r1, _ = assignments[act101]
        t2, r2, _ = assignments[act191]
        d = hour_diff(t1, t2)
        # same slot
        if d == 0:
            total_fitness -= 0.25
        # consecutive
        if d == 1:
            total_fitness += 0.5
            # check building mismatch if one is in Roman/Beach and the other is not
            def in_roman_beach(room_name):
                return ("Roman" in room_name) or ("Beach" in room_name)
            if in_roman_beach(r1) != in_roman_beach(r2):
                total_fitness -= 0.4
        if d == 2:
            total_fitness += 0.25

    check_101_191("SLA100A", "SLA191A")
    check_101_191("SLA100A", "SLA191B")
    check_101_191("SLA100B", "SLA191A")
    check_101_191("SLA100B", "SLA191B")

    return total_fitness

# Selection, crossovoer and Mutation fucnctions
def selection(population, fitnesses):
    probs = softmax(fitnesses)
    cdf = []
    current_sum = 0.0
    for p in probs:
        current_sum += p
        cdf.append(current_sum)

    def pick_one():
        rand = random.random()
        for i, val in enumerate(cdf):
            if rand <= val:
                return population[i]
        return population[-1]

    p1 = pick_one()
    p2 = pick_one()
    return p1, p2

def crossover(scheduleA, scheduleB):
    size = len(scheduleA)
    if size < 2:
        # trivial case
        return scheduleA[:], scheduleB[:]
    cx_point = random.randint(1, size - 1) # crossover point
    child1 = scheduleA[:cx_point] + scheduleB[cx_point:]
    child2 = scheduleB[:cx_point] + scheduleA[cx_point:]
    return child1, child2

def mutate(schedule, mutation_rate):
    size = len(schedule)
    if random.random() < (mutation_rate * size):
        idx = random.randint(0, size - 1)
        (time, room, facilitator) = schedule[idx]
        # pick which to mutate time, room, or facilitator
        choice = random.choice(["time", "room", "fac"])
        if choice == "time":
            time = random.choice(list(time_hour.keys()))
        elif choice == "room":
            room = random.choice(list(rooms.keys()))
        else:
            facilitator = random.choice(facilitators)
        schedule[idx] = (time, room, facilitator)

def genetic_algorithm(
    population_size=500, 
    max_generations=500, 
    initial_mutation_rate=0.01
):
    # Create initial population
    population = [random_schedule() for _ in range(population_size)]

    # Evaluate fitness
    fitnesses = [fitness(sch) for sch in population]
    
    mutation_rate = initial_mutation_rate
    best_fitness_so_far = max(fitnesses)
    
    avg_fitness_history = []
    
    for g in range(max_generations):
        # Store the old best fitness before evolving to next gen
        old_best_fitness_so_far = best_fitness_so_far
        
        new_population = []
        new_fitnesses = []

        # Build next generation
        while len(new_population) < population_size:
            # select parents
            p1, p2 = selection(population, fitnesses)

            # produce offspring
            c1, c2 = crossover(p1, p2)

            # mutate
            mutate(c1, mutation_rate)
            mutate(c2, mutation_rate)

            new_population.append(c1)
            if len(new_population) < population_size:
                new_population.append(c2)

        # Evaluate new population
        new_fitnesses = [fitness(sch) for sch in new_population]

        # Replace old population and fitnesses
        population = new_population
        fitnesses = new_fitnesses

        # Track stats
        current_best = max(fitnesses)
        current_avg = sum(fitnesses) / len(fitnesses)
        avg_fitness_history.append(current_avg)

        # If the new best fitness beats the old best fitness, cut mutation in half
        if current_best > old_best_fitness_so_far:
            mutation_rate /= 2.0
            best_fitness_so_far = current_best

        # log progress
        if g % 10 == 0:
            print(f"Generation {g} | Best fitness: {current_best:.3f} "
                  f"| Avg fitness: {current_avg:.3f} | Mutation: {mutation_rate:.5f}")

        # After 100 generations, check improvement in average fitness
        if g == 100:
            baseline_avg_100 = current_avg

        if g > 100:
            # if improvement < 1% over baseline, stop
            if baseline_avg_100 != 0 and (current_avg - baseline_avg_100) < 0.01 * baseline_avg_100:
                print(f"Stopping at generation {g}.")
                break

    # Return the best schedule and its fitness
    best_index = max(range(len(population)), key=lambda i: fitnesses[i])
    best_schedule = population[best_index]
    return best_schedule, fitnesses[best_index]

# Execution and Output
if __name__ == "__main__":
    best_sched, best_fit = genetic_algorithm(
        population_size=500, 
        max_generations=300,
        initial_mutation_rate=0.01
    )
    print("\nBest schedule found, fitness = {:.3f}:".format(best_fit))
    
    # Print schedule to console
    for i, activity in enumerate(activities_list):
        (t, r, f) = best_sched[i]
        print(f"{activity}: time={t}, room={r}, facilitator={f}")
    
    # Write the final schedule to a file
    with open("best_schedule.txt", "w") as out_file:
        out_file.write(f"Best schedule found, fitness = {best_fit:.3f}:\n\n")
        for i, activity in enumerate(activities_list):
            (time, room, facilitator) = best_sched[i]
            out_file.write(f"{activity}: time={time}, room={room}, facilitator={facilitator}\n")