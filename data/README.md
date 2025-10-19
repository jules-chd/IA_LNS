# Instance format

The provided instances are saved as JSON files with the following attributes:

 * __facilities__: list of available facilities, each facility is a two-key dictionary, indexed by facility ID 
   * __capacity__: maximum capacity of the facility, i.e., the total amount of customer demand that may be assigned to the facility
   * __opening_cost__: cost that is incurred if at least one customer is assigned to this facility
 * __customer_demands__: list of customer demands, indexed by customer ID
 * __assignment_costs__: 2D list describing the costs of assigning a __customer__ to a __facility__, assignment costs are accessed as instance['assignment_costs'][facility][customer] 
 * __best_cost__: cost of the globally optimal solution
 * __timeout__: timeout in seconds for the given instance

In all data structures, both customers and facilities are indexed from 0 (i.e., their IDs go as 0, 1, 2...).

# Notes to instance contents

## Global best solution

The instance files contain the costs of the globally optimal solutions in the __best_cost__ attribute. This information was added for your convenience so that you know the gap between yours and the optimal solution and may compare them visually (see the visualization tool README for more details). Note that you __must not__ use these values within the logic of your solver.

## Timeout

In order to make the evaluation of your homework possible, it is necessary to cap the available time for your solvers. Since instances are of different sizes, each is limited by a different timeout. Please respect the specified values. Solvers exceeding this limit by a larger margin will be terminated during the evaluation.

# Solution format

Your solver must produce a single JSON file containing one solution in the following required format:

 * The solution is a list, its length is the number of customers in the given instance
 * List indices are __customers__, values at these indices are __facilities__ assigned to the given customers

For example, the following list [0, 1, 0, 0, 1, 2, 2, 1, 0, 2, 1, 0, 2] would be a solution to a problem where:

 * There are 13 customers in the instance
 * 3 facilities are used, their IDs are 0, 1, and 2
 * E.g., customers with IDs 0, 5, and 9 are assigned to facilities 0, 2, and 2, respectively
