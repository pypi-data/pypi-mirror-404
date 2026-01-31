from .MemorybasedGreyWolfOptimizer import mGWO
from .Utils import Utils
import random as rd
import numpy as np
import math


class EEGWO(mGWO, Utils):

    def __init__(self,
                 N_WOLVES=150,
                 MAX_ITERATIONS=200,
                 MAX_KONVERGEN=15,
                 MODULATION_INDEX=1.5,
                 B1=0.53,
                 B2=0.2,
                 A_INITIAL=2,
                 A_FINAL=0,
                 OPTIMIZER_NAME='Exploration-enhanced Grey Wolf Optimizer',
                 FUNCTIONS={
                     'name': 'sphere',
                     'dimension': 15,
                     'lowerbound': -100,
                     'upperbound': 100,
                     'objective': 'min'
                 },
                 ):
        super().__init__(
            N_WOLVES=N_WOLVES,
            MAX_ITERATIONS=MAX_ITERATIONS,
            MAX_KONVERGEN=MAX_KONVERGEN,
            FUNCTIONS=FUNCTIONS,
        )
        self.optimizer['name'] = OPTIMIZER_NAME
        self.optimizer['params'].update({
            "MODULATION_INDEX": MODULATION_INDEX,
            "B1": B1,
            "B2": B2,
            "A_INITIAL": A_INITIAL,
            "A_FINAL": A_FINAL,
        })

    def solve(self):
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']

        best_agent = None
        best_fitness_old = float("-inf")

        # initialize agents
        # 1. initialize agents
        agents = self._initialize_agents()
        alpha_wolves, betha_wolves, delta_wolves = self._initialize_best_wolves(
            agents)
        self.LIST_BEST_FITNESS.append(alpha_wolves['fitness'])

        # 3. Optimization Process
        konvergen = 0
        for idx_iteration in range(MAX_ITERATIONS):

            # 5. Update wolves position
            agents = self._update_wolves_position(
                alpha_wolves, betha_wolves, delta_wolves, agents, idx_iteration)

            # 6. Evaluate agents
            agents = self._evaluate_fitness(agents)

            # update pBest wolves
            agents = self._update_pbest_wolves(agents)

            # 4. Evaluate wolves
            alpha_wolves, betha_wolves, delta_wolves = self._evaluate_wolves(
                alpha_wolves, betha_wolves, delta_wolves, agents)

            # 6. check konvergensi
            is_break, best_fitness_old, konvergen = self._check_convergence(
                agents, best_fitness_old, konvergen, idx_iteration)
            best_agent = alpha_wolves
            if is_break:
                break

        self._IS_SOLVE = True

        return best_agent

    def _update_wolves_position(self, alpha_wolves, betha_wolves, delta_wolves, agents, iteration):
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
        A_INITIAL = self.optimizer['params']['A_INITIAL']
        A_FINAL = self.optimizer['params']['A_FINAL']
        MODULATION_INDEX = self.optimizer['params']['MODULATION_INDEX']
        B1 = self.optimizer['params']['B1']
        B2 = self.optimizer['params']['B2']

        # update nilai a dan modulation
        modulation = (MAX_ITERATIONS-iteration)/MAX_ITERATIONS
        a = A_INITIAL - (A_INITIAL - A_FINAL) * \
            math.pow(modulation, MODULATION_INDEX)

        # update wolves position
        for idx_agent, agent in enumerate(agents):

            # hitung komponen Alpha
            r1, r2 = np.random.random(), np.random.random()
            A1, C1 = 2 * a * r1 - a, 2 * r2
            D_alpha = np.abs(C1 * alpha_wolves['position'] - agent['position'])
            X1 = alpha_wolves['position'] - A1*D_alpha

            # hitung komponen Betha
            r1, r2 = np.random.random(), np.random.random()
            A2, C2 = 2 * a * r1 - a, 2 * r2
            D_betha = np.abs(C2 * betha_wolves['position'] - agent['position'])
            X2 = betha_wolves['position'] - A2*D_betha

            # hitung komponen Deltha
            r1, r2 = np.random.random(), np.random.random()
            A3, C3 = 2 * a * r1 - a, 2 * r2
            D_delta = np.abs(C3 * delta_wolves['position'] - agent['position'])
            X3 = delta_wolves['position'] - A3*D_delta
            agents[idx_agent]['position'] = (X1+X2+X3)/3

            # update posisi Wolf ke-i
            random_agent = self.__generate_random_agent(agents, agent)
            agents[idx_agent]['position'] = (
                B1 * rd.uniform(0, 1) * (X1+X2+X3)/3
            ) + (
                B2 * rd.uniform(0, 1) *
                np.abs(random_agent['position'] - agent['position'])
            )
            # apply position boundaries
            agents[idx_agent] = self._adjust_boundaries([agents[idx_agent]])[0]
        return agents

    def __generate_random_agent(self, agents, agent):
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        random_agent = agents[rd.randint(0, N_AGENTS-1)]
        while random_agent['name'] == agent['name']:
            random_agent = agents[rd.randint(0, N_AGENTS-1)]
        return random_agent
