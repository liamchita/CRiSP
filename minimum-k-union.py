import math, time, json
from itertools import combinations
from ortools.sat.python import cp_model

### RESULTS ###

def conversion(best_int):
    best_set = []
    for pos in range(best_int.bit_length()):
        if (best_int >> pos) & 1: # Uses an AND gate to check if the bit at position "pos" (0 <= pos < best_int.count()) is a one
            best_set.append(pos)

    return best_set


def print_formated(best_comb, best_set, n, k, time_taken, recipes, algorithm, optimal=None):

    if isinstance(best_set, int):
        best_set = conversion(best_set)

    print("")
    print(f"Results for {algorithm}:")
    if optimal is not None:
        print(optimal)
    print(f"""The best combination of {k} recipes found was: {[data["recipes"][m]["name"] for m in best_comb]}
The number of ingredients needed for this was {n} and they are: {[data["ingredients"][m]["name"] for m in best_set]}
It took {time_taken} to find this combination of {k} recipes in a list of {len(recipes)} recipes
""")


### INITIALISATION ###

k = 20

with open("dataset_small.json", encoding="utf-8") as d:
    data = json.load(d)
recipes = data["recipes"] # Keeps only the recipes and ignores ingridients and metadata

# Builds a list with one set per recipe. Each set holds the IDs of that recipe's ingredients
def CreateIngSet(recipes):
    return [set(rcp["ingredient_ids"]) for rcp in recipes] 

#Converts each recipe into a single integer with the form: 001001110... where each bit represents an ingredient whose ID is equal to the position of the bit from the rightmost bit. 1 if its present in the recipe and 0 if its not.
def CreateMasks(recipes):
    bitmasks = []
    for recipe in recipes:
        mask = 0
        for ing_id in recipe["ingredient_ids"]:
            mask |= 1 << ing_id # OR gate between the current mask (initally 0) and an integer whose only one is at the ingredients ID position (eg.: 0 | 000000010000000000000000 for ID = 17) 
        bitmasks.append(mask)
    return bitmasks


## --- BRUTE FORCE --- ##

def BruteForce(recipes, k):

    start = time.perf_counter()

    set_of_ing = CreateIngSet(recipes)
    best = math.inf # infinity
    best_set = None
    best_comb = None

    # Go through every group of k elements possible with numbers from 0 to n-1. No repeats and no reordering.
    for comb in combinations(range(len(set_of_ing)), k):  # "combination" returns a data type comb with the form (1, 3, 54, ...) where len(comb) = k and  0 <= numbers in comb < len(recipes)
        current_set = set()
        for n in comb:
            current_set = current_set | set_of_ing[n] # Does union to create a set containing every element in every set of ingredients for that recipe
        
        if len(current_set) < best: # Checks if the length of this set is less than the current least
            best_comb = comb
            best_set = current_set
            best = len(current_set) # Updates any variable required
        
    elapsed = time.perf_counter() - start
        
    return best_comb, best_set, best, k, elapsed

#print_formated(*BruteForce(recipes, k), recipes, "Brute Force")


## --- BRUTE FORCE (BITMASK) --- ##

def BruteForceBitmask(recipes, k):

    start = time.perf_counter()
    
    bitmasks = CreateMasks(recipes)
    best = math.inf
    best_int = None
    best_comb = None

    for comb in combinations(range(len(recipes)), k):
        current = 0
        for n in comb:
            current = current | bitmasks[n]

        if current.bit_count() < best:
            best_comb = comb
            best_int = current
            best = current.bit_count()

    elapsed = time.perf_counter() - start

    return best_comb, best_int, best, k, elapsed

#print_formated(*BruteForceBitmask(recipes, k), recipes, "Brute Force (BITMASK)")


## --- BRANCH AND BOUND --- ##

def BranchAndBound(recipes, k, best=None, best_int=None, best_comb=None):

    start = time.perf_counter()

    bitmasks = CreateMasks(recipes)
    n = len(recipes)

    if best is None:
        best = math.inf
        best_int = None
        best_comb = None

    def RecursiveSearch(start, chosen, current):
        nonlocal best, best_int, best_comb

        # If the current number of ingredients in the current "set" is greater than out best we just skip this branch completely
        if current.bit_count() >= best: 
            return

        # If the the number of elements in the group is equal to k and it has reached this part (hasnt been skipped by the previous check) it means that it is the best solution found so far
        if len(chosen) == k:
            best_int = current
            best_comb = chosen
            best = current.bit_count()
            return

        # It will only reach this part of the function if the number of elements in the group is not euqal to k (not reached a leaf in the tree) and its number of ingridient is still less than the best solution so far
        for i in range(start, n):
            RecursiveSearch(i + 1, chosen + [i], current | bitmasks[i]) # Calls the function recursively starting from the next index and adding a arecipe to the group

    # Starting parameters. Starting with a preset group (chosen) gotten from a different approach such as greedy can greatly improve the efficiency of the BranchAndBound as it already starts with a good guess and even more of the branches are skipped directly
    RecursiveSearch(0, [], 0)

    elapsed = time.perf_counter() - start

    return best_comb, best_int, best, k, elapsed

#print_formated(*BranchAndBound(recipes, k), recipes, "Branch & Bound")


## --- GREEDY --- ##

