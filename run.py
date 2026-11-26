#A run: sequência de batalhas, posicionamento, recompensas e fim de jogo
import random

import cartas
import colecao
import dados
import efeitos
import estado
import loja
import pacotes
import xadrez

CFG = dados.CONFIG


def novo_jogo():
    colecao.dados_colecao['runs'] += 1
    colecao.salvar()
    estado.run = {'moedas': CFG['moedas_iniciais'], 'num': 1,
                  'exercito': list(dados.EXERCITO_INICIAL), 'tela': 'posicionamento',
                  'batalha': None, 'loja': None, 'relatorio': None,
                  'cartas': [], 'consumiveis': [], 'extras': {}, 'pacote': None,
                  'cupom': 0, 'moedas_proxima_loja': 0, 'ultima_compra': 0, 'compras_na_loja': 0}
    preparar_batalha()
    pacotes.abrir('pacote_inicial')  # toda run começa com um pacote inicial


def sanear_partida():
    #Partida salva com peça que deixou de existir (ex.: Incendiárias): troca pela peça comum do mesmo tipo
    r = estado.run
    if not isinstance(r, dict):
        return

    def valida(id_):
        return id_ if id_ in dados.CATALOGO else str(id_).split(':')[0] + ':comum'

    r['exercito'] = [valida(i) for i in r['exercito']]
    if r.get('loja'):
        r['loja']['ofertas'] = [valida(i) for i in r['loja']['ofertas']]
        r['loja']['misteriosa'] = valida(r['loja']['misteriosa'])


def niveis_da_maquina():
    #Dificuldades que o modo de teste oferece: uma básica e uma para cada estágio do jogo
    niveis = [{'nome': 'Básica', 'inteligencia': 0.0, 'olhar': 0}]
    for e in dados.ESTAGIOS:
        niveis.append({'nome': e['nome'], 'inteligencia': e['inteligencia'], 'olhar': e['olhar_a_frente']})
    return niveis


def montar_teste(d):
    #Modo de teste: monta uma batalha já em andamento com as peças e as posições escolhidas na tela de teste
    n = int(d['n'])
    if n not in (5, 6, 7):
        raise ValueError('O tabuleiro precisa ter 5, 6 ou 7 casas')
    lista = d['pecas']
    if not isinstance(lista, list) or len(lista) > n * n:
        raise ValueError('Peças demais para o tabuleiro')
    usadas, meus, inimigos = set(), [], []
    for item in lista:
        id_, lado, l, c = item['id'], item['lado'], int(item['linha']), int(item['col'])
        if id_ not in dados.CATALOGO or lado not in ('j', 'i') or not (0 <= l < n and 0 <= c < n) or (l, c) in usadas:
            raise ValueError('Cenário inválido')
        usadas.add((l, c))
        (meus if lado == 'j' else inimigos).append((id_, l, c))
    if not meus or not inimigos:
        raise ValueError('Coloque ao menos uma peça sua e uma inimiga')
    estado.run = {'moedas': 0, 'num': 1, 'exercito': [m[0] for m in meus], 'tela': 'posicionamento',
                  'batalha': None, 'loja': None, 'relatorio': None,
                  'cartas': [], 'consumiveis': [], 'extras': {}, 'pacote': None,
                  'cupom': 0, 'moedas_proxima_loja': 0, 'ultima_compra': 0, 'compras_na_loja': 0}
    preparar_batalha()
    b = estado.run['batalha']
    b['n'] = n
    b['modo_teste'] = True
    niveis = niveis_da_maquina()
    nivel = int(d.get('nivel', 1))
    if not (0 <= nivel < len(niveis)):
        raise ValueError('Dificuldade inválida')
    b['inteligencia'] = niveis[nivel]['inteligencia']  # a máquina joga com a dificuldade escolhida
    b['olhar'] = niveis[nivel]['olhar']
    b['nivel_teste'] = niveis[nivel]['nome']
    b['pecas'] = []
    for id_, l, c in inimigos:
        modelo = dados.CATALOGO[id_]
        b['pecas'].append(xadrez.criar_peca('i', modelo['tipo'], [dict(e) for e in modelo['efeitos']], l, c, id_))
    for i, (id_, l, c) in enumerate(meus):
        b['pecas'].append(peca_do_jogador(i, l, c))
    b['meus_iniciais'] = len(meus)
    efeitos.no_inicio_da_batalha(b)
    cartas.aplicar_no_inicio(b)
    b['fase'] = 'jogando'
    b['log'].append('Cenário de teste montado')
    estado.run['tela'] = 'batalha'


