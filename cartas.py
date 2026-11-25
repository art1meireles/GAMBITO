"""Cartas PERMANENTES: ficam ativas até o fim da run e alteram as regras (moedas, loja, batalha).

Cada carta permanente tem uma lista de "blocos" (em dados/cartas.json), por exemplo:
    {"tipo": "moedas_captura", "valor": 1, "peca": "P"}
Este arquivo lê esses blocos nos momentos certos do jogo.
"""
import random

import colecao
import dados
import efeitos
import estado

CFG = dados.CONFIG


# consultas básicas
def permanentes():
    run = estado.run
    return [dados.CARTAS[i] for i in run['cartas']] if run else []


def blocos(nome):
    #Todos os blocos de um tipo, de todas as cartas permanentes ativas.
    return [b for c in permanentes() for b in c['efeitos'] if b['tipo'] == nome]


def soma(nome, **filtros):
    #Soma o 'valor' dos blocos de um tipo. Um bloco só conta se combinar com os filtros que ele mesmo define.
    total = 0
    for b in blocos(nome):
        if all(b[k] == v for k, v in filtros.items() if k in b):
            total += b.get('valor', 1)
    return total


def tem(nome, **filtros):
    return any(all(b[k] == v for k, v in filtros.items() if k in b) for b in blocos(nome))


def primeiro(nome, chave='valor', padrao=None):
    bs = blocos(nome)
    return bs[0].get(chave, padrao) if bs else padrao


def produto(nome):
    total = 1
    for b in blocos(nome):
        total *= b.get('valor', 1)
    return total


def espacos():
    return CFG['espacos_cartas'] + int(soma('espaco_cartas'))


#  início da batalha
def zona_extra():
    return int(soma('zona_extra'))


def inimigos_a_menos():
    return int(soma('inimigo_menos'))


