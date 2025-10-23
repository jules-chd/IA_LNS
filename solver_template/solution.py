import random
import sys
import os

# let me import the helper modules from the parent folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cflp_viz.visualization import visualize_solution
from cflp_validator.validator import calculate_solution_cost, is_solution_feasible


# We start with a simple greedy feasible solution:
# assign each customer to the cheapest facility that still has enough remaining capacity.
def naive_feasible_solution(instance):
    facility_remain_capacity = [f["capacity"] for f in instance["facilities"]]
    initial_solution = []
    for i, demand in enumerate(instance["customer_demands"]):
        # list of (assignment_cost, facility_index) sorted by increasing cost for this customer
        assignment_costs = sorted(
            [(instance["assignment_costs"][j][i], j) for j in range(len(instance["facilities"]))]
        )
        assigned = None
        for cost, fac in assignment_costs:
            # pick the first facility that can fit this customer's demand
            if demand <= facility_remain_capacity[fac]:
                assigned = fac
                # update remaining capacity right away so next customers see the change
                facility_remain_capacity[fac] -= demand
                initial_solution.append(fac)
                break
    return initial_solution

# randomly "destroy" a portion of customers by unassigning them (set to None).
def random_destroy(solution, destroy_ratio):
    num_customers = len(solution)
    num_to_destroy = int(num_customers * destroy_ratio)
    customers_to_destroy = random.sample(range(num_customers), num_to_destroy)
    new_solution = solution.copy()
    for customer in customers_to_destroy:
        new_solution[customer] = None
    return new_solution


# "destroy" by randomly picking some facilities to close temporarily,
# and unassign all customers served by those facilities.
def facility_destroy(solution, instance, num_facilities=1):
    if not isinstance(instance, dict):
        raise TypeError(f"facility_destroy expected instance (dict), got {type(instance)}")

    new_solution = solution.copy()
    num_available = len(instance["facilities"])
    k = min(max(1, int(num_facilities)), num_available)
    facilities_to_close = random.sample(range(num_available), k)

    for i, assigned in enumerate(new_solution):
        if assigned is not None and assigned in facilities_to_close:
            new_solution[i] = None

    return new_solution


# destroy the most expensive customer assignments (by assignment cost),
# so the repair step can try to place them better.
def expensive_destroy(solution, instance, destroy_ratio):
    n = len(solution)
    k = int(n * destroy_ratio)
    if k <= 0:
        return solution.copy()
    costs = instance["assignment_costs"]
    pairs = []
    for c, f in enumerate(solution):
        if f is not None:
            # store (current_assignment_cost, customer_index)
            pairs.append((costs[f][c], c))
    # take the largest costs first
    pairs.sort(reverse=True)
    to_destroy = [c for _, c in pairs[:k]]
    new_solution = solution.copy()
    for c in to_destroy:
        new_solution[c] = None
    return new_solution


# precompute, for each customer, the list of facilities sorted by increasing assignment cost.
# this avoids re-sorting in every repair/improvement call.
def precompute_facility_order(instance):
    no_fac = len(instance["facilities"])
    no_cus = len(instance["customer_demands"])
    order = []
    for c in range(no_cus):
        facilities_sorted = sorted(range(no_fac), key=lambda f: instance["assignment_costs"][f][c])
        order.append(facilities_sorted)
    return order


# local improvement that tries to reassign a customer to a cheaper facility
# while considering capacity and the effect of opening/closing facilities.
# I only take improving moves (negative delta).
def local_improve(solution, instance, facility_order, max_passes=1, top_k=20):
    facilities = instance["facilities"]
    demands = instance["customer_demands"]
    costs = instance["assignment_costs"]

    # track remaining capacity and how many customers each facility has
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
        # try to fix the most expensive customers first
        order_c = sorted(
            range(len(new_solution)),
            key=lambda c: costs[new_solution[c]][c],
            reverse=True
        )

        for c in order_c:
            from_f = new_solution[c]
            d = demands[c]
            cur_assign = costs[from_f][c]

            best_f = None
            best_delta = 0  # negative is good (improvement)

            # check only the top_k cheapest facilities for this customer
            for to_f in facility_order[c][:top_k]:
                if to_f == from_f:
                    continue
                if remain[to_f] < d:
                    # not enough capacity there
                    continue

                # compute total delta: assignment change + possible open/close facility cost
                delta_assign = costs[to_f][c] - cur_assign
                open_delta = facilities[to_f]["opening_cost"] if counts[to_f] == 0 else 0
                close_delta = -facilities[from_f]["opening_cost"] if counts[from_f] == 1 else 0
                delta = delta_assign + open_delta + close_delta

                if delta < best_delta:
                    best_delta = delta
                    best_f = to_f

            if best_f is not None:
                # apply the improving move
                new_solution[c] = best_f
                remain[from_f] += d
                remain[best_f] -= d
                counts[from_f] -= 1
                counts[best_f] += 1
                changed = True

        if not changed:
            # no improvements found in this pass
            break

    return new_solution


