from .BaseMetaPy import BaseMetaPy
from .Utils import Utils
import random as rd
import numpy as np


class GA(BaseMetaPy, Utils):

    def __init__(self,
                 N_CHROMOSOMES=50,
                 MAX_ITERATIONS=100,
                 MUTATION_RATE=0.3,
                 IS_APPLY_ELITISM_STRATEGY=True,
                 ELITE_SIZE=5,
                 MAX_KONVERGEN=50,
                 N_TIMES_CROSSOVER=5,
                 OPTIMIZER_NAME='Genetic Algorithm',
                 PARENT_SELECTION='tournament',
                 TOURNAMENT_SIZE=10,
                 FUNCTIONS={
                     'name': 'sphere',
                     'dimension': 15,
                     'lowerbound': -100,
                     'upperbound': 100,
                     'objective': 'min'
                 },
                 ):
        super().__init__(
            N_AGENTS=N_CHROMOSOMES,
            MAX_ITERATIONS=MAX_ITERATIONS,
            MAX_KONVERGEN=MAX_KONVERGEN,
            FUNCTIONS=FUNCTIONS,
            DROP_KEY_AGENTS=None
        )

        N_POPULATION = N_CHROMOSOMES//2
        if IS_APPLY_ELITISM_STRATEGY:
            N_POPULATION = (N_CHROMOSOMES-ELITE_SIZE)//2

        if PARENT_SELECTION == 'tournament':
            PARENT_SELECTION = self.__tournament_selection
        elif PARENT_SELECTION == 'roulette':
            PARENT_SELECTION = self.__roulette_wheel_selection

        self.optimizer['name'] = OPTIMIZER_NAME
        self.optimizer['params'].update({
            "MUTATION_RATE": MUTATION_RATE,
            "IS_APPLY_ELITISM_STRATEGY": IS_APPLY_ELITISM_STRATEGY,
            "ELITE_SIZE": ELITE_SIZE,
            "N_TIMES_CROSSOVER": N_TIMES_CROSSOVER,
            'N_POPULATION': N_POPULATION,
            'PARENT_SELECTION': PARENT_SELECTION,
            'TOURNAMENT_SIZE': TOURNAMENT_SIZE,
        })

    def solve(self):
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
        IS_APPLY_ELITISM_STRATEGY = self.optimizer['params']['IS_APPLY_ELITISM_STRATEGY']
        N_POPULATION = self.optimizer['params']['N_POPULATION']

        # initialize agents
        # 1. initialize agents
        agents = self._initialize_agents()
        best_agent = agents[rd.randint(0, N_POPULATION-1)].copy()
        self.LIST_BEST_FITNESS.append(best_agent['fitness'])

        # 2. Evaluate agents
        agents = self._evaluate_fitness(agents)

        # 3. Optimization Process
        for idx_iteration in range(MAX_ITERATIONS):
            new_population = list()
            # 3. Apply Elitism Strategy (Mempertahankan generasi terbaik pada iterasi (t) ke iterasi berikutnya (t+1))
            if IS_APPLY_ELITISM_STRATEGY:
                elite_agents = self.__get_elite_individuals(agents)

            # each generation iteration will create two new child
            for _ in range(N_POPULATION):
                # 3. Parent selection (Tournament, roullete, or etc)
                agent_1 = self.optimizer['params']['PARENT_SELECTION'](agents)
                agent_2 = self.optimizer['params']['PARENT_SELECTION'](agents)

                # 4. Crossover
                child_1, child_2 = self.__crossover(agent_1, agent_2)

                # 5. Mutation child 1 and child 2
                new_population.append(self.__mutation(child_1))
                new_population.append(self.__mutation(child_2))

            # replace old population with new population
            if IS_APPLY_ELITISM_STRATEGY:
                new_population = np.array(new_population)
                agents = np.concatenate((new_population, elite_agents))
            else:
                agents = new_population

            # 5. Evaluate Agents
            agents = self._evaluate_fitness(agents)

            # 6. check konvergensi
            print('Iteration {}, Best Cost: {:.4f}'.format(
                idx_iteration, best_agent['fitness']))
            self.LIST_BEST_FITNESS.append(best_agent['fitness'])
            fitness = np.array([
                agent_data['fitness'] for agent_data in agents
            ])
            best_agent = agents[np.argmin(fitness)]

        self._IS_SOLVE = True
        return best_agent

    def __get_elite_individuals(self, agents):
        """
        Function to handly elitism strategy
        """
        ELITE_SIZE = self.optimizer['params']['ELITE_SIZE']
        elit_agents = list()
        # record only the fitnesses
        fitness = np.array([
            agent_data['fitness'] for agent_data in agents
        ])
        elite_indices = np.argsort(fitness)[:ELITE_SIZE]
        for elit_indeks in elite_indices:
            elit_agents.append(agents[elit_indeks])
        return elit_agents

    def __tournament_selection(self, agents):
        """
        Tournament selection pilih 10 parent secara acak lalu kembalikan 1 parent dengan best fitness
        """
        TOURNAMENT_SIZE = self.optimizer['params']['TOURNAMENT_SIZE']

        # record only the fitnesses
        fitness = np.array([
            agent_data['fitness'] for agent_data in agents
        ])

        # tournament selection
        selected = np.random.choice(len(agents), size=TOURNAMENT_SIZE)

        # return the first selected parent with best fitness
        best_index_agent = selected[
            np.argmin(fitness[selected])
        ]
        return agents[best_index_agent]

    def __roulette_wheel_selection(self, agents):
        """
        Semakin baik fitness suatu agent semakin besar probabilitynya untuk dipilih
        """
        # record only the fitnesses
        fitness = np.array([
            agent_data['fitness'] for agent_data in agents
        ])

        # Calculate selection probabilities
        total_fitness = np.sum(fitness)
        selection_probabilities = fitness / total_fitness

        # Generate cumulative probability distribution
        cumulative_probabilities = np.cumsum(selection_probabilities)

        # Select one individual based on roulette wheel
        r = np.random.random()
        for i, cumulative_prob in enumerate(cumulative_probabilities):
            if r <= cumulative_prob:
                return agents[i]

    def __crossover(self, agent_1, agent_2):
        """
        Crossover method:
        - n-point crossover
        """
        N_TIMES_CROSSOVER = self.optimizer['params']['N_TIMES_CROSSOVER']
        N_DIMENSION = self.optimizer['params']['FUNCTIONS']['dimension']
        child_1 = agent_1.copy()
        child_2 = agent_2.copy()
        for _ in range(N_TIMES_CROSSOVER):
            # stage x crossover
            if N_DIMENSION == 2:
                point_crossover = 1
            else:
                point_crossover = np.random.randint(
                    1, len(agent_1['position'])-1)
            child_1['position'] = np.concatenate([
                child_1['position'][:point_crossover], child_2['position'][point_crossover:]
            ])
            child_2['position'] = np.concatenate([
                child_2['position'][:point_crossover], child_1['position'][point_crossover:]
            ])
        return child_1, child_2

    def __mutation(self, agent):
        """
        Mutation rate, menentukan seberapa banyak gen yang akan dimutasi
        """
        MUTATION_RATE = self.optimizer['params']['MUTATION_RATE']
        N_DIMENSION = self.optimizer['params']['FUNCTIONS']['dimension']
        n_mutation = round(MUTATION_RATE*N_DIMENSION)
        LOWER_BOUND = self.optimizer['params']['FUNCTIONS']['lowerbound']
        UPPER_BOUND = self.optimizer['params']['FUNCTIONS']['upperbound']

        # mutasi gen
        count_mutation = 0
        while count_mutation < n_mutation:
            random_index_dimension = rd.randint(0, N_DIMENSION-1)
            agent['position'][random_index_dimension] = rd.uniform(
                LOWER_BOUND, UPPER_BOUND)
            count_mutation += 1
        return agent
