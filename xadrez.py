#(lado: 'j' = jogador, 'i' = inimigo)

import itertools
import random

import cartas
import dados
import efeitos
import estado


_uids = itertools.count(random.randrange(1, 10 ** 9))  # começa num número sorteado, pois o servidor não guarda estado


def criar_peca(lado, tipo, lista_de_efeitos, linha, col, id_=None):
    return {'uid': next(_uids), 'id': id_, 'tipo': tipo, 'efeitos': lista_de_efeitos, 'lado': lado, 'linha': linha, 'col': col,
            'escudo': efeitos.valor_total(lista_de_efeitos, 'escudo')}


def peca_em(pecas, linha, col):
    for p in pecas:
        if p['linha'] == linha and p['col'] == col:
            return p
    return None


def casa(linha, col, n):
    return 'abcdefg'[col] + str(n - linha)


def nome_da_peca(p):
    if p['id'] in dados.CATALOGO:
        return dados.CATALOGO[p['id']]['nome']
    icones = ''.join(dados.EFEITOS[e['tipo']]['icone'] for e in p['efeitos'])
    return dados.TIPOS[p['tipo']]['nome'] + ' ' + icones


def movimentos(pecas, p, n):
    #Lista de casas (linha, col) para onde a peça p pode ir
    res = []
    l, c = p['linha'], p['col']
    tipo = p['tipo']

    def pode_ir(nl, nc):
        if not (0 <= nl < n and 0 <= nc < n):
            return False
        outra = peca_em(pecas, nl, nc)
        return outra is None or outra['lado'] != p['lado']

    if tipo == 'P':
        frente = -1 if p['lado'] == 'j' else 1
        if 0 <= l + frente < n:
            if peca_em(pecas, l + frente, c) is None:
                res.append((l + frente, c))
            for dc in (-1, 1):  # captura na diagonal
                alvo = peca_em(pecas, l + frente, c + dc)
                if alvo and alvo['lado'] != p['lado']:
                    res.append((l + frente, c + dc))
    elif tipo == 'N':
        for dl, dc in [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]:
            if pode_ir(l + dl, c + dc):
                res.append((l + dl, c + dc))
    elif tipo == 'K':
        for dl in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (dl or dc) and pode_ir(l + dl, c + dc):
                    res.append((l + dl, c + dc))
    else:  # B, R, Q andam em linha reta até bater em algo
        direcoes = []
        if tipo in 'BQ':
            direcoes += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        if tipo in 'RQ':
            direcoes += [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for dl, dc in direcoes:
            nl, nc = l + dl, c + dc
            while pode_ir(nl, nc):
                res.append((nl, nc))
                if peca_em(pecas, nl, nc):  # capturou: para aqui
                    break
                nl += dl
                nc += dc
    return res


def mover(batalha, p, linha, col):
    #Executa o movimento da peça p, chama os efeitos (da peça e das cartas) e escreve no log
    pecas, n = batalha['pecas'], batalha['n']
    quem = 'Você' if p['lado'] == 'j' else 'Inimigo'
    texto = f"{quem}: {nome_da_peca(p)} {casa(p['linha'], p['col'], n)}→{casa(linha, col, n)}"
    alvo = peca_em(pecas, linha, col)
    if alvo:
        if efeitos.ao_receber_golpe(alvo):  # escudo: o atacante fica onde estava
            batalha['log'].append(texto + ' - o escudo absorveu o golpe!')
            return
        pecas.remove(alvo)
        texto += ' captura ' + nome_da_peca(alvo)
        cartas.ao_perder_peca(batalha, alvo)  # só age se a peça capturada era do jogador
        if efeitos.ao_ser_capturado(alvo):  # explodiu: leva o atacante junto
            pecas.remove(p)
            cartas.ao_perder_peca(batalha, p)
            if alvo['lado'] == 'j':
                batalha['bonus'] += cartas.moedas_explosao()
            batalha['log'].append(texto + ' - EXPLOSÃO! os dois caem.')
            return
        if alvo['lado'] == 'j' and cartas.contra_ataque():  # carta Contra-Ataque
            pecas.remove(p)
            batalha['log'].append(texto + ' - mas o contra-ataque destrói o atacante!')
            return
        moedas, destruidas = efeitos.ao_capturar(p, linha, col, pecas)
        moedas += cartas.moedas_ao_capturar(batalha, p, alvo)
        batalha['bonus'] += moedas
        if moedas:
            texto += f' (+{moedas} moedas)'
        for d in destruidas:
            texto += f' - destrói {nome_da_peca(d)}'
    p['linha'], p['col'] = linha, col
    ultima_linha = 0 if p['lado'] == 'j' else n - 1
    if p['tipo'] == 'P' and linha == ultima_linha:
        p['tipo'] = 'Q'
        texto += ' e vira Rainha!'
        if p['lado'] == 'j':
            batalha['bonus'] += cartas.moedas_promocao()
    batalha['log'].append(texto)


def casas_ameacadas(batalha):
    #Casas para onde alguma peça inimiga poderia ir (usado pelas cartas de visão)
    casas = set()
    for p in batalha['pecas']:
        if p['lado'] == 'i':
            for (l, c) in movimentos(batalha['pecas'], p, batalha['n']):
                casas.add((l, c))
    return sorted(casas)


def jogada_inimiga(batalha):
    aleatorio = batalha['inimigo_aleatorio'] > 0
    if aleatorio:
        batalha['inimigo_aleatorio'] -= 1
    sem = batalha['inimigo_sem_tipo']  # carta Cerco: o inimigo não move um tipo de peça
    tipo_proibido = sem['peca'] if sem and sem['rodadas'] > 0 else None
    if tipo_proibido:
        sem['rodadas'] -= 1
    opcoes = []
    for p in batalha['pecas']:
        if p['lado'] == 'i' and p['tipo'] != tipo_proibido:
            for (l, c) in movimentos(batalha['pecas'], p, batalha['n']):
                opcoes.append((p, l, c))
    if not opcoes:
        return
    inteligencia = batalha['inteligencia']  # chance de jogar bem (vem do estágio)
    if aleatorio or random.random() >= inteligencia:
        p, l, c = _jogada_simples(batalha, opcoes, aleatorio)
    else:
        if batalha['olhar'] >= 2:
            p, l, c = _melhor_jogada_profunda(batalha, opcoes)
        else:
            p, l, c = _melhor_jogada(batalha, opcoes)
    mover(batalha, p, l, c)


def _jogada_simples(batalha, opcoes, aleatorio):
    #Jogada básica: captura a peça mais valiosa que puder; senão anda aleatoriamente.
    melhor, melhor_valor = None, 0
    if not aleatorio:
        for (p, l, c) in opcoes:
            alvo = peca_em(batalha['pecas'], l, c)
            if alvo and _valor(alvo) > melhor_valor:
                melhor, melhor_valor = (p, l, c), _valor(alvo)
    return melhor or random.choice(opcoes)


def _valor(peca):
    return dados.TIPOS[peca['tipo']]['valor']


def _casa_ameacada(pecas, n, linha, col, lado):
    #True se alguma peça do 'lado' consegue ir para essa casa
    return any((linha, col) in movimentos(pecas, q, n) for q in pecas if q['lado'] == lado)


def _simular(pecas, p, l, c):
    #Devolve a lista de peças depois que p vai para (l, c). Escudo absorve a captura (o atacante não se move)
    alvo = peca_em(pecas, l, c)
    if alvo and alvo['escudo'] > 0:
        return [dict(q, escudo=q['escudo'] - 1) if q is alvo else q for q in pecas]
    return [q for q in pecas if q is not p and q is not alvo] + [dict(p, linha=l, col=c)]


def _material(pecas):
    #Quanto vale o exército inimigo menos o do jogador (escudo conta como um pouco mais de valor)
    total = 0
    for q in pecas:
        v = _valor(q) * (1 + 0.4 * q['escudo'])
        total += v if q['lado'] == 'i' else -v
    return total


def _melhor_jogada_profunda(batalha, opcoes):
    #Olha 2 jogadas à frente: para cada jogada inimiga, supõe a melhor resposta do jogador e compara o material
    pecas, n = batalha['pecas'], batalha['n']
    jogadores = [q for q in pecas if q['lado'] == 'j']
    melhor, melhor_nota = None, None
    for (p, l, c) in opcoes:
        depois = _simular(pecas, p, l, c)
        pior = _material(depois)
        for q in depois:
            if q['lado'] == 'j':
                for (ml, mc) in movimentos(depois, q, n):
                    pior = min(pior, _material(_simular(depois, q, ml, mc)))
        distancia = min((max(abs(q['linha'] - l), abs(q['col'] - c)) for q in jogadores), default=0)
        nota = pior - 0.05 * distancia + random.random() * 0.1
        if melhor_nota is None or nota > melhor_nota:
            melhor, melhor_nota = (p, l, c), nota
    return melhor


def _melhor_jogada(batalha, opcoes):
    #captura peças valiosas, evita casas onde seria capturada e foge quando está ameaçada
    pecas, n = batalha['pecas'], batalha['n']
    jogadores = [q for q in pecas if q['lado'] == 'j']
    melhor, melhor_nota = None, None
    for (p, l, c) in opcoes:
        alvo = peca_em(pecas, l, c)
        ganho = 0
        if alvo:
            ganho = _valor(alvo) * (0.5 if alvo['escudo'] > 0 else 1)  # escudo absorve a captura
        depois = [q for q in pecas if q is not p and q is not alvo] + [dict(p, linha=l, col=c)]
        arriscada = p['escudo'] == 0 and _casa_ameacada(depois, n, l, c, 'j')
        risco = _valor(p) if arriscada else 0
        fuga = 0
        if risco == 0 and p['escudo'] == 0 and _casa_ameacada(pecas, n, p['linha'], p['col'], 'j'):
            fuga = _valor(p)  # estava ameaçada e agora está segura
        distancia = min((max(abs(q['linha'] - l), abs(q['col'] - c)) for q in jogadores), default=0)
        nota = ganho - risco + fuga - 0.05 * distancia + random.random() * 0.1
        if melhor_nota is None or nota > melhor_nota:
            melhor, melhor_nota = (p, l, c), nota
    return melhor


def contar(batalha, lado):
    return len([p for p in batalha['pecas'] if p['lado'] == lado])