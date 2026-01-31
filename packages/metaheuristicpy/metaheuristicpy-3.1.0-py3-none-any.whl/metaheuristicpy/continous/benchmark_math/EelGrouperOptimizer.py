from .BaseMetaPy import BaseMetaPy
from .Utils import Utils
import random as rd
import numpy as np
import math


class EGO(BaseMetaPy, Utils):

    def __init__(self,
                 N_EELS=150,
                 MAX_ITERATIONS=200,
                 MAX_KONVERGEN=15,
                 OPTIMIZER_NAME='Eel and Grouper Optimizer',
                 FUNCTIONS={
                     'name': 'sphere',
                     'dimension': 15,
                     'lowerbound': -100,
                     'upperbound': 100,
                     'objective': 'min'
                 },
                 ):
        """
        Eel and Grouper Optimizer (EGO)
        - Inspiration: Interaction and Foraging Strategy of Eels and Groupers in Marine Ecosystems
        """
        super().__init__(
            N_AGENTS=N_EELS,
            MAX_ITERATIONS=MAX_ITERATIONS,
            MAX_KONVERGEN=MAX_KONVERGEN,
            FUNCTIONS=FUNCTIONS,
            DROP_KEY_AGENTS=None
        )
        self.optimizer['name'] = OPTIMIZER_NAME

    def solve(self):
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']

        # initialize agents
        # 1. initialize agents
        agents = self._initialize_agents()

        # 2. evaluate agents
        XPrey, XGrouper, XEel = self.__divide_eel_grouper(agents)
        best_fitness_old = XPrey['fitness']
        self.LIST_BEST_FITNESS.append(XPrey['fitness'])

        # 3. Optimization Process
        konvergen = 0
        for idx_iteration in range(MAX_ITERATIONS):

            # update a and starvation rate
            a = 2 - 2 * (idx_iteration/MAX_ITERATIONS)
            starvation_rate = 100 * (idx_iteration/MAX_ITERATIONS)

            # update position
            agents = self.__update_position(
                agents, XPrey, XGrouper, XEel, a, starvation_rate)

            # apply boundaries
            agents = self._adjust_boundaries(agents)

            # Evaluate agents
            agents = self._evaluate_fitness(agents)

            # retrieve best agent
            XPrey = self._retrieve_best_agent(agents)

            # 6. check konvergensi
            is_break, best_fitness_old, konvergen = self._check_convergence(
                agents, best_fitness_old, konvergen, idx_iteration)
            if is_break:
                break

        self._IS_SOLVE = True

        return XPrey

    def __divide_eel_grouper(self, agents):
        """
        Bagi agents ke dalam tiga kelompok: XPrey, XGrouper, XEel

        """
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        XPrey = agents[rd.randint(0, N_AGENTS-1)]
        XGrouper = agents[rd.randint(0, N_AGENTS-1)]
        XEel = agents[rd.randint(0, N_AGENTS-1)]
        return XPrey, XGrouper, XEel

    def __update_position(self, agents, XPrey, XGrouper, XEel, a, starvation_rate):

        for idx_agent, agent in enumerate(agents):
            # update r1, r2, r3, r4, C1, C2, and p
            r1 = np.random.random()
            r2 = np.random.random()
            r3 = (a-2) * r1 + 2

            # get random agent
            random_agent = self.__generate_random_agent(agents)

            # update agent position of grouper
            C1 = 2 * a * r1 - a
            C2 = 2*r1
            D_grouper = np.abs(agent['position'] -
                               C2 * random_agent['position'])
            agents[idx_agent]['position'] = random_agent['position'] - \
                C1 * D_grouper

            # calculate fitness of new position
            agents[idx_agent] = self._evaluate_fitness([agents[idx_agent]])[0]

            # change this to > for maximation
            if agents[idx_agent]['fitness'] < XGrouper['fitness']:
                XGrouper = agents[idx_agent].copy()

            # update XEel position
            r4 = 100 * np.random.random()
            C2 = 2 * r1
            if r4 <= starvation_rate:
                XEel['position'] = C2*XGrouper['position']
            else:
                random_agent = self.__generate_random_agent(agents)
                XEel['position'] = C2 * random_agent['position']

            # update variabel X1 and X2
            b = a*r2
            Distance2Eel = np.abs(XEel['position'] - XPrey['position'])
            X_1 = math.exp(b*r3) * math.sin(2*math.pi) * C1 * \
                Distance2Eel + XEel['position']

            Distance2Grouper = np.abs(XGrouper['position'] - XPrey['position'])
            X_2 = XGrouper['position'] + C1 * Distance2Grouper

            if np.random.random() < 0.5:
                agents[idx_agent]['position'] = (0.8*X_1 + 0.2*X_2)/2
            else:
                agents[idx_agent]['position'] = (0.2*X_1 + 0.8*X_2)/2

        return agents

    def __generate_random_agent(self, agents):
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        random_agent = agents[rd.randint(0, N_AGENTS-1)]
        return random_agent
