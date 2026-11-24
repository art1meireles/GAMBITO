#Servidor web: recebe os cliques do navegador e devolve o estado do jogo. Não guarda nada: a run e a coleção viajam com cada pedido
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import cartas
import colecao
import consumiveis
import dados
import estado
import loja
import pacotes
import run
import xadrez

ARQUIVOS = {'/': ('index.html', 'text/html'), '/style.css': ('style.css', 'text/css'),
            '/app.js': ('app.js', 'application/javascript')}
TRAVA = threading.Lock()  # uma requisição por vez mexe no estado


def _info_estagio(num):
    e = dados.estagio(num)
    return {'nome': e['nome'], 'media': e['media'], 'chefe': e['chefe_agora'], 'nivel': e['nivel']}


def estado_para_o_navegador():
    s = {'tela': 'menu', 'catalogo': dados.CATALOGO, 'efeitos': dados.EFEITOS, 'config': dados.CONFIG,
         'loja_chaves': dados.CHAVES_LOJA, 'colecao': colecao.dados_colecao,
         'cartas_catalogo': dados.CARTAS, 'pacotes': dados.PACOTES, 'raridades': dados.NOMES_RARIDADE,
         'ordem_raridades': dados.RARIDADES}
    r = estado.run
    if r is None:
        return s
    s.update({'tela': r['tela'], 'moedas': r['moedas'], 'num': r['num'], 'estagio': _info_estagio(r['num']),
              'exercito': r['exercito'], 'relatorio': r['relatorio'], 'loja': r['loja'], 'pacote': r['pacote'],
              'cartas': r['cartas'], 'consumiveis': r['consumiveis'], 'espacos': cartas.espacos(),
              'extras': r['extras'], 'cupom': r['cupom']})
    if r['tela'] == 'loja':
        lj = r['loja']
        s['precos'] = {'ofertas': [cartas.preco_da_peca(k) for k in lj['ofertas']],
                       'misteriosa': cartas.preco_da_misteriosa(), 'troca': cartas.custo_da_troca(lj)}
    b = r['batalha']
    if b and r['tela'] in ('posicionamento', 'batalha'):
        pecas = b['pecas']
        if b['fase'] == 'posicionando':  # mostra as peças já colocadas
            pecas = [dict(p) for p in b['inimigos']]
            for i, (l, c) in b['posicoes'].items():
                pecas.append(run.peca_do_jogador(int(i), l, c))
        jogadas = {}
        if b['fase'] == 'jogando' and b['vez'] == 'jogador':
            for p in pecas:
                if p['lado'] == 'j':
                    ms = xadrez.movimentos(pecas, p, b['n'])
                    if ms:
                        jogadas['%d,%d' % (p['linha'], p['col'])] = ms
        ameacas = xadrez.casas_ameacadas(b) if b['ameacas'] and b['fase'] == 'jogando' else []
        limite = cartas.limite_de_rodadas()
        s['batalha'] = {'n': b['n'], 'pecas': pecas, 'posicoes': b['posicoes'], 'rodadas': b['rodadas'],
                        'log': b['log'][-12:], 'jogadas': jogadas, 'zona_inicio': b['zona_inicio'],
                        'ameacas': ameacas, 'limite': limite, 'fase': b['fase'], 'vez': b['vez']}
    return s


def executar(acao, d):
    if acao == 'novo':
        run.novo_jogo()
    elif acao == 'abandonar':
        run.abandonar()
    elif acao == 'colocar':
        run.colocar(int(d['indice']), int(d['linha']), int(d['col']))
    elif acao == 'tirar':
        run.tirar(int(d['indice']))
    elif acao == 'auto':
        run.autoposicionar()
    elif acao == 'iniciar':
        run.iniciar_batalha()
    elif acao == 'mover':
        run.jogada_do_jogador(d['de'], d['para'])
    elif acao == 'vez_inimigo':
        run.vez_do_inimigo()
    elif acao == 'trocar':
        loja.trocar_ofertas()
    elif acao == 'comprar':
        slot = d['slot'] if d['slot'] == 'misteriosa' else int(d['slot'])
        loja.comprar(slot, int(d['substituir']))
    elif acao == 'comprar_pacote':
        loja.comprar_pacote(int(d['slot']))
    elif acao == 'escolher_carta':
        subst = d.get('substituir')
        pacotes.escolher(int(d['opcao']), None if subst is None else int(subst))
    elif acao == 'pular_pacote':
        pacotes.pular()
    elif acao == 'usar_carta':
        alvo = d.get('alvo')
        consumiveis.usar(int(d['indice']), None if alvo is None else int(alvo))
    elif acao == 'proxima':
        if estado.run['pacote'] is not None:
            raise ValueError('Escolha uma carta do pacote aberto primeiro.')
        run.proxima_batalha()
    elif acao != 'estado':
        raise ValueError('Ação desconhecida')


def processar(corpo):
    #Recebe {acao, dados, run, colecao} do navegador, executa a ação e devolve o novo estado
    run_recebida = corpo.get('run')
    if run_recebida is not None and not isinstance(run_recebida, dict):
        raise ValueError('partida salva inválida')
    with TRAVA:
        estado.run = run_recebida
        colecao.definir(corpo.get('colecao'))
        executar(str(corpo.get('acao') or 'estado'), corpo.get('dados') or {})
        s = estado_para_o_navegador()
        s['_run'] = estado.run  # o navegador guarda isto e manda de volta no próximo pedido
        return s


class Servidor(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # silencia o log do terminal

    def responder(self, codigo, conteudo, tipo='application/json'):
        if not isinstance(conteudo, bytes):
            conteudo = json.dumps(conteudo, ensure_ascii=False).encode('utf-8')
        self.send_response(codigo)
        self.send_header('Content-Type', tipo + '; charset=utf-8')
        self.end_headers()
        self.wfile.write(conteudo)

    def do_GET(self):
        arquivo, tipo = ARQUIVOS.get(self.path, ('index.html', 'text/html'))
        with open(os.path.join(dados.PASTA, 'public', arquivo), 'rb') as f:
            self.responder(200, f.read(), tipo)

    def do_POST(self):
        try:
            tamanho = int(self.headers.get('Content-Length') or 0)
            if tamanho > 2_000_000:
                raise ValueError('pedido grande demais')
            corpo = json.loads(self.rfile.read(tamanho) or b'{}')
            if not isinstance(corpo, dict):
                raise ValueError('requisição inválida')
            self.responder(200, processar(corpo))
        except (ValueError, KeyError, TypeError, IndexError, AttributeError) as erro:
            self.responder(400, {'erro': str(erro) or 'requisição inválida'})


def iniciar(porta=8000):
    print(f'GAMBITO rodando em http://localhost:{porta}  (Ctrl+C para parar)')
    HTTPServer(('0.0.0.0', porta), Servidor).serve_forever()