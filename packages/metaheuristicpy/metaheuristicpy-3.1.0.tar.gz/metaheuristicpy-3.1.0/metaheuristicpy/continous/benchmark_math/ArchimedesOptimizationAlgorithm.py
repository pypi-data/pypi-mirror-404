from .BaseMetaPy import BaseMetaPy
from .Utils import Utils
import random as rd
import numpy as np
import math


class AOA(BaseMetaPy, Utils):

    def __init__(self,
                 N_OBJECTS=15,
                 MAX_ITERATIONS=200,
                 MAX_KONVERGEN=15,
                 C1=2,
                 C2=6,
                 C3=2,
                 C4=0.5,
                 EXPLORATION_RATE=0.5,
                 OPTIMIZER_NAME='Archimedes Optimization Algorithm',
                 FUNCTIONS={
                     'name': 'sphere',
                     'dimension': 15,
                     'lowerbound': -100,
                     'upperbound': 100,
                     'objective': 'min'
                 },
                 ):
        super().__init__(
            N_AGENTS=N_OBJECTS,
            MAX_ITERATIONS=MAX_ITERATIONS,
            MAX_KONVERGEN=MAX_KONVERGEN,
            FUNCTIONS=FUNCTIONS,
            DROP_KEY_AGENTS=None,
        )
        self.optimizer['name'] = OPTIMIZER_NAME
        self.optimizer['params'].update({
            "C1": C1,
            "C2": C2,
            "C3": C3,
            "C4": C4,
            "EXPLORATION_RATE": EXPLORATION_RATE,
        })

    def solve(self):
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']

        best_agent = None
        best_fitness_old = float("-inf")

        # initialize agents
        # 1. initialize agents
        agents = self._initialize_agents()
        agents = self.__initialize_objects_properties(agents)

        # 2. evaluate fitness and select the best object
        agents = self._evaluate_fitness(agents)
        best_object = self._retrieve_best_agent(agents)
        self.LIST_BEST_FITNESS.append(best_object['fitness'])

        # 3. Optimization Process
        konvergen = 0
        for idx_iteration in range(MAX_ITERATIONS):
            # 4. update object position
            agents = self.__update_object_position(
                agents, best_object, idx_iteration)

            # 5. Evaluate object fitness
            agents = self._evaluate_fitness(agents)

            # 6. select object with best fitness
            best_object = self._retrieve_best_agent(agents)

            # 6. check konvergensi
            is_break, best_fitness_old, konvergen = self._check_convergence(
                agents, best_fitness_old, konvergen, idx_iteration)
            best_agent = best_object
            if is_break:
                break

        self._IS_SOLVE = True

        return best_agent

    def __initialize_objects_properties(self, agents):
        """
        Function for initialize object densities, volume, and acceleration
        """
        N_DIMENSION = self.optimizer['params']['FUNCTIONS']['dimension']
        LOWER_BOUND = self.optimizer['params']['FUNCTIONS']['lowerbound']
        UPPER_BOUND = self.optimizer['params']['FUNCTIONS']['upperbound']
        for idx_agent, agent in enumerate(agents):
            agents[idx_agent].update({
                'densities': np.array([np.random.random() for _ in range(N_DIMENSION)]),
                'volume': np.array([np.random.random() for _ in range(N_DIMENSION)]),
                'acceleration': np.array([
                    np.random.random() * (UPPER_BOUND - LOWER_BOUND) + LOWER_BOUND
                    for d in range(N_DIMENSION)
                ]
                ),
            })
        return agents

    def __update_object_position(self, agents, best_object, iteration):
        def normalize_acceleration(vector_acceleration):
            U = 0.9
            L = 0.1
            normalize_vector = U * ((vector_acceleration - np.min(vector_acceleration))/(
                np.max(vector_acceleration) - np.min(vector_acceleration))) + L
            return normalize_vector

        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
        EXPLORATION_RATE = self.optimizer['params']['EXPLORATION_RATE']
        C1 = self.optimizer['params']['C1']
        C2 = self.optimizer['params']['C2']
        C3 = self.optimizer['params']['C3']
        C4 = self.optimizer['params']['C4']

        for idx_agent, agent in enumerate(agents):
            # update density and volume of each object
            agents[idx_agent]['densities'] = agent['densities'] + np.random.random() * \
                (best_object['densities'] - agent['densities'])
            agents[idx_agent]['volume'] = agent['volume'] + \
                np.random.random() * (best_object['volume'] - agent['volume'])

            # update transfer and density decreasing factors TF and d
            TF = math.exp((iteration - MAX_ITERATIONS)/MAX_ITERATIONS)
            d = math.exp((MAX_ITERATIONS-iteration) /
                         MAX_ITERATIONS) - (iteration/MAX_ITERATIONS)

            # check exploration or exploitation based on TF
            if TF <= EXPLORATION_RATE:
                # exploration
                # get random object
                random_agent = self.__generate_random_agent(agents, agent)

                # update acceleration
                agents[idx_agent]['acceleration'] = (random_agent['densities'] + random_agent['volume'] *
                                                     random_agent['acceleration'])/(agents[idx_agent]['densities'] * agents[idx_agent]['volume'])

                # normalize acceleration
                agents[idx_agent]['acceleration'] = normalize_acceleration(
                    agents[idx_agent]['acceleration'])

                # update position
                agents[idx_agent]['position'] = agent['position'] + C1 * np.random.random(
                ) * agent['acceleration'] * d * (random_agent['position'] - agent['position'])

            else:
                # exploitation

                # update acceleration
                agents[idx_agent]['acceleration'] = (best_object['densities'] + best_object['volume'] * best_object['acceleration'])/(
                    agents[idx_agent]['densities'] * agents[idx_agent]['volume'])

                # normalize acceleration
                agents[idx_agent]['acceleration'] = normalize_acceleration(
                    agents[idx_agent]['acceleration'])

                # update direction flag F
                P = 2 * np.random.random() - C4
                F = -1
                if P <= 0.5:
                    F = 1

                # update position
                T = C3 * TF
                agents[idx_agent]['position'] = best_object['position'] + F * C2 * np.random.random(
                ) * agent['acceleration'] * d * (T * best_object['position'] - agent['position'])

            # apply boundaries for each agent new position
            agents[idx_agent] = self._adjust_boundaries([agents[idx_agent]])[0]
        return agents

    def __generate_random_agent(self, agents, agent):
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        random_agent = agents[rd.randint(0, N_AGENTS-1)].copy()
        while random_agent['name'] == agent['name']:
            random_agent = agents[rd.randint(0, N_AGENTS-1)].copy()
        return random_agent
