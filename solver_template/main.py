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

    # single run of our solver within the given timeout
    best_solution = solution_function.lns_solver(instance)

    write_instance_json(best_solution, output_path)
    print("Final cost:", calculate_solution_cost(best_solution, instance))

    # optional visualization (set VISUALIZE=1 to enable)
    if os.environ.get("VISUALIZE", "0") == "1":
        visualize_solution(instance_path, output_path)

if __name__ == "__main__":
    main()
