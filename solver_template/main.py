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
    time_limit = instance['timeout']
    start_time = time.time()
    if solution_function.is_infeasible(instance):
        raise Exception("Instance is infeasible, no solution possible.")

    solution = solution_function.naive_feasible_solution(instance)
    initial_cost = calculate_solution_cost(solution, instance)
    write_instance_json(solution, output_path)
    
    #LNS solver

    # precompute sorted facility lists per customer once
    facility_order = solution_function.precompute_facility_order(instance)

    current_solution = solution
    current_cost = initial_cost
    best = current_solution.copy()
    best_cost = current_cost

    # SA parameters (tunable)
    temp = 100.0
    cooling = 0.995
    min_temp = 1e-3

    no_customers = len(instance["customer_demands"])

    while time.time() - start_time < time_limit:
        elapsed = time.time() - start_time
        progress = elapsed / max(1e-9, time_limit)

        # adapt destroy ratio: for larger instances, destroy less;
        # near the end, destroy even less to intensify.
        if no_customers >= 100:
            base_low, base_high = (0.05, 0.15)
        else:
            base_low, base_high = (0.10, 0.30)
        if progress > 0.75:
            base_low, base_high = (0.03, 0.08)

        destroy_ratio = random.uniform(base_low, base_high)
        
        # pick a destroy operator
        destroy_op = random.choice([solution_function.random_destroy, solution_function.facility_destroy, solution_function.expensive_destroy])


        # apply the chosen destroy
        if destroy_op is solution_function.facility_destroy:
            num_available = len(instance["facilities"])
            num_facilities = max(1, int(destroy_ratio * num_available))
            destroyed_solution = destroy_op(current_solution, instance, num_facilities=num_facilities)
        elif destroy_op is solution_function.expensive_destroy:
            destroyed_solution = destroy_op(current_solution, instance, destroy_ratio)
        else:
            destroyed_solution = destroy_op(current_solution, destroy_ratio)

        # temporary diversification: close some low-load facilities during repair
        facility_count = [0] * len(instance["facilities"])
        for fac in current_solution:
            if fac is not None:
                facility_count[fac] += 1
        threshold = max(1, int(destroy_ratio * 5))
        small_facilities = [i for i, cnt in enumerate(facility_count) if cnt <= threshold]

        temp_closed = set()
        if small_facilities:
            num_to_close = int(len(small_facilities) * destroy_ratio)
            if num_to_close <= 0 and random.random() < 0.2:
                num_to_close = 1
            num_to_close = min(len(small_facilities), max(0, num_to_close))
            if num_to_close > 0:
                temp_closed = set(random.sample(small_facilities, num_to_close))

        # repair the partial solution (prefer using already-open facilities)
        try:
            repaired_solution = solution_function.repair(
                destroyed_solution, instance,
                closed_facilities=temp_closed,
                facility_order=facility_order,
                top_k=15
            )
        except Exception:
            # if temporary closures make it infeasible, retry without them
            repaired_solution = solution_function.repair(
                destroyed_solution, instance,
                closed_facilities=None,
                facility_order=facility_order,
                top_k=15
            )

        # increase polishing near the end
        passes = 2 if progress > 0.75 else 1
        repaired_solution = solution_function.local_improve(
            repaired_solution, instance, facility_order,
            max_passes=passes, top_k=20
        )

        # try some random 2-swaps among expensive customers
        swap_budget = 3000 if progress > 0.75 else 1500
        repaired_solution = solution_function.swap_improve(repaired_solution, instance, budget=swap_budget)

        new_cost = calculate_solution_cost(repaired_solution, instance)
        delta = new_cost - current_cost

        # decide whether to accept the new solution
        accept = False
        if new_cost < current_cost:
            accept = True
        else:
            prob = math.exp(-max(0, delta) / max(min_temp, temp))
            if random.random() < prob:
                accept = True

        if accept:
            current_solution = repaired_solution.copy()
            current_cost = new_cost

        if new_cost < best_cost:
            best = repaired_solution.copy()
            best_cost = new_cost

        # cool down the temperature
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