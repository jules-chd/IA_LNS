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

# ---------- NEW: destroy the most expensive assigned customers
def expensive_destroy(solution, instance, destroy_ratio):
    n = len(solution)
    k = int(n * destroy_ratio)
    if k <= 0:
        return solution.copy()
    costs = instance["assignment_costs"]
    pairs = []
    for c, f in enumerate(solution):
        if f is not None:
            pairs.append((costs[f][c], c))
    pairs.sort(reverse=True)
    to_destroy = [c for _, c in pairs[:k]]
    new_solution = solution.copy()
    for c in to_destroy:
        new_solution[c] = None
    return new_solution

# ---------- NEW: precompute facility order per customer (by ascending assignment cost)
def precompute_facility_order(instance):
    no_fac = len(instance["facilities"])
    no_cus = len(instance["customer_demands"])
    order = []
    for c in range(no_cus):
        facilities_sorted = sorted(range(no_fac), key=lambda f: instance["assignment_costs"][f][c])
        order.append(facilities_sorted)
    return order

# ---------- IMPROVED: cost-aware local improvement (considers facility open/close deltas)
def local_improve(solution, instance, facility_order, max_passes=1, top_k=20):
    facilities = instance["facilities"]
    demands = instance["customer_demands"]
    costs = instance["assignment_costs"]

    capacities = [f["capacity"] for f in facilities]
    remain = capacities[:]
    counts = [0] * len(facilities)
    for c, f in enumerate(solution):
        d = demands[c]
        counts[f] += 1
        remain[f] -= d

    new_solution = solution.copy()

    for _ in range(max_passes):
        changed = False
        # visit expensive customers first
        order_c = sorted(range(len(new_solution)),
                         key=lambda c: costs[new_solution[c]][c],
                         reverse=True)

        for c in order_c:
            from_f = new_solution[c]
            d = demands[c]
            cur_assign = costs[from_f][c]

            best_f = None
            best_delta = 0

            for to_f in facility_order[c][:top_k]:
                if to_f == from_f:
                    continue
                if remain[to_f] < d:
                    continue

                delta_assign = costs[to_f][c] - cur_assign
                open_delta = facilities[to_f]["opening_cost"] if counts[to_f] == 0 else 0
                close_delta = -facilities[from_f]["opening_cost"] if counts[from_f] == 1 else 0
                delta = delta_assign + open_delta + close_delta

                if delta < best_delta:
                    best_delta = delta
                    best_f = to_f

            if best_f is not None:
                # apply move
                new_solution[c] = best_f
                remain[from_f] += d
                remain[best_f] -= d
                counts[from_f] -= 1
                counts[best_f] += 1
                changed = True

        if not changed:
            break

    return new_solution

# ---------- IMPROVED: repair prefers already-open facilities to avoid opening-cost spikes
def repair(destroyed_solution, instance, closed_factories=None, facility_order=None, top_k=10):
    """
    Repair while avoiding assigning to factories in closed_factories (list or set).
    If facility_order is provided, sorting is avoided.
    """
    if closed_factories is None:
        closed_factories = set()
    else:
        closed_factories = set(closed_factories)

    F = len(instance["facilities"])
    demands = instance["customer_demands"]

    facility_remain_capacity = [instance["facilities"][i]["capacity"] for i in range(F)]
    used = [False] * F

    # mark closed factories capacity to 0
    for f in closed_factories:
        if 0 <= f < F:
            facility_remain_capacity[f] = 0

    customers_to_repair = []
    for customer, assigned in enumerate(destroyed_solution):
        if assigned is not None and assigned not in closed_factories:
            facility_remain_capacity[assigned] -= demands[customer]
            used[assigned] = True
        else:
            customers_to_repair.append(customer)

    # repair larger-demand customers first
    customers_to_repair.sort(key=lambda c: demands[c], reverse=True)

    new_solution = destroyed_solution.copy()

    for customer in customers_to_repair:
        demand = demands[customer]

        if facility_order is not None:
            ordered = [f for f in facility_order[customer] if f not in closed_factories]
            front = ordered[:top_k]
            open_cands = [f for f in front if used[f] and facility_remain_capacity[f] >= demand]
            closed_cands = [f for f in front if (not used[f]) and facility_remain_capacity[f] >= demand]

            if open_cands:
                chosen_fac = random.choice(open_cands[:min(3, len(open_cands))])
            elif closed_cands:
                chosen_fac = random.choice(closed_cands[:min(2, len(closed_cands))])
            else:
                # fallback scan beyond top_k
                chosen_fac = next((f for f in ordered if facility_remain_capacity[f] >= demand), None)
        else:
            assignment_costs = sorted(
                [(instance["assignment_costs"][j][customer], j)
                 for j in range(F) if j not in closed_factories]
            )
            feas = [fac for cost, fac in assignment_costs if facility_remain_capacity[fac] >= demand][:3]
            chosen_fac = random.choice(feas) if feas else next(
                (fac for cost, fac in assignment_costs if facility_remain_capacity[fac] >= demand), None
            )

        if chosen_fac is None:
            raise Exception(f"No feasible facility found for customer {customer} during repair (closed_factories={closed_factories})")

        new_solution[customer] = chosen_fac
        facility_remain_capacity[chosen_fac] -= demand
        used[chosen_fac] = True

    return new_solution

