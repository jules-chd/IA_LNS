import random
import sys
import json
import time
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cflp_viz.visualization import visualize_solution
from cflp_validator.validator import calculate_solution_cost, is_solution_feasible


def read_instance_json(file_path):
    with open(file_path) as f:
        return json.load(f)


def write_instance_json(solution, file_path):
    with open(file_path, 'w') as f:
        json.dump(solution, f)

def naive_feasible_solution(instance):
    facility_remain_capacity= [ instance["facilities"][i]["capacity"] for i in range (len(instance["facilities"]))]
    initial_solution=[]
    for i in range(len(instance["customer_demands"])):
        assignment_costs=[(instance["assignment_costs"][j][i],j) for j in range(len(instance["facilities"]))]  
        assignment_costs.sort()
        k=0
        while len(initial_solution) == i:
            if instance["customer_demands"][i] <= facility_remain_capacity[assignment_costs[k][1]]:
                initial_solution.append(assignment_costs[k][1])
            else:
                k+=1
    return initial_solution

def random_destroy(solution, destroy_ratio):
    num_customers = len(solution)
    num_to_destroy = int(num_customers * destroy_ratio)
    customers_to_destroy = random.sample(range(num_customers), num_to_destroy)
    new_solution = solution.copy()
    for customer in customers_to_destroy:
        new_solution[customer] = None
    return new_solution

def repair(destroyed_solution, instance):
    facility_remain_capacity= [ instance["facilities"][i]["capacity"] for i in range (len(instance["facilities"]))]
    for customer in range(len(destroyed_solution)):
        if destroyed_solution[customer] is not None:
            facility_remain_capacity[destroyed_solution[customer]] -= instance["customer_demands"][customer]
    new_solution = destroyed_solution.copy()
    for customer in range(len(destroyed_solution)):
        if destroyed_solution[customer] is None:
            assignment_costs=[(instance["assignment_costs"][j][customer],j) for j in range(len(instance["facilities"]))]  
            assignment_costs.sort()
            k=0
            while new_solution[customer] is None:
                if instance["customer_demands"][customer] <= facility_remain_capacity[assignment_costs[k][1]]:
                    new_solution[customer]=assignment_costs[k][1]
                    facility_remain_capacity[assignment_costs[k][1]] -= instance["customer_demands"][customer]
                else:
                    k+=1
    return new_solution


instance_path = sys.argv[1]
output_path = sys.argv[2]

instance = read_instance_json(instance_path)

solution = naive_feasible_solution(instance)
write_instance_json(solution, output_path)
print("cost initial:", calculate_solution_cost(solution, instance))

def lns_solver(instance):
    time_limit = instance['timeout']
    start_time = time.time()
    current_solution = naive_feasible_solution(instance)
    best=current_solution.copy()
    best_cost=calculate_solution_cost(best,instance)
    while time.time() - start_time < time_limit:
        destroy_ratio = random.uniform(0.1, 0.3)
        destroyed_solution = random_destroy(current_solution, destroy_ratio)
        repaired_solution = repair(destroyed_solution, instance)
        new_cost = calculate_solution_cost(repaired_solution, instance)

        if new_cost < best_cost:
            best = repaired_solution.copy()
            best_cost = new_cost
            current_solution = repaired_solution.copy()
        else:
            if random.random() < 0.05:
                current_solution = repaired_solution
    return best


print("cost final:", calculate_solution_cost(lns_solver(instance), instance))