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
    def __init__(self, env, nome, capacidade, atendimento, prob_routing=None, destinos=None, prob_saida=None):
        self.env = env
        self.nome = nome
        self.capacidade = capacidade
        self.atendimento = atendimento
        self.prob_routing = prob_routing
        self.destinos = destinos
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
        
        if fila.prob_routing and fila.destinos:
            destino_nome = random.choices(fila.destinos, fila.prob_routing)[0]
            if destino_nome != 'saida':
                destino_fila = filas[destino_nome]
                env.process(cliente(env, nome, destino_fila, clientes_atendidos))
        elif fila.prob_saida and fila.destinos:
            destino_nome = random.choices(fila.destinos, fila.prob_saida)[0]
            if destino_nome != 'saida':
                destino_fila = filas[destino_nome]
                env.process(cliente(env, nome, destino_fila, clientes_atendidos))

def main():
    with open('parametros.yml', 'r') as file:
        parametros = yaml.safe_load(file)
    
    env = simpy.Environment()
    
    global filas
    filas = {}
    
    for nome_fila, props in parametros['filas'].items():
        capacidade = props.get('capacidade', float('inf'))
        atendimento = (props['atendimento_min'], props['atendimento_max'])
        prob_routing = props.get('prob_routing')
        destinos = props.get('destinos')
        prob_saida = props.get('prob_saida')
        fila = Fila(env, nome_fila, capacidade, atendimento, prob_routing, destinos, prob_saida)
        filas[nome_fila] = fila
    
    total_clientes = parametros['total_clientes']
    clientes_atendidos = [0]
    
    env.process(chegada(env, 'Cliente', 
                        (parametros['filas']['fila1']['chegada_min'], parametros['filas']['fila1']['chegada_max']), filas['fila1'], total_clientes, clientes_atendidos))
    
    env.run()
    
    print("\nResultados da Simulação:")
    for nome_fila, fila in filas.items():
        print(f"Resultado da {nome_fila}:")
        print(f"   Tempo médio de espera = {fila.get_average_wait_time():.4f} minutos")
        print(f"   Número de clientes perdidos: {fila.num_perdidos}")
        print(f"   Probabilidade de clientes atendidos: {(fila.num_atendidos / total_clientes)*100:.2f} %")
        print()
    
    print(f"Tempo total de simulação: {env.now:.2f} minutos")

if __name__ == '__main__':
    main()
