import simpy
import random
import yaml
import numpy as np

class GeradorPseudo:
    def __init__(self, semente, a, c, m):
        self.semente = semente
        self.a = a
        self.c = c
        self.m = m
        self.x = semente

    def proximo(self):
        self.x = (self.a * self.semente + self.c) % self.m
        self.semente = self.x
        return self.x / self.m

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
        
def chegada(env, nome, intervalo_chegada, fila, total_clientes, clientes_atendidos):
    i = 0
    while clientes_atendidos[0] < total_clientes:
        yield env.timeout(random.uniform(*intervalo_chegada))
        i += 1
        env.process(cliente(env, f'{nome}-{i}', fila, clientes_atendidos))

def cliente(env, nome, fila, clientes_atendidos):
    chegada_fila = env.now

    with fila.resource.request() as req:
        resultado = yield req | env.timeout(0)
        if req not in resultado:
            # Cliente perdido
            fila.num_perdidos += 1
            return

        espera_na_fila = env.now - chegada_fila

        fila.num_atendidos += 1
        clientes_atendidos[0] += 1

        tempo_servico = random.uniform(*fila.atendimento)
        yield env.timeout(tempo_servico)

        tempo_total_espera = env.now - chegada_fila
        fila.add_wait_time(tempo_total_espera)
        
        if fila.nome == 'fila1':
            destino = random.choices(['fila2', 'fila3'], fila.prob_routing)[0]
            if destino == 'fila2':
                env.process(cliente(env, nome, fila2, clientes_atendidos))
            else:
                env.process(cliente(env, nome, fila3, clientes_atendidos))
        elif fila.nome == 'fila2':
            destino = random.choices(['saida', 'fila1'], fila.prob_saida)[0]
            if destino == 'fila1':
                env.process(cliente(env, nome, fila1, clientes_atendidos))
        elif fila.nome == 'fila3':
            destino = random.choices(['saida', 'fila1'], fila.prob_saida)[0]
            if destino == 'fila1':
                env.process(cliente(env, nome, fila1, clientes_atendidos))

def main():
    with open('parametros.yml', 'r') as file:
        parametros = yaml.safe_load(file)
    
    env = simpy.Environment()
    
    global fila1, fila2, fila3
    fila1 = Fila(env, 'fila1', float('inf'), 
                 (parametros['fila1']['atendimento_min'], parametros['fila1']['atendimento_max']),
                 prob_routing=parametros['fila1']['prob_routing'])
    
    fila2 = Fila(env, 'fila2', parametros['fila2']['capacidade'], 
                 (parametros['fila2']['atendimento_min'], parametros['fila2']['atendimento_max']),
                 prob_saida=parametros['fila2']['prob_saida'])
    
    fila3 = Fila(env, 'fila3', parametros['fila3']['capacidade'], 
                 (parametros['fila3']['atendimento_min'], parametros['fila3']['atendimento_max']),
                 prob_saida=parametros['fila3']['prob_saida'])
    
    total_clientes = 100000
    clientes_atendidos = [0]
    
    env.process(chegada(env, 'Cliente', 
                        (parametros['fila1']['chegada_min'], parametros['fila1']['chegada_max']), fila1, total_clientes, clientes_atendidos))
    
    env.run()
    
    print("\nResultados da Simulação:")
    print(f"1. Resultado da Fila 1: G/G/1, chegadas entre {parametros['fila1']['chegada_min']}..{parametros['fila1']['chegada_max']}, atendimento entre {parametros['fila1']['atendimento_min']}..{parametros['fila1']['atendimento_max']}:")
    print(f"   Tempo médio de espera = {fila1.get_average_wait_time():.4f} minutos")
    print(f"   Número de clientes perdidos: {fila1.num_perdidos}")
    print(f"   Probabilidade de clientes atendidos: {(fila1.num_atendidos / total_clientes)*100} %")
    print()

    print(f"2. Resultado da Fila 2: G/G/2/5, atendimento entre {parametros['fila2']['atendimento_min']}..{parametros['fila2']['atendimento_max']}:")
    print(f"   Tempo médio de espera = {fila2.get_average_wait_time():.4f} minutos")
    print(f"   Número de clientes perdidos: {fila2.num_perdidos}")
    print(f"   Probabilidade de clientes atendidos: {(fila2.num_atendidos / total_clientes)*100} %")
    print()

    print(f"3. Resultado da Fila 3: G/G/2/10, atendimento entre {parametros['fila3']['atendimento_min']}..{parametros['fila3']['atendimento_max']}:")
    print(f"   Tempo médio de espera = {fila3.get_average_wait_time():.4f} minutos")
    print(f"   Número de clientes perdidos: {fila3.num_perdidos}")
    print(f"   Probabilidade de clientes atendidos: {(fila3.num_atendidos / total_clientes)*100} %")

    print()
    print()

    print(f"4. Tempo total de simulação: {env.now:.2f} minutos")

if __name__ == '__main__':
    main()