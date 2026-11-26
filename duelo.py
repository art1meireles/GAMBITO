#Modo DUELO: dois jogadores no mesmo aparelho (azul e vermelho), um match de 10 batalhas
#Fluxo: sorteio -> banimentos -> draft -> (montagem -> batalha -> resultado) x 10 -> fim
#O estado do duelo fica no navegador (como a run) e viaja com cada pedido; o servidor só valida as regras
import random

import dados
import efeitos
import estado
import xadrez

CFG = dados.CONFIG
PARTIDAS = 10    #batalhas por match
ORCAMENTO = 20   #moedas de cada jogador no draft
MAX_PECAS = 4    #peças por exército
MAX_BANS = 5     #banimentos por jogador
JOGADORES = ('a', 'v')
LADO = {'a': 'j', 'v': 'i'}  #azul joga embaixo (lado 'j') e vermelho em cima (lado 'i')
NOME = {'a': 'Azul', 'v': 'Vermelho'}
COMUNS = ['P:comum', 'N:comum', 'B:comum', 'R:comum', 'K:comum']  #peças simples que não aparecem na loja, mas entram no draft
FASES = ('sorteio', 'banimentos', 'draft', 'montagem', 'batalha', 'resultado', 'fim')


def _sem_moedas(peca):
    return not any(e['tipo'].startswith('moedas') for e in peca['efeitos'])  #no duelo não há moedas: essas peças não servem


#peças que podem ser banidas e escolhidas no draft (as de efeito de moeda ficam escondidas)
ELEGIVEIS = [id_ for id_, p in dados.CATALOGO.items() if (p['loja'] or id_ in COMUNS) and _sem_moedas(p)]


def outro(j):
    return 'v' if j == 'a' else 'a'


def sanear(d):
    #Duelo salvo com problema (ou de uma versão antiga): descarta
    if not isinstance(d, dict) or d.get('fase') not in FASES:
        return None
    for chave in ('ordem', 'abre', 'vez', 'bans', 'fim_bans', 'exercitos', 'gasto', 'fim_draft', 'pontos', 'resultados', 'partida'):
        if chave not in d:
            return None
    ids = [i for j in JOGADORES for i in d['exercitos'].get(j, [])] + [i for j in JOGADORES for i in d['bans'].get(j, [])]
    if any(i not in dados.CATALOGO for i in ids):
        return None
    return d


def _batalha():
    return estado.duelo['batalha']


# ---------- começo
def novo():
    estado.duelo = {
        'fase': 'sorteio',
        'ordem': [random.choice(JOGADORES) for _ in range(PARTIDAS)],  #quem monta primeiro (e joga primeiro) em cada batalha
        'abre': random.choice(JOGADORES),                               #quem bane primeiro (e escolhe por último no draft)
        'vez': None, 'bans': {'a': [], 'v': []}, 'fim_bans': {'a': False, 'v': False},
        'exercitos': {'a': [], 'v': []}, 'gasto': {'a': 0, 'v': 0}, 'fim_draft': {'a': False, 'v': False},
        'pontos': {'a': 0, 'v': 0}, 'resultados': [], 'partida': 0, 'batalha': None}
    estado.duelo['vez'] = estado.duelo['abre']


def sair():
    estado.duelo = None


def avancar():
    d = estado.duelo
    if d['fase'] != 'sorteio':
        raise ValueError('O sorteio já passou')
    d['fase'] = 'banimentos'
    d['vez'] = d['abre']


# ---------- banimentos (alternados e públicos)
def _bans_ok(j):
    d = estado.duelo
    return d['fim_bans'][j] or len(d['bans'][j]) >= MAX_BANS


def _seguir_bans():
    d = estado.duelo
    if _bans_ok('a') and _bans_ok('v'):
        d['fase'] = 'draft'
        d['vez'] = outro(d['abre'])  #quem baniu primeiro escolhe por último
        return
    prox = outro(d['vez'])
    if not _bans_ok(prox):
        d['vez'] = prox


