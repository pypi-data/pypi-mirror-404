from .BaseMetaPy import BaseMetaPy
from .Utils import Utils
import random as rd
import numpy as np
import math


class SMA(BaseMetaPy, Utils):

    def __init__(self,
                 N_SLIMES=50,
                 MAX_ITERATIONS=100,
                 MAX_KONVERGEN=50,
                 Z_VALUE=0.67,
                 FUNCTIONS={
                     'name': 'sphere',
                     'dimension': 5,
                     'lowerbound': -100,
                     'upperbound': 100,
                     'objective': 'min'
                 },
                 OPTIMIZER_NAME='Slime Mould Algorithm'
                 ):
        super().__init__(
            N_AGENTS=N_SLIMES,
            MAX_ITERATIONS=MAX_ITERATIONS,
            MAX_KONVERGEN=MAX_KONVERGEN,
            FUNCTIONS=FUNCTIONS,
            DROP_KEY_AGENTS=None
        )
        self.optimizer['name'] = OPTIMIZER_NAME
        self.optimizer['params'].update({
            'Z_VALUE': Z_VALUE
        })

    def solve(self):
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
        N_SLIMES = self.optimizer['params']['N_AGENTS']

        # 1. initialize agents
        agents = self._initialize_agents()
        best_agent = agents[rd.randint(0, N_SLIMES-1)].copy()
        worst_agent = agents[rd.randint(0, N_SLIMES-1)].copy()
        self.LIST_BEST_FITNESS.append(best_agent['fitness'])

        # 3. Optimization Process
        for idx_iteration in range(MAX_ITERATIONS):
            # hitung Weight vector
            weights_vector = self.__calculate_weights_vector(
                agents, best_agent, worst_agent)

            # update slime mould position
            agents = self.__update_slime_position(
                agents, weights_vector, best_agent, worst_agent, idx_iteration)

            # evaluate fitness
            agents = self._evaluate_fitness(agents)

            # 6. retrieve best agents and worst agents
            best_agent = self._retrieve_best_agent(agents)
            worst_agent = self._retrieve_worst_agent(agents)

            # 7. check konvergensi
            print('Iteration {}, Best Cost: {:.4f}'.format(
                idx_iteration, best_agent['fitness']))
            self.LIST_BEST_FITNESS.append(best_agent['fitness'])

        self._IS_SOLVE = True

        return best_agent

    def __calculate_weights_vector(self, agents, best_agent, worst_agent):
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        OBJECTIVE = self.optimizer['params']['FUNCTIONS']['objective']
        weights_vector = list()
        slime_best_value = best_agent['fitness']
        slime_worst_value = worst_agent['fitness']

        # sort slime moulds base on their fitness values
        isDescendingOrder = True
        if OBJECTIVE == 'min':
            isDescendingOrder = False
        fitness = np.array([
            agent_data['fitness'] for agent_data in agents
        ])
        slimeMouldsWithFitness = list(zip(agents, fitness))
        slimeMouldsWithFitness.sort(
            key=lambda x: x[1], reverse=isDescendingOrder)
        sortedFitnessScores = [fitness for _,
                               fitness in slimeMouldsWithFitness]

        for idx_sorted_fitness_scores, fitness_score in enumerate(sortedFitnessScores):
            inside_log = (slime_best_value-fitness_score) / \
                (slime_best_value-slime_worst_value)
            w = rd.uniform(0, 1) * math.log2(inside_log+1)
            if idx_sorted_fitness_scores < math.ceil(N_AGENTS/2):
                # if S(i) ranks the first half of the population
                w = 1 + w
            else:
                w = 1 - w
            weights_vector.append(w)

        return np.array(weights_vector)

    def __update_slime_position(self, agents, weights_vector, best_agent, worst_agent, iteration):
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
        N_DIMENSION = self.optimizer['params']['FUNCTIONS']['dimension']
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        Z_VALUE = self.optimizer['params']['Z_VALUE']
        LOWER_BOUND = self.optimizer['params']['FUNCTIONS']['lowerbound']
        UPPER_BOUND = self.optimizer['params']['FUNCTIONS']['upperbound']
        slime_best_value = best_agent['fitness']

        for idx_agent, agent in enumerate(agents):
            # update nilai p
            p = math.tanh(abs(agent['fitness']-slime_best_value))

            # update nilai vb dan vc
            a = math.atanh(-(iteration/MAX_ITERATIONS)+np.finfo(float).eps)
            vb = np.array([rd.uniform(-a, a) for _ in range(N_DIMENSION)])
            vc = np.array([(1 - (iteration/MAX_ITERATIONS))
                          for _ in range(N_DIMENSION)])

            # update position
            r = rd.uniform(0, 1)
            if r < p:
                # pick 2 random slime mould from the population
                slime_mould_1 = agents[np.random.randint(0, N_AGENTS)]
                slime_mould_2 = agents[np.random.randint(0, N_AGENTS)]
                agents[idx_agent]['position'] = agent['position'] + (
                    vb * (
                        weights_vector[idx_agent] *
                        slime_mould_1['position'] - slime_mould_2['position']
                    )
                )
            elif r >= p:
                agents[idx_agent]['position'] = vc * agent['position']
            else:
                r = np.random.random()
                if r < Z_VALUE:
                    agents[idx_agent]['position'] = np.array([
                        r*(UPPER_BOUND - LOWER_BOUND)+LOWER_BOUND for _ in range(N_DIMENSION)
                    ])
            # apply boundaries
            agents[idx_agent]['position'] = np.clip(
                agents[idx_agent]['position'], LOWER_BOUND, UPPER_BOUND)

        return agents
