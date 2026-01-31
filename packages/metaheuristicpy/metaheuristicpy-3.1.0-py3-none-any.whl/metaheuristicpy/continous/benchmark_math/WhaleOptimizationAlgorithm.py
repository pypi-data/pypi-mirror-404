from .BaseMetaPy import BaseMetaPy
from .Utils import Utils
import random as rd
import numpy as np
import math

class WOA(BaseMetaPy, Utils):
    
    def __init__(self,
                 N_WHALES=50, 
                 MAX_ITERATIONS=100,
                 MAX_KONVERGEN=50,
                 FUNCTIONS={
                     'name': 'sphere',
                     'dimension': 5,
                     'lowerbound': -100,
                     'upperbound': 100,
                     'objective': 'min'
                },
                 OPTIMIZER_NAME='Whale Optimization Algorithm'
                 ):
        super().__init__(
            N_AGENTS=N_WHALES, 
            MAX_ITERATIONS=MAX_ITERATIONS, 
            MAX_KONVERGEN=MAX_KONVERGEN, 
            FUNCTIONS=FUNCTIONS,
            DROP_KEY_AGENTS=None
            )
        self.optimizer['name'] = OPTIMIZER_NAME
    
    def solve(self):
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
        N_WHALES = self.optimizer['params']['N_AGENTS']
        
        # 1. initialize agents
        agents = self._initialize_agents()
        best_agent = agents[rd.randint(0, N_WHALES-1)].copy()
        self.LIST_BEST_FITNESS.append(best_agent['fitness'])
        
        # 3. Optimization Process
        for idx_iteration in range(MAX_ITERATIONS):
            
            # 4. update whales position
            agents = self.__update_whales_position(agents, best_agent, idx_iteration)
            
            # 5. evaluate agents 
            agents = self._evaluate_fitness(agents)
            
            # 6. retrieve best agents
            best_agent = self._retrieve_best_agent(agents)
            
            # 7. check konvergensi
            print('Iteration {}, Best Cost: {:.4f}'.format(idx_iteration, best_agent['fitness']))
            self.LIST_BEST_FITNESS.append(best_agent['fitness'])

        self._IS_SOLVE = True
        
        return best_agent
        
    
    def __update_whales_position(self, agents, best_agent, iteration):
        def distance_vector(vector1, vector2, weight_vector1=1):
            return np.sqrt(np.sum(((weight_vector1* vector1) - vector2)**2))
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
        N_DIMENSION = self.optimizer['params']['FUNCTIONS']['dimension']
        LOWER_BOUND = self.optimizer['params']['FUNCTIONS']['lowerbound']
        UPPER_BOUND = self.optimizer['params']['FUNCTIONS']['upperbound']
        
        a = 2 * (1-(iteration/MAX_ITERATIONS))
        b = 2 # b is a constant factor for spiral updating position
        
        for idx_whale, whale in enumerate(agents):
            p = np.random.random() # probabilitas untuk menentukan spiral model atau shrinking encircling mechanism to update position
            l = rd.uniform(-1,1)
            
            # perbarui vektor A, C
            A = np.array([
                2 * a * np.random.random() - a for _ in range(N_DIMENSION)
            ])
            C = np.array([
                2 * np.random.random() for _ in range(N_DIMENSION)
            ])
            
            # perbarui vektor posisi dari whale
            if p>=0.5:
                # spiral updating position (mimic the helix-shaped movement of the humpback whales around prey)
                # distance vector
                dist = distance_vector(best_agent['position'], whale['position'])
                agents[idx_whale]['position'] = dist * math.pow(math.e, (b*l)) * math.cos(2*math.pi*rd.uniform(-1,1)) + best_agent['position']
            else:
                # shrinking encircling
                if np.sum(A)>=1:
                    #select random whale
                    random_whale = agents[rd.randint(0, N_AGENTS-1)]
                    # update whale position
                    dist = distance_vector(random_whale['position'], whale['position'], weight_vector1=C)
                    agents[idx_whale]['position'] = random_whale['position'] - (A*dist)
                else:
                    # update whale position
                    dist = distance_vector(best_agent['position'], whale['position'], weight_vector1=C)
                    agents[idx_whale]['position'] = best_agent['position'] - (A*dist)
            
            agents[idx_whale]['position'] = np.clip(
                agents[idx_whale]['position'],
                LOWER_BOUND,
                UPPER_BOUND
            )
        return agents