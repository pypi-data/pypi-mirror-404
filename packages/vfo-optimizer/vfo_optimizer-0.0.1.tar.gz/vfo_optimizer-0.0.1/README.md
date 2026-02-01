# Van Fish Optimization (VFO) Algorithm

**Van Fish Optimization (VFO)** is a meta-heuristic optimization algorithm inspired by the unique migration behavior of the Pearl Mullet (*Alburnus tarichi*) living in Lake Van, Turkey. These fish swim against the current and jump over obstacles during migration, behaviours which VFO models to solve complex optimization problems.

Key features include:
*   **Directional Search:** Mimics swimming against the current towards a target.
*   **Local Escape:** Uses a jumping mechanism (Lévy flight) to escape local minima, modeled after fish jumping obstacles.
*   **Adaptive Parameters:** Uses energy-based and time-varying parameters to balance exploration and exploitation.

---

## Installation

You can install the package via pip:

```bash
pip install vfo-optimizer
```

---

## Usage

Here is a simple example of how to use VFO to minimize the Sphere function:

```python
import numpy as np
import VFO

# 1. Define your objective function (must take a 1D array and return a scalar)
def sphere_function(x):
    return np.sum(x**2)

# 2. Define problem bounds (lower and upper limits for each dimension)
dim = 10
bounds = [[-100, 100]] * dim

# 3. Initialize the VFO optimizer
optimizer = VFO.VFO(
    objective_func=sphere_function,
    bounds=np.array(bounds),
    num_agents=30,      # Population size
    max_iter=100,       # Maximum iterations
    dimension=dim,      # Problem dimension
    verbose=True        # Print progress
)

# 4. Run optimization
best_position, best_fitness, history = optimizer.optimize()

print(f"Best Fitness Value: {best_fitness}")
# print(f"Best Position: {best_position}")
```

---

## Hyperparameters

When initializing the `VFO` class, you can tune the following parameters:

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `objective_func` | `callable` | **Required** | The objective function you want to minimize. |
| `bounds` | `array` | **Required** | A list of `[min, max]` tuples for each dimension. |
| `dimension` | `int` | `2` | The number of dimensions (variables) in the problem. |
| `num_agents` | `int` | `30` | **Population Size (N).** Higher values check more areas but increase computation time. |
| `max_iter` | `int` | `100` | **Maximum Iterations.** How many times the population updates itself. |
| `stagnation_threshold`| `int` | `5` | **Jump Trigger.** If an agent doesn't improve for this many steps, it performs a Lévy flight to jump out of local minima. |
| `verbose` | `bool` | `False` | If `True`, prints the best fitness value at each iteration. |

---

## Theoretical Model

The algorithm mathematically models the fish behavior using three main components:

1.  **Position Update (Swimming):**
    Fish move towards the leader ($X_{best}$) but are affected by the current ($A$) and randomness ($B$).
    $$X_{new} = X_{current} + A \cdot (X_{best} - X_{current}) + B \cdot R$$

2.  **Adaptive Coefficients:**
    *   $A$ (Current Resistance): Decreases linearly from 2 to 0. Promotes exploration early on and exploitation later.
    *   $B$ (Randomness): Decreases over time to reduce random scattering as the target is approached.

3.  **Lévy Flight (Jumping):**
    If a fish (agent) cannot improve its position for a certain number of steps (`stagnation_threshold`), it assumes it is stuck at an obstacle (local minimum) and performs a long-distance jump using a Lévy distribution.

---