# ---------- NEW: 2-customer swap local search (capacity-feasible, opening-cost neutral)
def swap_improve(solution, instance, budget=2000):
    demands = instance["customer_demands"]
    costs = instance["assignment_costs"]
    facilities = instance["facilities"]
    F, C = len(facilities), len(demands)

    capacities = [f["capacity"] for f in facilities]
    remain = capacities[:]
    for c, f in enumerate(solution):
        remain[f] -= demands[c]

    new_solution = solution.copy()
    cur_cost_per_c = [costs[new_solution[c]][c] for c in range(C)]
    top = sorted(range(C), key=lambda c: cur_cost_per_c[c], reverse=True)[:min(C, 100)]

    for _ in range(budget):
        c1 = random.choice(top)
        c2 = random.randrange(C)
        f1, f2 = new_solution[c1], new_solution[c2]
        if f1 == f2:
            continue
        d1, d2 = demands[c1], demands[c2]

        # capacity feasibility after swap
        if remain[f1] + d1 - d2 < 0:
            continue
        if remain[f2] + d2 - d1 < 0:
            continue

        delta = (costs[f2][c1] + costs[f1][c2]) - (costs[f1][c1] + costs[f2][c2])
        if delta < 0:
            # apply swap
            new_solution[c1], new_solution[c2] = f2, f1
            remain[f1] += (d1 - d2)
            remain[f2] += (d2 - d1)
            cur_cost_per_c[c1] = costs[f2][c1]
            cur_cost_per_c[c2] = costs[f1][c2]

    return new_solution

def lns_solver(instance):
    time_limit = instance['timeout']
    start_time = time.time()

    facility_order = precompute_facility_order(instance)

    current_solution = naive_feasible_solution(instance)
    current_cost = calculate_solution_cost(current_solution, instance)

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

        # adaptive destroy ratio
        if no_customers >= 100:
            base_low, base_high = (0.05, 0.15)
        else:
            base_low, base_high = (0.10, 0.30)
        if progress > 0.75:
            base_low, base_high = (0.03, 0.08)
        destroy_ratio = random.uniform(base_low, base_high)

        destroy_op = random.choice([random_destroy, factory_destroy, expensive_destroy])

        if destroy_op is factory_destroy:
            num_available = len(instance["facilities"])
            num_factories = max(1, int(destroy_ratio * num_available))
            destroyed_solution = destroy_op(current_solution, instance, num_factories=num_factories)
        elif destroy_op is expensive_destroy:
            destroyed_solution = destroy_op(current_solution, instance, destroy_ratio)
        else:
            destroyed_solution = destroy_op(current_solution, destroy_ratio)

        # temporarily close few low-load factories to diversify
        facility_count = [0] * len(instance["facilities"])
        for fac in current_solution:
            if fac is not None:
                facility_count[fac] += 1
        threshold = max(1, int(destroy_ratio * 5))
        small_factories = [i for i, cnt in enumerate(facility_count) if cnt <= threshold]

        temp_closed = set()
        if small_factories:
            num_to_close = int(len(small_factories) * destroy_ratio)
            if num_to_close <= 0 and random.random() < 0.2:
                num_to_close = 1
            num_to_close = min(len(small_factories), max(0, num_to_close))
            if num_to_close > 0:
                temp_closed = set(random.sample(small_factories, num_to_close))

        # repair (prefers already open facilities)
        try:
            repaired_solution = repair(destroyed_solution, instance, closed_factories=temp_closed, facility_order=facility_order, top_k=15)
        except Exception:
            repaired_solution = repair(destroyed_solution, instance, closed_factories=None, facility_order=facility_order, top_k=15)

        # intensification: more passes later
        passes = 2 if progress > 0.75 else 1
        repaired_solution = local_improve(repaired_solution, instance, facility_order, max_passes=passes, top_k=20)

        # 2-swap refinement
        swap_budget = 3000 if progress > 0.75 else 1500
        repaired_solution = swap_improve(repaired_solution, instance, budget=swap_budget)

        new_cost = calculate_solution_cost(repaired_solution, instance)
        delta = new_cost - current_cost

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

        temp = max(min_temp, temp * cooling)

    return best