def teste_parado(valor):
    estado.run['batalha']['inimigo_parado'] = valor  # no modo de teste o inimigo pode ficar sem jogar


def teste_avancar(quantidade):
    #Modo de teste: passa rodadas sem jogar, para ver efeitos que dependem de tempo
    b = estado.run['batalha']
    for _ in range(max(0, min(quantidade, 20))):
        b['turnos'] += 1
        b['rodadas'] += 1
        efeitos.ao_fim_da_rodada(b)


def abandonar():
    estado.run = None


#efeitos de movimento que os inimigos podem receber (só os automáticos, que não pedem decisão)
EFEITOS_DE_MOVIMENTO_INIMIGO = {'P': ['berserker', 'peao_saltador', 'peao_independente'], 'N': ['berserker', 'parasita'],
                                'B': ['parasita', 'bispo_independente'], 'R': ['parasita'], 'Q': ['parasita']}


def _sortear_inimigos(e, quantidade, casas, chefe):
    """Cria as peças inimigas do estágio `e`. Chefe: composição definida em estagios.json."""
    tipos = []
    if chefe:
        tipos = list(chefe['obrigatorias'])
    pesos = {t: v for t, v in e['pesos'].items() if v > 0}
    while len(tipos) < quantidade:
        tipos.append(random.choices(list(pesos), list(pesos.values()))[0])
    tipos = tipos[:quantidade]
    efeitos_de_cada = [[] for _ in tipos]
    if chefe:
        for i in range(min(chefe['escudos'], len(tipos))):  # as obrigatórias vêm primeiro
            efeitos_de_cada[i].append({'tipo': 'escudo', 'valor': e['escudo_valor']})
        for i in range(len(tipos) - 1, len(tipos) - 1 - min(chefe['explosivas'], len(tipos)), -1):
            efeitos_de_cada[i].append({'tipo': 'explodir_ao_ser_capturado'})
    else:
        for lista in efeitos_de_cada:
            if random.random() < e['chance_escudo']:
                lista.append({'tipo': 'escudo', 'valor': e['escudo_valor']})
            if random.random() < e['chance_explosivo']:
                lista.append({'tipo': 'explodir_ao_ser_capturado'})
    for tipo, lista in zip(tipos, efeitos_de_cada):  # alguns inimigos andam de um jeito especial
        opcoes = EFEITOS_DE_MOVIMENTO_INIMIGO.get(tipo)
        if opcoes and random.random() < e.get('chance_movimento', 0):
            nome = random.choice(opcoes)
            lista.append({'tipo': nome, 'max': 3} if nome == 'berserker' else {'tipo': nome})
    inimigos = []
    for tipo, lista, (l, c) in zip(tipos, efeitos_de_cada, casas):
        inimigos.append(xadrez.criar_peca('i', tipo, lista, l, c))
    return inimigos


def preparar_batalha():
    run = estado.run
    num = run['num']
    e = dados.estagio(num)
    n = random.choice(e['tabuleiros'])
    zona_inicio = max(2, n - 2 - cartas.zona_extra())  # primeira linha da zona do jogador
    casas = [(l, c) for l in range(zona_inicio) for c in range(n)]  # inimigo ocupa a parte de cima
    maximo = int(len(casas) * dados.INIMIGOS['ocupacao_maxima'])
    chefe = e['chefe'] if e['chefe_agora'] else None
    quantidade = chefe['quantidade'] if chefe else e['inimigos']
    quantidade = min(maximo, dados.MAXIMO_INIMIGOS, quantidade)
    quantidade = max(1, quantidade - cartas.inimigos_a_menos())
    random.shuffle(casas)
    inimigos = _sortear_inimigos(e, quantidade, casas, chefe)

    run['batalha'] = {'n': n, 'inimigos': inimigos, 'posicoes': {}, 'pecas': [], 'rodadas': 0, 'turnos': 0,
                      'estagio': e, 'chefe': bool(chefe), 'inteligencia': e['inteligencia'], 'olhar': e['olhar_a_frente'],
                      'log': [], 'bonus': 0, 'fase': 'posicionando', 'vez': 'jogador', 'zona_inicio': zona_inicio,
                      'capturas': 0, 'perdidas': [], 'meus_iniciais': 0,
                      'inimigo_pula': 0, 'inimigo_aleatorio': 0, 'inimigo_sem_tipo': None,
                      'rodadas_gratis': 0, 'proxima_captura': 0, 'ameacas': False, 'sem_escudos': False,
                      'bonus_vitoria': 0, 'mult_recompensa': 1, 'contrato': 0, 'aposta': 0, 'tudo_ou_nada': None}
    run['tela'] = 'posicionamento'
    run['cupom'] = 0


