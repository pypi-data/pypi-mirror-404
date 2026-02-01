import numpy as np
import math

class VFO:
    """
    Van Fish Optimization (VFO) algorithm implementation.
    
    Based on Van Fish Optimization (VFO) context:
    - Biological Inspiration: Migration behavior of Van Fish (Alburnus tarichi).
    - Features: Directional search (current resistance), local minimum escape (obstacle jumping),
      swarm leadership, and target-oriented movement.
    """
    
    def __init__(self, objective_func, bounds, num_agents=30, max_iter=100, dimension=2, stagnation_threshold=5, verbose=False):
        """
        Initialize VFO algorithm.
        
        Args:
            import numpy as np
            import math


            class VFO:
                """
                Van Fish Optimization (VFO) algorithm implementation.
    
                Based on Van Fish Optimization (VFO) context:
                - Biological Inspiration: Migration behavior of Van Fish (Alburnus tarichi).
                - Features: Directional search (current resistance), local minimum escape (obstacle jumping),
                  swarm leadership, and target-oriented movement.
                """
    
                def __init__(self, objective_func, bounds, num_agents=30, max_iter=100, dimension=2, stagnation_threshold=5, verbose=False):
                    """
                    Initialize VFO algorithm.
        
                    Args:
                        objective_func (callable): The objective function to minimize.
                        bounds (list of tuples or array): The bounds for variables [(min, max), ...].
                        num_agents (int): Population size (N).
                        max_iter (int): Maximum number of iterations.
                        dimension (int): Dimension of the problem (d).
                        stagnation_threshold (int): Variance threshold to trigger Levy flight jumps.
                        verbose (bool): Whether to print progress at each iteration.
                    """
                    self.objective_func = objective_func
                    self.bounds = np.array(bounds)
                    self.dim = dimension
                    self.n = num_agents
                    self.max_iter = max_iter
                    self.stagnation_threshold = stagnation_threshold
                    self.verbose = verbose
        
                    # Determine strict bounds for clipping
                    if self.bounds.shape == (self.dim, 2):
                        self.lb = self.bounds[:, 0]
                        self.ub = self.bounds[:, 1]
                    else:
                        # Assume same bounds for all dims if shape is (2,) or (1, 2)
                        # This handles cases where user passes e.g. [-100, 100] for all dims
                        if len(self.bounds) == 2 and self.bounds.ndim == 1:
                             self.lb = np.full(self.dim, self.bounds[0])
                             self.ub = np.full(self.dim, self.bounds[1])
                        else:
                             self.lb = self.bounds[:, 0]
                             self.ub = self.bounds[:, 1]

                def _levy_flight(self, beta=1.5):
                    """
                    Generates a step based on Levy distribution using Mantegna's algorithm.
                    """
                    sigma_u = (math.gamma(1 + beta) * math.sin(math.pi * beta / 2) / 
                               (math.gamma((1 + beta) / 2) * beta * 2 ** ((beta - 1) / 2))) ** (1 / beta)
                    sigma_v = 1
        
                    u = np.random.normal(0, sigma_u, self.dim)
                    v = np.random.normal(0, sigma_v, self.dim)
        
                    step = u / (np.abs(v) ** (1 / beta))
                    return step

                def optimize(self):
                    """
                    Execute the optimization process.
        
                    Returns:
                        X_best (array): Best position found.
                        f_best (float): Best fitness value found.
                        history (list): Convergence history.
                    """
                    # 1. Initialize population X_i within bounds
                    X = np.random.uniform(self.lb, self.ub, (self.n, self.dim))
        
                    # 2. Calculate fitness for all
                    fitness = np.array([self.objective_func(ind) for ind in X])
        
                    # 3. Find initial best
                    best_idx = np.argmin(fitness)
                    X_best = X[best_idx].copy()
                    f_best = fitness[best_idx]
        
                    # Init Stagnation counters (implicitly part of logic flow)
                    stagnation_counter = np.zeros(self.n)
        
                    # Enerji modeli parametreleri (Section 3.2 reference)
                    # E_i is initialized, though Algorithm 1 doesn't explicitly loop it, 
                    # we track it to stay true to the "Energy Model" feature.
                    E = np.full(self.n, 100.0) # Initial energy could be arbitrary or 100
                    C = 1.0 # Cost per step
                    G = 5.0 # Gain per improvement
        
                    history = []
        
                    # 5. Iteration loop
                    for t in range(1, self.max_iter + 1):
                        # Update adaptive parameters
                        # A(t) = 2 * (1 - t/MaxIter) -- Akıntı direnci
                        A = 2 * (1 - t / self.max_iter)
            
                        # B(t) = 1 - 0.9 * t/MaxIter -- Rastgelelik
                        B = 1 - 0.9 * t / self.max_iter
            
                        for i in range(self.n):
                            old_X = X[i].copy()
                            old_fit = fitness[i]
                
                            # Equation 3.1: Position Update
                            # X_i(t+1) = X_i(t) + A(t)*(X_best(t) - X_i(t)) + B(t)*R
                            R = np.random.randn(self.dim) # Standard normal distribution
                
                            # Calculate candidate position
                            X_new = X[i] + A * (X_best - X[i]) + B * R
                
                            # 17. Clip to bounds
                            X_new = np.clip(X_new, self.lb, self.ub)
                
                            # Check improvement separately to handle stagnation/energy
                            # Note: Algo 1 implies direct update, then "update fitness". 
                            # Metaheuristics usually evaluate candidate. 
                            # Given "A(t) * (X_best - X_i)", they are pulled to best.
                            # We will accept the move to follow standard swarm dynamics (like PSO)
                            # unless it's strictly greedy. The phrasing "X_i <- ..." usually means update.
                            new_fit = self.objective_func(X_new)
                
                            if new_fit < old_fit:
                                X[i] = X_new
                                fitness[i] = new_fit
                                stagnation_counter[i] = 0
                                E[i] = E[i] - C + G # Gain energy
                            else:
                                # If no improvement, do we move?
                                X[i] = X_new
                                fitness[i] = new_fit
                                stagnation_counter[i] += 1
                                E[i] = E[i] - C # Lose energy
                
                            # 13. Stagnation Check & Levy Flight
                            # If stagnation counter > threshold: X_i = X_i + Levy(lambda)
                            if stagnation_counter[i] > self.stagnation_threshold:
                                levy_step = self._levy_flight(beta=1.5)
                                # Scale levy step, typically 0.01 * (ub-lb) * step
                                # Using a scaling factor alpha related to problem scale
                                alpha = 0.01
                                step_size = alpha * (self.ub - self.lb) * levy_step
                    
                                X[i] = X[i] + step_size
                                # Re-clip
                                X[i] = np.clip(X[i], self.lb, self.ub)
                                # Re-eval
                                fitness[i] = self.objective_func(X[i])
                                # Reset counter after jump
                                stagnation_counter[i] = 0
            
                        # 21. Update X_best
                        current_best_idx = np.argmin(fitness)
                        if fitness[current_best_idx] < f_best:
                            f_best = fitness[current_best_idx]
                            X_best = X[current_best_idx].copy()
            
                        history.append(f_best)
            
                        # Print progress if verbose is enabled
                        if self.verbose:
                            print(f"Iter {t}/{self.max_iter}, Best Fitness: {f_best:.6f}")

                    return X_best, f_best, history