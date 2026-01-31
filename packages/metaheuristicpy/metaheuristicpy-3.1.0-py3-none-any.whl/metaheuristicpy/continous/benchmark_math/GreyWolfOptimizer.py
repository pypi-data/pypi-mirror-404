from .BaseMetaPy import BaseMetaPy
from .Utils import Utils
import random as rd
import numpy as np


class GWO(BaseMetaPy, Utils):

    def __init__(self,
                 N_WOLVES=50,
                 MAX_ITERATIONS=100,
                 MAX_KONVERGEN=50,
                 OPTIMIZER_NAME='Grey Wolf Optimizer',
                 FUNCTIONS={
                     'name': 'sphere',
                     'dimension': 15,
                     'lowerbound': -100,
                     'upperbound': 100,
                     'objective': 'min'
                 },
                 ):
        super().__init__(
            N_AGENTS=N_WOLVES,
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
        alpha_wolves, betha_wolves, delta_wolves = self._initialize_best_wolves(
            agents)
        best_agent = alpha_wolves
        self.LIST_BEST_FITNESS.append(best_agent['fitness'])

        # 3. Optimization Process
        for idx_iteration in range(MAX_ITERATIONS):
            # 4. Evaluate wolves
            alpha_wolves, betha_wolves, delta_wolves = self._evaluate_wolves(
                alpha_wolves, betha_wolves, delta_wolves, agents)

            # 5. Update wolves position
            agents = self._update_wolves_position(
                alpha_wolves, betha_wolves, delta_wolves, agents, idx_iteration)

            # 6. Evaluate agents
            agents = self._evaluate_fitness(agents)

            # 6. check konvergensi
            print('Iteration {}, Best Cost: {:.4f}'.format(
                idx_iteration, best_agent['fitness']))
            self.LIST_BEST_FITNESS.append(best_agent['fitness'])
            best_agent = alpha_wolves

        self._IS_SOLVE = True

        return best_agent

    def _initialize_best_wolves(self, agents):
        """
        Pilih 3 serigala awal secara acak sebagai Alpha, Beta, dan Delta
        """
        alpha_wolves = agents[rd.randint(0, len(agents)-1)]
        betha_wolves = agents[rd.randint(0, len(agents)-1)]
        delta_wolves = agents[rd.randint(0, len(agents)-1)]
        return alpha_wolves, betha_wolves, delta_wolves

    def _evaluate_wolves(self, alpha_wolves, betha_wolves, delta_wolves, agents):
        # record only the fitnesses
        for agent_data in agents:
            if agent_data['fitness'] < alpha_wolves['fitness']:
                alpha_wolves = agent_data.copy()
            elif agent_data['fitness'] < betha_wolves['fitness']:
                betha_wolves = agent_data.copy()
            elif agent_data['fitness'] < delta_wolves['fitness']:
                delta_wolves = agent_data.copy()
        return alpha_wolves, betha_wolves, delta_wolves

    def _update_wolves_position(self, alpha_wolves, betha_wolves, delta_wolves, agents, iteration):
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
        BATAS_BAWAH = self.optimizer['params']['FUNCTIONS']['lowerbound']
        BATAS_ATAS = self.optimizer['params']['FUNCTIONS']['upperbound']

        a = 2*(1-(iteration/MAX_ITERATIONS))
        for idx_agent, agent in enumerate(agents):

            # calculate X1 (how far each agent with alpha wolves)
            r1, r2 = np.random.random(), np.random.random()
            A1, C1 = 2 * a * r1 - a, 2 * r2
            D_alpha = np.abs(C1 * alpha_wolves['position'] - agent['position'])
            X1 = alpha_wolves['position'] - A1*D_alpha

            # calculate X2 (how far each agent with betha wolves)
            r1, r2 = np.random.random(), np.random.random()
            A2, C2 = 2 * a * r1 - a, 2 * r2
            D_betha = np.abs(C2 * betha_wolves['position'] - agent['position'])
            X2 = betha_wolves['position'] - A2*D_betha

            # calculate X3 (how far each agent with delta wolves)
            r1, r2 = np.random.random(), np.random.random()
            A3, C3 = 2 * a * r1 - a, 2 * r2
            D_delta = np.abs(C3 * delta_wolves['position'] - agent['position'])
            X3 = delta_wolves['position'] - A3*D_delta
            agents[idx_agent]['position'] = (X1+X2+X3)/3

            # apply position boundaries
            agents[idx_agent]['position'] = np.clip(
                agents[idx_agent]['position'], BATAS_BAWAH, BATAS_ATAS)
        return agents
