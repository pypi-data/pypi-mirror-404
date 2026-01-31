from .BaseMetaFeatureSelection import BaseMetaheuristics
from sklearn.neighbors import KNeighborsClassifier
import numpy as np
import time
import random as rd
import math


class WaOA(BaseMetaheuristics):
    def __init__(self,
                 N_WALRUS=50,
                 MAX_ITERATIONS=100,
                 MAX_CONVERGENCE=15,
                 OPTIMIZER_NAME='Walrus Optimization Algorithm',
                 BREAK_IF_CONVERGENCE=True,
                 FUNCTIONS={
                     'classifier': KNeighborsClassifier(),
                     'objective': 'max',
                     'transfer_binary_function': 'v_shaped_f2',
                     # f1_macro, f1_weighted, recall_macro, recall_weighted, precision_macro, precision_weighted, roc_auc_score_macro, roc_auc_score_weighted
                     'fitness_metric': 'f1_macro'
                 },
                 ):
        """Walrus Optimization Algorithm for optimizing features subset in Discrete Optimization

        Args:
            N_WALRUS (int): number of slime mould individual. Defaults to 50.
            MAX_ITERATIONS (int): maximum iterations. Defaults to 100.
            MAX_KONVERGEN (int): optimization will be stoped after MAX_KONVERGEN iterations. Defaults to 4.
            OPTIMIZER_NAME (str): your optimizer name will be. Defaults to 'Grey Wolf Optimizer'.
            FUNCTIONS (dict): objective function criteria. 
                - Defaults to { 'classifier': KNeighborsClassifier(),  'objective': 'max', 'transfer_binary_function':'s_shaped_f2', 'metric': 'accuracy' # (f1_macro, f1_weighted, recall_macro, recall_weighted, precision_macro, precision_weighted, roc_auc_score_macro, roc_auc_score_weighted) }.
            BREAK_IF_CONVERGENCE (bool): flag if optimization will be stopped after MAX_KONVERGEN. Defaults to True.
        """
        super().__init__(
            N_AGENTS=N_WALRUS,
            MAX_ITERATIONS=MAX_ITERATIONS,
            MAX_CONVERGENCE=MAX_CONVERGENCE,
            BREAK_IF_CONVERGENCE=BREAK_IF_CONVERGENCE,
            FUNCTIONS=FUNCTIONS
        )
        self.optimizer['name'] = OPTIMIZER_NAME

    def fit(self, X_train, y_train, X_test, y_test):
        super().fit(X_train, y_train, X_test, y_test)
        self._IS_FIT = True
        return self

    def solve(self):
        if self._IS_FIT:
            MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
            N_WALRUS = self.optimizer['params']['N_AGENTS']

            start_time = time.time()
            # 1. initialize agents
            agents, agents_fitness, best_fitness_previous = self._initialize_agents()

            # 2. Evaluate Agents and find the strongest walrus
            best_agent_position, best_agent_fitness = self._retrieve_best_agent(
                agents, agents_fitness)
            strongest_walrus = {
                'position': best_agent_position,
                'fitness': best_agent_fitness
            }

            self.LIST_BEST_FITNESS.append(strongest_walrus['fitness'])

            # 3. Optimization Process
            convergence = 0
            for idx_iteration in range(MAX_ITERATIONS):
                # exploration vs exploitation
                agents = self.__exploration_vs_exploitation(
                    agents, agents_fitness, strongest_walrus, idx_iteration)

                # adjust boundaries
                agents = self._adjust_boundaries(agents)

                # evaluate fitness
                for i in range(N_WALRUS):
                    # binarization and evaluate fitness
                    binary_walrus = self._standard_binarization_rule(
                        np.array([agents[i]])
                    )[0]
                    agents_fitness[i] = self._evaluate_fitness(binary_walrus)

                # select best agent
                best_agent_position_current, best_agent_fitness_current = self._retrieve_best_agent(
                    agents, agents_fitness)

                # 5. Terapkan Elitisme: Perbarui strongest_walrus HANYA JIKA fitness saat ini lebih baik
                # Karena objective adalah 'max', kita cari nilai yang lebih besar.
                if best_agent_fitness_current > strongest_walrus['fitness']:
                    strongest_walrus = {
                        'position': best_agent_position_current,
                        'fitness': best_agent_fitness_current
                    }

                # check convergence
                self.LIST_BEST_FITNESS.append(strongest_walrus['fitness'])
                is_break, best_fitness_previous, convergence = self._check_convergence(
                    strongest_walrus['fitness'], best_fitness_previous, convergence, idx_iteration)
                if is_break and self.BREAK_IF_CONVERGENCE:
                    break

            end_time = time.time()
            # Get optimal features
            binary_strongest_walrus_position = self._standard_binarization_rule(
                np.array([strongest_walrus['position']])
            )[0]
            optimal_solution = {
                'features_subset': binary_strongest_walrus_position,
                'selected_features': np.where(binary_strongest_walrus_position == 1)[0],
                'optimal_n_features': len(np.where(binary_strongest_walrus_position == 1)[0]),
                'best_fitness': strongest_walrus['fitness'],
                'start_time_computation': start_time,
                'end_time_computation': end_time,
                'total_train_time_computation': self._calculate_total_training_time_computation(start_time, end_time)
            }
            return optimal_solution

        else:
            raise Exception('Please fit your dataset first!')

    def __exploration_vs_exploitation(self, agents, agents_fitness, strongest_walrus, iteration):
        """
        Updates the positions of all agents based on the three WaOA phases.

        FIX: This method has been refactored to ensure the position updates are
        sequential. The result of each phase is used as the starting point for
        the next phase, preventing the trend of decreasing fitness and stagnation.
        """
        LB = self.optimizer['params']['LB']
        UB = self.optimizer['params']['UB']
        for idx_agent, agent in enumerate(agents):
            # Use a temporary variable to hold the agent's state as it is updated
            # through each phase. This ensures the updates are chained.
            current_agent = {
                'position': agent.copy(),
                'fitness': agents_fitness[idx_agent]
            }

            # Phase 1: Feeding Strategy (Exploration)
            # This uses the strongest walrus to guide the agent.
            current_agent = self.__feeding_strategy(
                current_agent, strongest_walrus)

            # Phase 2: Migration
            # This uses a randomly selected agent as a migration destination.
            random_agent = self.__generate_random_agent(
                agents, agents_fitness, current_agent)
            current_agent = self.__migration(
                current_agent, random_agent)

            # Phase 3: Escaping and Fighting with predators (Exploitation)
            # This performs local search around the current agent's position.
            current_agent = self.__attacking_predators(
                current_agent, iteration)

            # Update the agent in the main list with the final, updated state
            agents[idx_agent] = np.clip(
                current_agent['position'], LB, UB)

        return agents

    def __feeding_strategy(self, agent, strongest_walrus):
        """
        Implements Phase 1: Feeding Strategy (Exploration).
        Equation (3) from the paper.
        """
        I = rd.randint(1, 2)
        agent_phase_1 = agent.copy()
        # Generate a random vector for each dimension.
        rand = np.random.random(self.N_FEATURES)

        agent_phase_1.update({
            'position': agent['position'] + rand * (
                strongest_walrus['position'] - I * agent['position'])
        })

        # evaluate fitness function
        binary_agent_phase_1_position = self._standard_binarization_rule(
            np.array([agent_phase_1['position']])
        )[0]
        agent_phase_1['fitness'] = self._evaluate_fitness(
            binary_agent_phase_1_position)

        # update agent position if the new fitness is better
        # For maximization, '>' is the correct operator.
        if agent_phase_1['fitness'] > agent['fitness']:
            agent = agent_phase_1.copy()

        return agent

    def __migration(self, agent, random_agent):
        """
        Implements Phase 2: Migration.
        Equation (5) from the paper.
        """
        I = rd.randint(1, 2)
        agent_phase_2 = agent.copy()
        # Generate a random vector for each dimension.
        rand = np.random.random(self.N_FEATURES)

        # Corrected the condition for maximization.
        # The logic is: if the random agent is better, move towards it.
        # if the random agent is worse, move away from it.
        if random_agent['fitness'] > agent['fitness']:
            agent_phase_2['position'] = agent['position'] + rand * (
                random_agent['position'] - I * agent['position'])
        else:
            agent_phase_2['position'] = agent['position'] + \
                rand * (agent['position'] - random_agent['position'])

        # evaluate fitness function
        binary_agent_phase_2_position = self._standard_binarization_rule(
            np.array([agent_phase_2['position']])
        )[0]
        agent_phase_2['fitness'] = self._evaluate_fitness(
            binary_agent_phase_2_position)

        # update agent position if the new fitness is better
        if agent_phase_2['fitness'] > agent['fitness']:
            agent = agent_phase_2.copy()

        return agent

    def __attacking_predators(self, agent, iteration):
        """
        Implements Phase 3: Escaping and Fighting with predators (Exploitation).
        Equation (7) and (8) from the paper.
        """
        BATAS_BAWAH = self.optimizer['params']['LB']
        BATAS_ATAS = self.optimizer['params']['UB']
        t = iteration + 1  # iteration starts from 0, paper uses t from 1

        # calculate local upper and lower bound
        # Based on equation (8) from the paper.
        local_lb = BATAS_BAWAH / t
        local_up = BATAS_ATAS / t

        # calculate agent_phase_3
        # Corrected the formula to match equation (7) from the paper.
        agent_phase_3 = agent.copy()
        rand1 = np.random.random(self.N_FEATURES)
        rand2 = np.random.random(self.N_FEATURES)
        agent_phase_3['position'] = agent['position'] + \
            (local_lb + rand1 * (local_up - rand2 * local_lb))

        # evaluate fitness
        # evaluate fitness function
        binary_agent_phase_3_position = self._standard_binarization_rule(
            np.array([agent_phase_3['position']])
        )[0]
        agent_phase_3['fitness'] = self._evaluate_fitness(
            binary_agent_phase_3_position)

        # update agent position
        if agent_phase_3['fitness'] > agent['fitness']:
            agent = agent_phase_3.copy()

        return agent

    def __generate_random_agent(self, agents, agents_fitness, agent):
        """
        Randomly selects an agent that is not the same as the current one.
        """
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        # randomly select new agent m where m!=indeks agent
        # It's important to select from the original list, not the one being updated in the loop.
        # This prevents picking a walrus that has already moved in the current iteration.
        idx_random_agent = rd.randint(0, N_AGENTS - 1)
        random_agent = {
            'position': agents[idx_random_agent].copy(),
            'fitness': agents_fitness[idx_random_agent]
        }
        while np.array_equal(random_agent['position'], agent['position']):
            idx_random_agent = rd.randint(0, N_AGENTS - 1)
            random_agent = {
                'position': agents[idx_random_agent].copy(),
                'fitness': agents_fitness[idx_random_agent]
            }

        return random_agent