def adicionar_inimigos(batalha, quantidade, com_escudo):
    """Usado por cartas de risco: coloca inimigos extras nas casas livres da zona inimiga."""
    ocupadas = {(p['linha'], p['col']) for p in batalha['inimigos']}
    livres = [(l, c) for l in range(batalha['zona_inicio']) for c in range(batalha['n']) if (l, c) not in ocupadas]
    random.shuffle(livres)
    for (l, c) in livres[:quantidade]:
        tipo = random.choices('PNBR', [40, 20, 20, 15])[0]
        ef = [{'tipo': 'escudo', 'valor': 1}] if com_escudo else []
        batalha['inimigos'].append(xadrez.criar_peca('i', tipo, ef, l, c))


def peca_do_jogador(indice, linha, col):
    id_da_peca = estado.run['exercito'][indice]
    modelo = dados.CATALOGO[id_da_peca]
    lista_de_efeitos = [dict(e) for e in modelo['efeitos']] + cartas.efeitos_extras_da_peca(modelo['tipo'], indice)
    p = xadrez.criar_peca('j', modelo['tipo'], lista_de_efeitos, linha, col, id_da_peca)
    p['indice'] = indice
    return p


# ---------------- posicionamento
def colocar(indice, linha, col):
    b = estado.run['batalha']
    if not (b['zona_inicio'] <= linha < b['n'] and 0 <= col < b['n']):
        raise ValueError('Posicione dentro da sua zona (azul)')
    for k, v in list(b['posicoes'].items()):  # se já havia outra peça na casa, ela volta para a bandeja
        if v == [linha, col]:
            del b['posicoes'][k]
    b['posicoes'][str(indice)] = [linha, col]


def tirar(indice):
    estado.run['batalha']['posicoes'].pop(str(indice), None)


def autoposicionar():
    b = estado.run['batalha']
    n = b['n']
    exercito = estado.run['exercito']
    ordem = sorted(range(len(exercito)), key=lambda i: dados.CATALOGO[exercito[i]]['tipo'] != 'P')  # peões na frente
    colunas = sorted(range(n), key=lambda c: abs(c - (n - 1) / 2))  # do centro para as bordas
    casas = [(l, c) for l in range(b['zona_inicio'], n) for c in colunas]
    b['posicoes'] = {str(i): list(casas[k]) for k, i in enumerate(ordem)}


def iniciar_batalha():
    b = estado.run['batalha']
    if len(b['posicoes']) < len(estado.run['exercito']):
        raise ValueError('Posicione todas as peças primeiro')
    b['pecas'] = [dict(p) for p in b['inimigos']]
    for i, (l, c) in b['posicoes'].items():
        b['pecas'].append(peca_do_jogador(int(i), l, c))
    b['meus_iniciais'] = len(b['posicoes'])
    efeitos.no_inicio_da_batalha(b)  # habilidades das peças (escudos iniciais, mutantes...)
    cartas.aplicar_no_inicio(b)
    b['fase'] = 'jogando'
    b['vez'] = 'inimigo'  #o inimigo já estava montado, então joga primeiro (mesma regra do duelo)
    b['abertura'] = True  #a primeira jogada do inimigo não fecha rodada
    b['log'].append('A batalha começou! O inimigo joga primeiro.')
    estado.run['tela'] = 'batalha'


