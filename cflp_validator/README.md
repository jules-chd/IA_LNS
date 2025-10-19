# Solution validator

The provided utility functions allow you to validate the correctness of your solutions. You may run the script as follows:

```
python3 validator.py <path-to-instance-file-JSON> <path-to-solution-file-JSON> <MODE>
```

__MODE__ is either "VALIDATE" or "COST". The first option check solution feasibility, i.e., whether capacity constraints 
have been met for all facilities and whether each customer is assigned to a facility. The second option calculates cost 
of the solution (with a 10k infeasibility penalty for each unassigned customer).
