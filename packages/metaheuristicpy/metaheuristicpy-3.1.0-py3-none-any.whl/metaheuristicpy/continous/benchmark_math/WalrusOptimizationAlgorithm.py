from .BaseMetaPy import BaseMetaPy
from .Utils import Utils
import random as rd
import numpy as np
import math


class WaOA(BaseMetaPy, Utils):

    def __init__(self,
                 N_WALRUS=150,
                 MAX_ITERATIONS=200,
                 MAX_KONVERGEN=15,
                 OPTIMIZER_NAME='Walrus Optimization Algorithm',
                 FUNCTIONS={
                     'name': 'sphere',
                     'dimension': 15,
                     'lowerbound': -100,
                     'upperbound': 100,
                     'objective': 'min'
                 },
                 ):
        super().__init__(
            N_AGENTS=N_WALRUS,
            MAX_ITERATIONS=MAX_ITERATIONS,
            MAX_KONVERGEN=MAX_KONVERGEN,
            FUNCTIONS=FUNCTIONS,
            DROP_KEY_AGENTS=None
        )
        self.optimizer['name'] = OPTIMIZER_NAME

    def solve(self):
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']

        best_agent = None
        best_fitness_old = float("-inf")

        # initialize agents
        # 1. initialize agents
        agents = self._initialize_agents()

        # 2. Evaluate agents
        agents = self._evaluate_fitness(agents)
        strongest_walrus = self._retrieve_best_agent(agents)
        self.LIST_BEST_FITNESS.append(strongest_walrus['fitness'])

        # 3. Optimization Process
        konvergen = 0
        for idx_iteration in range(1, MAX_ITERATIONS+1):

            # exploration vs exploitation
            agents = self.__exploration_vs_exploitation(
                agents, strongest_walrus, idx_iteration)

            # apply boundaries
            agents = self._adjust_boundaries(agents)

            # evaluate fitness
            agents = self._evaluate_fitness(agents)

            # select best agent
            strongest_walrus = self._retrieve_best_agent(agents)

            # 6. check konvergensi
            is_break, best_fitness_old, konvergen = self._check_convergence(
                agents, best_fitness_old, konvergen, idx_iteration)
            if is_break:
                break

        self._IS_SOLVE = True
        return strongest_walrus

    def __exploration_vs_exploitation(self, agents, strongest_walrus, iteration):
        for idx_agent, agent in enumerate(agents):
            # phase 1: Feeding Strategy (Exploration)
            agents[idx_agent] = self.__feeding_strategy(
                agent, strongest_walrus)

            # phase 2: Migration
            random_agent = self.__random_select_agent(agents, agent)
            agents[idx_agent] = self.__migration(agent, random_agent)

            # phase 3: Escaping and Fighting with predators (Exploitation)
            agents[idx_agent] = self.__attacking_predators(
                agent, iteration)

        return agents

    def __feeding_strategy(self, agent, strongest_walrus):
        I = rd.randint(1, 2)
        agent_phase_1 = agent.copy()
        agent_phase_1['position'] = agent['position'] + np.random.random() * (
            strongest_walrus['position'] - I * agent['position'])

        # adjust boundaries
        agent_phase_1 = self._adjust_boundaries([agent_phase_1])[0]

        # evaluate fitness function
        agent_phase_1 = self._evaluate_fitness([agent_phase_1])[0]

        # change to '>' for maximation
        if agent_phase_1['fitness'] < agent['fitness']:
            agent = agent_phase_1.copy()

        return agent

    def __migration(self, agent, random_agent):
        I = rd.randint(1, 2)
        agent_phase_2 = agent.copy()

        if random_agent['fitness'] < agent['fitness']:
            agent_phase_2['position'] = agent['position'] + np.random.random() * (
                random_agent['position'] - I * agent['position'])
        else:
            agent_phase_2['position'] = agent['position'] + \
                np.random.random() * \
                (agent['position'] - random_agent['position'])

        # adjust boundaries
        agent_phase_2 = self._adjust_boundaries([agent_phase_2])[0]

        # evaluate fitness
        agent_phase_2 = self._evaluate_fitness([agent_phase_2])[0]

        # change to '>' for maximation
        if agent_phase_2['fitness'] < agent['fitness']:
            agent = agent_phase_2.copy()

        return agent

    def __attacking_predators(self, agent, iteration):
        BATAS_BAWAH = self.optimizer['params']['FUNCTIONS']['lowerbound']
        BATAS_ATAS = self.optimizer['params']['FUNCTIONS']['upperbound']

        # calculate local upper and lower bound
        local_lb = BATAS_BAWAH/(iteration+np.random.random())
        local_up = BATAS_ATAS/(iteration+np.random.random())

        # calculate agent_phase_3
        agent_phase_3 = agent.copy()
        agent_phase_3['position'] = agent['position'] + \
            local_lb + np.random.random() * (local_up - local_lb)

        # adjust boundaries
        agent_phase_3 = self._adjust_boundaries([agent_phase_3])[0]

        # evaluate fitness
        agent_phase_3 = self._evaluate_fitness([agent_phase_3])[0]

        # update agent position
        # change to '>' for maximation
        if agent_phase_3['fitness'] < agent['fitness']:
            agent = agent_phase_3.copy()

        return agent

    def __random_select_agent(self, agents, agent):
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        # randomly select new agent m where m!=indeks agent
        random_agent = agents[rd.randint(0, N_AGENTS-1)]
        while random_agent['name'] == agent['name']:
            random_agent = agents[rd.randint(0, N_AGENTS-1)]
        return random_agent
