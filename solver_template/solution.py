import random
import sys
import json
import time
import os
import math
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cflp_viz.visualization import visualize_solution
from cflp_validator.validator import calculate_solution_cost, is_solution_feasible

def naive_feasible_solution(instance):
    facility_remain_capacity = [f["capacity"] for f in instance["facilities"]]
    initial_solution = []
    for i, demand in enumerate(instance["customer_demands"]):
        # list (cost, facility) sorted by increasing cost
        assignment_costs = sorted([(instance["assignment_costs"][j][i], j) for j in range(len(instance["facilities"]))])
        assigned = None
        for cost, fac in assignment_costs:
            if demand <= facility_remain_capacity[fac]:
                assigned = fac
                facility_remain_capacity[fac] -= demand   # <-- important update
                initial_solution.append(fac)
                break
        if assigned is None:
            raise Exception(f"No feasible facility found for customer {i} in naive_feasible_solution")
    return initial_solution

def random_destroy(solution, destroy_ratio):
    num_customers = len(solution)
    num_to_destroy = int(num_customers * destroy_ratio)
    customers_to_destroy = random.sample(range(num_customers), num_to_destroy)
    new_solution = solution.copy()
    for customer in customers_to_destroy:
        new_solution[customer] = None
    return new_solution

def factory_destroy(solution, instance, num_factories=1):
    if not isinstance(instance, dict):
        raise TypeError(f"factory_destroy expected instance (dict), got {type(instance)}")

    new_solution = solution.copy()
    num_available = len(instance["facilities"])
    k = min(max(1, int(num_factories)), num_available)
    factories_to_close = random.sample(range(num_available), k)

    for i, assigned in enumerate(new_solution):
        if assigned is not None and assigned in factories_to_close:
            new_solution[i] = None

    return new_solution

def repair(destroyed_solution, instance, closed_factories=None):
    """
    Repair while avoiding assigning to factories in closed_factories (list or set).
    closed_factories can be None or an iterable of factory indices.
    """
    if closed_factories is None:
        closed_factories = set()
    else:
        closed_factories = set(closed_factories)

    facility_remain_capacity = [instance["facilities"][i]["capacity"] for i in range(len(instance["facilities"]))]
    # set capacity to zero for temporarily closed (forbidden) factories
    for f in closed_factories:
        if 0 <= f < len(facility_remain_capacity):
            facility_remain_capacity[f] = 0

    customers_to_repair = []
    for customer in range(len(destroyed_solution)):
        assigned = destroyed_solution[customer]
        if assigned is not None:
            # if the existing assignment is to a closed factory, consider it destroyed
            if assigned in closed_factories:
                customers_to_repair.append(customer)
            else:
                facility_remain_capacity[assigned] -= instance["customer_demands"][customer]
        else:
            customers_to_repair.append(customer)

    new_solution = destroyed_solution.copy()
    random.shuffle(customers_to_repair)

    for customer in customers_to_repair:
        demand = instance["customer_demands"][customer]
        # build sorted list while ignoring temporarily closed factories
        assignment_costs = sorted(
            [(instance["assignment_costs"][j][customer], j)
             for j in range(len(instance["facilities"])) if j not in closed_factories]
        )

        candidates = [fac for cost, fac in assignment_costs if facility_remain_capacity[fac] >= demand][:3]

        if candidates:
            chosen_fac = random.choice(candidates)
        else:
            chosen_fac = None
            for cost, fac in assignment_costs:
                if facility_remain_capacity[fac] >= demand:
                    chosen_fac = fac
                    break
            if chosen_fac is None:
                # no open factory can serve this customer -> raise exception
                raise Exception(f"No feasible facility found for customer {customer} during repair (closed_factories={closed_factories})")

        new_solution[customer] = chosen_fac
        facility_remain_capacity[chosen_fac] -= demand

    return new_solution


def lns_solver(instance):
    time_limit = instance['timeout']
    start_time = time.time()

    current_solution = naive_feasible_solution(instance)
    current_cost = calculate_solution_cost(current_solution, instance)

    best = current_solution.copy()
    best_cost = current_cost

    # SA parameters (tunable)
    temp = 100.0
    cooling = 0.995  # multiplicative per iteration
    min_temp = 1e-3

    while time.time() - start_time < time_limit:
        destroy_ratio = random.uniform(0.1, 0.3)
        destroy = random.choice([random_destroy, factory_destroy])

        if destroy is factory_destroy:
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
            repaired_solution = repair(destroyed_solution, instance, closed_factories=temp_closed)
        except Exception:
            # if repair fails (e.g., temporary closures make it infeasible), retry without temporary closures
            repaired_solution = repair(destroyed_solution, instance, closed_factories=None)

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

    return best