def _escolher_alvos(bloco, meus, n, zona_inicio):
    sel = bloco.get('sel', 'tipo')
    peca = bloco.get('peca')
    candidatos = [p for p in meus if not peca or p['tipo'] == peca]
    if 'min' in bloco and len(candidatos) < bloco['min']:
        return []
    if sel in ('tipo', 'todas'):
        return candidatos
    if sel == 'aleatoria':
        return [random.choice(candidatos)] if candidatos else []
    if sel == 'canto':
        return [p for p in candidatos if p['linha'] == n - 1 and p['col'] in (0, n - 1)]
    if sel == 'centro':
        return [p for p in candidatos if p['col'] == n // 2]
    if sel == 'frente':
        return [p for p in candidatos if p['linha'] == zona_inicio]
    return []


def aplicar_no_inicio(batalha):
    #Chamada quando a batalha começa: escudos iniciais, turnos do inimigo etc.
    n = batalha['n']
    meus = [p for p in batalha['pecas'] if p['lado'] == 'j']
    inimigas = [p for p in batalha['pecas'] if p['lado'] == 'i']
    for bloco in blocos('escudo_inicial'):
        for p in _escolher_alvos(bloco, meus, n, batalha['zona_inicio']):
            p['escudo'] += bloco['valor']
    extra = soma('escudo_extra')
    if extra:
        for p in meus:
            if p['escudo'] > 0:
                p['escudo'] += extra
    if tem('sem_escudo_inimigo'):
        for p in inimigas:
            p['escudo'] = 0
    batalha['rodadas_gratis'] += int(soma('rodadas_gratis_inicio'))
    batalha['inimigo_pula'] += int(soma('inimigo_pula_inicio'))
    batalha['inimigo_aleatorio'] += int(soma('inimigo_aleatorio_inicio'))
    if tem('mostrar_ameacas'):
        batalha['ameacas'] = True
    if batalha.get('sem_escudos'):  # carta de risco "Sem Rede"
        for p in batalha['pecas']:
            p['escudo'] = 0


def efeitos_extras_da_peca(tipo_da_peca, indice):
    #Efeitos que cartas dão a uma peça sua quando ela é criada.
    extras = [dict(b['efeito']) for b in blocos('efeito_para_tipo') if b['peca'] == tipo_da_peca]
    extras += [dict(e) for e in estado.run['extras'].get(str(indice), [])]
    return extras


def limite_de_rodadas():
    if tem('sem_limite_rodadas'):
        return None
    return CFG['max_rodadas'] + int(soma('limite_rodadas_mais'))


# durante a batalha
def moedas_ao_capturar(batalha, atacante, alvo):
    #Moedas que as cartas dão por uma captura feita por uma peça do jogador.
    if atacante['lado'] != 'j':
        return 0
    n = batalha['n']
    batalha['capturas'] += 1
    total = 0
    for b in blocos('moedas_captura'):
        if 'peca' in b and b['peca'] != atacante['tipo']:
            continue
        if 'alvo' in b and b['alvo'] != alvo['tipo']:
            continue
        if b.get('borda') and atacante['col'] not in (0, n - 1):
            continue
        if b.get('com_escudo') and atacante['escudo'] <= 0:
            continue
        total += b['valor']
    if any(e['tipo'] == 'moedas_ao_capturar' for e in atacante['efeitos']):
        total += soma('moedas_extra_mercenario')
    for b in blocos('moedas_a_cada_n_capturas'):
        if batalha['capturas'] % b['n'] == 0:
            total += b['valor']
    if batalha['turnos'] == 1:
        total += soma('moedas_primeira_jogada')
    if not [p for p in batalha['pecas'] if p['lado'] == 'i']:
        total += soma('moedas_ultima_peca')
    total += batalha['proxima_captura']  # carta "Munição"
    batalha['proxima_captura'] = 0
    return total


def ao_perder_peca(batalha, peca):
    #Uma peça do jogador foi capturada: guarda para 'reviver' e dá moedas de 'Vingança'.
    if peca['lado'] != 'j':
        return
    batalha['perdidas'].append(dict(peca))
    batalha['serie'] = 0  # quebra a sequência de capturas sem perder peça
    batalha['bonus'] += int(soma('moedas_peca_perdida'))


def contra_ataque():
    for b in blocos('contra_ataque'):
        if random.random() < b['chance']:
            return True
    return False

def moedas_explosao():
    return int(soma('moedas_explosao'))

def moedas_promocao():
    return int(soma('moedas_promocao'))


# recompensa
def calcular_recompensa(run, b, d):
    #Devolve o relatório de recompensa de uma vitória (base, velocidade, capturas, cartas...).
    num = run['num']
    base = d['recompensa_base']  # fixa por estágio; o resto vem de bônus
    if tem('recompensa_primeira_dobra') and num == 1:
        base *= 2

    media = d['media'] - int(soma('media_menos')) + int(soma('media_mais'))
    dif = media - b['rodadas']
    bonus_max = CFG['bonus_max_por_velocidade'] + int(soma('bonus_velocidade_max'))
    if tem('bonus_max_fixo'):
        bonus_max = primeiro('bonus_max_fixo')
    if tem('bonus_sem_limite'):
        bonus_max = 999
    penalidade_max = CFG['penalidade_max_por_lentidao']
    if tem('penalidade_max'):
        penalidade_max = min(penalidade_max, primeiro('penalidade_max'))
    if tem('sem_penalidade'):
        penalidade_max = 0
    if dif >= 0:
        tempo = round(min(dif, bonus_max) * produto('bonus_velocidade_mult'))
        for fortuna in blocos('fortuna'):
            if random.random() < fortuna['chance']:
                tempo *= 2
    else:
        tempo = -min(-dif, penalidade_max)
        tempo = round(tempo * produto('penalidade_fator'))

    vivas = [p for p in b['pecas'] if p['lado'] == 'j']
    fim_de_batalha = efeitos.moedas_no_fim_da_batalha(b)

    cartas = int(soma('moedas_fim_vitoria'))
    for bl in blocos('juros'):
        juros = (run['moedas'] // bl['por']) * bl['valor']
        cartas += min(juros, bl['max']) if 'max' in bl else juros
    for bl in blocos('moedas_fim_pecas_vivas'):
        if len(vivas) >= bl['min']:
            cartas += bl['valor']
    for bl in blocos('moedas_fim_por_tipo'):
        cartas += (len([p for p in vivas if p['tipo'] == bl['peca']]) // bl['por']) * bl['valor']
    for bl in blocos('moedas_tabuleiro'):
        if b['n'] == bl['tamanho']:
            cartas += bl['valor']
    for bl in blocos('moedas_sem_perder'):
        if not any(p['tipo'] == bl['peca'] for p in b['perdidas']):
            cartas += bl['valor']
    if len([p for p in b['inimigos']]) > b['meus_iniciais']:
        cartas += int(soma('moedas_se_inimigo_maior'))
    if b['rodadas'] < media / 2:
        cartas += int(soma('moedas_rapido_metade'))
    for bl in blocos('moedas_colecao'):
        cartas += (len(colecao.dados_colecao['pecas']) // bl['por']) * bl['valor']
    extra_fim = soma('moedas_extra_fim_efeito')
    if extra_fim:
        cartas += extra_fim * len([p for p in vivas if any(e['tipo'] == 'moedas_fim_batalha' for e in p['efeitos'])])
    cartas += int(soma('recompensa_por_vitoria')) * (num - 1)
    cartas += b['bonus_vitoria']

    # cartas de risco desta batalha
    perdeu_peca = len(b['perdidas']) > 0
    if b['contrato'] and not perdeu_peca:
        cartas += b['contrato']
    if b['aposta'] and b['rodadas'] < media:
        cartas += b['aposta']
    if b['tudo_ou_nada']:
        cartas += -b['tudo_ou_nada']['perda'] if perdeu_peca else b['tudo_ou_nada']['ganho']

    soma_total = base + tempo + b['bonus'] + fim_de_batalha + cartas
    mult = produto('recompensa_mult') * b['mult_recompensa']
    total = max(1, round(soma_total * mult))
    return {'base': base, 'rodadas': b['rodadas'], 'media': media, 'tempo': tempo, 'capturas': b['bonus'],
            'fim_de_batalha': fim_de_batalha, 'cartas': cartas, 'mult': mult, 'total': total}


# loja
def preco_da_peca(id_da_peca):
    run = estado.run
    peca = dados.CATALOGO[id_da_peca]
    desconto = soma('desconto_global') + soma('desconto_tipo', peca=peca['tipo'])
    if run['compras_na_loja'] >= 1:
        desconto += soma('barganha')
    preco = max(1, peca['preco'] - desconto)
    if tem('segunda_compra_gratis') and run['compras_na_loja'] == 1:
        preco = 0
    return max(0, preco - run['cupom'])


def preco_da_misteriosa():
    run = estado.run
    preco = max(1, CFG['preco_misteriosa'] - int(soma('misteriosa_desconto')))
    return max(0, preco - run['cupom'])


def custo_da_troca(loja):
    if loja['trocas'] == 0 and tem('troca_primeira_gratis'):
        return 0
    if loja['sorteio_gratis']:
        return 0
    if tem('troca_fixo'):
        return primeiro('troca_fixo')
    custo = max(1, loja['custo_troca'] - int(soma('troca_menos')))
    if tem('troca_max'):
        custo = min(custo, primeiro('troca_max'))
    return custo


def ofertas_de_pecas():
    return CFG['ofertas_na_loja'] + int(soma('ofertas_extra'))


def moedas_ao_entrar_na_loja():
    run = estado.run
    total = int(soma('moedas_entrar_loja')) + run['moedas_proxima_loja']
    run['moedas_proxima_loja'] = 0
    for bl in blocos('loteria'):
        if random.random() < bl['chance']:
            total += bl['valor']
    return total


def sorteio_troca_gratis():
    return any(random.random() < bl['chance'] for bl in blocos('troca_gratis_chance'))