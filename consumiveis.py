import random
import dados
import estado
import xadrez

CFG = dados.CONFIG
MOMENTOS = {  # em que telas cada valor de "quando" permite usar a carta
    'qualquer': ('loja', 'posicionamento', 'batalha'),
    'loja': ('loja',),
    'batalha': ('batalha',),
    'posicionamento': ('posicionamento',),
    'combate': ('posicionamento', 'batalha'),
    'preparo': ('loja', 'posicionamento'),
}


#utilidades
def _batalha():
    return estado.run['batalha']


def _inimigos(b):
    """Lista das peças inimigas (antes da batalha ficam em b['inimigos'], depois em b['pecas'])."""
    if b['fase'] == 'posicionando':
        return b['inimigos']
    return [p for p in b['pecas'] if p['lado'] == 'i']


def _remover_inimigo(b, p):
    lista = b['inimigos'] if b['fase'] == 'posicionando' else b['pecas']
    lista.remove(p)


def _minha_peca(b, indice):
    if b['fase'] != 'jogando':
        raise ValueError('Use esta carta durante a batalha.')
    for p in b['pecas']:
        if p['lado'] == 'j' and p.get('indice') == indice:
            return p
    raise ValueError('Essa peça não está mais no tabuleiro.')


#ações (uma por bloco)
def ganhar_moedas(bl, alvo):
    estado.run['moedas'] += bl['valor']


def investimento(bl, alvo):
    estado.run['moedas'] += bl['agora']
    estado.run['moedas_proxima_loja'] += bl['loja']


def cupom(bl, alvo):
    estado.run['cupom'] = bl['valor']


def reembolso(bl, alvo):
    run = estado.run
    run['moedas'] += (run['ultima_compra'] + 1) // 2
    run['ultima_compra'] = 0


def escudo_todas(bl, alvo):
    for p in _batalha()['pecas']:
        if p['lado'] == 'j':
            p['escudo'] += bl['valor']


def escudo_alvo(bl, alvo):
    _minha_peca(_batalha(), alvo)['escudo'] += bl['valor']


def efeito_alvo(bl, alvo):
    p = _minha_peca(_batalha(), alvo)
    p['efeitos'] = p['efeitos'] + [dict(bl['efeito'])]


def remendo(bl, alvo):
    p = _minha_peca(_batalha(), alvo)
    p['escudo'] = max(p['escudo'], 1)


def promover_alvo(bl, alvo):
    p = _minha_peca(_batalha(), alvo)
    if p['tipo'] != 'P':
        raise ValueError('Escolha um peão.')
    p['tipo'] = 'Q'


def promover_peoes(bl, alvo):
    peoes = [p for p in _batalha()['pecas'] if p['lado'] == 'j' and p['tipo'] == 'P']
    if not peoes:
        raise ValueError('Você não tem peões vivos.')
    for p in random.sample(peoes, min(bl['valor'], len(peoes))):
        p['tipo'] = 'Q'


def inimigo_pula(bl, alvo):
    _batalha()['inimigo_pula'] += bl['valor']


def inimigo_aleatorio(bl, alvo):
    _batalha()['inimigo_aleatorio'] += bl['valor']


def inimigo_sem_tipo(bl, alvo):
    _batalha()['inimigo_sem_tipo'] = {'peca': bl['peca'], 'rodadas': bl['valor']}


def mostrar_ameacas(bl, alvo):
    _batalha()['ameacas'] = True


def municao(bl, alvo):
    _batalha()['proxima_captura'] += bl['valor']


def rodadas_gratis(bl, alvo):
    _batalha()['rodadas_gratis'] += bl['valor']


def destruir_aleatorias(bl, alvo):
    b = _batalha()
    inimigos = _inimigos(b)
    for p in random.sample(inimigos, min(bl['valor'], len(inimigos))):
        _remover_inimigo(b, p)


def destruir_maior(bl, alvo):
    b = _batalha()
    inimigos = _inimigos(b)
    if inimigos:
        _remover_inimigo(b, max(inimigos, key=lambda p: dados.TIPOS[p['tipo']]['valor']))