def Greedy(recipes, k, masks=None, first=None):

    start = time.perf_counter()

    if masks is None:
        masks = CreateMasks(recipes)
    
    best_comb = []
    best_int = 0
    x = 0

    if first is not None:
        best_comb.append(first)
        best_int = masks[first]
        x = 1

    for _ in range(k - x):
        smallest = math.inf
        
        for i in range(len(recipes)):
            if i in best_comb: # Skips recipes already chosen
                continue

            n = (~best_int & masks[i]).bit_count() # Number of ingridients in recipe i which aren't already needed (AND with NOT current)

            if n < smallest:
                smallest, index = n, i

        best_comb.append(index)
        best_int = best_int | masks[index]
    
    best = best_int.bit_count()

    elapsed = time.perf_counter() - start

    return best_comb, best_int, best, k, elapsed
        
def MultiStartGreedy(recipes, k): # Starts the Greedy algorith from every recipe in recipes to improve its accuracy

    start = time.perf_counter()

    masks = CreateMasks(recipes)
    optimal_int = 0
    optimal_comb = None
    min_num = math.inf

    for i in range(len(recipes)):
        combination, integer, num_ing, _, _ = Greedy(recipes, k, masks, i)
        if num_ing < min_num:
            optimal_int = integer
            optimal_comb = combination
            min_num = num_ing

    elapsed = time.perf_counter() - start

    return optimal_comb, optimal_int, min_num, k, elapsed

#print_formated(*Greedy(recipes, k), recipes, "Greedy")
#print_formated(*MultiStartGreedy(recipes, k), recipes, "Mutli-start Greedy")


## --- GREEDY + BaB --- ##

def MutliStartGreedyBaB(recipes, k):

    start = time.perf_counter()

    comb, integer, num, _, _ = MultiStartGreedy(recipes, k)
    comb, integer, num, _, _ = BranchAndBound(recipes, k, num, integer, comb)
    
    elapsed = time.perf_counter() - start

    return comb, integer, num, k, elapsed

#print_formated(*MutliStartGreedyBaB(recipes, k), recipes, "Mutli-start Greedy + Branch & Bound")


## --- GREEDY (LOCAL SEARCH) ---

def GreedyLocalSearch(recipes, k):

    start = time.perf_counter()

    masks = CreateMasks(recipes)
    best_comb, best_int, min_num, _, _ = MultiStartGreedy(recipes, k)
    improved = True

    while improved:
        improved = False

        for i in range(k):
            rest = 0 # Rest contains the bits (ingredients) that would be needed if recipe i is removed from the group
            for j in range(k):
                if j == i:
                    continue
                rest = rest | masks[best_comb[j]]

            for j in range(len(recipes)): # Cycles through the entire recipe list swapping each of them with the recipe to be removed, if it finds an improvement it swaps them and updates all the variables required
                if j in best_comb:
                    continue

                if (rest | masks[j]).bit_count() < min_num:
                    best_int = rest | masks[j]
                    best_comb[i] = j
                    min_num = (rest | masks[j]).bit_count()
                    improved = True

    elapsed = time.perf_counter() - start

    return  best_comb, best_int, min_num, k, elapsed

#print_formated(*GreedyLocalSearch(recipes, k), recipes, "Greedy Local Search")

## --- INTEGER LINEAR PROGRAMMING ---

def ILP(recipes, k):
    global optimal

    start = time.perf_counter()

    masks = CreateMasks(recipes)
    n = len(masks)
    best_comb = []

    model = cp_model.CpModel() #Creates a blank model
    x = [model.NewBoolVar(f"x{r}") for r in range(n)] #Creates a list of boolean variables for each recipe
    y = [model.NewBoolVar(f"y{i}") for i in range(len(data["ingredients"]))] # Creates a list of boolean variables for each ingridient

    model.Add(sum(x) == k) # Adds a rule to the model saying that the sum of all the elemetns in x must be equal to k. Since elements in x can only be 1 or 0, it is basically saying that the amount of elements in x (the recipes) must be equal to k since if an element in x = 1 it means that that element is ticked

    for i in range(n):
        for ing_id in recipes[i]["ingredient_ids"]: # Goes through all the elements of each recipe in the "ingridients" category (basically all the ingridients in each recipe) and creates a rule for each ingredient in the recipe  saying that if recipe i is ticked then that ingredient (element in y) must also be ticked. Basically making it that if a recipe is ticked then all its ingredients must also be.
            model.Add(x[i] <= y[ing_id])

    model.Minimize(sum(y)) #Set the goal; minimize the sum of y. Again since y only has boolean elements (1 or 0) it is minimising the total amount of ingridients ticked

    
    solver = cp_model.CpSolver() # Sets the solver 
    solver.parameters.max_time_in_seconds = 120 # Sets a time limit for the solver
    status = solver.Solve(model) # Contains a flag explaining the outcome of the solver: OPTIMAL/FEASABLE/INFEASABLE/MODEL_INVALID/UNKNOWN

    for i in range(len(x)): # Creates the best combination list by checking what elements in x (recipes) have been solved to be ticked (x[recipe] = 1) 
        if solver.Value(x[i]) == 1:
            best_comb.append(i)

    best_int = 0
    for recipe in best_comb:
        best_int |= masks[recipe]

    best = best_int.bit_count()

    if status == cp_model.OPTIMAL: #Uses the flags to see if it has found the optimal answer
        optimal = "This is the optimal solution"
    elif status == cp_model.FEASIBLE:
        optimal = "This is not proven to be the optimal solution"
    else:
        optimal = "UNKNOWN"
    
    elapsed = time.perf_counter() - start

    return  best_comb, best_int, best, k, elapsed

#print_formated(*ILP(recipes, k), recipes, "Integer Linear Programming", optimal)