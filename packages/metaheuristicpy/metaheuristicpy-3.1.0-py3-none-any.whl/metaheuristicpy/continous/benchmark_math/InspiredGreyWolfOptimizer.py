from .GreyWolfOptimizer import GWO
from .MemorybasedGreyWolfOptimizer import mGWO
from .Utils import Utils
import random as rd
import numpy as np
import math


class IGWO(mGWO, Utils):

    def __init__(self,
                 N_WOLVES=150,
                 MAX_ITERATIONS=200,
                 MAX_KONVERGEN=15,
                 COGNITIVE_PARAMETER=0.75,
                 SOCIAL_PARAMETER=0.43,
                 INERTIA_INITIAL=1.9,
                 INERTIA_FINAL=0.4,
                 A_INITIAL=2,
                 A_FINAL=0,
                 OPTIMIZER_NAME='Inspired Grey Wolf Optimizer',
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
            "COGNITIVE_PARAMETER": COGNITIVE_PARAMETER,
            "SOCIAL_PARAMETER": SOCIAL_PARAMETER,
            "INERTIA_INITIAL": INERTIA_INITIAL,
            "INERTIA_FINAL": INERTIA_FINAL,
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
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        A_INITIAL = self.optimizer['params']['A_INITIAL']
        A_FINAL = self.optimizer['params']['A_FINAL']
        COGNITIVE_PARAMETER = self.optimizer['params']['COGNITIVE_PARAMETER']
        SOCIAL_PARAMETER = self.optimizer['params']['SOCIAL_PARAMETER']
        INERTIA_INITIAL = self.optimizer['params']['INERTIA_INITIAL']
        INERTIA_FINAL = self.optimizer['params']['INERTIA_FINAL']
        BATAS_BAWAH = self.optimizer['params']['FUNCTIONS']['lowerbound']
        BATAS_ATAS = self.optimizer['params']['FUNCTIONS']['upperbound']

        # update nilai a dan inertia
        a = A_INITIAL - (A_INITIAL - A_FINAL) * math.log10(1 +
                                                           (math.e-1)*(iteration/MAX_ITERATIONS))
        inertia = ((MAX_ITERATIONS-iteration)/MAX_ITERATIONS) * \
            (INERTIA_INITIAL - INERTIA_FINAL) + INERTIA_FINAL

        for idx_agent, agent in enumerate(agents):
            pbest_agent = agent['PBest']

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
            cognitive_learning = (
                COGNITIVE_PARAMETER * np.random.random() *
                np.abs(pbest_agent['position'] - agent['position'])
            )
            social_learning = (
                SOCIAL_PARAMETER * np.random.random() * np.abs(X1 -
                                                               agent['position'])
            )
            agents[idx_agent]['position'] = (
                inertia * (X1+X2+X3)/3
            ) + cognitive_learning + social_learning

            # apply position boundaries
            agents[idx_agent] = self._adjust_boundaries([agents[idx_agent]])[0]
        return agents
