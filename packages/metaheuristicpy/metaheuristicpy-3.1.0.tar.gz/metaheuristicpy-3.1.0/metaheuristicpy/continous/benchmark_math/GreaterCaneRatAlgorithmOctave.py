from .BaseMetaPy import BaseMetaPy
from .Utils import Utils
import random as rd
import numpy as np


class GCRA(BaseMetaPy, Utils):

    def __init__(self,
                 N_RATS=30,
                 MAX_ITERATIONS=200,
                 MAX_KONVERGEN=50,
                 RHO=0.58,
                 OPTIMIZER_NAME='Greater Cane Rat Algorithm from Original Octave',
                 FUNCTIONS={
                     'name': 'sphere',
                     'dimension': 15,
                     'lowerbound': -100,
                     'upperbound': 100,
                     'objective': 'min'
                 },
                 ):
        super().__init__(
            N_AGENTS=N_RATS,
            MAX_ITERATIONS=MAX_ITERATIONS,
            MAX_KONVERGEN=MAX_KONVERGEN,
            FUNCTIONS=FUNCTIONS,
            DROP_KEY_AGENTS=None
        )
        self.optimizer['name'] = OPTIMIZER_NAME
        self.optimizer['params'].update({
            "RHO": RHO,
        })

    def solve(self):
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
        RHO = self.optimizer['params']['RHO']
        OBJECTIVE = self.optimizer['params']['FUNCTIONS']['objective']
        N_DIMENSION = self.optimizer['params']['FUNCTIONS']['dimension']
        Lower_bound = self.optimizer['params']['FUNCTIONS']['lowerbound']
        Upper_bound = self.optimizer['params']['FUNCTIONS']['upperbound']
        FITNESS_FUNCTION = super().sphere

        # initialization
        Position = np.zeros()
        Score = float('inf')
        Gcanerats = np.random.uniform(
            Lower_bound, Upper_bound, (N_AGENTS, N_DIMENSION))
        Convergence = np.zeros(MAX_ITERATIONS)

        # select dominant male
        for i in range(Gcanerats.shape[0]):
            Flag4Upper_bound = Gcanerats[i, :] > Upper_bound
            Flag4Lower_bound = Gcanerats[i, :] < Lower_bound
            Gcanerats[i, :] = (Gcanerats[i, :] * (~(Flag4Upper_bound + Flag4Lower_bound))) + \
                Upper_bound * Flag4Upper_bound + Lower_bound * Flag4Lower_bound

            fitness = FITNESS_FUNCTION(Gcanerats[i, :])
            if fitness < Score:
                Score = fitness
                Position = Gcanerats[i, :]
                Alpha_pos1 = Position
                Alpha_score = Score

        # optimization
        while l < MAX_ITERATIONS:
            Alpha_pos = np.max(Alpha_pos1)
            GR_m = np.random.permutation(N_AGENTS - 1)[0]
            GR_rho = 0.5
            GR_r = Alpha_score - l * (Alpha_score / MAX_ITERATIONS)
            x, y = 1, 4
            GR_mu = np.floor((y - x) * np.random.rand() + x)
            GR_c = np.random.rand()
            GR_alpha = 2 * GR_r * np.random.rand() - GR_r
            GR_beta = 2 * GR_r * GR_mu - GR_r

            # update other gcr using equation 3
            for i in range(Gcanerats.shape[0]):
                for j in range(Gcanerats.shape[1]):
                    Gcanerats[i, j] = (Gcanerats[i, j] + Alpha_pos) / 2

            # update position: exploration vs exploitation
            for i in range(Gcanerats.shape[0]):
                for j in range(Gcanerats.shape[1]):
                    if np.random.rand() < GR_rho:
                        # exploration
                        Gcanerats[i, j] = Gcanerats[i, j] + GR_c * \
                            (Alpha_pos - GR_r * Gcanerats[i, j])
                        Flag4Upper_bound = Gcanerats[i, j] > Upper_bound
                        Flag4Lower_bound = Gcanerats[i, j] < Lower_bound
                        Gcanerats[i, j] = (Gcanerats[i, j] * (~(Flag4Upper_bound + Flag4Lower_bound))) + \
                            Upper_bound * Flag4Upper_bound + Lower_bound * Flag4Lower_bound

                        fitness = FITNESS_FUNCTION(Gcanerats[i, j])
                        if fitness < Score:
                            Score = fitness
                            Position = Gcanerats[i, j]
                        else:
                            Gcanerats[i, j] = Gcanerats[i, j] + GR_c * \
                                (Gcanerats[i, j] - GR_alpha * Alpha_pos)
                            Flag4Upper_bound = Gcanerats[i, j] > Upper_bound
                            Flag4Lower_bound = Gcanerats[i, j] < Lower_bound
                            Gcanerats[i, j] = (Gcanerats[i, j] * (~(Flag4Upper_bound + Flag4Lower_bound))) + \
                                Upper_bound * Flag4Upper_bound + Lower_bound * Flag4Lower_bound

                            fitness = FITNESS_FUNCTION(Gcanerats[i, j])
                            if fitness < Score:
                                Score = fitness
                                Position = Gcanerats[i, j]
                    else:
                        # exploitation
                        Gcanerats[i, j] = Gcanerats[i, j] + GR_c * \
                            (Alpha_pos - GR_mu * Gcanerats[GR_m, j])
                        Flag4Upper_bound = Gcanerats[i, j] > Upper_bound
                        Flag4Lower_bound = Gcanerats[i, j] < Lower_bound
                        Gcanerats[i, j] = (Gcanerats[i, j] * (~(Flag4Upper_bound + Flag4Lower_bound))) + \
                            Upper_bound * Flag4Upper_bound + Lower_bound * Flag4Lower_bound

                        fitness = FITNESS_FUNCTION(Gcanerats[i, j])
                        if fitness < Score:
                            Score = fitness
                            Position = Gcanerats[i, j]
                        else:
                            Gcanerats[i, j] = Gcanerats[i, j] + GR_c * \
                                (Gcanerats[GR_m, j] - GR_beta * Alpha_pos)
                            Flag4Upper_bound = Gcanerats[i, j] > Upper_bound
                            Flag4Lower_bound = Gcanerats[i, j] < Lower_bound
                            Gcanerats[i, j] = (Gcanerats[i, j] * (~(Flag4Upper_bound + Flag4Lower_bound))) + \
                                Upper_bound * Flag4Upper_bound + Lower_bound * Flag4Lower_bound

                            fitness = FITNESS_FUNCTION(Gcanerats[i, j])
                            if fitness < Score:
                                Score = fitness
                                Position = Gcanerats[i, j]

                    Alpha_pos1 = Position
                    Alpha_score = Score

            l += 1
            Convergence[l] = Score

        # variabel untuk menampung solusi akhir jika ditemukan solusi paling optimum
        best_agent = None
        best_fitness_old = float('-inf')
        if OBJECTIVE == 'min':
            best_fitness_old = float('inf')

        # initialize agents
        # 1. initialize agents
        agents = self._initialize_agents()
        # make sure each agents is inside the boundaries
        agents = self._adjust_boundaries(agents)

        # 2. Evaluate fitness
        agents = self._evaluate_fitness(agents)

        # 3. Select the fittest GCR as dominant male [Xk]
        GBest = self._retrieve_best_agent(agents)
        dominant_male = GBest.copy()

        # 5. Optimization Process
        konvergen = 0
        for idx_iteration in range(MAX_ITERATIONS):

            # Evaluate parameters: C,r, miu, alpha, betha
            params = self.__update_parameters(
                dominant_male, idx_iteration)

            # 4. Update GCR position based on Xk using Equation 3
            agents = self.__update_gcr_position_eq3(agents, dominant_male)

            # Exploitation vs Exploration
            agents, dominant_male = self.__exploitation_vs_exploration(
                agents, dominant_male, GBest, params)

            # 6. check konvergensi
            is_break, best_fitness_old, konvergen = self._check_convergence(
                agents, best_fitness_old, konvergen, idx_iteration)

            if is_break:
                best_agent = dominant_male.copy()
                break

        self._IS_SOLVE = True

        return best_agent

    def __update_gcr_position_eq3(self, agents, dominant_male):
        for idx_agent, agent in enumerate(agents):
            agents[idx_agent]['position'] = (
                agent['position']+dominant_male['position'])/2
        return agents

    def __update_parameters(self, dominant_male, current_iteration):
        """
        - C: random number defined within the problem space boundaries
        - r: simulates the effect of an abundant food source
        - alpha: A coefficient that simulates a diminishing food source
        - betha: A coefficient that prompts the GCR to move to other available abundant food sources within the breeding area
        - miu: randomly takes the values from 1 to 4
        """
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
        LOWER_BOUND = self.optimizer['params']['FUNCTIONS']['lowerbound']
        UPPER_BOUND = self.optimizer['params']['FUNCTIONS']['upperbound']

        fitness_dominant_male = dominant_male['fitness']

        r = fitness_dominant_male - current_iteration * \
            (fitness_dominant_male/MAX_ITERATIONS)
        miu = rd.randint(1, 3)  # constant between 1 to 3 (inclusive)
        C = np.random.random()
        alpha = 2 * r * np.random.random() - r
        betha = 2 * r * miu - r

        params = {
            'C': C,
            'r': r,
            'miu': miu,
            'alpha': alpha,
            'betha': betha,
        }
        return params

    def __exploitation_vs_exploration(self, agents, dominant_male, GBest, params):
        RHO = self.optimizer['params']['RHO']
        C = params['C']
        r = params['r']
        miu = params['miu']
        alpha = params['alpha']
        betha = params['betha']
        female = self.__random_select_female(agents, dominant_male)

        for idx_agent, agent in enumerate(agents):
            if np.random.random() < RHO:
                # Exploration (berburu sumber makanan baru)
                agents[idx_agent]['position'] = agent['position'] + \
                    C*(dominant_male['position']-r*agent['position'])

                # adjust boundaries
                agents[idx_agent] = self._adjust_boundaries(
                    [agents[idx_agent]])[0]

                # hitung fitness objective
                agents[idx_agent] = self._evaluate_fitness(
                    [agents[idx_agent]])[0]

                # jika objective functionnya min
                if agents[idx_agent]['fitness'] < GBest['fitness']:
                    GBest = agents[idx_agent].copy()
                else:
                    agents[idx_agent]['position'] = agent['position'] + \
                        C*(agent['position'] - alpha *
                           dominant_male['position'])

                    # adjust boundaries
                    agents[idx_agent] = self._adjust_boundaries(
                        [agents[idx_agent]])[0]

                    # hitung fitness objective
                    agents[idx_agent] = self._evaluate_fitness(
                        [agents[idx_agent]])[0]

                    if agents[idx_agent]['fitness'] < GBest['fitness']:
                        GBest = agents[idx_agent].copy()

            else:
                # exploitation (breeding season so the foraging activities are concentrated within areas with abundant food sources)
                agents[idx_agent]['position'] = agent['position'] + \
                    C*(dominant_male['position']-miu*female['position'])

                # adjust boundaries
                agents[idx_agent] = self._adjust_boundaries(
                    [agents[idx_agent]])[0]

                # hitung fitness objective
                agents[idx_agent] = self._evaluate_fitness(
                    [agents[idx_agent]])[0]

                if agents[idx_agent]['fitness'] < GBest['fitness']:
                    GBest = agents[idx_agent].copy()
                else:
                    agents[idx_agent]['position'] = agent['position'] + \
                        C*(female['position']-betha*dominant_male['position'])

                    # adjust boundaries
                    agents[idx_agent] = self._adjust_boundaries(
                        [agents[idx_agent]])[0]

                    # hitung fitness objective
                    agents[idx_agent] = self._evaluate_fitness(
                        [agents[idx_agent]])[0]
                    if agents[idx_agent]['fitness'] < GBest['fitness']:
                        GBest = agents[idx_agent].copy()

            dominant_male = GBest.copy()

        return agents, dominant_male

    def __random_select_female(self, agents, dominant_male):
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        # randomly select female m where m!=indeks dominant_male
        female = agents[rd.randint(0, N_AGENTS-1)]
        while female['name'] == dominant_male['name']:
            female = agents[rd.randint(0, N_AGENTS-1)]
        return female
