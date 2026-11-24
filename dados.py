# Carrega os arquivos da pasta dados/ e confere se estão corretos.Se você errar algo ao editar um JSON, o jogo avisa aqui.

import json
import os

PASTA = os.path.dirname(os.path.abspath(__file__))


def ler(nome):
    caminho = os.path.join(PASTA, 'dados', nome)
    try:
        with open(caminho, encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as erro:
        raise SystemExit(f'ERRO em dados/{nome}, linha {erro.lineno}: {erro.msg}\n'
                         'Dica: confira vírgulas (toda linha leva vírgula, menos a última) e aspas.')


TIPOS = ler('tipos.json')
EFEITOS = ler('efeitos.json')
CONFIG = ler('config.json')
INIMIGOS = ler('inimigos.json')
_pecas = ler('pecas.json')


def descricao_dos_efeitos(lista_de_efeitos):
    #Monta o texto da peça a partir dos blocos de efeito dela
    partes = []
    for e in lista_de_efeitos:
        modelo = EFEITOS[e['tipo']]['desc']
        partes.append(modelo.replace('{valor}', str(e.get('valor', 1))))
    return ' '.join(partes) if partes else 'Peça comum, sem habilidade.'


def montar_catalogo():
    catalogo = {}
    for p in _pecas['pecas']:
        id_ = p.get('id', '???')
        for campo in ('id', 'nome', 'tipo', 'preco'):
            if campo not in p:
                raise SystemExit(f'ERRO em dados/pecas.json: a peça "{id_}" não tem o campo "{campo}".')
        if p['id'] in catalogo:
            raise SystemExit(f'ERRO em dados/pecas.json: o id "{id_}" aparece duas vezes.')
        if p['tipo'] not in TIPOS:
            raise SystemExit(f'ERRO em dados/pecas.json: peça "{id_}" tem tipo "{p["tipo"]}". Use: {", ".join(TIPOS)}')
        p.setdefault('efeitos', [])
        p.setdefault('loja', True)
        for e in p['efeitos']:
            if e.get('tipo') not in EFEITOS:
                raise SystemExit(f'ERRO em dados/pecas.json: peça "{id_}" usa o efeito "{e.get("tipo")}", '
                                 f'que não existe. Efeitos disponíveis: {", ".join(EFEITOS)}')
        if not p.get('desc'):
            p['desc'] = descricao_dos_efeitos(p['efeitos'])
        catalogo[p['id']] = p
    for id_ in _pecas['exercito_inicial']:
        if id_ not in catalogo:
            raise SystemExit(f'ERRO em dados/pecas.json: "{id_}" está no exercito_inicial mas não existe nas peças.')
    return catalogo


CATALOGO = montar_catalogo()
CHAVES_LOJA = [id_ for id_, p in CATALOGO.items() if p['loja']]
EXERCITO_INICIAL = _pecas['exercito_inicial']


# CARTAS E PACOTES
RARIDADES = ['comum', 'incomum', 'rara', 'epica', 'lendaria']
NOMES_RARIDADE = {'comum': 'Comum', 'incomum': 'Incomum', 'rara': 'Rara', 'epica': 'Épica', 'lendaria': 'Lendária'}
PACOTES = ler('pacotes.json')

# ESTÁGIOS (dificuldade que sobe a cada batalha)
_est = ler('estagios.json')
MAXIMO_INIMIGOS = _est['maximo_inimigos']
ESTAGIOS = _est['estagios']
_CAMPOS_ESTAGIO = ['nome', 'ate', 'inimigos', 'inteligencia', 'olhar_a_frente', 'media', 'recompensa_base', 'tabuleiros',
                   'pesos', 'chance_escudo', 'escudo_valor', 'chance_explosivo', 'chefe']
for _i, _e in enumerate(ESTAGIOS):
    for _c in _CAMPOS_ESTAGIO:
        if _c not in _e:
            raise SystemExit(f'ERRO em dados/estagios.json: o estágio {_i + 1} está sem o campo "{_c}".')
    if _e['chefe']['pacote'] not in PACOTES:
        raise SystemExit(f'ERRO em dados/estagios.json: o pacote "{_e["chefe"]["pacote"]}" do chefe de "{_e["nome"]}" não existe em pacotes.json.')
    if _e['ate'] is None and _i != len(ESTAGIOS) - 1:
        raise SystemExit('ERRO em dados/estagios.json: só o último estágio pode ter "ate": null.')
if ESTAGIOS[-1]['ate'] is not None:
    raise SystemExit('ERRO em dados/estagios.json: o último estágio precisa ter "ate": null (sem fim).')


def estagio(num):
    # Configuração da batalha número (1, 2, 3...). Devolve uma cópia que pode ser alterada
    inicio = 1
    for e in ESTAGIOS:
        if e['ate'] is not None and num > e['ate']:
            inicio = e['ate'] + 1
            continue
        r = dict(e)
        r['inicio'] = inicio
        r['nivel'] = 0
        if e['ate'] is not None:
            r['chefe_agora'] = (num == e['ate'])
        else:  # último estágio: continua subindo a cada batalha
            cr = e['crescimento']
            r['nivel'] = (num - inicio) // cr['a_cada']
            r['chefe_agora'] = ((num - inicio + 1) % cr['a_cada'] == 0)
            r['chance_escudo'] = min(1.0, e['chance_escudo'] + cr['chance_escudo_mais'] * r['nivel'])
            r['chance_explosivo'] = min(1.0, e['chance_explosivo'] + cr['chance_explosivo_mais'] * r['nivel'])
            r['escudo_valor'] = min(cr['escudo_valor_max'], e['escudo_valor'] + r['nivel'] // cr['escudo_valor_a_cada_niveis'])
            r['media'] = e['media'] + cr['media_mais'] * r['nivel']
        r['inimigos'] = min(r['inimigos'], MAXIMO_INIMIGOS)
        return r
_cartas = ler('cartas.json')


def montar_cartas():
    cartas = {}
    for c in _cartas['cartas']:
        id_ = c.get('id', '???')
        for campo in ('id', 'nome', 'raridade', 'categoria', 'desc'):
            if campo not in c:
                raise SystemExit(f'ERRO em dados/cartas.json: a carta "{id_}" não tem o campo "{campo}".')
        if c['id'] in cartas:
            raise SystemExit(f'ERRO em dados/cartas.json: o id "{id_}" aparece duas vezes.')
        if c['raridade'] not in RARIDADES:
            raise SystemExit(f'ERRO em dados/cartas.json: carta "{id_}" tem raridade "{c["raridade"]}". Use: {", ".join(RARIDADES)}')
        if c['categoria'] not in ('permanente', 'consumivel', 'risco'):
            raise SystemExit(f'ERRO em dados/cartas.json: carta "{id_}" tem categoria "{c["categoria"]}". '
                             'Use: permanente, consumivel ou risco.')
        c.setdefault('efeitos', [])
        c.setdefault('implementado', True)
        c.setdefault('quando', 'batalha')
        c.setdefault('alvo', 'nenhum')
        cartas[c['id']] = c
    return cartas


CARTAS = montar_cartas()
# Cartas que podem sair nos pacotes (só as que já têm efeito programado), por raridade
CARTAS_POR_RARIDADE = {r: [c['id'] for c in CARTAS.values() if c['raridade'] == r and c['implementado']]
                       for r in RARIDADES}

for _id, _p in PACOTES.items():
    _soma = sum(_p['probabilidades'].values())
    if abs(_soma - 100) > 0.01:
        raise SystemExit(f'ERRO em dados/pacotes.json: as probabilidades de "{_id}" somam {_soma}, e deveriam somar 100.')