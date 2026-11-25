#Testa todas as cartas implementadas: dá a carta ao jogador e joga algumas batalhas com ela
import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import colecao
import cartas, consumiveis, dados, estado, run, loja, pacotes, servidor

def jogar(max_turnos=60):
    b = estado.run['batalha']
    while estado.run['tela'] == 'batalha' and max_turnos:
        max_turnos -= 1
        if estado.run['batalha']['vez'] == 'inimigo':  #o inimigo joga primeiro
            run.vez_do_inimigo(); continue
        s = servidor.estado_para_o_navegador()['batalha']
        js = s['jogadas']; ini = {(p['linha'], p['col']) for p in s['pecas'] if p['lado'] == 'i'}
        o = [(k, t) for k, ts in js.items() for t in ts]
        c = [x for x in o if tuple(x[1]) in ini] or o
        k, t = random.choice(c)
        estado.run = json.loads(json.dumps(estado.run))  # como no site: o estado viaja pelo navegador
        run.jogada_do_jogador(list(map(int, k.split(','))), t)
        if estado.run['tela'] == 'batalha':
            estado.run = json.loads(json.dumps(estado.run))
            run.vez_do_inimigo()

erros = []
for cid, c in dados.CARTAS.items():
    if not c['implementado']:
        continue
    for tentativa in range(3):
        try:
            run.novo_jogo(); estado.run['pacote'] = None
            estado.run['moedas'] = 50
            if c['categoria'] == 'permanente':
                estado.run['cartas'].append(cid)
            else:
                estado.run['consumiveis'].append(cid)
            run.preparar_batalha(); run.autoposicionar()
            if c['categoria'] == 'risco' or c['quando'] in ('posicionamento', 'combate', 'preparo', 'qualquer'):
                consumiveis.usar(0, 0 if c['alvo'] == 'minha_peca' else None)
            run.iniciar_batalha()
            if c['categoria'] == 'consumivel' and estado.run['consumiveis']:
                alvo = None
                if c['alvo'] == 'minha_peca':
                    pecas = [p for p in estado.run['batalha']['pecas'] if p['lado'] == 'j']
                    if c['efeitos'][0]['tipo'] == 'promover_alvo':
                        pecas = [p for p in pecas if p['tipo'] == 'P'] or pecas
                    alvo = pecas[0]['indice']
                try:
                    consumiveis.usar(0, alvo)
                except ValueError as e:
                    pass  # ex.: 'revive' sem peças capturadas ainda é um erro válido
            jogar()
            if estado.run['tela'] == 'loja':  # testa entrar na loja com a carta
                servidor.estado_para_o_navegador()
        except Exception as e:
            import traceback; erros.append((cid, repr(e), traceback.format_exc().splitlines()[-3]))
            break
print('cartas testadas:', sum(1 for c in dados.CARTAS.values() if c['implementado']), '| erros:', len(erros))
for e in erros[:15]: print(e)