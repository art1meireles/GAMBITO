"""Os BLOCOS DE EFEITO. Cada função abaixo é um momento do jogo em que efeitos podem agir.

Para criar um efeito novo:
  1) adicione o nome dele em dados/efeitos.json (ícone e descrição);
  2) escreva o que ele faz na função do momento certo aqui (um novo "if");
  3) use o nome dele no campo "efeitos" de qualquer peça em dados/pecas.json.
"""
import random
import estado

import dados


def valor_total(lista_de_efeitos, tipo):
    #Soma o 'valor' de todos os efeitos de um tipo (0 se a peça não tiver)
    return sum(e.get('valor', 1) for e in lista_de_efeitos if e['tipo'] == tipo)


def tem(peca, tipo):
    return any(e['tipo'] == tipo for e in peca['efeitos'])


def _valor(peca):
    return dados.TIPOS[peca['tipo']]['valor']


def _distancia(p, linha, col):
    return max(abs(p['linha'] - linha), abs(p['col'] - col))


def _vizinhas(pecas, linha, col, alcance=1):
    #Peças a até 'alcance' casas da casa (linha, col), sem contar a peça que está nela
    return [p for p in pecas if _distancia(p, linha, col) <= alcance and (p['linha'], p['col']) != (linha, col)]


# habilidades que a peça Mutante pode receber
SORTEIO_MUTANTE = [{'tipo': 'escudo', 'valor': 1}, {'tipo': 'moedas_ao_capturar', 'valor': 2},
                   {'tipo': 'moedas_fim_batalha', 'valor': 2}, {'tipo': 'explodir_ao_ser_capturado'},
                   {'tipo': 'explosao_ao_capturar'}, {'tipo': 'quebra_escudo'}]


# Momento 0: a batalha vai começar (depois de posicionar as peças)
def no_inicio_da_batalha(batalha):
    pecas = batalha['pecas']
    for p in pecas:  # primeiro as mutantes, para as habilidades sorteadas já valerem abaixo
        for e in list(p['efeitos']):
            if e['tipo'] == 'mutante':
                sorteio = SORTEIO_MUTANTE if estado.duelo is None else [x for x in SORTEIO_MUTANTE if not x['tipo'].startswith('moedas')]  #o duelo não tem moedas
                novo = dict(random.choice(sorteio))
                p['efeitos'] = [x for x in p['efeitos'] if x is not e] + [novo]
                if novo['tipo'] == 'escudo':
                    p['escudo'] += novo['valor']
    for p in pecas:
        aliadas = [q for q in pecas if q['lado'] == p['lado']]
        adversarias = [q for q in pecas if q['lado'] != p['lado']]
        for e in p['efeitos']:
            t, v = e['tipo'], e.get('valor', 1)
            if t == 'escudo_primeira_rodada':
                p['escudo'] += v
                p['temp'] = p.get('temp', 0) + v
            elif t == 'escudo_todos_inicio':
                for q in aliadas:
                    q['escudo'] += v
            elif t == 'escudo_vizinhos_inicio':
                for q in _vizinhas(aliadas, p['linha'], p['col'], e.get('alcance', 1)):
                    if q is not p:
                        q['escudo'] += v
            elif t == 'escudo_linha_inicio':
                for q in aliadas:
                    if q is not p and q['linha'] == p['linha']:
                        q['escudo'] += v
            elif t == 'escudo_parado':
                p['escudo'] += v
                p['parado'] = v
            elif t == 'escudo_minoria' and len(aliadas) < len(adversarias):
                p['escudo'] += v


# Momento 1: a peça vai ser capturada. Devolve o texto do que aconteceu se o golpe foi evitado, ou None.
def ao_receber_golpe(alvo, atacante):
    if tem(atacante, 'quebra_escudo'):
        alvo['escudo'] = 0
    if alvo['escudo'] > 0:          # efeito "escudo"
        alvo['escudo'] -= 1
        return 'o escudo absorveu o golpe!'
    for e in alvo['efeitos']:
        if e['tipo'] == 'imortal':  # sobrevive uma vez e perde as habilidades
            alvo['efeitos'] = []
            return 'a peça imortal sobreviveu (e perdeu as habilidades)!'
        if e['tipo'] in ('chance_evitar', 'chance_evitar_uma_vez') and random.random() < e['chance']:
            if e['tipo'] == 'chance_evitar_uma_vez':
                alvo['efeitos'].remove(e)
            return 'a peça escapou da captura!'
    return None


