class Fila:
    def __init__(self, env, nome, capacidade, atendimento, prob_routing=None, prob_saida=None):
        self.env = env
        self.nome = nome
        self.capacidade = capacidade
        self.atendimento = atendimento
        self.prob_routing = prob_routing
        self.prob_saida = prob_saida
        self.resource = simpy.Resource(env, capacidade)
        self.wait_times = []
        self.num_perdidos = 0
        self.num_atendidos = 0

    def add_wait_time(self, wait_time):
        self.wait_times.append(wait_time)

    def get_average_wait_time(self):
        total_wait_time = sum(self.wait_times)
        total_clients = len(self.wait_times)
        if total_clients > 0:
            return total_wait_time / total_clients
        else:
            return 0

    def get_wait_time_distribution(self):
        if self.wait_times:
            return {
                'min': np.min(self.wait_times),
                'max': np.max(self.wait_times),
                'mean': np.mean(self.wait_times),
                'std': np.std(self.wait_times),
                'quantiles': np.percentile(self.wait_times, [25, 50, 75])
            }
        else:
            return {'min': 0, 'max': 0, 'mean': 0, 'std': 0, 'quantiles': [0, 0, 0]}