def banir(id_):
    d = estado.duelo
    if d['fase'] != 'banimentos':
        raise ValueError('Não é a hora de banir')
    j = d['vez']
    if _bans_ok(j):
        raise ValueError('Você não pode banir mais peças')
    if id_ not in ELEGIVEIS or id_ in d['bans']['a'] + d['bans']['v']:
        raise ValueError('Peça inválida')
    d['bans'][j].append(id_)
    _seguir_bans()


def fim_bans():
    d = estado.duelo
    if d['fase'] != 'banimentos':
        raise ValueError('Não é a hora de banir')
    d['fim_bans'][d['vez']] = True
    _seguir_bans()


# ---------- draft (escolhas alternadas, peças únicas)
def disponiveis():
    d = estado.duelo
    fora = set(d['bans']['a'] + d['bans']['v'] + d['exercitos']['a'] + d['exercitos']['v'])
    return [i for i in ELEGIVEIS if i not in fora]


def restante(j):
    return ORCAMENTO - estado.duelo['gasto'][j]


def _draft_ok(j):
    d = estado.duelo
    if d['fim_draft'][j] or len(d['exercitos'][j]) >= MAX_PECAS:
        return True
    return not any(dados.CATALOGO[i]['preco'] <= restante(j) for i in disponiveis())  #não sobrou nada que caiba


def _seguir_draft():
    d = estado.duelo
    if _draft_ok('a') and _draft_ok('v'):
        _iniciar_partida()
        return
    prox = outro(d['vez'])
    if not _draft_ok(prox):
        d['vez'] = prox


def escolher(id_):
    d = estado.duelo
    if d['fase'] != 'draft':
        raise ValueError('Não é a hora do draft')
    j = d['vez']
    if _draft_ok(j):
        raise ValueError('Você já terminou o draft')
    if id_ not in disponiveis():
        raise ValueError('Essa peça não está mais disponível')
    preco = dados.CATALOGO[id_]['preco']
    if preco > restante(j):
        raise ValueError('Moedas insuficientes')
    d['exercitos'][j].append(id_)
    d['gasto'][j] += preco
    _seguir_draft()


def parar():
    d = estado.duelo
    if d['fase'] != 'draft':
        raise ValueError('Não é a hora do draft')
    j = d['vez']
    if not d['exercitos'][j]:
        raise ValueError('Escolha pelo menos 1 peça')
    d['fim_draft'][j] = True
    _seguir_draft()


# ---------- montagem do tabuleiro
def _iniciar_partida():
    d = estado.duelo
    n = random.choice(CFG['tamanhos_tabuleiro'])
    primeiro = d['ordem'][d['partida']]
    segundo = outro(primeiro)
    fundo = {primeiro: n - 2, segundo: 2}  #3/5, 4/6 ou 5/7 do tabuleiro para quem monta primeiro; 2 linhas para o outro
    zonas = {}
    for j in JOGADORES:
        zonas[j] = [n - fundo[j], n] if LADO[j] == 'j' else [0, fundo[j]]  #[primeira linha, última linha + 1]
    d['batalha'] = {'n': n, 'pecas': [], 'posicoes': {'a': {}, 'v': {}}, 'zonas': zonas, 'primeiro': primeiro,
                    'montando': primeiro, 'vez': primeiro, 'rodadas': 0, 'turnos': 0, 'movs': 0, 'log': [],
                    'fase': 'montando', 'resultado': None, 'nomes': {'j': NOME['a'], 'i': NOME['v']},
                    # campos que o motor de xadrez e os efeitos esperam encontrar
                    'bonus': 0, 'capturas': 0, 'perdidas': [], 'proxima_captura': 0, 'serie': 0}
    d['fase'] = 'montagem'


def _ocupadas(b):
    return {tuple(p) for j in JOGADORES for p in b['posicoes'][j].values()}


def colocar(indice, linha, col):
    d = estado.duelo
    if d['fase'] != 'montagem':
        raise ValueError('Não é a hora de montar')
    b = d['batalha']
    j = b['montando']
    if not (0 <= indice < len(d['exercitos'][j])):
        raise ValueError('Peça inválida')
    z = b['zonas'][j]
    if not (z[0] <= linha < z[1] and 0 <= col < b['n']):
        raise ValueError('Coloque a peça na sua zona')
    outras = _ocupadas(b) - {tuple(b['posicoes'][j].get(str(indice)) or ())}  #a própria casa antiga fica livre
    if (linha, col) in outras:
        raise ValueError('Casa ocupada')
    b['posicoes'][j][str(indice)] = [linha, col]