# repair function: reassign unassigned customers.
# it prefers already-open facilities first to avoid paying new opening costs when possible.
def repair(destroyed_solution, instance, closed_facilities=None, facility_order=None, top_k=10):
    """
    destroyed_solution: list of facility indices or None for unassigned customers
    closed_facilities: a set of facilities we temporarily don't allow
    facility_order: precomputed sorted facilities per customer (cheapest first)
    """
    if closed_facilities is None:
        closed_facilities = set()
    else:
        closed_facilities = set(closed_facilities)

    F = len(instance["facilities"])
    demands = instance["customer_demands"]

    # set remaining capacities and track which facilities are already used
    facility_remain_capacity = [instance["facilities"][i]["capacity"] for i in range(F)]
    used = [False] * F

    # mark closed facilities by setting remaining capacity to 0 so we won't use them
    for f in closed_facilities:
        if 0 <= f < F:
            facility_remain_capacity[f] = 0

    customers_to_repair = []
    for customer, assigned in enumerate(destroyed_solution):
        if assigned is not None and assigned not in closed_facilities:
            facility_remain_capacity[assigned] -= demands[customer]
            used[assigned] = True
        else:
            customers_to_repair.append(customer)

    # assign bigger demands first; they are harder to place
    customers_to_repair.sort(key=lambda c: demands[c], reverse=True)

    new_solution = destroyed_solution.copy()

    for customer in customers_to_repair:
        demand = demands[customer]

        if facility_order is not None:
            # try the k cheapest facilities first
            ordered = [f for f in facility_order[customer] if f not in closed_facilities]
            front = ordered[:top_k]
            # prioritize facilities we already used (to avoid extra opening costs)
            open_cands = [f for f in front if used[f] and facility_remain_capacity[f] >= demand]
            closed_cands = [f for f in front if (not used[f]) and facility_remain_capacity[f] >= demand]

            if open_cands:
                # add a bit of randomness among the best few
                chosen_fac = random.choice(open_cands[:min(3, len(open_cands))])
            elif closed_cands:
                chosen_fac = random.choice(closed_cands[:min(2, len(closed_cands))])
            else:
                # fallback: scan beyond top_k to find any feasible facility
                chosen_fac = next((f for f in ordered if facility_remain_capacity[f] >= demand), None)
        else:
            # slower fallback: compute and sort costs on the fly
            assignment_costs = sorted(
                [(instance["assignment_costs"][j][customer], j)
                 for j in range(F) if j not in closed_facilities]
            )
            feas = [fac for cost, fac in assignment_costs if facility_remain_capacity[fac] >= demand][:3]
            chosen_fac = random.choice(feas) if feas else next(
                (fac for cost, fac in assignment_costs if facility_remain_capacity[fac] >= demand), None
            )

        if chosen_fac is None:
            # if this triggers, something is off (maybe too many facilities closed)
            raise Exception(f"No feasible facility found for customer {customer} during repair (closed_facilities={closed_facilities})")

        # assign and update remaining capacity + used flag
        new_solution[customer] = chosen_fac
        facility_remain_capacity[chosen_fac] -= demand
        used[chosen_fac] = True

    return new_solution


# simple 2-customer swap local search:
# try swapping the facilities of two customers if it lowers total assignment cost and is capacity-feasible.
# this does not change opening costs because the set of used facilities stays the same.
def swap_improve(solution, instance, budget=2000):
    demands = instance["customer_demands"]
    costs = instance["assignment_costs"]
    facilities = instance["facilities"]
    F, C = len(facilities), len(demands)

    # set up remaining capacity given current solution
    capacities = [f["capacity"] for f in facilities]
    remain = capacities[:]
    for c, f in enumerate(solution):
        remain[f] -= demands[c]

    new_solution = solution.copy()
    # keep current per-customer assignment cost for quicker ordering
    cur_cost_per_c = [costs[new_solution[c]][c] for c in range(C)]
    # focus on the top expensive customers to intensify
    top = sorted(range(C), key=lambda c: cur_cost_per_c[c], reverse=True)[:min(C, 100)]

    for _ in range(budget):
        c1 = random.choice(top)
        c2 = random.randrange(C)
        f1, f2 = new_solution[c1], new_solution[c2]
        if f1 == f2:
            # swapping within the same facility does nothing
            continue
        d1, d2 = demands[c1], demands[c2]

        # check capacity after swap (simulate removing and adding)
        if remain[f1] + d1 - d2 < 0:
            continue
        if remain[f2] + d2 - d1 < 0:
            continue

        # compute the assignment delta for the swap
        delta = (costs[f2][c1] + costs[f1][c2]) - (costs[f1][c1] + costs[f2][c2])
        if delta < 0:
            # apply beneficial swap
            new_solution[c1], new_solution[c2] = f2, f1
            remain[f1] += (d1 - d2)
            remain[f2] += (d2 - d1)
            cur_cost_per_c[c1] = costs[f2][c1]
            cur_cost_per_c[c2] = costs[f1][c2]

    return new_solution


def is_infeasible(instance):
    """
    Minimal feasibility check (instance assumed well-formed).
    Returns True if infeasible, False otherwise.

    Checks:
      - any single customer demand > max facility capacity
      - total demand > total capacity
      - attempts a Best-Fit-Decreasing packing (if fails, declare infeasible)
    """
    capacities = [int(f["capacity"]) for f in instance["facilities"]]
    demands = [int(d) for d in instance["customer_demands"]]

    if not capacities:
        return True

    # quick checks
    max_cap = max(capacities)
    if any(d > max_cap for d in demands):
        return True
    if sum(demands) > sum(capacities):
        return True

    # Best-Fit-Decreasing: sort demands desc and place each in the bin that will have the smallest leftover >= 0
    bins = capacities.copy()
    for d in sorted(demands, reverse=True):
        best_idx = None
        best_rem_after = None
        for i, rem in enumerate(bins):
            if rem >= d:
                rem_after = rem - d
                if best_idx is None or rem_after < best_rem_after:
                    best_idx = i
                    best_rem_after = rem_after
        if best_idx is None:
            return True
        bins[best_idx] -= d

    return False