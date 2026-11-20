# Minimum k-Union (Recipes & Ingredients)

Given a list of recipes, each made of some ingredients, find the **k recipes that together need the fewest different ingredients**. This is the *minimum k-union* problem.

The project includes several solvers, from exact (brute force, branch and bound, ILP) to fast approximations (greedy, local search), so you can compare speed against answer quality.

## Requirements

- Python 3.10 or newer (the code uses `int.bit_count()`)
- [OR-Tools](https://developers.google.com/optimization), used by the ILP solver

```bash
pip install ortools
```

## Files

| File | What it is |
|---|---|
| `minimum-k-union.py` | The script with all the algorithms |
| `dataset_small.json` | Small dataset |
| `dataset_big.json` | Big dataset |

## How to use it

You only edit three things in `minimum-k-union.py`, then run it:

### 1. Choose the dataset (line 35)

```python
with open("dataset_small.json", encoding="utf-8") as d:
```

Write `"dataset_small.json"` or `"dataset_big.json"`.

### 2. Choose k (line 33)

```python
k = 20
```

Set `k` to the number of recipes you want to pick.

> **Warning:** a higher `k` makes the exact algorithms (Brute Force, Brute Force Bitmask and, to a lesser degree, Branch and Bound) much slower. The number of combinations grows explosively, so a large `k` can mean **very long waiting times, or no answer at all**. With a high `k`, use Greedy, Multi-start Greedy, Greedy Local Search or ILP instead.

### 3. Choose the algorithm (uncomment its `print_formated` line)

Every algorithm has a commented-out `print_formated(...)` line under it. **Remove the `#` at the start of the line for the algorithm you want to run.** You can uncomment several to compare them.

| Algorithm | Line | Type | Notes |
|---|---|---|---|
| Brute Force | 80 | Exact | Tries every combination using Python sets. Slowest. |
| Brute Force (Bitmask) | 108 | Exact | Same idea, but uses bitmasks, so it is much faster. |
| Branch & Bound | 150 | Exact | Skips branches that can't beat the best answer found so far. |
| Greedy | 212 | Approximate | Very fast, but not always optimal. |
| Multi-start Greedy | 213 | Approximate | Runs Greedy from every recipe and keeps the best result. |
| Multi-start Greedy + Branch & Bound | 229 | Exact | Greedy gives Branch & Bound a good starting answer, so it prunes more. |
| Greedy Local Search | 266 | Approximate | Multi-start Greedy, then keeps swapping recipes while that helps. |
| Integer Linear Programming (ILP) | 317 | Exact* | Uses the OR-Tools CP-SAT solver with a 120 s time limit. |

\* ILP says in its output whether the solution is proven optimal or just the best found before the time limit.

For example, to run Branch & Bound, change line 150 from

```python
#print_formated(*BranchAndBound(recipes, k), recipes, "Branch & Bound")
```

to

```python
print_formated(*BranchAndBound(recipes, k), recipes, "Branch & Bound")
```

### 4. Run it

```bash
python minimum-k-union.py
```

## Example output

```
Results for Branch & Bound:
The best combination of 20 recipes found was: [...]
The number of ingredients needed for this was ... and they are: [...]
It took ... to find this combination of 20 recipes in a list of ... recipes
```

## Dataset format

The JSON files contain:

- `recipes`: a list of recipes, each with a `name` and `ingredient_ids`
- `ingredients`: a list of ingredients, each with a `name`. A recipe's `ingredient_ids` are positions in this list.
