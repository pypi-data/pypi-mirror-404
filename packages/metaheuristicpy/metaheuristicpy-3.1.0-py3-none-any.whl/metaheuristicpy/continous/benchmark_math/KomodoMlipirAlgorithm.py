from .BaseMetaPy import BaseMetaPy
from .Utils import Utils
import random as rd
import numpy as np
import math


class KMA(BaseMetaPy, Utils):

    def __init__(self,
                 N_KOMODOS=20,
                 MAX_ITERATIONS=200,
                 MAX_KONVERGEN=10,
                 BIG_MALES_PORTION=0.1,
                 MLIPIR_RATE=0.7,
                 RADIUS_PARTHENOGENESIS=0.1,
                 N_POPULATION_ADJUSTMENT=7,
                 FUNCTIONS={
                     'name': 'sphere',
                     'dimension': 5,
                     'lowerbound': -100,
                     'upperbound': 100,
                     'objective': 'min'
                 },
                 OPTIMIZER_NAME='Komodo Mlipir Algorithm'
                 ):
        """
        KMA sangat sensitif terhadap N_KOMODOS, karena itu sangat kuat mengontrol strategi eksplorasi dan eksploitasi, sementara BIG_MALE_PORTION dan MLIPIR_RATE bisa didefinisikan dengan nilai tetap sebesar 0.5

        Setting optimal setelah menguji coba kodingan KMA dengan Sphere, Griewank, dan Rastrigin:
        N_KOMODOS=20,
        MAX_ITERATIONS=200,
        MAX_KONVERGEN=10,
        BIG_MALES_PORTION=0.1,
        MLIPIR_RATE=0.7,
        RADIUS_PARTHENOGENESIS=0.1,
        N_POPULATION_ADJUSTMENT=7,

        Notes:
        - N_POPULATION_ADJUSTMENT harus < N_KOMODOS
        - N_KOMODOS > 20 menyebabkan solusi melenceng (berkebalikan) dari objektif yang seharusnya
        """

        super().__init__(
            N_AGENTS=N_KOMODOS,
            MAX_ITERATIONS=MAX_ITERATIONS,
            MAX_KONVERGEN=MAX_KONVERGEN,
            FUNCTIONS=FUNCTIONS,
            DROP_KEY_AGENTS=None
        )
        self.optimizer['name'] = OPTIMIZER_NAME
        self.optimizer['params'].update({
            'BIG_MALES_PORTION': BIG_MALES_PORTION,
            'RADIUS_PARTHENOGENESIS': RADIUS_PARTHENOGENESIS,
            'MLIPIR_RATE': MLIPIR_RATE,
            'N_POPULATION_ADJUSTMENT': N_POPULATION_ADJUSTMENT,
        })

    def solve(self):
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
        N_KOMODOS = self.optimizer['params']['N_AGENTS']

        # 1. initialize agents
        agents = self._initialize_agents()
        best_agent = agents[rd.randint(0, N_KOMODOS-1)].copy()
        best_fitness_old = best_agent['fitness']
        self.LIST_BEST_FITNESS.append(best_agent['fitness'])

        # 3. Optimization Process
        konvergen = 0
        for idx_iteration in range(MAX_ITERATIONS):

            # 3. Find big males, female, and small males
            big_males, female, small_males = self.__split_agents_to_three_groups(
                agents)

            # 4. update big males
            big_males = self.__update_komodo_big_males(big_males)
            if len(big_males) == 1:
                big_males = list(big_males)

            # 5. update female: it can be returned [big_male, female] from mating procedure OR [female] only from parthenogenesis
            females = self.__update_komodo_female(big_males[0], female)
            if len(females) > 1:
                # replace highest solution with offspring_1
                big_males[0] = females[0]
                female = [females[1]]
            else:
                female = females

            # 6. update small males
            small_males = self.__update_komodo_small_males(
                big_males, small_males)

            # 7. replace agents with merged big_males, female, and small_males
            agents = self.__replace_agents(big_males, female, small_males)

            # 8. update population size adaptively
            if idx_iteration >= 2:
                agents = self.__update_population_size(agents, idx_iteration)

            # 2. evaluate agents
            agents = self._evaluate_fitness(agents)

            # 9. Select the highest-quality Komodo (best agent) from the three groups as the best-so-far solution
            # retrieve best agents
            best_agent = self._retrieve_best_agent(agents)

            # 10. check konvergensi
            is_break, best_fitness_old, konvergen = self._check_convergence(
                agents, best_fitness_old, konvergen, idx_iteration)
            if is_break:
                break

        self._IS_SOLVE = True

        return best_agent

    def __split_agents_to_three_groups(self, agents):
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        BIG_MALES_PORTION = self.optimizer['params']['BIG_MALES_PORTION']
        OBJECTIVE = self.optimizer['params']['FUNCTIONS']['objective']
        big_males, female, small_males = None, None, None

        # calculate n portion of Komodos as big males
        n_big_males = math.floor((N_AGENTS*BIG_MALES_PORTION))

        # sort agents by fitness (descending order)
        isDescendingOrder = True
        if OBJECTIVE == 'min':
            isDescendingOrder = False
        fitness = np.array([
            agent_data['fitness'] for agent_data in agents
        ])
        komodosWithFitness = list(zip(agents, fitness))
        komodosWithFitness.sort(key=lambda x: x[1], reverse=isDescendingOrder)
        sortedKomodos = [komodo for komodo, fitness in komodosWithFitness]

        # select big males, female, and small males
        big_males = sortedKomodos[0:n_big_males]
        female = sortedKomodos[n_big_males]
        small_males = sortedKomodos[n_big_males+1:]

        return big_males, female, small_males

    def __update_komodo_big_males(self, big_males):
        N_DIMENSION = self.optimizer['params']['FUNCTIONS']['dimension']

        n_big_males = len(big_males)
        for i in range(n_big_males):
            sum_position_j_komodos = np.zeros(N_DIMENSION)
            for j in range(n_big_males):
                if i == j:
                    continue
                if (big_males[i]['fitness'] < big_males[j]['fitness']) or (np.random.random() < 0.5):
                    wij = np.random.random() * \
                        (big_males[j]['position']-big_males[i]['position'])
                else:
                    wij = np.random.random() * \
                        (big_males[i]['position']-big_males[j]['position'])

                sum_position_j_komodos += wij

            # update i-th big males position
            big_males[i]['position'] += sum_position_j_komodos

        return big_males

    def __update_komodo_female(self, big_male, female):
        RADIUS_PARTHENOGENESIS = self.optimizer['params']['RADIUS_PARTHENOGENESIS']
        LOWER_BOUND = self.optimizer['params']['FUNCTIONS']['lowerbound']
        UPPER_BOUND = self.optimizer['params']['FUNCTIONS']['upperbound']

        females = list()
        if np.random.random() > 0.5:
            # asexual reproduction
            female['position'] += (2*np.random.random()-1) * \
                RADIUS_PARTHENOGENESIS*np.abs(UPPER_BOUND-LOWER_BOUND)
            females.append(female)
        else:
            # sexual reproduction by mating the highest quality of big males
            offspring_1 = big_male.copy()
            offspring_1['position'] = (np.random.random(
            ) * big_male['position']) + (1-np.random.random())*female['position']
            females.append(offspring_1)

            offspring_2 = female.copy()
            offspring_2['position'] = (np.random.random(
            ) * female['position']) + (1-np.random.random())*big_male['position']
            females.append(offspring_2)
        return females

    def __update_komodo_small_males(self, big_males, small_males):
        MLIPIR_RATE = self.optimizer['params']['MLIPIR_RATE']
        N_DIMENSION = self.optimizer['params']['FUNCTIONS']['dimension']

        for idx_small_male, small_male in enumerate(small_males):
            sum_position_j_komodos = np.zeros(N_DIMENSION)
            for big_male in big_males:
                temp_small_male_position = list()
                for i_dimension in range(N_DIMENSION):
                    if np.random.random() < MLIPIR_RATE:
                        temp_small_male_position.append(
                            np.random.random() *
                            (big_male['position'][i_dimension] -
                             small_male['position'][i_dimension])
                        )
                    else:
                        temp_small_male_position.append(0)
                sum_position_j_komodos += np.array(temp_small_male_position)
            # update i-th small male position
            small_males[idx_small_male]['position'] += sum_position_j_komodos

        return small_males

    def __replace_agents(self, big_males, female, small_males):
        return big_males+female+small_males

    def __update_population_size(self, agents, idx_iterasi_saat_ini):
        """
        <Input>:
        - idx_iterasi_saat_ini: iterasi saat ini dengan t>=2 and t<MAX_ITERATIONS, indeks dimulai dari 0
        """
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        t = idx_iterasi_saat_ini
        population_adjustment = self.optimizer['params']['N_POPULATION_ADJUSTMENT']

        # get the list of the best fitness history
        list_best_fitness_values = self.LIST_BEST_FITNESS

        delta_f1 = abs(
            list_best_fitness_values[t-2] - list_best_fitness_values[t-1])
        delta_f2 = abs(
            list_best_fitness_values[t-1] - list_best_fitness_values[t])

        # hitung nilai N_NEW_AGENT dan lalukan adjustment terhadap population
        if delta_f1 > 0 and delta_f2 > 0:
            if N_AGENTS-population_adjustment > 5:
                N_NEW_AGENTS = N_AGENTS - population_adjustment
                # trim agents sebelumnya sebenyak N_NEW_AGENTS
                agents = agents[:N_NEW_AGENTS]
        elif math.isclose(delta_f1, 0, rel_tol=1e-9, abs_tol=1e-9) and math.isclose(delta_f2, 0, rel_tol=1e-9, abs_tol=1e-9):
            # generate new agents sebanyak population adjustment lalu append ke agents sebelumnya
            new_agents = self._initialize_agents(
                new_N_AGENTS=population_adjustment)

            # append each items of new_agents into agents
            agents = agents + new_agents

        return agents
