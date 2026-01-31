from .BaseMetaFeatureSelection import BaseMetaheuristics
from sklearn.neighbors import KNeighborsClassifier
import numpy as np
import time


class GA(BaseMetaheuristics):

    def __init__(self,
                 N_POPULATION=30,
                 MAX_ITERATIONS=100,
                 MUTATION_RATE_PROBABILITY=0.3,
                 MAX_CONVERGENCE=10,
                 OPTIMIZER_NAME='Genetic Algorithm',
                 BREAK_IF_CONVERGENCE=True,
                 FUNCTIONS={
                     'classifier': KNeighborsClassifier(),
                     'objective': 'max',
                     'transfer_binary_function': 's_shaped_f2',
                     # f1_macro, f1_weighted, recall_macro, recall_weighted, precision_macro, precision_weighted, roc_auc_score_macro, roc_auc_score_weighted
                     'fitness_metric': 'accuracy'
                 },
                 ):
        super().__init__(
            N_AGENTS=N_POPULATION,
            MAX_ITERATIONS=MAX_ITERATIONS,
            MAX_CONVERGENCE=MAX_CONVERGENCE,
            FUNCTIONS=FUNCTIONS,
            BREAK_IF_CONVERGENCE=BREAK_IF_CONVERGENCE,
        )
        self.optimizer['name'] = OPTIMIZER_NAME
        self.optimizer['params'].update({
            "MUTATION_RATE_PROBABILITY": MUTATION_RATE_PROBABILITY,
        })

    def fit(self, X_train, y_train, X_test, y_test):
        super().fit(X_train, y_train, X_test, y_test)
        self._IS_FIT = True
        return self

    def solve(self):
        if self._IS_FIT:
            MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
            N_POPULATION = self.optimizer['params']['N_AGENTS']
            N_FEATURES = self.N_FEATURES
            MUTATION_RATE_PROBABILITY = self.optimizer['params']['MUTATION_RATE_PROBABILITY']

            # checkpoint start time
            start_time = time.time()

            # 1. Initialize agents
            agents, agents_fitness, best_fitness_previous = self.__initialize_populations()

            # 2. GA main loop
            convergence = 0
            for iteration in range(MAX_ITERATIONS):

                # 3. selection: memilih parents yang akan kawin
                parents = self.__tournament_selection(
                    agents, agents_fitness, number_of_selected_parents=N_POPULATION//2)

                # 4. crossover
                offsprings = self.__single_point_crossover(
                    parents, offspring_size=(N_POPULATION - parents.shape[0]))

                # 5. mutation
                offsprings = self.__mutation(offsprings)

                # 6. replacement populations
                agents[:parents.shape[0]] = parents.copy()
                agents[parents.shape[0]:] = offsprings.copy()

                # 7. evaluate fitness from new solution
                agents_fitness = np.array([
                    self._evaluate_fitness(agent) for agent in agents
                ])

                # 8. get best chromosome
                best_chromosome, best_fitness = self._retrieve_best_agent(
                    agents, agents_fitness)

                # check convergence
                self.LIST_BEST_FITNESS.append(best_fitness)
                is_break, best_fitness_previous, convergence = self._check_convergence(
                    best_fitness, best_fitness_previous, convergence, iteration)

                if is_break and self.BREAK_IF_CONVERGENCE:
                    break

            # calculate end time
            end_time = time.time()

            # Get optimal features
            optimal_solution = {
                'features_subset': best_chromosome,
                'selected_features': np.where(best_chromosome == 1)[0],
                'optimal_n_features': len(np.where(best_chromosome == 1)[0]),
                'best_fitness': best_fitness,
                'start_time_computation': start_time,
                'end_time_computation': end_time,
                'total_train_time_computation': self._calculate_total_training_time_computation(start_time, end_time)
            }
            return optimal_solution

        else:
            raise Exception('Please fit your dataset first!')

    def __initialize_populations(self):
        N_POPULATION = self.optimizer['params']['N_AGENTS']
        N_FEATURES = self.N_FEATURES

        agents = np.random.randint(
            2, size=(N_POPULATION, N_FEATURES))
        agents_fitness = np.zeros(N_POPULATION)
        best_fitness_previous = -np.inf
        if self.OBJECTIVE == 'min':
            best_fitness_previous = np.inf
        return agents, agents_fitness, best_fitness_previous

    def __tournament_selection(self, agents, agents_fitness, number_of_selected_parents):
        """
        Function untuk memilih sejumlah number_of_selected_parents untuk dilakukan crossover dan mutation menggunakan metode tournament selection
        """
        parents = np.empty((number_of_selected_parents, agents.shape[1]))
        for i in range(number_of_selected_parents):
            tournament_indices = np.random.choice(
                len(agents), size=3, replace=False)
            tournament_fitness = agents_fitness[tournament_indices]
            winner_index = tournament_indices[np.argmax(tournament_fitness)]
            parents[i] = agents[winner_index].copy()
        return parents

    def __single_point_crossover(self, parents, offspring_size):
        """
        Function untuk melakukan proses kawin silang sehingga menghasilkan sejumlah (offspring_size) kromosom anak
        """
        N_FEATURES = self.N_FEATURES

        # array untuk child
        offsprings = np.empty((offspring_size, N_FEATURES))

        # pilih titik kawin silang
        crossover_point = np.random.randint(0, N_FEATURES+1, size=1)[0]
        # crossover_point = N_FEATURES//2
        for k in range(offspring_size):
            parent1_idx = k % parents.shape[0]
            parent2_idx = (k + 1) % parents.shape[0]
            offsprings[k, :crossover_point] = parents[parent1_idx,
                                                      :crossover_point].copy()
            offsprings[k, crossover_point:] = parents[parent2_idx,
                                                      crossover_point:].copy()
        return offsprings

    def __mutation(self, offsprings):
        MUTATION_RATE_PROBABILITY = self.optimizer['params']['MUTATION_RATE_PROBABILITY']
        for idx_offspring, offspring in enumerate(offsprings):
            for index_col in range(len(offspring)):
                if np.random.rand() < MUTATION_RATE_PROBABILITY:
                    offsprings[idx_offspring, index_col] = 1 - \
                        offsprings[idx_offspring, index_col]
        return offsprings
