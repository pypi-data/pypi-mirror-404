from .GreyWolfOptimizer import GWO
from .Utils import Utils
import random as rd
import numpy as np


class mGWO(GWO, Utils):

    def __init__(self,
                 N_WOLVES=150,
                 MAX_ITERATIONS=200,
                 MAX_KONVERGEN=15,
                 CROSSOVER_RATE=0.67,
                 OPTIMIZER_NAME='Memory-based Grey Wolf Optimizer',
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
            "CROSSOVER_RATE": CROSSOVER_RATE,
        })

    def solve(self):
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
        best_agent = None
        best_fitness_old = float('-inf')

        # initialize agents
        # 1. initialize agents
        agents = self._initialize_agents()
        alpha_wolves, betha_wolves, delta_wolves = self._initialize_best_wolves(
            agents)
        self.LIST_BEST_FITNESS.append(alpha_wolves['fitness'])

        # 3. Optimization Process
        konvergen = 0
        for idx_iteration in range(MAX_ITERATIONS):
            # 4. Evaluate wolves
            alpha_wolves, betha_wolves, delta_wolves = self._evaluate_wolves(
                alpha_wolves, betha_wolves, delta_wolves, agents)

            # 5. Update wolves position
            agents = self._update_wolves_position(
                alpha_wolves, betha_wolves, delta_wolves, agents, idx_iteration)

            # 6. Evaluate agents
            agents = self._evaluate_fitness(agents)

            # update pBest wolves
            agents = self._update_pbest_wolves(agents)

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
        CROSSOVER_RATE = self.optimizer['params']['CROSSOVER_RATE']
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        BATAS_BAWAH = self.optimizer['params']['FUNCTIONS']['lowerbound']
        BATAS_ATAS = self.optimizer['params']['FUNCTIONS']['upperbound']

        a = 2*(1-(iteration/MAX_ITERATIONS))
        k = 1 - (1*iteration/MAX_ITERATIONS)

        for idx_agent, agent in enumerate(agents):
            pbest_agent = agent['PBest']

            # apply memory gwo logic here
            if np.random.random() < CROSSOVER_RATE:
                # calculate X1 (how far each agent with alpha wolves)
                r1, r2 = np.random.random(), np.random.random()
                A1, C1 = 2 * a * r1 - a, 2 * r2
                D_alpha = np.abs(
                    C1 * alpha_wolves['position'] - pbest_agent['position'])
                X1 = alpha_wolves['position'] - A1*D_alpha

                # calculate X2 (how far each agent with betha wolves)
                r1, r2 = np.random.random(), np.random.random()
                A2, C2 = 2 * a * r1 - a, 2 * r2
                D_betha = np.abs(
                    C2 * betha_wolves['position'] - pbest_agent['position'])
                X2 = betha_wolves['position'] - A2*D_betha

                # calculate X3 (how far each agent with delta wolves)
                r1, r2 = np.random.random(), np.random.random()
                A3, C3 = 2 * a * r1 - a, 2 * r2
                D_delta = np.abs(
                    C3 * delta_wolves['position'] - pbest_agent['position'])
                X3 = delta_wolves['position'] - A3*D_delta
                agents[idx_agent]['position'] = (X1+X2+X3)/3

            else:
                # find two wolves randomly
                random_wolf_1 = agents[rd.randint(0, N_AGENTS-1)]
                random_wolf_2 = agents[rd.randint(0, N_AGENTS-1)]
                agents[idx_agent]['position'] = pbest_agent['position'] + k * \
                    np.abs(random_wolf_1['position']-random_wolf_2['position'])

            # apply position boundaries
            agents[idx_agent] = self._adjust_boundaries([agents[idx_agent]])[0]
        return agents

    def _update_pbest_wolves(self, agents):
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        OBJECTIVE = self.optimizer['params']['FUNCTIONS']['objective']
        # mekanisme perhitungan PBest
        for idx_agent in range(N_AGENTS):
            if ((agents[idx_agent]['fitness'] < agents[idx_agent]['PBest']['fitness']) and (OBJECTIVE == 'min')) or ((agents[idx_agent]['fitness'] > agents[idx_agent]['PBest']['fitness']) and (OBJECTIVE == 'max')):
                # update nilai PBest setiap agent
                agents[idx_agent]['PBest']['position'] = agents[idx_agent]['position']
                agents[idx_agent]['PBest']['fitness'] = agents[idx_agent]['fitness']
        return agents
