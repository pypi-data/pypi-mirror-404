from .BaseMetaFeatureSelection import BaseMetaheuristics
from sklearn.neighbors import KNeighborsClassifier
import numpy as np
import time
import random as rd
import math


class SMA(BaseMetaheuristics):
    def __init__(self,
                 N_SLIMES=50,
                 MAX_ITERATIONS=100,
                 MAX_CONVERGENCE=10,
                 Z_VALUE=0.57,
                 OPTIMIZER_NAME='Slime Mould Algorithm',
                 BREAK_IF_CONVERGENCE=True,
                 FUNCTIONS={
                     'classifier': KNeighborsClassifier(),
                     'objective': 'max',
                     'transfer_binary_function': 's_shaped_f2',
                     # f1_macro, f1_weighted, recall_macro, recall_weighted, precision_macro, precision_weighted, roc_auc_score_macro, roc_auc_score_weighted
                     'fitness_metric': 'f1_macro'
                 },
                 ):
        """Slime Mould Algorithm for optimizing features subset in Discrete Optimization

        Args:
            N_SLIMES (int): number of slime mould individual. Defaults to 50.
            MAX_ITERATIONS (int): maximum iterations. Defaults to 100.
            MAX_KONVERGEN (int): optimization will be stoped after MAX_KONVERGEN iterations. Defaults to 4.
            OPTIMIZER_NAME (str): your optimizer name will be. Defaults to 'Grey Wolf Optimizer'.
            FUNCTIONS (dict): objective function criteria.
                - Defaults to { 'classifier': KNeighborsClassifier(),  'objective': 'max', 'transfer_binary_function':'s_shaped_f2', 'metric': 'accuracy' # (f1_macro, f1_weighted, recall_macro, recall_weighted, precision_macro, precision_weighted, roc_auc_score_macro, roc_auc_score_weighted) }.
            BREAK_IF_CONVERGENCE (bool): flag if optimization will be stopped after MAX_KONVERGEN. Defaults to True.
        """
        super().__init__(
            N_AGENTS=N_SLIMES,
            MAX_ITERATIONS=MAX_ITERATIONS,
            MAX_CONVERGENCE=MAX_CONVERGENCE,
            BREAK_IF_CONVERGENCE=BREAK_IF_CONVERGENCE,
            FUNCTIONS=FUNCTIONS
        )
        self.optimizer['name'] = OPTIMIZER_NAME
        self.optimizer['params'].update({
            'Z_VALUE': Z_VALUE
        })

    def fit(self, X_train, y_train, X_test, y_test):
        super().fit(X_train, y_train, X_test, y_test)
        self._IS_FIT = True
        return self

    def solve(self):
        if self._IS_FIT:
            MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
            N_SLIMES = self.optimizer['params']['N_AGENTS']
            UB = self.optimizer['params']['UB']
            LB = self.optimizer['params']['LB']

            start_time = time.time()
            # 1. initialize agents
            agents, agents_fitness, best_fitness_previous = self._initialize_agents()

            # 1.1 initialize best and worst agent
            idx_best_agent = rd.randint(0, N_SLIMES-1)
            best_agent = {
                'position': agents[idx_best_agent].copy(),
                'fitness': agents_fitness[idx_best_agent].copy()
            }
            idx_worst_agent = rd.randint(0, N_SLIMES-1)
            worst_agent = {
                'position': agents[idx_worst_agent].copy(),
                'fitness': agents_fitness[idx_worst_agent].copy()
            }
            self.LIST_BEST_FITNESS.append(best_agent['fitness'])

            # 3. Optimization Process
            convergence = 0
            for idx_iteration in range(MAX_ITERATIONS):
                # hitung Weight vector
                weights_vector = self.__calculate_weights_vector(
                    agents, agents_fitness, best_agent, worst_agent)

                # update slime mould position
                agents = self.__update_slime_position(
                    agents, agents_fitness, weights_vector, best_agent, idx_iteration)

                # binarization rules and evaluate fitness
                for idx_slime, slime in enumerate(agents):
                    # memastikan bahwa hasil pembaharuan posisi slime berada dalam ruang solusi dan mengantisipasi semua nilai position menjadi 0
                    agents[idx_slime] = np.clip(
                        slime, LB, UB
                    )
                    binary_slime = self._standard_binarization_rule(
                        np.array([slime])
                    )[0]
                    agents_fitness[idx_slime] = self._evaluate_fitness(
                        binary_slime)

                # 6. retrieve best agents and worst agents
                best_agent_position_current, best_agent_fitness_current = self._retrieve_best_agent(
                    agents, agents_fitness)
                worst_agent_position_current, worst_agent_fitness_current = self._retrieve_worst_agent(
                    agents, agents_fitness)
                # best_agent = {
                #     'position': best_agent_position_current.copy(),
                #     'fitness': best_agent_fitness_current
                # }
                # worst_agent = {
                #     'position': worst_agent_position_current.copy(),
                #     'fitness': worst_agent_fitness_current
                # }

                # 7. terapkan elitism: perbarui best_agent hanya jika fitness saat ini lebih baik
                # karena objektifnya adalah 'max', kita cari nilai yang lebih besar
                if best_agent_fitness_current > best_agent['fitness']:
                    best_agent = {
                        'position': best_agent_position_current.copy(),
                        'fitness': best_agent_fitness_current
                    }
                if worst_agent_fitness_current < worst_agent['fitness']:
                    worst_agent = {
                        'position': worst_agent_position_current.copy(),
                        'fitness': worst_agent_fitness_current
                    }

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

    def __calculate_weights_vector(self, agents, agents_fitness, best_agent, worst_agent):
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        OBJECTIVE = self.OBJECTIVE
        weights_vector = list()
        slime_best_value = best_agent['fitness']
        slime_worst_value = worst_agent['fitness']

        # sort slime moulds base on their fitness values
        isDescendingOrder = True
        if OBJECTIVE == 'min':
            isDescendingOrder = False
        fitness = np.array([
            fitness for fitness in agents_fitness
        ])
        slimeMouldsWithFitness = list(zip(agents, fitness))
        slimeMouldsWithFitness.sort(
            key=lambda x: x[1], reverse=isDescendingOrder)
        sortedFitnessScores = [fitness for _,
                               fitness in slimeMouldsWithFitness]

        denominator = slime_best_value - \
            slime_worst_value + np.finfo(float).eps
        for idx_sorted_fitness_scores, fitness_score in enumerate(sortedFitnessScores):
            inside_log = (slime_best_value-fitness_score) / denominator
            w = rd.uniform(0, 1) * math.log2(inside_log+1)
            if idx_sorted_fitness_scores < math.ceil(N_AGENTS/2):
                # if S(i) ranks the first half of the population
                w = 1 + w
            else:
                w = 1 - w
            weights_vector.append(w)

        return np.array(weights_vector)

    def __update_slime_position(self, agents, agents_fitness, weights_vector, best_agent, iteration):
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
        N_DIMENSION = self.N_FEATURES
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        Z_VALUE = self.optimizer['params']['Z_VALUE']
        LOWER_BOUND = self.optimizer['params']['LB']
        UPPER_BOUND = self.optimizer['params']['UB']
        slime_best_value = best_agent['fitness']
        slime_best_position = best_agent['position']

        a = math.atanh(-(iteration/MAX_ITERATIONS)+np.finfo(float).eps)
        for idx_agent, agent in enumerate(agents):
            # update nilai p
            p = math.tanh(abs(agents_fitness[idx_agent]-slime_best_value))

            # update position
            r = np.random.random()
            if r < p:
                slime_mould_1 = agents[np.random.randint(
                    0, N_AGENTS)].copy()
                slime_mould_2 = agents[np.random.randint(
                    0, N_AGENTS)].copy()
                vb = np.array([rd.uniform(-a, a)
                               for _ in range(N_DIMENSION)])
                agents[idx_agent] = slime_best_position + (
                    vb * (
                        weights_vector[idx_agent] *
                        slime_mould_1 - slime_mould_2
                    )
                )
            elif r >= p:
                vc = np.array([(1 - (iteration/MAX_ITERATIONS))
                               for _ in range(N_DIMENSION)])
                agents[idx_agent] = vc * agent
            else:
                r = np.random.random()
                if r < Z_VALUE:
                    agents[idx_agent] = np.array([
                        r*(UPPER_BOUND - LOWER_BOUND)+LOWER_BOUND for _ in range(N_DIMENSION)
                    ])

            # r = np.random.random()
            # if r < Z_VALUE:
            #     agents[idx_agent] = np.array([
            #         r*(UPPER_BOUND - LOWER_BOUND)+LOWER_BOUND for _ in range(N_DIMENSION)
            #     ])
            # else:
            #     r = rd.uniform(0, 1)
            #     if r < p:
            #         vb = np.array([rd.uniform(-a, a)
            #                       for _ in range(N_DIMENSION)])
            #         # pick 2 random slime mould from the population
            #         slime_mould_1 = agents[np.random.randint(
            #             0, N_AGENTS)].copy()
            #         slime_mould_2 = agents[np.random.randint(
            #             0, N_AGENTS)].copy()
            #         agents[idx_agent] = slime_best_position + (
            #             vb * (
            #                 weights_vector[idx_agent] *
            #                 slime_mould_1 - slime_mould_2
            #             )
            #         )
            #     elif r >= p:
            #         vc = np.array([(1 - (iteration/MAX_ITERATIONS))
            #                        for _ in range(N_DIMENSION)])
            #         agents[idx_agent] = vc * agent

            # apply boundaries
            # agents[idx_agent] = np.clip(
            #     agents[idx_agent], LOWER_BOUND, UPPER_BOUND)

        return agents