# Momento 2: a peça foi capturada (já saiu da lista de peças). Devolve (o atacante morre junto?, peças destruídas).
def ao_ser_capturado(alvo, atacante, batalha):
    pecas = batalha['pecas']
    l, c = alvo['linha'], alvo['col']
    inimigas = [q for q in pecas if q['lado'] != alvo['lado']]
    destruidas = []

    def atingir(condicao):
        for q in inimigas:
            if condicao(q) and q not in destruidas:
                destruidas.append(q)

    for e in alvo['efeitos']:
        t = e['tipo']
        dl = lambda q: q['linha'] - l
        dc = lambda q: q['col'] - c
        if t == 'explosao_cruz_ao_ser_capturada':
            atingir(lambda q: abs(dl(q)) + abs(dc(q)) == 1)
        elif t == 'explosao_diagonal_ao_ser_capturada':
            atingir(lambda q: abs(dl(q)) == 1 and abs(dc(q)) == 1)
        elif t == 'explosao_diagonais_inteiras':
            atingir(lambda q: abs(dl(q)) == abs(dc(q)) and dl(q) != 0)
        elif t == 'explosao_linha_coluna_ao_ser_capturada':
            atingir(lambda q: (dl(q) == 0 or dc(q) == 0) and 0 < _distancia(q, l, c) <= e['alcance'])
        elif t == 'explosao_vizinhas_ao_ser_capturada':
            atingir(lambda q: _distancia(q, l, c) == 1)
        elif t == 'explosao_area_ao_ser_capturada':
            atingir(lambda q: 0 < _distancia(q, l, c) <= e['alcance'])
        elif t == 'explosao_ao_redor_do_atacante':
            atingir(lambda q: q is not atacante and _distancia(q, atacante['linha'], atacante['col']) == 1)
    if alvo['lado'] == 'j':  # moedas só valem para o jogador
        batalha['bonus'] += valor_total(alvo['efeitos'], 'moedas_ao_ser_capturada')
    escudo = valor_total(alvo['efeitos'], 'escudo_aliados_ao_ser_capturada')
    if escudo:
        for q in pecas:
            if q['lado'] == alvo['lado']:
                q['escudo'] += escudo
    return tem(alvo, 'explodir_ao_ser_capturado'), destruidas


#  Momento 3: a peça acabou de capturar (o alvo já saiu da lista). Devolve (moedas ganhas, peças destruídas).
def ao_capturar(atacante, alvo, linha, col, batalha):
    pecas = batalha['pecas']
    jogador = atacante['lado'] == 'j'  # moedas só valem para o jogador
    moedas = 0
    destruidas = []
    if jogador:
        batalha['serie'] = batalha.get('serie', 0) + 1  # capturas seguidas sem perder peça
    atacante['capturas'] = atacante.get('capturas', 0) + 1
    for e in atacante['efeitos']:
        if e['tipo'] == 'berserker':  # cada captura sobe um nível de alcance
            atacante['nivel'] = min(e.get('max', 3), atacante.get('nivel', 0) + 1)
        elif e['tipo'] == 'parasita' and alvo['tipo'] != atacante['tipo']:  # no próximo movimento anda como a peça capturada
            atacante['copia'] = alvo['tipo']
    ao_redor_do_alvo = _vizinhas([q for q in pecas if q is not atacante], linha, col)
    aliadas_do_alvo = [q for q in ao_redor_do_alvo if q['lado'] == alvo['lado']]
    for e in atacante['efeitos']:
        t, v = e['tipo'], e.get('valor', 1)
        if jogador:
            if t == 'moedas_ao_capturar':
                moedas += v
            elif t == 'moedas_aleatorias_ao_capturar':
                moedas += random.randint(e['min'], e['max'])
            elif t == 'moedas_serie':
                moedas += min(batalha['serie'], e['max'])
            elif t == 'moedas_alvo_rei' and alvo['tipo'] == 'K':
                moedas += v
            elif t == 'moedas_alvo_mais_caro' and _valor(alvo) > _valor(atacante):
                moedas += v
            elif t == 'moedas_alvo_especial' and alvo['efeitos']:
                moedas += v
            elif t == 'moedas_alvo_com_moedas' and any(x['tipo'].startswith('moedas') for x in alvo['efeitos']):
                moedas += v
            elif t == 'moedas_alvo_isolado' and not aliadas_do_alvo:
                moedas += v
            elif t == 'moedas_alvo_cercado' and len(aliadas_do_alvo) >= 2:
                moedas += v
        if t == 'explosao_ao_capturar':
            for q in ao_redor_do_alvo:
                if q['lado'] != atacante['lado'] and q not in destruidas:
                    destruidas.append(q)
        elif t == 'cadeia_ao_capturar':
            vizinhas = sorted([q for q in ao_redor_do_alvo if q['lado'] != atacante['lado'] and q not in destruidas],
                              key=_valor, reverse=True)
            destruidas += vizinhas[:v]
        elif t == 'escudo_ao_capturar':
            atacante['escudo'] += v
        elif t == 'escudo_ao_capturar_mais_caro' and _valor(alvo) > _valor(atacante):
            atacante['escudo'] += v
        elif t == 'escudo_a_cada_capturas' and atacante['capturas'] % e['n'] == 0:
            atacante['escudo'] += v
        elif t == 'escudo_aliado_ao_capturar':
            aliados = [q for q in ao_redor_do_alvo if q['lado'] == atacante['lado']]
            if aliados:
                min(aliados, key=lambda q: q['escudo'])['escudo'] += v
    return moedas, destruidas


