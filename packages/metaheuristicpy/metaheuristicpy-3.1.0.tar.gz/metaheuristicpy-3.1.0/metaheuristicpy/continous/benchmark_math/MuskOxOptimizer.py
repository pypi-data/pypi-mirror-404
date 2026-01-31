from .BaseMetaPy import BaseMetaPy
from .Utils import Utils
import random as rd
import numpy as np
import math


class MO(BaseMetaPy, Utils):

    def __init__(self,
                 N_MUSKOX=50,
                 MALE_FEMALE_PERCENTAGE=0.4,
                 MAX_ITERATIONS=500,
                 MAX_KONVERGEN=100,
                 OPTIMIZER_NAME='Musk-ox Optimizer',
                 FUNCTIONS={
                     'name': 'sphere',
                     'dimension': 15,
                     'lowerbound': -100,
                     'upperbound': 100,
                     'objective': 'min'
                 },
                 ):
        super().__init__(
            N_AGENTS=N_MUSKOX,
            MAX_ITERATIONS=MAX_ITERATIONS,
            MAX_KONVERGEN=MAX_KONVERGEN,
            FUNCTIONS=FUNCTIONS,
            DROP_KEY_AGENTS=None
        )
        self.optimizer['name'] = OPTIMIZER_NAME

        MALE_MO_NUMBER = round(N_MUSKOX*MALE_FEMALE_PERCENTAGE)
        FEMALE_JUVENILE_MO_NUMBER = N_MUSKOX - MALE_MO_NUMBER
        self.optimizer['params'].update({
            "MALE_FEMALE_PERCENTAGE": MALE_FEMALE_PERCENTAGE,
            "MALE_MO_NUMBER": MALE_MO_NUMBER,
            "FEMALE_JUVENILE_MO_NUMBER": FEMALE_JUVENILE_MO_NUMBER,
        })

    def solve(self):
        MAX_ITERATIONS = self.optimizer['params']['MAX_ITERATIONS']
        LOWER_BOUND = self.optimizer['params']['FUNCTIONS']['lowerbound']
        UPPER_BOUND = self.optimizer['params']['FUNCTIONS']['upperbound']
        N_AGENTS = self.optimizer['params']['N_AGENTS']
        MALE_MO_NUMBER = self.optimizer['params']['MALE_MO_NUMBER']
        FEMALE_JUVENILE_MO_NUMBER = self.optimizer['params']['FEMALE_JUVENILE_MO_NUMBER']
        OBJECTIVE = self.optimizer['params']['FUNCTIONS']['objective']
        N_DIMENSION = self.optimizer['params']['FUNCTIONS']['dimension']

        # Inisialisasi Populasi awal
        agents = self._initialize_agents()
        # Variabel untuk menyimpan Global Best Solution
        state_fitness = float('inf')
        if OBJECTIVE == 'max':
            state_fitness = float('-inf')
        best_global_agent = {
            'fitness': state_fitness,
            'position': np.zeros(N_DIMENSION)
        }
        best_fitness_old = state_fitness

        # Optimization process
        konvergen_count = 0
        for idx_iteration in range(MAX_ITERATIONS):

            # ----------------------------------------------------------------
            # STEP 1: Boundary Check, Fitness Evaluation, Update Best/Second/Worst
            # Sesuai Matlab baris 10-22
            # ----------------------------------------------------------------

            # adjust boundaries
            agents = self._adjust_boundaries(agents)

            # hitung fitness
            agents = self._evaluate_fitness(agents)

            # initialize best agent, second best agent, worst agent
            current_best_agent = agents[rd.randint(0, N_AGENTS-1)].copy()
            current_second_best_agent = agents[rd.randint(
                0, N_AGENTS-1)].copy()
            current_worst_agent = agents[rd.randint(0, N_AGENTS-1)].copy()

            # ----------------------------------------------------------------
            # STEP 2: Update Sinyal Kewaspadaan (Alert dan Safety Signal)
            # ----------------------------------------------------------------

            # Update Sinyal Kewaspadaan (Alert dan Safety Signal)
            Alpha1 = 1 - (idx_iteration/MAX_ITERATIONS)
            # Eq. (5): A = 2 * Alpha1 * (1 - r1) [cite: 180]
            r1 = np.random.rand()
            A = 2 * Alpha1
            Danger_signal = A * (1 - r1)
            # Eq. (6): Safety signal = r2 [cite: 183]
            r2 = np.random.rand()
            Safety_signal = r2

            # ----------------------------------------------------------------
            # STEP 3: Fase Update Posisi (Exploration & Exploitation)
            # ----------------------------------------------------------------

            # Fase Eksplorasi
            if abs(Danger_signal) >= 1:
                # Eq. (9): Menghitung faktor langkah alpha2 (Beta di Matlab)
                Beta = 1 - 1 / \
                    (1 + math.exp((0.5 * MAX_ITERATIONS -
                     idx_iteration) / MAX_ITERATIONS * 10))

                # Eq. (8): Migration Step secara Vectorized (Sesuai Matlab X(randperm) - X(randperm))
                # Kita butuh random permutation indices
                idx_perm_1 = np.random.permutation(N_AGENTS)
                idx_perm_2 = np.random.permutation(N_AGENTS)

                # Buat matriks posisi seluruh agent
                X_all = np.array([agent['position'] for agent in agents])

                # Generate random r3 vector (N, 1)
                r3 = np.random.rand(N_AGENTS, 1)

                # Hitung step untuk seluruh populasi sekaligus
                # Shape: (N, 1) * (N, Dim) = (N, Dim)
                Migration_step_vector = (
                    Beta ** 2) * (r3 ** 4) * (X_all[idx_perm_1] - X_all[idx_perm_2])

                # Update posisi
                for i in range(N_AGENTS):
                    agents[i]['position'] = agents[i]['position'] + \
                        Migration_step_vector[i]

            # 4. Fase Eksploitasi: Roosting [cite: 200, 201]
            else:
                # a. Perilaku Mencari Makan (Foraging Behavior)
                if Safety_signal >= 0.5:
                    # Eq. (12): Faktor Wi [cite: 212]
                    G01 = 0.001
                    Alpha2 = 0.01
                    Wi = G01 * \
                        (1 / math.exp(Alpha2 * idx_iteration / MAX_ITERATIONS))

                    for i in range(N_AGENTS):
                        r4 = np.random.rand()
                        # Eq. (11): Delta x1 [cite: 211]
                        # X_new = X + (Best - X) + rand^3 * Wi * (X - Best)
                        # Term (Best - X) ditambahkan ke X hasilnya Best.
                        # Jadi rumusnya simplifikasinya: Best + rand^3 * Wi * (X - Best)
                        # Implementasi sesuai Matlab baris 46:
                        current_pos = agents[i]['position']

                        term1 = current_best_agent['position'] - current_pos
                        term2 = (np.random.rand()**3) * Wi * \
                            (current_pos - current_best_agent['position'])

                        agents[i]['position'] = current_pos + term1 + term2

                # b. Perilaku Bertahan (Defensive Behavior)
                else:
                    G02 = 100
                    Alpha3 = 0.01
                    # Eq. (15): Faktor Mi (Wi di Matlab untuk fase ini) [cite: 224]
                    Mi = G02 * \
                        (1 / math.exp(Alpha3 * idx_iteration / MAX_ITERATIONS))

                    # Group 1: Male Musk Oxen (Adults) [cite: 222]
                    for i in range(MALE_MO_NUMBER):
                        r5 = np.random.rand()
                        # Eq. (14): Delta x2 [cite: 223]
                        term1 = (np.random.rand(
                        )**2) * (current_second_best_agent['position'] - current_best_agent['position'])
                        term2 = np.random.rand() * Mi * \
                            (current_best_agent['position'] -
                             current_worst_agent['position'])

                        agents[i]['position'] = agents[i]['position'] + \
                            term1 + term2

                    # Group 2: Female and Juvenile [cite: 229]
                    # Indeks M_number sampai selesai.
                    # PERBAIKAN: Di Matlab aslinya loop i=1:FC_number lalu update X(i,:).
                    # Itu MENIMPA hasil Group 1. Ini jelas bug di source code Matlab asli.
                    # Di sini kita gunakan indeks yang benar: range(M_number, self.N)
                    levy_vec = self._levy_flight()
                    for idx_female_juvenile in range(MALE_MO_NUMBER, N_AGENTS):
                        r6 = np.random.rand()
                        # Eq. (16): X_new = X + r6 * (Best - X) * Levy [cite: 230]
                        # Perhatikan Matlab baris 60: X(i,:) = rand*(Best_Pos-X(i,:)).*levyFlight(dim);
                        # Matlab code menggunakan '=' bukan '+='. Namun Paper Eq 16 biasanya update.
                        # Tetapi melihat kode Matlab baris 60: "X(i,:) = ..." (Assignment).
                        # Kita ikuti kode Matlab untuk "Implementation according to source code".
                        agents[idx_female_juvenile]['position'] = r6 * (
                            current_best_agent['position'] - agents[idx_female_juvenile]['position']) * levy_vec

            # ----------------------------------------------------------------
            # Check Convergence (Opsional)
            # ----------------------------------------------------------------
            is_break, best_fitness_old, konvergen_count = self._check_convergence(
                agents, best_fitness_old, konvergen_count, idx_iteration
            )
            if is_break:
                break

            # update best agent, second best, and worst agent
            current_best_agent = self._retrieve_best_agent(agents)
            current_second_best_agent = self._update_second_best_leader(
                agents, current_best_agent, current_second_best_agent)
            current_worst_agent = self._retrieve_worst_agent(agents)

            # update best_global_agent
            best_global_agent = self._update_best_global_agent(
                best_global_agent, current_best_agent)

            # Record convergence history
            self.LIST_BEST_FITNESS.append(best_global_agent['fitness'])
            print(
                f'Iteration {idx_iteration}, Best Cost: {best_global_agent["fitness"]:.4e}')

        self._IS_SOLVE = True
        return best_global_agent

    def _update_best_global_agent(self, best_global_agent, current_best_agent):
        OBJECTIVE = self.optimizer['params']['FUNCTIONS']['objective']
        if OBJECTIVE == 'min':
            if current_best_agent['fitness'] < best_global_agent['fitness']:
                best_global_agent = current_best_agent.copy()
        elif OBJECTIVE == 'max':
            if current_best_agent['fitness'] > best_global_agent['fitness']:
                best_global_agent = current_best_agent.copy()
        return best_global_agent

    def _update_second_best_leader(self, agents, best_agent, second_best_agent):
        for agent_data in agents:
            if agent_data['fitness'] < best_agent['fitness']:
                continue
            elif agent_data['fitness'] < second_best_agent['fitness']:
                second_best_agent = agent_data.copy()
        return second_best_agent
