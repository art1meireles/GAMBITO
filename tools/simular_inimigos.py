#Compara batalhas SEM e COM efeitos de movimento nos inimigos, para ver se a dificuldade ficou justa
#Uso: python tools/simular_inimigos.py [batalhas_por_celula] [semente]
import collections
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  #a pasta do projeto
import colecao, dados, estado, run, xadrez

colecao.definir(None)
N = int(sys.argv[1]) if len(sys.argv) > 1 else 150
random.seed(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
FASES = [6, 11, 16, 25]  #uma batalha de cada estágio (Fácil, Intermediário, Difícil, GM)
EXERCITOS = {'básico': ['R:comum', 'B:comum', 'N:comum', 'P:comum'],
             'forte': ['Q:comum', 'R:comum', 'N:comum', 'B:comum']}
ORIGINAL = dict(run.EFEITOS_DE_MOVIMENTO_INIMIGO)
NOMES_DOS_EFEITOS = sum(ORIGINAL.values(), [])
ESTAGIO_ORIGINAL = dados.estagio


def jogar():
    for _ in range(200):  #o robô: captura se puder, senão anda para casa segura, senão qualquer uma
        if estado.run['tela'] != 'batalha':
            return
        b = estado.run['batalha']
        if b['vez'] == 'inimigo':
            run.vez_do_inimigo()
            continue
        ameaca = {tuple(a) for a in xadrez.casas_ameacadas(b)}
        ini = {(p['linha'], p['col']) for p in b['pecas'] if p['lado'] == 'i'}
        caps, seguras, todas = [], [], []
        for p in b['pecas']:
            if p['lado'] != 'j':
                continue
            for m in xadrez.movimentos(b['pecas'], p, b['n']):
                x = ((p['linha'], p['col']), m)
                todas.append(x)
                if tuple(m) in ini:
                    caps.append(x)
                elif tuple(m) not in ameaca:
                    seguras.append(x)
        escolha = caps or seguras or todas
        if not escolha:
            return
        de, para = random.choice(escolha)
        run.jogada_do_jogador(list(de), list(para))


def definir_chance(chance):
    #None = valor do estagios.json; número = força essa chance em todos os estágios
    if chance is None:
        dados.estagio = ESTAGIO_ORIGINAL
    else:
        dados.estagio = lambda n: dict(ESTAGIO_ORIGINAL(n), chance_movimento=chance)


def batalha(exercito, num, com_efeitos):
    run.EFEITOS_DE_MOVIMENTO_INIMIGO.clear()
    if com_efeitos:
        run.EFEITOS_DE_MOVIMENTO_INIMIGO.update(ORIGINAL)
    run.novo_jogo()
    estado.run['pacote'] = None
    estado.run['num'] = num
    estado.run['exercito'] = list(exercito)
    run.preparar_batalha()
    efs = collections.Counter(e['tipo'] for i in estado.run['batalha']['inimigos'] for e in i['efeitos']
                              if e['tipo'] in NOMES_DOS_EFEITOS)
    run.autoposicionar()
    run.iniciar_batalha()
    jogar()
    return estado.run['tela'] == 'loja', estado.run['batalha']['turnos'], efs


print('Taxa de vitória do robô e turnos médios, por exército e fase. N =', N, 'batalhas por célula')
print('exército | batalha | SEM efeitos | COM efeitos (estagios.json) | efeito forçado em todos')
for nome, ex in EXERCITOS.items():
    for num in FASES:
        linha = []
        for modo in ('sem', 'com', 'forcado'):
            definir_chance(1.0 if modo == 'forcado' else None)
            vit = turnos = 0
            for _ in range(N):
                v, t, _ = batalha(ex, num, modo != 'sem')
                vit += v
                turnos += t
            linha.append('%5.1f%% (%.0f turnos)' % (100 * vit / N, turnos / N))
        print('%-8s | %7d | %s' % (nome, num, ' | '.join(linha)))

print('\nEfeito por efeito (exército básico, inimigos com efeito forçado, batalhas 11 e 16):')
definir_chance(1.0)
res = collections.defaultdict(lambda: [0, 0])
for num in (11, 16):
    for _ in range(N * 2):
        v, t, efs = batalha(EXERCITOS['básico'], num, True)
        for k in efs:
            res[k][0] += v
            res[k][1] += 1
definir_chance(None)
for k, (v, n) in sorted(res.items(), key=lambda x: x[1][0] / max(1, x[1][1])):
    print('  %-20s vitórias do robô: %5.1f%%  (em %d batalhas)' % (k, 100 * v / n, n))