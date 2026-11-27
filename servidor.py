#Servidor web: recebe os cliques do navegador e devolve o estado do jogo. Não guarda nada: a run e a coleção viajam com cada pedido
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import cartas
import colecao
import consumiveis
import dados
import duelo
import estado
import loja
import pacotes
import run
import xadrez

TIPOS = {'.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript', '.wav': 'audio/wav',
         '.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.png': 'image/png', '.ico': 'image/x-icon', '.svg': 'image/svg+xml'}
TRAVA = threading.Lock()  # uma requisição por vez mexe no estado


def _info_estagio(num):
    e = dados.estagio(num)
    return {'nome': e['nome'], 'media': e['media'], 'chefe': e['chefe_agora'], 'nivel': e['nivel']}


def estado_para_o_navegador():
    s = {'tela': 'menu', 'catalogo': dados.CATALOGO, 'efeitos': dados.EFEITOS, 'config': dados.CONFIG,
         'loja_chaves': dados.CHAVES_LOJA, 'colecao': colecao.dados_colecao,
         'cartas_catalogo': dados.CARTAS, 'pacotes': dados.PACOTES, 'raridades': dados.NOMES_RARIDADE,
         'ordem_raridades': dados.RARIDADES, 'niveis_ia': run.niveis_da_maquina()}
    if estado.duelo is not None:  #duelo em andamento: a tela é a do duelo
        s.update({'tela': 'duelo', 'duelo': duelo.visao()})
        return s
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
        s['venda'] = {'pecas': [loja.valor_da_peca(k) for k in r['exercito']],
                      'cartas': [loja.valor_da_carta(k) for k in r['cartas']],
                      'consumiveis': [loja.valor_da_carta(k) for k in r['consumiveis']]}
    b = r['batalha']
    if b and r['tela'] in ('posicionamento', 'batalha', 'loja', 'derrota'):  # loja e derrota: o tabuleiro final aparece na transição
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
        ameacas = xadrez.casas_ameacadas(b) if (b['ameacas'] or b.get('modo_teste')) and b['fase'] == 'jogando' else []
        limite = cartas.limite_de_rodadas()
        s['batalha'] = {'n': b['n'], 'pecas': pecas, 'posicoes': b['posicoes'], 'rodadas': b['rodadas'],
                        'log': b['log'][-12:], 'jogadas': jogadas, 'zona_inicio': b['zona_inicio'],
                        'ameacas': ameacas, 'limite': limite, 'fase': b['fase'], 'vez': b['vez'], 'aviso': b.get('aviso', '')}
        if b.get('modo_teste'):
            s['teste'] = {'bonus': b['bonus'], 'serie': b.get('serie', 0), 'turnos': b['turnos'],
                          'parado': bool(b.get('inimigo_parado')), 'nivel': b.get('nivel_teste', '')}
    return s


def executar_duelo(acao, d):
    if acao == 'duelo_novo':
        duelo.novo(bool(d.get('maquina')), int(d.get('nivel', 1)))
        duelo.rodar_bot()
        return
    if estado.duelo is None:
        raise ValueError('Não há duelo em andamento')
    if acao == 'duelo_sair':
        duelo.sair()
    elif acao == 'duelo_avancar':
        duelo.avancar()
    elif acao == 'duelo_banir':
        duelo.banir(str(d['id']))
    elif acao == 'duelo_fim_bans':
        duelo.fim_bans()
    elif acao == 'duelo_escolher':
        duelo.escolher(str(d['id']))
    elif acao == 'duelo_parar':
        duelo.parar()
    elif acao == 'duelo_colocar':
        duelo.colocar(int(d['indice']), int(d['linha']), int(d['col']))
    elif acao == 'duelo_tirar':
        duelo.tirar(int(d['indice']))
    elif acao == 'duelo_auto':
        duelo.auto()
    elif acao == 'duelo_pronto':
        duelo.pronto()
    elif acao == 'duelo_mover':
        duelo.mover(list(map(int, d['de'])), list(map(int, d['para'])))
    elif acao == 'duelo_proxima':
        duelo.proxima()
    else:
        raise ValueError('Ação desconhecida')
    if estado.duelo is not None:
        duelo.rodar_bot()  #se for contra a máquina, ela joga até chegar a vez da pessoa


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
    elif acao == 'vender_peca':
        loja.vender_peca(int(d['indice']))
    elif acao == 'vender_carta':
        loja.vender_carta(bool(d.get('consumivel')), int(d['indice']))
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
    elif acao.startswith('duelo_'):
        executar_duelo(acao, d)
    elif acao == 'teste_montar':
        run.montar_teste(d)
    elif acao == 'teste_parado':
        run.teste_parado(bool(d.get('valor')))
    elif acao == 'teste_avancar':
        run.teste_avancar(int(d.get('n', 1)))
    elif acao == 'proxima':
        if estado.run['pacote'] is not None:
            raise ValueError('Escolha uma carta do pacote aberto primeiro.')
        run.proxima_batalha()
    elif acao != 'estado':
        raise ValueError('Ação desconhecida')


