import json
import sys
UNASSIGNED_CUSTOMER_PENALTY = 10_000


def read_json(file_path):
    with open(file_path) as f:
        return json.load(f)

"""
Checks feasibility of the given solution. Returns True if the solution is feasible, i.e., facility capacity constraints 
are respected and all customers are assigned to a facility. 
Instance and solution must match the data formats described in __../data/README.md__. 
"""
def is_solution_feasible(solution, instance):
    no_facilities, no_customers = len(instance['facilities']), len(instance['customer_demands'])
    if len(solution) != no_customers:
        print(f'Invalid shape of solution. Expected a list with {no_customers} numbers (number of customers) describing the facilities assigned to individual customers.')
        return False

    facility_demands = [0 for _ in range(no_facilities)]
    for customer in range(no_customers):
        customer_demand = instance['customer_demands'][customer]
        customer_facility = solution[customer]
        if customer_facility is None:
            print(f"Customer {customer} has not been assigned to any facility.")
            return False
        facility_demands[customer_facility] += customer_demand

    for facility, total_demand in enumerate(facility_demands):
        facility_capacity = instance['facilities'][facility]['capacity']
        if total_demand > facility_capacity:
            print(f"The total demand ({total_demand}) assigned to facility {facility} exceeds its capacity ({facility_capacity}).")
            return False
    return True


"""
Calculates the costs (objective function) for the provided solution. The costs consist of facility opening costs, 
customer-facility assignment costs and possible infeasibility penalties (10k per unassigned customer).
Instance and solution must match the data formats described in __../data/README.md__. 
"""
def calculate_solution_cost(solution, instance):
    used_facilities = set()
    assignment_costs_total = 0
    for customer, facility in enumerate(solution):
        assignment_costs_total += UNASSIGNED_CUSTOMER_PENALTY if facility is None else instance['assignment_costs'][facility][customer]
        used_facilities.add(facility)

    total_cost = assignment_costs_total
    for facility in used_facilities:
        total_cost += instance['facilities'][facility]['opening_cost']
    return total_cost


instance_file_path, solution_file_path, mode = sys.argv[1], sys.argv[2], sys.argv[3]
instance, solution = read_json(instance_file_path), read_json(solution_file_path)
if mode == 'VALIDATE':
    print(is_solution_feasible(solution, instance))
elif mode == 'COST':
    print(5)
    print(calculate_solution_cost(solution, instance))
else:
    raise "Invalid mode"
