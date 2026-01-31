import numpy as np
from .BenchmarkFormulas import BenchmarkMathematicFormulas
import random as rd
import math


class BaseMetaPy(BenchmarkMathematicFormulas):
    def __init__(self,
                 N_AGENTS,
                 MAX_ITERATIONS,
                 MAX_KONVERGEN,
                 FUNCTIONS,
                 **kwargs):
        """
        Base class for other metaheuristic classes

        <Args>
        - N_AGENTS <Integer>: number of population or swarm size 
        - MAX_ITERATIONS <Integer>: number of maximum iteration
        - MAX_KONVERGEN <Integer>: The iteration process will be stoped if the fitness value is the same for MAX_KONVERGEN consecutive iterations 
        - FUNCTIONS <String>: Name of benchmark mathematical formula
            -> Options: sphere, rastrigin, griewank, ackley_function, rosenbrock_function, schwefel_function, levi_function, zakharov_function, sum_of_different_powers_function, michalewicz_function, easom_function, six_hump_camel_function, beale_function
        """
        self.optimizer = {
            "name": None,
            "params": {
                'N_AGENTS': N_AGENTS,
                'MAX_ITERATIONS': MAX_ITERATIONS,
                "MAX_KONVERGEN": MAX_KONVERGEN,
                "FUNCTIONS": FUNCTIONS
            }
        }
        self.DROP_KEY_AGENTS = kwargs['DROP_KEY_AGENTS']
        self._IS_SOLVE = False
        self.__retrieve_fitness_function(
            function_name=self.optimizer['params']['FUNCTIONS']['name']
        )

        # record best fitness each iterations:
        self.LIST_BEST_FITNESS = list()

    def solve(self):
        pass

    def __retrieve_fitness_function(self, function_name):
        self.FITNESS_FUNCTION = super().sphere
        if function_name == "rastrigin":
            self.FITNESS_FUNCTION = super().rastrigin
        elif function_name == "griewank":
            self.FITNESS_FUNCTION = super().griewank
        elif function_name == "ackley_function":
            self.FITNESS_FUNCTION = super().ackley_function
        elif function_name == "rosenbrock_function":
            self.FITNESS_FUNCTION = super().rosenbrock_function
        elif function_name == "schwefel_function":
            self.FITNESS_FUNCTION = super().schwefel_function
        elif function_name == "levi_function":
            self.FITNESS_FUNCTION = super().levi_function
        elif function_name == "zakharov_function":
            self.FITNESS_FUNCTION = super().zakharov_function
        elif function_name == "sum_of_different_powers_function":
            self.FITNESS_FUNCTION = super().sum_of_different_powers_function
        elif function_name == "michalewicz_function":
            self.FITNESS_FUNCTION = super().michalewicz_function
        elif function_name == "easom_function":
            self.FITNESS_FUNCTION = super().easom_function
        elif function_name == "six_hump_camel_function":
            self.FITNESS_FUNCTION = super().six_hump_camel_function
        elif function_name == "beale_function":
            self.FITNESS_FUNCTION = super().beale_function

    def _initialize_agents(self, new_N_AGENTS=None):
        """
        Function untuk inisialisasi agents sesuai jumlah dimensi
        """
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        if new_N_AGENTS is not None:
            N_AGENTS = new_N_AGENTS
        N_DIMENSION = self.optimizer['params']['FUNCTIONS']['dimension']
        LOWER_BOUND = self.optimizer['params']['FUNCTIONS']['lowerbound']
        UPPER_BOUND = self.optimizer['params']['FUNCTIONS']['upperbound']
        OBJECTIVE = self.optimizer['params']['FUNCTIONS']['objective']

        agents = [None for _ in range(N_AGENTS)]
        for idx_agent in range(N_AGENTS):
            random_position = np.array(
                [
                    np.random.random() * (UPPER_BOUND - LOWER_BOUND) + LOWER_BOUND
                    for d in range(N_DIMENSION)
                ]
            )
            agents[idx_agent] = {
                "name": f"Agent-{idx_agent}",
                "position": random_position,

            }
            # update inisialisasi nilai fitness
            fitness = {
                'fitness': float("-inf")
            }
            agents[idx_agent].update()
            if OBJECTIVE == 'min':
                fitness = {
                    'fitness': float("inf")
                }
            agents[idx_agent].update(fitness)

            # update inisialisasi nilai PBest
            agents[idx_agent].update({
                'PBest': {
                    'position': random_position,
                    **fitness
                }
            })

        return agents

    def _adjust_boundaries(self, agents):
        BATAS_BAWAH = self.optimizer['params']['FUNCTIONS']['lowerbound']
        BATAS_ATAS = self.optimizer['params']['FUNCTIONS']['upperbound']
        for idx_agent, agent in enumerate(agents):
            agents[idx_agent]['position'] = np.clip(
                agents[idx_agent]['position'], BATAS_BAWAH, BATAS_ATAS)
        return agents

    def _evaluate_fitness(self, agents):
        """
        Fungsi untuk evaluasi fitness berdasarkan fungsi fitness yang diinputkan
        F(P[i]) = fitness_function(P[i])
        fitness_function:
            -sphere: Sphere Function
            -rastrigin: Rastrigin Function
            -griewank: Griewank Function
            dst
        """

        for idx_agent, agent in enumerate(agents):
            agents[idx_agent]['fitness'] = self.FITNESS_FUNCTION(
                agent['position'])
        return agents

    def _retrieve_best_agent(self, agents):
        """
        Function untuk retrieve best agent pada iterasi terakhir setelah di solve
        """
        OBJECTIVE = self.optimizer['params']['FUNCTIONS']['objective']

        fitness = np.array([
            agent_data['fitness'] for agent_data in agents
        ])
        best_indices_agents = np.argmin(fitness)
        if OBJECTIVE == 'max':
            best_indices_agents = np.argmax(fitness)

        return agents[best_indices_agents].copy()

    def _retrieve_worst_agent(self, agents):
        """
        Function untuk retrieve worst agent pada iterasi terakhir setelah di solve
        """
        OBJECTIVE = self.optimizer['params']['FUNCTIONS']['objective']

        fitness = np.array([
            agent_data['fitness'] for agent_data in agents
        ])
        worst_indices_agents = np.argmax(fitness)
        if OBJECTIVE == 'max':
            worst_indices_agents = np.argmin(fitness)

        return agents[worst_indices_agents].copy()

    def _check_convergence(self, agents, best_fitness_old, konvergen, idx_iteration):
        MAX_KONVERGEN = self.optimizer['params']['MAX_KONVERGEN']
        OBJECTIVE = self.optimizer['params']['FUNCTIONS']['objective']
        is_break = False

        # retrieve semua nilai fitness dari agents
        fitnesses = [agent_data['fitness'] for agent_data in agents]
        best_fitness = min(fitnesses)
        if OBJECTIVE == 'max':
            best_fitness = max(fitnesses)

        self.LIST_BEST_FITNESS.append(best_fitness)
        if math.isclose(best_fitness_old, best_fitness, rel_tol=1e-9, abs_tol=1e-9):
            konvergen += 1
        else:
            konvergen = 0
        print(
            f'Generation {idx_iteration + 1}, Best Fitness: {best_fitness}, Konvergen: {konvergen}')
        best_fitness_old = best_fitness
        if konvergen == MAX_KONVERGEN:
            print(f'Convergent is reached = {MAX_KONVERGEN}')
            is_break = True
        return is_break, best_fitness_old, konvergen

    def get_optimizer_params(self):
        return self.optimizer['params']

    def get_fitness_values(self):
        if self._IS_SOLVE:
            return self.LIST_BEST_FITNESS
        else:
            raise Exception("Please solve the problem first!")

    def _levy_flight(self):
        N_DIMENSION = self.optimizer['params']['FUNCTIONS']['dimension']
        beta = 1.5
        # Perhitungan Sigma sesuai Eq. 18 [cite: 238]
        sigma = (math.gamma(1 + beta) * math.sin(math.pi * beta / 2) /
                 (math.gamma((1 + beta) / 2) * beta * 2 ** ((beta - 1) / 2))) ** (1 / beta)

        u = np.random.randn(N_DIMENSION) * sigma
        v = np.random.randn(N_DIMENSION)

        # Perhitungan step sesuai Eq. 17 [cite: 234]
        step = u / (np.abs(v) ** (1 / beta))

        # Catatan: Source code Matlab asli tidak mengalikan dengan 0.05 di dalam fungsi ini,
        # Namun paper (Eq 17) menyebutkan 0.05.
        # Kita mengikuti source code Matlab MO.m baris 60 yang menggunakannya langsung sebagai pengali.
        return step
