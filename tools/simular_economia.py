import os, sys, random, collections, statistics, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  #a pasta do projeto (uma acima de tools)
import colecao, dados, estado, run, loja, pacotes, cartas, xadrez
colecao.definir(None)
random.seed(int(sys.argv[2]) if len(sys.argv)>2 else 1)
POLITICA=sys.argv[1] if len(sys.argv)>1 else 'aleatorio'
N=int(sys.argv[3]) if len(sys.argv)>3 else 200
MAXB=30

def valor(id_):
    p=dados.CATALOGO[id_]; return p['preco']
def jogar():
    t=0
    while estado.run['tela']=='batalha' and t<200:
        t+=1
        b=estado.run['batalha']
        if b['vez']=='inimigo': run.vez_do_inimigo(); continue
        ameaca={tuple(a) for a in xadrez.casas_ameacadas(b)} if True else set()
        ini={(p['linha'],p['col']) for p in b['pecas'] if p['lado']=='i'}
        caps=[];seguras=[];todas=[]
        for p in b['pecas']:
            if p['lado']!='j': continue
            for m in xadrez.movimentos(b['pecas'],p,b['n']):
                x=((p['linha'],p['col']),m); todas.append(x)
                if tuple(m) in ini: caps.append(x)
                elif tuple(m) not in ameaca: seguras.append(x)
        esc=caps or seguras or todas
        if not esc: break
        de,para=random.choice(esc)
        run.jogada_do_jogador(list(de),list(para))
def tem_moeda(id_):
    return any('moeda' in e['tipo'] for e in dados.CATALOGO[id_]['efeitos'])
def escolher_carta():
    r=estado.run
    cheio=len(r['cartas'])>=cartas.espacos()
    try: pacotes.escolher(random.randrange(len(r['pacote']['opcoes'])), 0 if cheio else None)
    except ValueError: pacotes.pular()  #consumíveis cheios: o robô desiste da carta


def comprar_tudo():
    r=estado.run; lj=r['loja']; comp=[]
    for _ in range(12):
        feito=False
        cand=[]
        for i,k in enumerate(lj['ofertas']):
            if lj['vendidas'][i]: continue
            pr=cartas.preco_da_peca(k)
            if pr<=r['moedas']: cand.append((i,k,pr))
        if POLITICA=='moeda': cand.sort(key=lambda x:(not tem_moeda(x[1]),-x[2]))
        elif POLITICA=='caro': cand.sort(key=lambda x:-x[2])
        else: random.shuffle(cand)
        for i,k,pr in cand:
            fraco=min(range(len(r['exercito'])),key=lambda j:valor(r['exercito'][j]))
            if valor(k)<=valor(r['exercito'][fraco]) and r['exercito'][fraco]!='P:comum': continue
            loja.comprar(i,fraco); comp.append(k); feito=True; break
        if not feito: break
    # pacotes
    for i,pid in enumerate(lj['pacotes']):
        if lj['pacotes_vendidos'][i]: continue
        if r['moedas']>=dados.PACOTES[pid]['preco'] and r['moedas']-dados.PACOTES[pid]['preco']>=3 and r['pacote'] is None:
            loja.comprar_pacote(i)
            op=r['pacote']['opcoes']
            escolher_carta()
    return comp
def escolher_ok():
    pass
dados_b=collections.defaultdict(lambda: {'n':0,'rec':[],'ent':[],'sai':[]})
compradas=collections.Counter(); fim=[]
for runn in range(N):
    run.novo_jogo()
    # pacote inicial: escolhe aleatório
    r=estado.run
    try:
        op=r['pacote']['opcoes']; j=random.randrange(len(op))
        c=dados.CARTAS[op[j]]
        pacotes.escolher(j, None)
    except Exception as e: r['pacote']=None
    while True:
        r=estado.run
        if r['tela']=='posicionamento':
            run.autoposicionar(); run.iniciar_batalha()
        jogar()
        r=estado.run
        if r['tela']=='derrota': fim.append(r['num']-1); break
        if r['tela']!='loja': fim.append(r['num']-1); break
        d=dados_b[r['num']]; d['n']+=1; d['rec'].append(r['relatorio']['total']+r['relatorio'].get('loja',0)); d['ent'].append(r['moedas'])
        if r['pacote'] is not None:
            try: pacotes.escolher(0, 0)
            except Exception: pacotes.pular()
        try: comp=comprar_tudo()
        except Exception as e:
            import traceback; traceback.print_exc(); break
        for k in comp: compradas[k]+=1
        if estado.run['pacote'] is not None:
            try: pacotes.escolher(0,0 if len(estado.run['cartas'])>=cartas.espacos() else None)
            except Exception: pacotes.pular()
        d['sai'].append(estado.run['moedas'])
        if r['num']>=MAXB: fim.append(r['num']); break
        run.proxima_batalha()
print('POLITICA',POLITICA,'runs',N)
print('batalha | runs vivas | recompensa média | moedas ao entrar na loja | moedas ao sair (sobra)')
for n in sorted(dados_b):
    d=dados_b[n]
    if d['n']<5: continue
    print('%7d | %10d | %16.1f | %24.1f | %.1f'%(n,d['n'],statistics.mean(d['rec']),statistics.mean(d['ent']),statistics.mean(d['sai'])))
print('batalhas vencidas por run: média %.1f mediana %s'%(statistics.mean(fim),statistics.median(fim)))
print('top 12 peças compradas:',[(k,v) for k,v in compradas.most_common(12)])
print('total de compras:',sum(compradas.values()),'| com efeito de moeda: %.0f%%'%(100*sum(v for k,v in compradas.items() if tem_moeda(k))/max(1,sum(compradas.values()))))