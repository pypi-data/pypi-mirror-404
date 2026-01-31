from .BaseMetaPy import BaseMetaPy
from .Utils import Utils
import random as rd
import numpy as np


class PSOClassic(BaseMetaPy, Utils):

    def __init__(self,
                 N_PARTICLES=50,
                 MAX_ITERATIONS=100,
                 INERTIA_MAX=0.9,
                 INERTIA_MIN=0.4,
                 COGNITION_RATE=0.5,
                 SOCIAL_RATE=0.3,
                 MAX_KONVERGEN=50,
                 V_MAX=3,
                 FUNCTIONS={
                     'name': 'sphere',
                     'dimension': 5,
                     'lowerbound': -100,
                     'upperbound': 100,
                     'objective': 'min'
                 },
                 OPTIMIZER_NAME='Particle Swarm Optimization (Classic)'
                 ):
        super().__init__(
            N_AGENTS=N_PARTICLES,
            MAX_ITERATIONS=MAX_ITERATIONS,
            MAX_KONVERGEN=MAX_KONVERGEN,
            FUNCTIONS=FUNCTIONS,
            DROP_KEY_AGENTS=None
        )
        self.optimizer['name'] = OPTIMIZER_NAME
        self.optimizer['params'].update({
            "INERTIA_MAX": INERTIA_MAX,
            "INERTIA_MIN": INERTIA_MIN,
            "COGNITION_RATE": COGNITION_RATE,
            "SOCIAL_RATE": SOCIAL_RATE,
            "V_MAX": V_MAX,
            "V_MIN": -1*V_MAX
        })

    def solve(self):
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
        N_PARTICLES = self.optimizer['params']['N_AGENTS']

        # initialize agents
        # 1. initialize agents
        agents = self._initialize_agents()
        agents = self.__initialize_agents_velocities(agents)
        best_agent = agents[rd.randint(0, N_PARTICLES-1)].copy()
        self.LIST_BEST_FITNESS.append(best_agent['fitness'])

        # 3. Optimization Process
        for idx_iteration in range(MAX_ITERATIONS):
            # 3. Update vector velocities and position
            agents = self.__update_vector_velocities_position(
                agents, best_agent, idx_iteration)

            # 4. Evaluate agents
            agents = self._evaluate_fitness(agents)

            # 5. Update pBest and gBest
            agents, best_agent = self.__update_pBest_gBest(agents, best_agent)

            # 6. check konvergensi
            print('Iteration {}, Best Cost: {:.4f}'.format(
                idx_iteration, best_agent['fitness']))
            self.LIST_BEST_FITNESS.append(best_agent['fitness'])

        self._IS_SOLVE = True

        return best_agent

    def __initialize_agents_velocities(self, agents):
        N_DIMENSION = self.optimizer['params']['FUNCTIONS']['dimension']
        for idx_agent, agent in enumerate(agents):
            random_velocities = np.array([0 for d in range(N_DIMENSION)])
            agent.update({
                "velocities": random_velocities,
            })
        return agents

    def __update_pBest_gBest(self, agents, best_agent):
        current_fitness = list()
        for idx_particle, particle in enumerate(agents):
            current_fitness.append(particle['fitness'])
            if particle['fitness'] < particle['PBest']['fitness']:
                # update position dan fitness PBest
                particle['PBest']['position'] = particle['position'].copy()
                particle['PBest']['fitness'] = particle['fitness']

        # mekanisme perhitungan best_agent
        # cari pBest terbaik dari swarm saat iterasi saat ini (t)
        best_fitness_index = np.argmin(current_fitness)
        if current_fitness[best_fitness_index] < best_agent['fitness']:
            best_agent = agents[best_fitness_index].copy()

        return agents, best_agent

    def __update_vector_velocities_position(self, agents, best_agent, iteration):
        INERTIA_MAX = self.optimizer['params']['INERTIA_MAX']
        INERTIA_MIN = self.optimizer['params']['INERTIA_MIN']
        COGNITION_RATE = self.optimizer['params']['COGNITION_RATE']
        SOCIAL_RATE = self.optimizer['params']['SOCIAL_RATE']
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
        V_MAX = self.optimizer['params']['V_MAX']
        V_MIN = self.optimizer['params']['V_MIN']
        BATAS_BAWAH = self.optimizer['params']['FUNCTIONS']['lowerbound']
        BATAS_ATAS = self.optimizer['params']['FUNCTIONS']['upperbound']

        for idx_particle, particle in enumerate(agents):
            pbest = particle['PBest']['position']
            gbest = best_agent['position']
            positions = particle['position']
            velocities = particle['velocities']

            # perbarui vektor kecepatan
            INERTIA = (INERTIA_MAX - INERTIA_MIN) * \
                ((MAX_ITERATIONS-iteration)/MAX_ITERATIONS) + INERTIA_MIN
            velocities = (INERTIA*velocities) + (COGNITION_RATE * np.random.random()*(
                pbest-positions)) + (SOCIAL_RATE * np.random.random() * (gbest - positions))

            # apply velocities boundaries
            agents[idx_particle]['velocities'] = np.clip(
                velocities, V_MIN, V_MAX)

            # update position
            positions += velocities

            # apply position boundaries
            agents[idx_particle]['position'] = np.clip(
                positions, BATAS_BAWAH, BATAS_ATAS)

        return agents
