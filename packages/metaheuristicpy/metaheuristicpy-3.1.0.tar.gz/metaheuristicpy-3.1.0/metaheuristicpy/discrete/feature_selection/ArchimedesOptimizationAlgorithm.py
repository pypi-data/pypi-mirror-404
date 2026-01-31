from .BaseMetaFeatureSelection import BaseMetaheuristics
from sklearn.neighbors import KNeighborsClassifier
import numpy as np
import time
import random as rd
import math


class AOA(BaseMetaheuristics):
    def __init__(self,
                 N_OBJECTS=50,
                 MAX_ITERATIONS=200,
                 MAX_CONVERGENCE=15,
                 C1=2,
                 C2=6,
                 C3=2,
                 C4=0.5,
                 EXPLORATION_RATE=0.5,
                 OPTIMIZER_NAME='Archimedes Optimization Algorithm',
                 BREAK_IF_CONVERGENCE=True,
                 FUNCTIONS={
                     'classifier': KNeighborsClassifier(),
                     'objective': 'max',
                     'transfer_binary_function': 's_shaped_f2',
                     # f1_macro, f1_weighted, recall_macro, recall_weighted, precision_macro, precision_weighted, roc_auc_score_macro, roc_auc_score_weighted
                     'fitness_metric': 'f1_macro'
                 },
                 ):
        """Archimedes Optimization Algorithm for optimizing features subset in Discrete Optimization

        Args:
            N_OBJECTS (int): number of object individual. Defaults to 50.
            MAX_ITERATIONS (int): maximum iterations. Defaults to 100.
            MAX_KONVERGEN (int): optimization will be stoped after MAX_KONVERGEN iterations. Defaults to 4.
            OPTIMIZER_NAME (str): your optimizer name will be. Defaults to 'Grey Wolf Optimizer'.
            FUNCTIONS (dict): objective function criteria.
                - Defaults to { 'classifier': KNeighborsClassifier(),  'objective': 'max', 'transfer_binary_function':'s_shaped_f2', 'metric': 'accuracy' # (f1_macro, f1_weighted, recall_macro, recall_weighted, precision_macro, precision_weighted, roc_auc_score_macro, roc_auc_score_weighted) }.
            BREAK_IF_CONVERGENCE (bool): flag if optimization will be stopped after MAX_KONVERGEN. Defaults to True.
        """
        super().__init__(
            N_AGENTS=N_OBJECTS,
            MAX_ITERATIONS=MAX_ITERATIONS,
            MAX_CONVERGENCE=MAX_CONVERGENCE,
            BREAK_IF_CONVERGENCE=BREAK_IF_CONVERGENCE,
            FUNCTIONS=FUNCTIONS
        )
        self.optimizer['name'] = OPTIMIZER_NAME
        self.optimizer['params'].update({
            'C1': C1,
            'C2': C2,
            'C3': C3,
            'C4': C4,
            'EXPLORATION_RATE': EXPLORATION_RATE,
        })

    def fit(self, X_train, y_train, X_test, y_test):
        super().fit(X_train, y_train, X_test, y_test)
        self._IS_FIT = True
        return self

    def solve(self):
        if self._IS_FIT:
            MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
            LB = self.optimizer['params']['LB']
            UB = self.optimizer['params']['UB']

            start_time = time.time()
            # 1. initialize agents and initialize objects properties
            agents, best_fitness_previous = self._initialize_agents()

            # 2. Evaluate fitness and select best object
            for idx_agent, agent in enumerate(agents['position']):
                binary_agent = self._standard_binarization_rule([
                    agent
                ])[0]

                fitness_score = self._evaluate_fitness(
                    binary_agent)
                agents['fitness'][idx_agent] = fitness_score

            best_agent = self._retrieve_best_agent(agents)
            self.LIST_BEST_FITNESS.append(best_agent['fitness'])

            # 3. Optimization Process
            convergence = 0
            for idx_iteration in range(MAX_ITERATIONS):

                # 4. update object position
                agents = self.__update_object_position(
                    agents, best_agent, idx_iteration)

                # 5. evaluate object fitness
                for idx_agent, agent_position in enumerate(agents['position']):
                    # apply boundaries
                    agents['position'][idx_agent] = np.clip(
                        agents['position'][idx_agent], LB, UB
                    )
                    # binarization and evaluate fitness
                    binary_object = self._standard_binarization_rule(
                        np.array([agent_position])
                    )[0]
                    agents['fitness'][idx_agent] = self._evaluate_fitness(
                        binary_object)

                # 6. select object with best fitness
                best_agent_current = self._retrieve_best_agent(agents)

                # 7. terapkan elitism: perbarui best_agent hanya jika fitness saat ini lebih baik
                # karena objektifnya adalah 'max', kita cari nilai yang lebih besar
                if (best_agent_current['fitness'] > best_agent['fitness']) and (self.OBJECTIVE == 'max'):
                    best_agent = best_agent_current.copy()

                # 8. check convergence

                # check convergence
                self.LIST_BEST_FITNESS.append(best_agent['fitness'])
                is_break, best_fitness_previous, convergence = self._check_convergence(
                    best_agent['fitness'], best_fitness_previous, convergence, idx_iteration)
                if is_break and self.BREAK_IF_CONVERGENCE:
                    break

            end_time = time.time()
            # Get optimal features
            binary_best_agent_position = self._standard_binarization_rule(
                np.array([best_agent['position']])
            )[0]
            optimal_solution = {
                'features_subset': binary_best_agent_position,
                'selected_features': np.where(binary_best_agent_position == 1)[0],
                'optimal_n_features': len(np.where(binary_best_agent_position == 1)[0]),
                'best_fitness': best_agent['fitness'],
                'start_time_computation': start_time,
                'end_time_computation': end_time,
                'total_train_time_computation': self._calculate_total_training_time_computation(start_time, end_time)
            }
            return optimal_solution

        else:
            raise Exception('Please fit your dataset first!')

    def _initialize_agents(self):
        agents_position, agents_fitness, best_fitness_previous = super()._initialize_agents()

        # initialize objects properties
        N_FEATURES = self.N_FEATURES
        N_OBJECTS = self.optimizer['params']['N_AGENTS']
        LB = self.optimizer['params']['LB']
        UB = self.optimizer['params']['UB']

        agents = {
            'position': agents_position,
            'densities': np.random.uniform(LB, UB, (N_OBJECTS, N_FEATURES)),
            'volume': np.random.uniform(LB, UB, (N_OBJECTS, N_FEATURES)),
            'acceleration': np.array([
                [np.random.random() * (UB - LB) + LB
                 for d in range(N_FEATURES)] for _ in range(N_OBJECTS)
            ]),
            'fitness': agents_fitness
        }

        return agents, best_fitness_previous

    def __update_object_position(self, agents, best_agent, iteration):
        def normalize_acceleration(vector_acceleration):
            U = 0.9
            L = 0.1
            normalize_vector = U * ((vector_acceleration - np.min(vector_acceleration))/(
                np.max(vector_acceleration) - np.min(vector_acceleration))) + L
            return normalize_vector

        LB = self.optimizer['params']['LB']
        UB = self.optimizer['params']['UB']
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
        EXPLORATION_RATE = self.optimizer['params']['EXPLORATION_RATE']
        C1 = self.optimizer['params']['C1']
        C2 = self.optimizer['params']['C2']
        C3 = self.optimizer['params']['C3']
        C4 = self.optimizer['params']['C4']
        agents_acceleration = agents['acceleration']

        # update transfer and density decreasing factors TF and d
        TF = math.exp((iteration - MAX_ITERATIONS)/MAX_ITERATIONS)
        d = math.exp((MAX_ITERATIONS-iteration) /
                     MAX_ITERATIONS) - (iteration/MAX_ITERATIONS)

        for idx_agent, agent in enumerate(agents['position']):
            # update density and volume of each object
            agents['densities'][idx_agent] = agents['densities'][idx_agent] + np.random.random() * \
                (best_agent['densities'] - agents['densities'][idx_agent])
            agents['volume'][idx_agent] = agents['volume'][idx_agent] + np.random.random() * \
                (best_agent['volume'] - agents['volume'][idx_agent])

            if TF <= EXPLORATION_RATE:
                # exploration
                # get random object
                random_agent = self.__generate_random_agent(agents, agent)

                # update acceleration
                agents['acceleration'][idx_agent] = (random_agent['densities'] + random_agent['volume'] *
                                                     random_agent['acceleration'])/(agents['densities'][idx_agent] * agents['volume'][idx_agent])

                # normalize acceleration
                agents['acceleration'][idx_agent] = normalize_acceleration(
                    agents['acceleration'][idx_agent])

                # update position
                agents['position'][idx_agent] = agent + C1 * np.random.random(
                ) * agents['acceleration'][idx_agent] * d * (random_agent['position'] - agent)
            else:
                # exploitation
                # update acceleration
                agents['acceleration'][idx_agent] = (best_agent['densities'] + best_agent['volume'] * best_agent['acceleration'])/(
                    agents['densities'][idx_agent] * agents['volume'][idx_agent])

                # normalize acceleration
                agents['acceleration'][idx_agent] = normalize_acceleration(
                    agents['acceleration'][idx_agent])

                # update direction flag F
                P = 2 * np.random.random() - C4
                F = -1
                if P <= 0.5:
                    F = 1

                # update position
                T = C3 * TF
                agents['position'][idx_agent] = best_agent['position'] + F * C2 * np.random.random(
                ) * agents['acceleration'][idx_agent] * d * (T * best_agent['position'] - agent)

            # # clipping agent new position
            # agents['position'][idx_agent] = np.clip(
            #     agents['position'][idx_agent], LB, UB)
        return agents

    def __generate_random_agent(self, agents, agent):
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        # randomly select new agent m where m!=indeks agent
        # It's important to select from the original list, not the one being updated in the loop.
        # This prevents picking a walrus that has already moved in the current iteration.
        idx_random_agent = rd.randint(0, N_AGENTS - 1)
        random_agent = {
            'position': agents['position'][idx_random_agent].copy(),
            'densities': agents['densities'][idx_random_agent].copy(),
            'volume': agents['volume'][idx_random_agent].copy(),
            'acceleration': agents['acceleration'][idx_random_agent].copy(),
            'fitness': agents['fitness'][idx_random_agent]
        }
        while np.array_equal(random_agent['position'], agent):
            idx_random_agent = rd.randint(0, N_AGENTS - 1)
            random_agent = {
                'position': agents['position'][idx_random_agent].copy(),
                'densities': agents['densities'][idx_random_agent].copy(),
                'volume': agents['volume'][idx_random_agent].copy(),
                'acceleration': agents['acceleration'][idx_random_agent].copy(),
                'fitness': agents['fitness'][idx_random_agent]
            }
        return random_agent

    def _retrieve_best_agent(self, agents):
        """Retrieve best agent from AOA initialization properties

        Args:
            agents (dictionary): contains position, densities, volume, acceleration in numpy array format for each object, and store each object's fitness value
        """
        agents_fitness = agents['fitness']
        idx_best_fitness = np.argmax(agents_fitness)
        best_agent = {
            'position': agents['position'][idx_best_fitness].copy(),
            'densities': agents['densities'][idx_best_fitness].copy(),
            'volume': agents['volume'][idx_best_fitness].copy(),
            'acceleration': agents['acceleration'][idx_best_fitness].copy(),
            'fitness': agents['fitness'][idx_best_fitness]
        }
        if self.OBJECTIVE == 'min':
            idx_best_fitness = np.argmin(agents_fitness)
            best_agent = {
                'position': agents['position'][idx_best_fitness].copy(),
                'densities': agents['densities'][idx_best_fitness].copy(),
                'volume': agents['volume'][idx_best_fitness].copy(),
                'acceleration': agents['acceleration'][idx_best_fitness].copy(),
                'fitness': agents['fitness'][idx_best_fitness]
            }
        return best_agent
