import random
import sys
import json
import time
import os
import math

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cflp_viz.visualization import visualize_solution
from cflp_validator.validator import calculate_solution_cost, is_solution_feasible
import solver_template.solution as solution_function

def read_instance_json(file_path):
    with open(file_path) as f:
        return json.load(f)

def write_instance_json(solution, file_path):
    with open(file_path, 'w') as f:
        json.dump(solution, f)

instance_path = sys.argv[1]
output_path = sys.argv[2]


def main():
    instance = read_instance_json(instance_path)
    solution = solution_function.naive_feasible_solution(instance)
    initial_cost = calculate_solution_cost(solution, instance)
    write_instance_json(solution, output_path)
    visualize_solution(instance_path, output_path)
    print("Initial cost:", initial_cost)
    
    #LNS solver
    time_limit = instance['timeout']
    start_time = time.time()
    current_solution = solution
    current_cost = initial_cost
    best = current_solution.copy()
    best_cost = current_cost


    # SA parameters (tunable)
    temp = 100.0
    cooling = 0.995
    min_temp = 1e-3

    while time.time() - start_time < time_limit:
        destroy_ratio = random.uniform(0.1, 0.3)
        destroy = random.choice([solution_function.random_destroy, solution_function.factory_destroy])

        if destroy is solution_function.factory_destroy:
            num_available = len(instance["facilities"])
            num_factories = max(1, int(destroy_ratio * num_available))
            destroyed_solution = destroy(current_solution, instance, num_factories=num_factories)
        else:
            destroyed_solution = destroy(current_solution, destroy_ratio)

        # temporary closure: choose factories with few customers in current_solution
        facility_count = [0] * len(instance["facilities"])
        for cust_idx, fac in enumerate(current_solution):
            if fac is not None:
                facility_count[fac] += 1

        # simple threshold depending on destroy_ratio (adjustable)
        threshold = max(1, int(destroy_ratio * 5))
        small_factories = [i for i, cnt in enumerate(facility_count) if cnt <= threshold]

        temp_closed = set()
        if small_factories:
            # number to temporarily close proportional to destroy_ratio
            num_to_close = int(len(small_factories) * destroy_ratio)
            if num_to_close <= 0 and random.random() < 0.2:
                num_to_close = 1
            num_to_close = min(len(small_factories), max(0, num_to_close))
            if num_to_close > 0:
                temp_closed = set(random.sample(small_factories, num_to_close))

        # repair while forbidding temp_closed (the chosen factories will not be reopened during this repair)
        try:
            repaired_solution = solution_function.repair(destroyed_solution, instance, closed_factories=temp_closed)
        except Exception:
            # if repair fails (e.g., temporary closures make it infeasible), retry without temporary closures
            repaired_solution = solution_function.repair(destroyed_solution, instance, closed_factories=None)

        new_cost = calculate_solution_cost(repaired_solution, instance)
        delta = new_cost - current_cost

        # acceptance rule: always if better, else probabilistic (SA)
        accept = False
        if new_cost < current_cost:
            accept = True
        else:
            if temp > min_temp:
                prob = math.exp(-max(0, delta) / temp)
            else:
                prob = 0.0
            if random.random() < prob:
                accept = True

        if accept:
            current_solution = repaired_solution.copy()
            current_cost = new_cost

        # keep the global best
        if new_cost < best_cost:
            best = repaired_solution.copy()
            best_cost = new_cost

        # cooling
        temp = max(min_temp, temp * cooling)
    
    best_solution = best

    write_instance_json(best_solution, output_path)
    print("Final cost:", calculate_solution_cost(best_solution, instance))
    visualize_solution(instance_path, output_path)

    # facility_capacities = [f["capacity"] for f in instance["facilities"]]
    # used_capacity = [0] * len(facility_capacities)
    # clients_count = [0] * len(facility_capacities)

    # for cust_idx, fac in enumerate(best_solution):
    #     if fac is not None:
    #         used_capacity[fac] += instance["customer_demands"][cust_idx]
    #         clients_count[fac] += 1

    # print("Facility | Capacity | Used | Clients | Not Used")
    # for i, cap in enumerate(facility_capacities):
    #     restante = cap - used_capacity[i]
    #     print(f"{i:5d} | {cap:8d} | {used_capacity[i]:7d} | {clients_count[i]:7d} | {restante:8d}")


if __name__ == "__main__":
    main()