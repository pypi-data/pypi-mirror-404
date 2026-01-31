from .BaseMetaFeatureSelection import BaseMetaheuristics
from sklearn.neighbors import KNeighborsClassifier
import numpy as np
import time
import random as rd


class GCRA(BaseMetaheuristics):

    def __init__(self,
                 N_RATS=30,
                 MAX_ITERATIONS=100,
                 RHO=0.5,
                 MAX_CONVERGENCE=10,
                 OPTIMIZER_NAME='Greater Cane Rat Algorithm',
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
            N_AGENTS=N_RATS,
            MAX_ITERATIONS=MAX_ITERATIONS,
            MAX_CONVERGENCE=MAX_CONVERGENCE,
            FUNCTIONS=FUNCTIONS,
            BREAK_IF_CONVERGENCE=BREAK_IF_CONVERGENCE,
        )
        self.optimizer['name'] = OPTIMIZER_NAME
        self.optimizer['params'].update({
            "RHO": RHO,
        })

    def fit(self, X_train, y_train, X_test, y_test):
        super().fit(X_train, y_train, X_test, y_test)
        self._IS_FIT = True
        return self

    def solve(self):
        if self._IS_FIT:
            N_AGENTS = self.optimizer['params']['N_AGENTS']
            MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
            LB = self.optimizer['params']['LB']
            UB = self.optimizer['params']['UB']
            N_FEATURES = self.N_FEATURES
            RHO = self.optimizer['params']['RHO']
            TRANSFER_FUNCTION = self.optimizer['transfer_function']

            start_time = time.time()
            # 1. Initialize agents
            agents, agents_fitness, best_fitness_previous = self._initialize_agents()

            # 2. Initialize Dominant male (Xk)
            dominant_male = self.__initialize_dominant_male(
                agents, agents_fitness)

            # 3. update the remaining GR based on Xk using Eq.3
            agents = self.__update_gcr_position(agents, dominant_male)

            # 4. GCRA main loop
            convergence = 0
            for iteration in range(MAX_ITERATIONS):
                # 6. update parameters
                params = self.__update_parameters(
                    dominant_male['fitness'], iteration)

                # 7.update position: exploitation vs exploration
                agents, agents_fitness, dominant_male = self.__update_position_exploration_exploitation(
                    agents, agents_fitness, dominant_male, params)

                # check convergence
                dominant_male_binary_solution = self._standard_binarization_rule(
                    [dominant_male['position']])[0]
                GBest = dominant_male_binary_solution.copy()
                GBest_fitness = dominant_male['fitness']

                self.LIST_BEST_FITNESS.append(GBest_fitness)
                is_break, best_fitness_previous, convergence = self._check_convergence(
                    GBest_fitness, best_fitness_previous, convergence, iteration)
                if is_break and self.BREAK_IF_CONVERGENCE:
                    break

            end_time = time.time()
            # Get optimal features
            optimal_solution = {
                'features_subset': GBest,
                'selected_features': np.where(GBest == 1)[0],
                'optimal_n_features': len(np.where(GBest == 1)[0]),
                'best_fitness': GBest_fitness,
                'start_time_computation': start_time,
                'end_time_computation': end_time,
                'total_train_time_computation': self._calculate_total_training_time_computation(start_time, end_time)
            }
            return optimal_solution

        else:
            raise Exception('Please fit your dataset first!')

    def __initialize_dominant_male(self, agents, agents_fitness):
        # calculate the fitness values from all agents, and then select the fittest agent as dominant male
        binary_agents = self._standard_binarization_rule(agents)
        agents_fitness = np.array([
            self._evaluate_fitness(agent) for agent in binary_agents
        ])

        idx_best_fitness = np.argmax(agents_fitness)
        best_fitness = agents_fitness[idx_best_fitness]
        best_agent = agents[idx_best_fitness].copy()
        if self.OBJECTIVE == 'min':
            idx_best_fitness = np.argmin(agents_fitness)
            best_fitness = agents_fitness[idx_best_fitness]
            best_agent = agents[idx_best_fitness].copy()

        dominant_male = {
            'position': best_agent,
            'fitness': best_fitness
        }
        return dominant_male

    def __update_gcr_position(self, agents, dominant_male):
        """
        Update GCR position using Equation 3
        """
        for idx_agent, agent in enumerate(agents):
            agents[idx_agent] = 0.7 * ((agent+dominant_male['position'])/2)
        return agents

    def __update_parameters(self, dominant_male_fitness, current_idx_teration):
        """
        - C: random number defined within the problem space boundaries
        - r: simulates the effect of an abundant food source
        - alpha: A coefficient that simulates a diminishing food source
        - betha: A coefficient that prompts the GCR to move to other available abundant food sources within the breeding area
        - miu: randomly takes the values from 1 to 4
        """
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
        r = dominant_male_fitness - current_idx_teration * \
            (dominant_male_fitness/MAX_ITERATIONS)
        miu = np.random.randint(1, 5)  # constant between 1 to 4 (inclusive)
        C = np.random.rand()
        alpha = 2 * r * np.random.rand() - r
        betha = 2 * r * miu - r
        params = {
            'C': C,
            'r': r,
            'miu': miu,
            'alpha': alpha,
            'betha': betha,
        }
        return params

    def __update_position_exploration_exploitation(self, agents, agents_fitness, dominant_male, params):
        """
        Function untuk update posisi GCR berdasarkan phase exploration (berburu sumber makanan, diversification) atau exploitation (breeding season so the foraging activities are concentrated within areas with abundant food sources atau Intensification) 
        """
        RHO = self.optimizer['params']['RHO']
        UB = self.optimizer['params']['UB']
        LB = self.optimizer['params']['LB']
        C = params['C']
        r = params['r']
        alpha = params['alpha']
        miu = params['miu']
        betha = params['betha']

        for idx_agent, agent in enumerate(agents):
            if np.random.rand() < RHO:
                # exploration
                temp_new_position = agent + C * \
                    (dominant_male['position'] - r * agent)
                new_fitness_agent = self._evaluate_fitness(
                    self._standard_binarization_rule(
                        np.array([temp_new_position])
                    )[0]
                )
                if new_fitness_agent > dominant_male['fitness']:
                    agents[idx_agent] = temp_new_position.copy()
                else:
                    agents[idx_agent] = agents[idx_agent] + C * \
                        (agents[idx_agent] - alpha * dominant_male['position'])
            else:
                # exploitation

                # random female rat
                female_rat = self.__select_random_female_rat(agents)
                temp_new_position = agent + C * \
                    (dominant_male['position'] - miu * female_rat)
                new_fitness_agent = self._evaluate_fitness(
                    self._standard_binarization_rule(
                        np.array([temp_new_position])
                    )[0]
                )
                if new_fitness_agent > dominant_male['fitness']:
                    agents[idx_agent] = temp_new_position.copy()
                else:
                    # update search agent using Eq.5
                    agents[idx_agent] = agents[idx_agent] + C * \
                        (female_rat - betha * dominant_male['position'])

            # apply boundary constraint
            agents[idx_agent] = np.clip(agents[idx_agent], LB, UB)
            binary_agent = self._standard_binarization_rule(
                [agents[idx_agent]])[0]
            agents_fitness[idx_agent] = self._evaluate_fitness(binary_agent)

            # update dominant male
            if agents_fitness[idx_agent] > dominant_male['fitness']:
                dominant_male = {
                    'position': agents[idx_agent],
                    'fitness': agents_fitness[idx_agent]
                }

            # update agent position
            agents[idx_agent] = 0.7 * \
                ((agents[idx_agent]+dominant_male['position'])/2)

        return agents, agents_fitness, dominant_male

    def __select_random_female_rat(self, agents):
        """
        Function untuk memilih female rat secara random
        """
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        female_rat = agents[np.random.randint(
            0, N_AGENTS
        )].copy()
        return female_rat
