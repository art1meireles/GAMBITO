#A loja que aparece depois de cada vitória: peças, peça misteriosa e pacotes de cartas
import random

import cartas
import colecao
import dados
import estado
import pacotes

CFG = dados.CONFIG


def _sortear_sem_repetir(ids, pesos, quantidade):
    ids, pesos, res = list(ids), list(pesos), []
    while ids and len(res) < quantidade:
        i = random.choices(range(len(ids)), pesos)[0]
        res.append(ids.pop(i))
        pesos.pop(i)
    return res


def gerar_loja(custo_troca, trocas=0):
    run = estado.run
    candidatas = list(dados.CHAVES_LOJA)
    if cartas.tem('loja_evita_exercito'):
        filtradas = [k for k in candidatas if k not in run['exercito']]
        candidatas = filtradas or candidatas
    ofertas = _sortear_sem_repetir(candidatas, [1 / dados.CATALOGO[k]['preco'] for k in candidatas],
                                   cartas.ofertas_de_pecas())  # peças baratas aparecem mais
    ids_pacotes = [k for k, p in dados.PACOTES.items() if p['loja']]
    pacotes_na_loja = _sortear_sem_repetir(ids_pacotes, [1 / dados.PACOTES[k]['preco'] ** 0.8 for k in ids_pacotes],
                                           CFG['pacotes_na_loja'])
    return {'ofertas': ofertas, 'vendidas': [False] * len(ofertas),
            'misteriosa': random.choice(dados.CHAVES_LOJA), 'misteriosa_vendida': False,
            'pacotes': pacotes_na_loja, 'pacotes_vendidos': [False] * len(pacotes_na_loja),
            'custo_troca': custo_troca, 'trocas': trocas, 'sorteio_gratis': cartas.sorteio_troca_gratis()}


def _checar_loja():
    run = estado.run
    if run['tela'] != 'loja':
        raise ValueError('Loja fechada')
    if run['pacote'] is not None:
        raise ValueError('Escolha uma carta do pacote aberto primeiro.')


def trocar_ofertas():
    _checar_loja()
    run = estado.run
    loja = run['loja']
    custo = cartas.custo_da_troca(loja)
    if run['moedas'] < custo:
        raise ValueError('Moedas insuficientes')
    run['moedas'] -= custo
    run['loja'] = gerar_loja(loja['custo_troca'] * 2, loja['trocas'] + 1)  # o custo dobra a cada troca


def comprar(slot, substituir):
    _checar_loja()
    run = estado.run
    loja = run['loja']
    if not (0 <= substituir < len(run['exercito'])):
        raise ValueError('Escolha qual peça substituir')
    if slot == 'misteriosa':
        if loja['misteriosa_vendida']:
            raise ValueError('Já comprada')
        id_da_peca, preco = loja['misteriosa'], cartas.preco_da_misteriosa()
    else:
        if not (0 <= slot < len(loja['ofertas'])) or loja['vendidas'][slot]:
            raise ValueError('Oferta inválida')
        id_da_peca = loja['ofertas'][slot]
        preco = cartas.preco_da_peca(id_da_peca)
    if run['moedas'] < preco:
        raise ValueError('Moedas insuficientes')
    run['moedas'] -= preco
    run['exercito'][substituir] = id_da_peca  # a nova peça toma o lugar de uma antiga
    if slot == 'misteriosa':
        loja['misteriosa_vendida'] = True
    else:
        loja['vendidas'][slot] = True
    # moedas extras de cartas
    run['moedas'] += int(cartas.soma('moedas_ao_substituir'))
    if id_da_peca not in colecao.dados_colecao['pecas']:
        run['moedas'] += int(cartas.soma('moedas_peca_nova'))
    run['compras_na_loja'] += 1
    run['ultima_compra'] = preco
    run['cupom'] = 0
    if run['compras_na_loja'] == 2:
        run['moedas'] += int(cartas.soma('compra_lote'))
    colecao.registrar_compra(id_da_peca)


def comprar_pacote(slot):
    _checar_loja()
    run = estado.run
    loja = run['loja']
    if not (0 <= slot < len(loja['pacotes'])) or loja['pacotes_vendidos'][slot]:
        raise ValueError('Pacote inválido')
    id_do_pacote = loja['pacotes'][slot]
    preco = dados.PACOTES[id_do_pacote]['preco']
    if run['moedas'] < preco:
        raise ValueError('Moedas insuficientes')
    run['moedas'] -= preco
    loja['pacotes_vendidos'][slot] = True
    pacotes.abrir(id_do_pacote)