# Momento 4: a peça acabou de se mover. Devolve as moedas ganhas por isso.
def ao_mover(batalha, p):
    moedas = 0
    n = batalha['n']
    p['moveu'] = True
    for e in p['efeitos']:
        t = e['tipo']
        if t == 'escudo_parado' and p.get('parado'):  # perde o escudo ao se mexer
            p['escudo'] = max(0, p['escudo'] - p['parado'])
            p['parado'] = 0
        elif p['lado'] == 'j' and t == 'moedas_ultima_linha' and p['linha'] == 0:
            moedas += e['valor']
        elif p['lado'] == 'j' and t == 'moedas_centro' and not p.get('centro_ok'):
            meio = (n - 1) / 2
            if abs(p['linha'] - meio) <= 0.5 and abs(p['col'] - meio) <= 0.5:
                p['centro_ok'] = True
                moedas += e['valor']
    return moedas


# Momento 5: terminou uma rodada (o jogador e o inimigo já jogaram)
def ao_fim_da_rodada(batalha):
    for p in batalha['pecas']:
        if p.get('espera', 0) > 0:  # tempo de recarga da troca de lugar
            p['espera'] -= 1
        if p.get('temp') and batalha['turnos'] >= 1:  # o escudo da primeira rodada acaba
            p['escudo'] = max(0, p['escudo'] - p['temp'])
            p['temp'] = 0
        for e in p['efeitos']:
            if e['tipo'] == 'escudo_renovavel' and batalha['turnos'] % e['a_cada'] == 0 and p['escudo'] < 1:
                p['escudo'] = 1


# Momento 6: a batalha acabou (vitória). Devolve as moedas das peças que sobreviveram.
def moedas_no_fim_da_batalha(batalha):
    vivas = [p for p in batalha['pecas'] if p['lado'] == 'j']
    rodadas = batalha['rodadas']
    total = 0
    for p in vivas:
        for e in p['efeitos']:
            t, v = e['tipo'], e.get('valor', 1)
            if t == 'moedas_fim_batalha':
                total += v
            elif t == 'moedas_por_rodada':
                total += (rodadas // e['a_cada']) * v
            elif t == 'moedas_crescentes':
                k = rodadas // 4
                total += min(e['max'], k * (k + 1) // 2)
            elif t == 'moedas_ultima_viva' and len(vivas) == 1:
                total += v
            elif t == 'moedas_por_aliado':
                total += v * (len(vivas) - 1)
            elif t == 'moedas_por_tipo':
                total += v * len({q['tipo'] for q in vivas})
            elif t == 'moedas_se_parada' and not p.get('moveu'):
                total += v
    return total