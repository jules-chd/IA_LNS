import random
import sys
import json
import time


def read_instance_json(file_path):
    with open(file_path) as f:
        return json.load(f)


def write_instance_json(solution, file_path):
    with open(file_path, 'w') as f:
        json.dump(solution, f)


instance_path = sys.argv[1]
output_path = sys.argv[2]

instance = read_instance_json(instance_path)
naive_infeasible_solution = [None for _ in range(len(instance['customer_demands']))] # TODO - implement something better
write_instance_json(naive_infeasible_solution, output_path)


#######################################################################
# Example of the required timeout mechanism within the LNS structure: #
#######################################################################
# ...
# time_limit = instance['timeout']
# start_time = time.time()
# for iteration in range(9999999999):
#     ...logic of one search iteration...
#     if time.time() - start_time >= time_limit:
#         break
# ...
#######################################################################
#######################################################################