def destruir_tipo(bl, alvo):
    b = _batalha()
    for p in [p for p in _inimigos(b) if p['tipo'] == bl['peca']]:
        _remover_inimigo(b, p)


def destruir_metade(bl, alvo):
    b = _batalha()
    inimigos = _inimigos(b)
    quantidade = len(inimigos) if bl.get('todas') else (len(inimigos) + 1) // 2
    for p in random.sample(inimigos, quantidade):
        _remover_inimigo(b, p)


def embaralhar_inimigas(bl, alvo):
    inimigos = _inimigos(_batalha())
    posicoes = [(p['linha'], p['col']) for p in inimigos]
    random.shuffle(posicoes)
    for p, (l, c) in zip(inimigos, posicoes):
        p['linha'], p['col'] = l, c


def remover_escudos_inimigos(bl, alvo):
    for p in _inimigos(_batalha()):
        p['escudo'] = 0


def reviver(bl, alvo):
    b = _batalha()
    if b['fase'] != 'jogando':
        raise ValueError('Use esta carta durante a batalha.')
    if not b['perdidas']:
        raise ValueError('Nenhuma peça sua foi capturada ainda.')
    for _ in range(bl['valor']):
        if not b['perdidas']:
            break
        livres = [(l, c) for l in range(b['zona_inicio'], b['n']) for c in range(b['n'])
                  if xadrez.peca_em(b['pecas'], l, c) is None]
        if not livres:
            break
        p = b['perdidas'].pop()
        p['linha'], p['col'] = random.choice(livres)
        b['pecas'].append(p)


def permanente_alvo(bl, alvo):
    run = estado.run
    if not (0 <= alvo < len(run['exercito'])):
        raise ValueError('Escolha uma peça do seu exército.')
    run['extras'].setdefault(str(alvo), []).append(dict(bl['efeito']))


#cartas de risco (só no posicionamento)
def risco_sem_escudos(bl, alvo):
    b = _batalha()
    b['sem_escudos'] = True
    b['bonus_vitoria'] += bl['valor']


def risco_desafio(bl, alvo):
    import run as modulo_run
    b = _batalha()
    modulo_run.adicionar_inimigos(b, bl['extra'], bl['escudos'])
    b['mult_recompensa'] *= bl['mult']


def risco_pacto(bl, alvo):
    run = estado.run
    run['exercito'][random.randrange(len(run['exercito']))] = 'P:comum'
    run['moedas'] += bl['moedas']


def risco_contrato(bl, alvo):
    _batalha()['contrato'] = bl['ganho']


def risco_aposta(bl, alvo):
    run = estado.run
    if run['moedas'] < bl['custo']:
        raise ValueError('Você precisa de %d moedas para apostar.' % bl['custo'])
    run['moedas'] -= bl['custo']
    _batalha()['aposta'] = bl['ganho']


def risco_tudo_ou_nada(bl, alvo):
    _batalha()['tudo_ou_nada'] = {'ganho': bl['ganho'], 'perda': bl['perda']}


ACOES = {nome: f for nome, f in globals().items() if callable(f) and not nome.startswith('_')
         and nome not in ('xadrez',)}


#usar uma carta
def usar(posicao, alvo=None):
    run = estado.run
    if not (0 <= posicao < len(run['consumiveis'])):
        raise ValueError('Carta inválida')
    carta = dados.CARTAS[run['consumiveis'][posicao]]
    if run['tela'] not in MOMENTOS[carta['quando']]:
        raise ValueError('Esta carta não pode ser usada agora.')
    if carta['categoria'] == 'risco' and run['batalha']['fase'] != 'posicionando':
        raise ValueError('Cartas de risco só valem antes da batalha começar.')
    if carta['alvo'] == 'minha_peca' and alvo is None:
        raise ValueError('Escolha uma peça.')
    for bloco in carta['efeitos']:
        ACOES[bloco['tipo']](bloco, alvo)
    run['consumiveis'].pop(posicao)
    if run['tela'] == 'batalha':
        import run as modulo_run
        modulo_run.checar_vitoria()