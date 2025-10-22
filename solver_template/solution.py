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
        # liste (cost, facility) triée par coût croissant
        assignment_costs = sorted([(instance["assignment_costs"][j][i], j) for j in range(len(instance["facilities"]))])
        assigned = None
        for cost, fac in assignment_costs:
            if demand <= facility_remain_capacity[fac]:
                assigned = fac
                facility_remain_capacity[fac] -= demand   # <-- mise à jour importante
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
        raise TypeError(f"factory_destroy attendu instance(dict), reçu {type(instance)}")

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
    Repair en évitant d'affecter vers les usines dans closed_factories (list ou set).
    closed_factories peut être None ou un iterable d'indices d'usines.
    """
    if closed_factories is None:
        closed_factories = set()
    else:
        closed_factories = set(closed_factories)

    facility_remain_capacity = [instance["facilities"][i]["capacity"] for i in range(len(instance["facilities"]))]
    # rendre la capacité nulle pour les usines temporairement fermées (interdites)
    for f in closed_factories:
        if 0 <= f < len(facility_remain_capacity):
            facility_remain_capacity[f] = 0

    customers_to_repair = []
    for customer in range(len(destroyed_solution)):
        assigned = destroyed_solution[customer]
        if assigned is not None:
            # si l'affectation existante est vers une usine fermée, on la considère détruite
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
        # construire liste triée en ignorant les usines temporairement fermées
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
                # aucune usine ouverte ne peut servir ce client -> levée d'exception
                raise Exception(f"No feasible facility found for customer {customer} during repair (closed_factories={closed_factories})")

        new_solution[customer] = chosen_fac
        facility_remain_capacity[chosen_fac] -= demand

    return new_solution

