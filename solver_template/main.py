import random
import sys
import json
import time
import os

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


instance = read_instance_json(instance_path)
solution = solution_function.naive_feasible_solution(instance)
write_instance_json(solution, output_path)
visualize_solution(instance_path, output_path)
print("cost initial:", calculate_solution_cost(solution, instance))

for i in range(5):
    print(f"--- LNS iteration {i+1} ---")
    best_solution = solution_function.lns_solver(instance)
    write_instance_json(best_solution, output_path)
    print("cost final:", calculate_solution_cost(best_solution, instance))
    print("best cost", instance["best_cost"])
    print("visualize_solution...")
    visualize_solution(instance_path, output_path)

    # Affiche la capacité, la capacité utilisée et le nombre de clients par usine
    facility_capacities = [f["capacity"] for f in instance["facilities"]]
    used_capacity = [0] * len(facility_capacities)
    clients_count = [0] * len(facility_capacities)

    for cust_idx, fac in enumerate(best_solution):
        if fac is not None:
            used_capacity[fac] += instance["customer_demands"][cust_idx]
            clients_count[fac] += 1

    print("Usine | Capacité | Utilisée | Clients | Restante")
    for i, cap in enumerate(facility_capacities):
        restante = cap - used_capacity[i]
        print(f"{i:5d} | {cap:8d} | {used_capacity[i]:7d} | {clients_count[i]:7d} | {restante:8d}")
