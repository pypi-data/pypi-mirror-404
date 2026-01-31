from .BaseMetaFeatureSelection import BaseMetaheuristics
from sklearn.neighbors import KNeighborsClassifier
import numpy as np
import time


class PSO(BaseMetaheuristics):

    def __init__(self,
                 N_PARTICLES=30,
                 MAX_ITERATIONS=100,
                 INERTIA=0.75,
                 COGNITION_RATE=0.9,
                 SOCIAL_RATE=1.4,
                 MAX_CONVERGENCE=10,
                 OPTIMIZER_NAME='Particle Swarm Optimization (Classic)',
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
            N_AGENTS=N_PARTICLES,
            MAX_ITERATIONS=MAX_ITERATIONS,
            MAX_CONVERGENCE=MAX_CONVERGENCE,
            FUNCTIONS=FUNCTIONS,
            BREAK_IF_CONVERGENCE=BREAK_IF_CONVERGENCE,
        )
        self.optimizer['name'] = OPTIMIZER_NAME
        self.optimizer['params'].update({
            "INERTIA": INERTIA,
            "COGNITION_RATE": COGNITION_RATE,
            "SOCIAL_RATE": SOCIAL_RATE,
        })

    def fit(self, X_train, y_train, X_test, y_test):
        super().fit(X_train, y_train, X_test, y_test)
        self._IS_FIT = True
        return self

    def solve(self):
        if self._IS_FIT:
            MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
            N_PARTICLES = self.optimizer['params']['N_AGENTS']
            N_FEATURES = self.N_FEATURES
            INERTIA = self.optimizer['params']['INERTIA']
            COGNITION_RATE = self.optimizer['params']['COGNITION_RATE']
            SOCIAL_RATE = self.optimizer['params']['SOCIAL_RATE']
            TRANSFER_FUNCTION = self.optimizer['transfer_function']

            start_time = time.time()
            # 1. Initialize agents
            agents, velocities, pbest, pbest_fitness, gbest, gbest_fitness, best_fitness_previous = self.__initialize_particles()

            # 2. BPSO main loop
            convergence = 0
            for iteration in range(MAX_ITERATIONS):

                # perbarui vektor kecepatan dan posisi setiap partikel
                velocities, agents = self.__update_velocities_position_vectors(
                    velocities, agents, pbest, gbest)

                # Hitung fitness dan perbarui pbest dan gbest
                for idx_particle, particle in enumerate(agents):
                    fitness = self._evaluate_fitness(particle)
                    if fitness > pbest_fitness[idx_particle]:
                        pbest_fitness[idx_particle] = fitness
                        pbest[idx_particle] = particle

                    if fitness > gbest_fitness:
                        gbest_fitness = fitness
                        gbest = particle

                # check convergence
                self.LIST_BEST_FITNESS.append(gbest_fitness)
                is_break, best_fitness_previous, convergence = self._check_convergence(
                    gbest_fitness, best_fitness_previous, convergence, iteration)

                if is_break and self.BREAK_IF_CONVERGENCE:
                    break

            end_time = time.time()
            # Get optimal features
            optimal_solution = {
                'features_subset': gbest,
                'selected_features': np.where(gbest == 1)[0],
                'optimal_n_features': len(np.where(gbest == 1)[0]),
                'best_fitness': gbest_fitness,
                'start_time_computation': start_time,
                'end_time_computation': end_time,
                'total_train_time_computation': self._calculate_total_training_time_computation(start_time, end_time)
            }
            return optimal_solution

        else:
            raise Exception('Please fit your dataset first!')

    def __initialize_particles(self):
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        N_FEATURES = self.N_FEATURES
        UB = self.optimizer['params']['UB']
        LB = self.optimizer['params']['UB']

        # initialize agents and velocities
        agents = np.random.uniform(LB, UB, (N_AGENTS, N_FEATURES))
        velocities = np.random.rand(N_AGENTS, N_FEATURES)

        # initialize pbest and gbest
        pbest = agents.copy()
        pbest_fitness = np.zeros(N_AGENTS)
        gbest = np.zeros(N_FEATURES)
        gbest_fitness = -np.inf
        best_fitness_previous = -np.inf
        if self.OBJECTIVE == 'min':
            gbest_fitness = np.inf
            best_fitness_previous = np.inf
        return agents, velocities, pbest, pbest_fitness, gbest, gbest_fitness, best_fitness_previous

    def __update_velocities_position_vectors(self, velocities, positions, pbest, gbest):
        N_PARTICLES = self.optimizer['params']['N_AGENTS']
        INERTIA = self.optimizer['params']['INERTIA']
        COGNITION_RATE = self.optimizer['params']['COGNITION_RATE']
        SOCIAL_RATE = self.optimizer['params']['SOCIAL_RATE']

        new_velocities = velocities.copy()
        new_positions = positions.copy()

        for i in range(N_PARTICLES):
            r1, r2 = np.random.rand(), np.random.rand()

            # update velocity (continous values)
            COGNITIVE_COMPONENT = COGNITION_RATE * \
                r1 * (pbest[i] - positions[i])
            SOCIAL_COMPONENT = SOCIAL_RATE * r2 * (gbest - positions[i])
            new_velocities[i] = INERTIA * velocities[i] + \
                COGNITIVE_COMPONENT + SOCIAL_COMPONENT

            # update position using the transfer functions on the new velocity
            new_positions[i] = self._standard_binarization_rule(
                [new_velocities[i]])[0].copy()

        return new_velocities, new_positions