def tirar(indice):
    d = estado.duelo
    if d['fase'] != 'montagem':
        raise ValueError('Não é a hora de montar')
    b = d['batalha']
    b['posicoes'][b['montando']].pop(str(indice), None)


def auto():
    d = estado.duelo
    if d['fase'] != 'montagem':
        raise ValueError('Não é a hora de montar')
    b = d['batalha']
    j = b['montando']
    n, z = b['n'], b['zonas'][j]
    frente = z[0] if LADO[j] == 'j' else z[1] - 1  #linha mais perto do inimigo
    livres = [(l, c) for l in range(z[0], z[1]) for c in range(n) if (l, c) not in _ocupadas(b)]
    livres.sort(key=lambda lc: (abs(lc[0] - frente), abs(lc[1] - (n - 1) / 2)))
    faltam = [i for i in range(len(d['exercitos'][j])) if str(i) not in b['posicoes'][j]]
    faltam.sort(key=lambda i: dados.CATALOGO[d['exercitos'][j][i]]['tipo'] != 'P')  #peões na frente
    for i, (l, c) in zip(faltam, livres):
        b['posicoes'][j][str(i)] = [l, c]


def pronto():
    d = estado.duelo
    if d['fase'] != 'montagem':
        raise ValueError('Não é a hora de montar')
    b = d['batalha']
    j = b['montando']
    if len(b['posicoes'][j]) < len(d['exercitos'][j]):
        raise ValueError('Posicione todas as peças primeiro')
    if j == b['primeiro']:
        b['montando'] = outro(j)  #agora monta o outro, já vendo o tabuleiro do primeiro
        return
    _comecar_batalha()


def peca_montada(j, indice, linha, col):
    d = estado.duelo
    id_ = d['exercitos'][j][indice]
    modelo = dados.CATALOGO[id_]
    p = xadrez.criar_peca(LADO[j], modelo['tipo'], [dict(e) for e in modelo['efeitos']], linha, col, id_)
    p['indice'] = indice
    p['dono'] = j
    return p


def _comecar_batalha():
    d = estado.duelo
    b = d['batalha']
    for j in JOGADORES:
        for i, (l, c) in b['posicoes'][j].items():
            b['pecas'].append(peca_montada(j, int(i), l, c))
    b['fase'] = 'jogando'
    efeitos.no_inicio_da_batalha(b)
    d['fase'] = 'batalha'
    b['log'].append('A batalha começou! %s joga primeiro.' % NOME[b['primeiro']])
    b['vez'] = b['primeiro']
    if not _tem_jogada(b['primeiro']):
        _proxima_vez(outro(b['primeiro']))


# ---------- batalha
def _tem_jogada(j):
    b = _batalha()
    return any(xadrez.movimentos(b['pecas'], p, b['n']) for p in b['pecas'] if p['lado'] == LADO[j])


def jogadas(j):
    b = _batalha()
    res = {}
    for p in b['pecas']:
        if p['lado'] == LADO[j]:
            ms = xadrez.movimentos(b['pecas'], p, b['n'])
            if ms:
                res['%d,%d' % (p['linha'], p['col'])] = ms
    return res


def _proxima_vez(quem_jogou):
    #passa a vez ao outro; quem não tem jogada perde a vez; se nenhum tem, é empate
    b = _batalha()
    prox = outro(quem_jogou)
    if _tem_jogada(prox):
        b['vez'] = prox
    elif _tem_jogada(quem_jogou):
        b['vez'] = quem_jogou
        b['log'].append('%s não tem jogadas e perde a vez.' % NOME[prox])
    else:
        _fim(None, 'Nenhum jogador consegue se mover.')


