from .GreyWolfOptimizer import GWO
from sklearn.neighbors import KNeighborsClassifier
import numpy as np
import time
import random as rd


class MGWO(GWO):

    def __init__(self,
                 N_WOLVES=50,
                 MAX_ITERATIONS=100,
                 MAX_CONVERGENCE=10,
                 CROSSOVER_RATE=0.57,
                 OPTIMIZER_NAME='Memory-based Grey Wolf Optimizer',
                 BREAK_IF_CONVERGENCE=True,
                 FUNCTIONS={
                     'classifier': KNeighborsClassifier(),
                     'objective': 'max',
                     'transfer_binary_function': 's_shaped_f2',
                     # f1_macro, f1_weighted, recall_macro, recall_weighted, precision_macro, precision_weighted, roc_auc_score_macro, roc_auc_score_weighted
                     'fitness_metric': 'accuracy'
                 },
                 ):
        super().__init__(
            N_WOLVES=N_WOLVES,
            MAX_ITERATIONS=MAX_ITERATIONS,
            MAX_CONVERGENCE=MAX_CONVERGENCE,
            FUNCTIONS=FUNCTIONS,
            BREAK_IF_CONVERGENCE=BREAK_IF_CONVERGENCE,
        )
        self.optimizer['name'] = OPTIMIZER_NAME
        self.optimizer['params'].update({
            "CROSSOVER_RATE": CROSSOVER_RATE,
        })

    def fit(self, X_train, y_train, X_test, y_test):
        super().fit(X_train, y_train, X_test, y_test)
        self._IS_FIT = True
        return self

    def solve(self):
        if self._IS_FIT:
            MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
            N_WOLVES = self.optimizer['params']['N_AGENTS']

            start_time = time.time()
            # 1. Initialize agents
            agents, agents_fitness, pbest_agents, pbest_agents_fitness, best_fitness_previous = self._initialize_agents()
            # Initialize alpha, beta, and delta positions
            alpha_wolves, betha_wolves, delta_wolves = self._initialize_alpha_betha_delta_wolves()

            # 2. mGWO main loop
            convergence = 0
            for iteration in range(MAX_ITERATIONS):
                # 4. update wolves position
                agents = self.__update_wolves_position(
                    agents, pbest_agents, iteration, alpha_wolves, betha_wolves, delta_wolves)

                # evaluate fitness, update pbest, and update alpha betha and delta wolves
                for i in range(N_WOLVES):
                    # binarization and evaluate fitness
                    binary_wolf = self._standard_binarization_rule(
                        np.array([agents[i]])
                    )[0]
                    agents_fitness[i] = self._evaluate_fitness(binary_wolf)

                    # update pbest agents
                    if agents_fitness[i] > pbest_agents_fitness[i]:
                        pbest_agents[i] = agents[i].copy()
                        pbest_agents_fitness[i] = agents_fitness[i]

                    # Update alpha, beta, and delta positions
                    if agents_fitness[i] > alpha_wolves['fitness']:
                        alpha_wolves = {
                            'position': agents[i].copy(),
                            'fitness': agents_fitness[i]
                        }
                    elif agents_fitness[i] > betha_wolves['fitness']:
                        betha_wolves = {
                            'position': agents[i].copy(),
                            'fitness': agents_fitness[i]
                        }
                    elif agents_fitness[i] > delta_wolves['fitness']:
                        delta_wolves = {
                            'position': agents[i].copy(),
                            'fitness': agents_fitness[i]
                        }

                # binarization of best wolves
                alpha_wolf_position = [alpha_wolves['position']].copy()
                GBest = self._standard_binarization_rule(
                    np.array(alpha_wolf_position)
                )[0]
                GBest_fitness = alpha_wolves['fitness']

                # check convergence
                self.LIST_BEST_FITNESS.append(GBest_fitness)
                is_break, best_fitness_previous, convergence = self._check_convergence(
                    GBest_fitness, best_fitness_previous, convergence, iteration)
                if is_break and self.BREAK_IF_CONVERGENCE:
                    break

            end_time = time.time()
            # Get optimal features
            optimal_solution = {
                'features_subset': GBest,
                'selected_features': np.where(GBest == 1)[0],
                'optimal_n_features': len(np.where(GBest == 1)[0]),
                'best_fitness': GBest_fitness,
                'start_time_computation': start_time,
                'end_time_computation': end_time,
                'total_train_time_computation': self._calculate_total_training_time_computation(start_time, end_time)
            }
            return optimal_solution

        else:
            raise Exception('Please fit your dataset first!')

    def _initialize_agents(self):
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        UB = self.optimizer['params']['UB']
        LB = self.optimizer['params']['UB']
        N_FEATURES = self.N_FEATURES
        # Continuous positions in [lb, ub]
        agents = np.random.uniform(LB, UB, (N_AGENTS, N_FEATURES))
        agents_fitness = np.zeros(N_AGENTS)
        pbest_agents = agents.copy()
        pbest_agents_fitness = agents_fitness.copy()
        best_fitness_previous = -np.inf
        if self.OBJECTIVE == 'min':
            best_fitness_previous = np.inf
        return agents, agents_fitness, pbest_agents, pbest_agents_fitness, best_fitness_previous

    def __update_wolves_position(self, agents, pbest_agents, current_index_iteration, alpha_wolves, betha_wolves, delta_wolves):
        """
        Function for update wolves position
        """
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
        CROSSOVER_RATE = self.optimizer['params']['CROSSOVER_RATE']
        UB = self.optimizer['params']['UB']
        LB = self.optimizer['params']['LB']

        alpha_pos = alpha_wolves['position']
        betha_pos = betha_wolves['position']
        delta_pos = delta_wolves['position']

        # update a and k variable
        a = 2*(1-(current_index_iteration/MAX_ITERATIONS))
        k = 1 - (1*current_index_iteration/MAX_ITERATIONS)

        for idx_agent, agent in enumerate(agents):
            pbest_agent = pbest_agents[idx_agent]

            # apply memory gwo logic here
            if np.random.rand() < CROSSOVER_RATE:
                r1, r2 = np.random.rand(), np.random.rand()
                A1, C1 = 2 * a * r1 - a, 2 * r2
                D_alpha = np.abs(
                    C1 * alpha_pos - pbest_agent)
                X1 = alpha_pos - A1*D_alpha

                r1, r2 = np.random.rand(), np.random.rand()
                A2, C2 = 2 * a * r1 - a, 2 * r2
                D_betha = np.abs(
                    C2 * betha_pos - pbest_agent)
                X2 = betha_pos - A2*D_betha

                r1, r2 = np.random.rand(), np.random.rand()
                A3, C3 = 2 * a * r1 - a, 2 * r2
                D_delta = np.abs(
                    C3 * delta_pos - pbest_agent)
                X3 = delta_pos - A3*D_delta

                agents[idx_agent] = (X1+X2+X3)/3
            else:
                # find two wolves randomly
                random_wolf_1 = agents[rd.randint(0, N_AGENTS-1)].copy()
                random_wolf_2 = agents[rd.randint(0, N_AGENTS-1)].copy()
                agents[idx_agent] = pbest_agent + k * \
                    abs(random_wolf_1-random_wolf_2)

            # ensure new positions are within the bounds
            agents[idx_agent] = np.clip(
                agents[idx_agent], LB, UB)

        return agents