# ---------------- batalha
def jogada_do_jogador(de, para):
    b = estado.run['batalha']
    p = xadrez.peca_em(b['pecas'], de[0], de[1])
    if b['fase'] != 'jogando' or b['vez'] != 'jogador' or not p or p['lado'] != 'j':
        raise ValueError('Jogada inválida')
    if tuple(para) not in xadrez.movimentos(b['pecas'], p, b['n']):
        raise ValueError('Movimento ilegal')
    b['aviso'] = ''
    b['turnos'] += 1
    if b['rodadas_gratis'] > 0:  # algumas cartas fazem jogadas não contarem como rodada
        b['rodadas_gratis'] -= 1
    else:
        b['rodadas'] += 1
    xadrez.mover(b, p, para[0], para[1])
    if xadrez.contar(b, 'i') == 0:
        return fim_de_batalha(True)
    if xadrez.contar(b, 'j') == 0:  # explosões podem eliminar o seu último pedaço do exército
        return fim_de_batalha(False, 'Todo o seu exército foi capturado.')
    b['vez'] = 'inimigo'  # o navegador espera 1 segundo e então chama vez_do_inimigo()


def vez_do_inimigo():
    b = estado.run['batalha']
    if b['fase'] != 'jogando' or b['vez'] != 'inimigo':
        raise ValueError('Não é a vez do inimigo')
    b['vez'] = 'jogador'
    if b.get('inimigo_parado'):
        b['log'].append('Inimigo parado (modo de teste).')
    elif b['inimigo_pula'] > 0:
        b['inimigo_pula'] -= 1
        b['log'].append('O inimigo perdeu o turno.')
    else:
        xadrez.jogada_inimiga(b)
    if xadrez.contar(b, 'i') == 0:  # o inimigo perdeu as últimas peças na própria jogada (explosões)
        return fim_de_batalha(True)
    if xadrez.contar(b, 'j') == 0:
        return fim_de_batalha(False, 'Todo o seu exército foi capturado.')
    if not b.pop('abertura', False):  #na jogada de abertura a rodada só fecha depois da resposta do jogador
        efeitos.ao_fim_da_rodada(b)
        limite = cartas.limite_de_rodadas()
        if limite and b['turnos'] >= limite:
            return fim_de_batalha(False, f'Acabou o tempo ({limite} rodadas).')
    tem_jogada = any(xadrez.movimentos(b['pecas'], q, b['n']) for q in b['pecas'] if q['lado'] == 'j')
    if not tem_jogada:  # sem jogadas, o jogador perde a vez (como no duelo); se o inimigo também não pode se mover, a batalha acaba
        if not any(xadrez.movimentos(b['pecas'], q, b['n']) for q in b['pecas'] if q['lado'] == 'i'):
            return fim_de_batalha(False, 'Nenhum lado consegue se mover.')
        b['turnos'] += 1  # a vez perdida conta como rodada, para o limite de rodadas continuar valendo
        b['rodadas'] += 1
        b['vez'] = 'inimigo'
        b['log'].append('Você não tem jogadas e perde a vez.')
        b['aviso'] = 'Você não tem jogadas e perde a vez.'


def checar_vitoria():
    """Chamada depois de usar uma carta: se ela destruiu todos os inimigos, a batalha termina."""
    b = estado.run['batalha']
    if estado.run['tela'] == 'batalha' and b['fase'] == 'jogando' and xadrez.contar(b, 'i') == 0:
        fim_de_batalha(True)


def fim_de_batalha(venceu, motivo=''):
    run = estado.run
    b = run['batalha']
    d = b['estagio']
    b['fase'] = 'fim'
    col = colecao.dados_colecao
    if not venceu:
        run['tela'] = 'derrota'
        run['relatorio'] = {'motivo': motivo, 'vencidas': run['num'] - 1}
        col['melhor'] = max(col['melhor'], run['num'] - 1)
        colecao.salvar()
        return
    rel = cartas.calcular_recompensa(run, b, d)
    run['moedas'] += rel['total']
    run['relatorio'] = rel
    col['melhor'] = max(col['melhor'], run['num'])
    run['tela'] = 'loja'
    run['compras_na_loja'] = 0
    run['loja'] = loja.gerar_loja(CFG['custo_inicial_troca'])
    rel['loja'] = cartas.moedas_ao_entrar_na_loja()  # Moeda da Sorte, Lotérica, Investimento...
    run['moedas'] += rel['loja']
    rel['chefe'] = b['chefe']
    if b['chefe']:  # chefe derrotado: pacote grátis
        pacotes.abrir(d['chefe']['pacote'])
        rel['pacote_chefe'] = dados.PACOTES[d['chefe']['pacote']]['nome']
    colecao.salvar()


def proxima_batalha():
    estado.run['num'] += 1
    preparar_batalha()