#Pacotes de cartas: o jogador compra um pacote e ESCOLHE 1 carta entre as opções sorteadas
import random

import cartas
import colecao
import dados
import estado

CFG = dados.CONFIG


def sortear_raridade(probabilidades):
    raridades = list(probabilidades)
    return random.choices(raridades, [probabilidades[r] for r in raridades])[0]


def _carta_da_raridade(raridade, ja_sorteadas):
    """Sorteia uma carta da raridade. Se não houver, desce para a raridade mais baixa mais próxima."""
    ordem = dados.RARIDADES
    i = ordem.index(raridade)
    tentativas = ordem[i::-1] + ordem[i + 1:]
    donas = estado.run['cartas']
    for r in tentativas:
        pool = [c for c in dados.CARTAS_POR_RARIDADE[r] if c not in ja_sorteadas and c not in donas]
        if pool:
            return random.choice(pool)
    pool = [c for c in dados.CARTAS if dados.CARTAS[c]['implementado'] and c not in ja_sorteadas]
    return random.choice(pool)


def gerar_opcoes(id_do_pacote):
    pacote = dados.PACOTES[id_do_pacote]
    opcoes = []
    for _ in range(pacote['opcoes']):
        raridade = sortear_raridade(pacote['probabilidades'])
        opcoes.append(_carta_da_raridade(raridade, opcoes))
    return opcoes


def abrir(id_do_pacote):
    estado.run['pacote'] = {'id': id_do_pacote, 'opcoes': gerar_opcoes(id_do_pacote)}


def escolher(opcao, substituir=None):
    run = estado.run
    pacote = run['pacote']
    if pacote is None:
        raise ValueError('Nenhum pacote aberto')
    id_da_carta = pacote['opcoes'][opcao]
    carta = dados.CARTAS[id_da_carta]
    if carta['categoria'] == 'permanente':
        lista, limite = run['cartas'], cartas.espacos()
    else:
        lista, limite = run['consumiveis'], CFG['max_consumiveis']
    if len(lista) < limite:
        lista.append(id_da_carta)
    else:
        if substituir is None or not (0 <= substituir < len(lista)):
            raise ValueError('Seus espaços estão cheios: escolha qual carta substituir.')
        lista[substituir] = id_da_carta
    registradas = colecao.dados_colecao.setdefault('cartas', {})
    registradas[id_da_carta] = registradas.get(id_da_carta, 0) + 1
    colecao.salvar()
    run['pacote'] = None


def pular():
    estado.run['pacote'] = None