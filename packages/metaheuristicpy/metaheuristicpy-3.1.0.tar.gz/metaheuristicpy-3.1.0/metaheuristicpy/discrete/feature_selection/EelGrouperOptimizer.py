from .BaseMetaFeatureSelection import BaseMetaheuristics
from sklearn.neighbors import KNeighborsClassifier
import numpy as np
import time
import random as rd
import math


class EGO(BaseMetaheuristics):

    def __init__(self,
                 N_EELS=30,
                 MAX_ITERATIONS=100,
                 MAX_CONVERGENCE=10,
                 OPTIMIZER_NAME='Eel and Grouper Optimizer',
                 BREAK_IF_CONVERGENCE=True,
                 FUNCTIONS={
                     'classifier': KNeighborsClassifier(),
                     'objective': 'max',
                     'transfer_binary_function': 's_shaped_f2',
                     # f1_macro, f1_weighted, recall_macro, recall_weighted, precision_macro, precision_weighted, roc_auc_score_macro, roc_auc_score_weighted
                     'fitness_metric': 'accuracy'
                 },
                 ):
        """
        Eel and Grouper Optimizer (EGO)
        - Inspiration: Interaction and Foraging Strategy of Eels and Groupers in Marine Ecosystems
        """
        super().__init__(
            N_AGENTS=N_EELS,
            MAX_ITERATIONS=MAX_ITERATIONS,
            MAX_CONVERGENCE=MAX_CONVERGENCE,
            FUNCTIONS=FUNCTIONS,
            BREAK_IF_CONVERGENCE=BREAK_IF_CONVERGENCE,
        )
        self.optimizer['name'] = OPTIMIZER_NAME

    def fit(self, X_train, y_train, X_test, y_test):
        super().fit(X_train, y_train, X_test, y_test)
        self._IS_FIT = True
        return self

    def solve(self):
        if self._IS_FIT:
            MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']

            start_time = time.time()
            # 1. initialize particle population
            agents, agents_fitness, best_fitness_previous = self._initialize_agents()

            # 2. Divide eel group into Xprey, Xgrouper, and Xeel
            XPrey, XGrouper, XEel = self.__divide_eel_grouper(agents)

            # 5. EGO main loop
            convergence = 0
            for iteration in range(MAX_ITERATIONS):

                # 6. update a and starvation rate
                params = self.__update_parameters(iteration)

                # 7. update eel position and simultaneously update the fitness
                agents, agents_fitness, XGrouper = self.__update_eel_position(
                    agents, agents_fitness, XPrey, XGrouper, XEel, params)

                # 8. update XGrouper
                XPrey = self.__update_XPrey(agents, agents_fitness)

                # binarization of XGrouper
                # GBest = self._standard_binarization_rule(
                #     np.array([XGrouper_position])
                # )[0]
                GBest = XGrouper['position']
                GBest_fitness = XGrouper['fitness']

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

    def __update_parameters(self, current_index_iteration):
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
        params = {
            'a': 2 - 2 * (current_index_iteration/MAX_ITERATIONS),
            'starvation_rate': 100 * (current_index_iteration/MAX_ITERATIONS)
        }
        return params

    def __generate_random_agent(self, agents):
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        random_agent = agents[rd.randint(0, N_AGENTS-1)].copy()
        return random_agent

    def __divide_eel_grouper(self, agents):
        """
        Bagi agents ke dalam tiga kelompok: 
        - XPrey (solusi terbaik), 
        - XGrouper, 
        - XEel
        """
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        N_FEATURES = self.N_FEATURES
        XPrey = {
            'position': agents[rd.randint(0, N_AGENTS-1)].copy(),
            'fitness': -np.inf
        }
        XGrouper = {
            'position': agents[rd.randint(0, N_AGENTS-1)].copy(),
            'fitness': -np.inf
        }
        XEel = {
            'position': agents[rd.randint(0, N_AGENTS-1)].copy(),
            'fitness': -np.inf
        }
        return XPrey, XGrouper, XEel

    def __update_eel_position(self, agents, agents_fitness, XPrey, XGrouper, XEel, params):
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        LB = self.optimizer['params']['LB']
        UB = self.optimizer['params']['UB']
        a = params['a']
        starvation_rate = params['starvation_rate']

        # 7. update position based on Grouper and Eel
        for i in range(N_AGENTS):

            r1 = np.random.rand()
            r2 = np.random.rand()
            r3 = (a - 2) * r1 + 2
            r4 = 100 * np.random.rand()
            b = a * r2
            C1 = 2 * a * r1 - a  # Coefficient for Grouper update
            C2 = 2 * r2  # Coefficient for Eel update

            # update agent position based on grouper
            X_rand = self.__generate_random_agent(agents)
            D_grouper = abs(agents[i] - C2 * X_rand)
            agents[i] = X_rand + C1 * D_grouper

            # update XEeel position
            if r4 <= starvation_rate:
                XEel['position'] = C2*XGrouper['position'].copy()
            else:
                XEel['position'] = C2 * self.__generate_random_agent(agents)

            # update variable X1 and X2
            Distance2Eel = abs(XEel['position'] - XPrey['position'])
            X_1 = math.exp(b*r3) * math.sin(2*math.pi*r3) * C1 * \
                Distance2Eel + XEel['position']

            Distance2Grouper = abs(XGrouper['position'] - XPrey['position'])
            X_2 = XGrouper['position'] + C1 * Distance2Grouper

            if np.random.rand() < 0.5:
                agents[i] = (0.8*X_1 + 0.2*X_2)/2
            else:
                agents[i] = (0.2*X_1 + 0.8*X_2)/2

            # 8. apply boundaries clip: make sure no search agents leave the search space area
            agents[i] = np.clip(
                agents[i], LB, UB)

            # update XGrouper (best search agent)
            continous_agent_position = [agents[i]].copy()
            binary_agent = self._standard_binarization_rule(
                continous_agent_position)[0]
            agents_fitness[i] = self._evaluate_fitness(binary_agent)
            if agents_fitness[i] > XGrouper['fitness']:
                XGrouper = {
                    'position': agents[i].copy(),
                    'fitness': agents_fitness[i]
                }

        return agents, agents_fitness, XGrouper

    def __update_XPrey(self, agents, agents_fitness):
        best_agent, best_fitness = self._retrieve_best_agent(
            agents, agents_fitness)
        XPrey = {
            'position': best_agent.copy(),
            'fitness': best_fitness
        }
        return XPrey