def processar(corpo):
    #Recebe {acao, dados, run, colecao, duelo} do navegador, executa a ação e devolve o novo estado
    run_recebida = corpo.get('run')
    if run_recebida is not None and not isinstance(run_recebida, dict):
        raise ValueError('partida salva inválida')
    acao = str(corpo.get('acao') or 'estado')
    with TRAVA:
        estado.duelo = duelo.sanear(corpo.get('duelo'))
        em_duelo = estado.duelo is not None or acao == 'duelo_novo'
        estado.run = None if em_duelo else run_recebida  #durante o duelo a run (se houver) fica guardada e não participa
        if estado.run is not None:
            run.sanear_partida()
        colecao.definir(corpo.get('colecao'))
        executar(acao, corpo.get('dados') or {})
        if estado.duelo is None and em_duelo:  #saiu do duelo: volta a run guardada
            estado.run = run_recebida
            if estado.run is not None:
                run.sanear_partida()
        s = estado_para_o_navegador()
        s['_run'] = run_recebida if estado.duelo is not None else estado.run  # o navegador guarda isto e manda de volta no próximo pedido
        s['_duelo'] = estado.duelo
        return s


def tratar_pedido(texto):
    #Recebe o corpo (texto JSON) de um POST e devolve (código HTTP, resposta). Usado pelo servidor local e pela Vercel
    try:
        if len(texto) > 2_000_000:
            raise ValueError('pedido grande demais')
        corpo = json.loads(texto or b'{}')
        if not isinstance(corpo, dict):
            raise ValueError('requisição inválida')
        return 200, processar(corpo)
    except (ValueError, KeyError, TypeError, IndexError, AttributeError) as erro:
        return 400, {'erro': str(erro) or 'requisição inválida'}


class Servidor(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # silencia o log do terminal

    def responder(self, codigo, conteudo, tipo='application/json'):
        if not isinstance(conteudo, bytes):
            conteudo = json.dumps(conteudo, ensure_ascii=False).encode('utf-8')
        self.send_response(codigo)
        self.send_header('Content-Type', tipo + ('; charset=utf-8' if tipo.startswith(('text/', 'application/')) else ''))
        self.end_headers()
        self.wfile.write(conteudo)

    def do_GET(self):
        #serve qualquer arquivo da pasta public/ (html, css, js, sons...)
        pasta = os.path.realpath(os.path.join(dados.PASTA, 'public'))
        pedido = self.path.split('?')[0].lstrip('/') or 'index.html'
        caminho = os.path.realpath(os.path.join(pasta, pedido))
        if not caminho.startswith(pasta + os.sep) or not os.path.isfile(caminho):
            return self.responder(404, {'erro': 'arquivo não encontrado'})
        tipo = TIPOS.get(os.path.splitext(caminho)[1].lower(), 'application/octet-stream')
        with open(caminho, 'rb') as f:
            self.responder(200, f.read(), tipo)

    def do_POST(self):
        tamanho = int(self.headers.get('Content-Length') or 0)
        codigo, resposta = tratar_pedido(self.rfile.read(tamanho))
        self.responder(codigo, resposta)


def iniciar(porta=8000):
    print(f'GAMBITO rodando em http://localhost:{porta}  (Ctrl+C para parar)')
    HTTPServer(('0.0.0.0', porta), Servidor).serve_forever()