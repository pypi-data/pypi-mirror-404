from .GreyWolfOptimizer import GWO
from sklearn.neighbors import KNeighborsClassifier
import numpy as np
import time
import random as rd
import math


class EEGWO(GWO):

    def __init__(self,
                 N_WOLVES=30,
                 MAX_ITERATIONS=100,
                 MAX_CONVERGENCE=10,
                 MODULATION_INDEX=1.5,
                 B1=0.1,
                 B2=0.9,
                 A_INITIAL=2,
                 A_FINAL=0,
                 OPTIMIZER_NAME='Exploration Enhanced Grey Wolf Optimizer',
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
            "MODULATION_INDEX": MODULATION_INDEX,
            "B1": B1,
            "B2": B2,
            "A_INITIAL": A_INITIAL,
            "A_FINAL": A_FINAL,
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
            agents, agents_fitness, best_fitness_previous = self._initialize_agents()
            # Initialize alpha, beta, and delta positions
            alpha_wolves, betha_wolves, delta_wolves = self._initialize_alpha_betha_delta_wolves()

            # 2. mGWO main loop
            convergence = 0
            for iteration in range(MAX_ITERATIONS):
                # 4. update wolves position
                agents = self.__update_wolves_position(
                    agents, iteration, alpha_wolves, betha_wolves, delta_wolves)

                # evaluate fitness and update alpha betha and delta wolves
                for i in range(N_WOLVES):
                    # binarization and evaluate fitness
                    binary_wolf = self._standard_binarization_rule(
                        np.array([agents[i]])
                    )[0]
                    agents_fitness[i] = self._evaluate_fitness(binary_wolf)

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
                GBest = self._standard_binarization_rule(
                    np.array([alpha_wolves['position']])
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

    def __update_wolves_position(self, agents, current_index_iteration, alpha_wolves, betha_wolves, delta_wolves):
        """
        Function for update wolves position
        """
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
        UB = self.optimizer['params']['UB']
        LB = self.optimizer['params']['LB']
        A_INITIAL = self.optimizer['params']['A_INITIAL']
        A_FINAL = self.optimizer['params']['A_FINAL']
        MODULATION_INDEX = self.optimizer['params']['MODULATION_INDEX']
        B1 = self.optimizer['params']['B1']
        B2 = self.optimizer['params']['B2']
        N_FEATURES = self.N_FEATURES

        alpha_pos = alpha_wolves['position']
        betha_pos = betha_wolves['position']
        delta_pos = delta_wolves['position']

        # update nilai a dan modulation index
        modulation = (MAX_ITERATIONS-current_index_iteration)/MAX_ITERATIONS
        a = A_INITIAL - (A_INITIAL - A_FINAL) * \
            math.pow(modulation, MODULATION_INDEX)

        # update wolves positions
        for idx_agent, agent in enumerate(agents):
            # hitung komponen alpha
            r1, r2 = np.random.rand(), np.random.rand()
            A1, C1 = 2 * a * r1 - a, 2 * r2
            D_alpha = np.abs(
                C1 * alpha_pos - agent)
            X1 = alpha_pos - A1*D_alpha

            # hitung komponen betha
            r1, r2 = np.random.rand(), np.random.rand()
            A2, C2 = 2 * a * r1 - a, 2 * r2
            D_betha = np.abs(
                C2 * betha_pos - agent)
            X2 = betha_pos - A2*D_betha

            # hitung komponen delta
            r1, r2 = np.random.rand(), np.random.rand()
            A3, C3 = 2 * a * r1 - a, 2 * r2
            D_delta = np.abs(
                C3 * delta_pos - agent)
            X3 = delta_pos - A3*D_delta

            # hitung posisi agent keseluruhan
            average_leader_wolves = (X1+X2+X3)/3
            agents[idx_agent] = average_leader_wolves.copy()

            # update posisi wolf ke-i dengan teknik EEGWO
            random_wolf_1 = agents[rd.randint(0, N_AGENTS-1)].copy()
            agents[idx_agent] = (
                B1 * np.random.uniform(0, 1) * average_leader_wolves
            ) + (B2 * np.random.uniform(0, 1) * abs(random_wolf_1 - agent)
                 )

            # ensure new positions are within the bounds
            agents[idx_agent] = np.clip(
                agents[idx_agent], LB, UB-np.random.rand())

        return agents