def _fim(vencedor, motivo):
    d = estado.duelo
    b = d['batalha']
    b['fase'] = 'fim'
    b['resultado'] = {'vencedor': vencedor, 'motivo': motivo}
    if vencedor:
        d['pontos'][vencedor] += 1
    else:
        d['pontos']['a'] += 0.5
        d['pontos']['v'] += 0.5
    d['resultados'].append({'partida': d['partida'], 'vencedor': vencedor, 'primeiro': b['primeiro'], 'n': b['n']})
    d['fase'] = 'resultado'


def mover(de, para):
    d = estado.duelo
    if d['fase'] != 'batalha':
        raise ValueError('Não há batalha em andamento')
    b = d['batalha']
    j = b['vez']
    p = xadrez.peca_em(b['pecas'], de[0], de[1])
    if not p or p['lado'] != LADO[j]:
        raise ValueError('Essa peça não é sua')
    if tuple(para) not in xadrez.movimentos(b['pecas'], p, b['n']):
        raise ValueError('Movimento ilegal')
    b['movs'] += 1
    xadrez.mover(b, p, para[0], para[1])
    azul, vermelho = xadrez.contar(b, 'j'), xadrez.contar(b, 'i')
    if not azul and not vermelho:
        return _fim(None, 'Todas as peças caíram.')
    if not vermelho:
        return _fim('a', 'O Vermelho ficou sem peças.')
    if not azul:
        return _fim('v', 'O Azul ficou sem peças.')
    if b['movs'] % 2 == 0:  #terminou uma rodada (os dois jogaram)
        b['rodadas'] += 1
        b['turnos'] = b['rodadas']
        efeitos.ao_fim_da_rodada(b)
        if b['rodadas'] >= CFG['max_rodadas']:
            return _fim(None, 'Acabou o tempo (%d rodadas).' % CFG['max_rodadas'])
    _proxima_vez(j)


def proxima():
    d = estado.duelo
    if d['fase'] != 'resultado':
        raise ValueError('A batalha ainda não acabou')
    d['partida'] += 1
    if d['partida'] >= PARTIDAS:
        d['fase'] = 'fim'
    else:
        _iniciar_partida()


# ---------- o que o navegador recebe
def _ameacas(b):
    #Casas que o adversário de quem joga poderia alcançar (realce de alcance inimigo)
    outro = LADO['v' if b['vez'] == 'a' else 'a']
    casas = set()
    for p in b['pecas']:
        if p['lado'] == outro:
            casas.update(xadrez.movimentos(b['pecas'], p, b['n']))
    return sorted(casas)


def visao():
    d = estado.duelo
    v = {k: d[k] for k in ('fase', 'ordem', 'abre', 'vez', 'bans', 'fim_bans', 'exercitos', 'gasto', 'fim_draft',
                           'pontos', 'resultados', 'partida')}
    v.update({'total': PARTIDAS, 'orcamento': ORCAMENTO, 'max_pecas': MAX_PECAS, 'max_bans': MAX_BANS,
              'elegiveis': ELEGIVEIS, 'nomes': NOME, 'limite': CFG['max_rodadas']})
    if d['fase'] == 'draft':
        v['disponiveis'] = disponiveis()
        v['restante'] = {j: restante(j) for j in JOGADORES}
        v['encerrado'] = {j: _draft_ok(j) for j in JOGADORES}
    b = d['batalha']
    if b:
        pecas = b['pecas']
        if d['fase'] == 'montagem':  #peças já colocadas (do primeiro e, depois, do segundo)
            pecas = [peca_montada(j, int(i), l, c) for j in JOGADORES for i, (l, c) in b['posicoes'][j].items()]
        v['batalha'] = {'n': b['n'], 'pecas': pecas, 'zonas': b['zonas'], 'primeiro': b['primeiro'], 'montando': b['montando'],
                        'vez': b['vez'], 'rodadas': b['rodadas'], 'log': b['log'][-10:], 'resultado': b['resultado'],
                        'fase': b['fase'], 'posicoes': b['posicoes'],
                        'jogadas': jogadas(b['vez']) if d['fase'] == 'batalha' else {},
                        'ameacas': _ameacas(b) if d['fase'] == 'batalha' else []}
    return v