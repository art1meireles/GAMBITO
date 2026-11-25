# Peças e cartas já descobertas, recorde e número de runs. Fica guardada no navegador (localStorage); o servidor só a recebe, altera e devolve

import dados

PADRAO = {'pecas': {}, 'cartas': {}, 'runs': 0, 'vitorias': 0, 'melhor': 0}

dados_colecao = dict(PADRAO)


def definir(recebida):
    #Troca a coleção pela que veio do navegador (valores ruins são ignorados)
    nova = {k: (dict(v) if isinstance(v, dict) else v) for k, v in PADRAO.items()}
    if isinstance(recebida, dict):
        for chave, padrao in PADRAO.items():
            valor = recebida.get(chave)
            if isinstance(valor, type(padrao)) and not isinstance(valor, bool):
                nova[chave] = valor
    nova['pecas'] = {k: v for k, v in nova['pecas'].items() if k in dados.CATALOGO}  # tira peças que não existem mais
    dados_colecao.clear()
    dados_colecao.update(nova)


def salvar():
    pass  # nada a fazer: o navegador guarda a coleção que o servidor devolve


def registrar_compra(id_da_peca):
    pecas = dados_colecao['pecas']
    pecas[id_da_peca] = pecas.get(id_da_peca, 0) + 1