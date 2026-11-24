#Gera dados/cartas.json e dados/pacotes.json (rode uma vez; depois edite os JSON à mão)
import json, re, unicodedata

def slug(nome):
    s = unicodedata.normalize('NFD', nome).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '_', s).strip('_')

def b(tipo, **kw):
    d = {'tipo': tipo}; d.update(kw); return d

CARTAS = []
def add(raridade, nome, cat, desc, efeitos=None, quando=None, alvo='nenhum'):
    c = {'id': slug(nome), 'nome': nome, 'raridade': raridade, 'categoria': cat, 'desc': desc,
         'implementado': efeitos is not None, 'efeitos': efeitos or []}
    if cat != 'permanente':
        c['quando'] = quando or 'batalha'; c['alvo'] = alvo
    CARTAS.append(c)

def P(r, nome, desc, *ef): add(r, nome, 'permanente', desc, list(ef))
def C(r, nome, desc, quando, ef, alvo='nenhum'): add(r, nome, 'consumivel', desc, [ef] if isinstance(ef, dict) else ef, quando, alvo)
def R(r, nome, desc, ef): add(r, nome, 'risco', desc, [ef], 'posicionamento')
def X(r, nome, cat, desc): add(r, nome, cat, desc, None, 'batalha' if cat != 'permanente' else None)

esc = lambda **kw: b('escudo_inicial', **kw)
cap = lambda **kw: b('moedas_captura', **kw)

# COMUM
r = 'comum'
P(r, 'Pé de Meia', '+2 moedas no fim de toda vitória.', b('moedas_fim_vitoria', valor=2))
P(r, 'Cambista', 'A troca de ofertas custa 1 moeda a menos, com mínimo de 1.', b('troca_menos', valor=1))
P(r, 'Paciência', 'A penalidade por lentidão cai pela metade.', b('penalidade_fator', valor=0.5))
P(r, 'Infantaria', 'Peões ganham +1 moeda ao capturar.', cap(valor=1, peca='P'))
C(r, 'Muralha', 'Todas as suas peças ganham escudo nesta batalha.', 'batalha', b('escudo_todas', valor=1))
X(r, 'Trocar de Lugar', 'consumivel', 'Troca a posição de duas peças suas durante a batalha.')
P(r, 'Cofrinho', '+1 moeda no fim de toda batalha vencida.', b('moedas_fim_vitoria', valor=1))
P(r, 'Moeda da Sorte', 'Ao entrar em cada loja, você ganha 1 moeda.', b('moedas_entrar_loja', valor=1))
C(r, 'Cupom', 'Sua próxima compra de peça na loja custa 2 moedas a menos.', 'loja', b('cupom', valor=2))
P(r, 'Mão Leve', 'Torres ganham +1 moeda ao capturar.', cap(valor=1, peca='R'))
P(r, 'Olhar de Águia', 'Bispos ganham +1 moeda ao capturar.', cap(valor=1, peca='B'))
P(r, 'Salto Certeiro', 'Cavalos ganham +1 moeda ao capturar.', cap(valor=1, peca='N'))
P(r, 'Guarda Real', 'O rei começa cada batalha com escudo.', esc(sel='tipo', peca='K', valor=1))
P(r, 'Peão Teimoso', 'Um peão aleatório seu começa cada batalha com escudo.', esc(sel='aleatoria', peca='P', valor=1))
X(r, 'Reforço', 'consumivel', 'Adiciona 1 peão comum temporário à sua zona nesta batalha.')
X(r, 'Primeiro Passo', 'consumivel', 'Move uma peça sua 1 casa antes da batalha, sem gastar rodada.')
C(r, 'Calmaria', 'O inimigo perde o próximo turno.', 'batalha', b('inimigo_pula', valor=1))
C(r, 'Espião', 'Marca no tabuleiro as casas que o inimigo pode alcançar nesta batalha.', 'combate', b('mostrar_ameacas'))
P(r, 'Casas Ameaçadas', 'Marca sempre as casas que o inimigo pode alcançar.', b('mostrar_ameacas'))
X(r, 'Contador', 'permanente', 'Mostra durante a batalha quantas moedas de bônus ou penalidade você está a caminho de receber.')
P(r, 'Lista de Compras', 'A loja evita oferecer peças que você já tem no exército.', b('loja_evita_exercito'))
P(r, 'Troca Barata', 'A primeira troca de ofertas de cada loja é grátis.', b('troca_primeira_gratis'))
P(r, 'Estoque', 'A peça misteriosa custa 1 moeda a menos.', b('misteriosa_desconto', valor=1))
P(r, 'Desconto de Rei', 'Variações de rei custam 2 moedas a menos na loja.', b('desconto_tipo', peca='K', valor=2))
P(r, 'Desconto de Peão', 'Variações de peão custam 1 moeda a menos na loja.', b('desconto_tipo', peca='P', valor=1))
P(r, 'Feira de Cavalos', 'Variações de cavalo custam 1 moeda a menos na loja.', b('desconto_tipo', peca='N', valor=1))
P(r, 'Promoção de Torre', 'Variações de torre custam 1 moeda a menos na loja.', b('desconto_tipo', peca='R', valor=1))
P(r, 'Bispos em Oferta', 'Variações de bispo custam 1 moeda a menos na loja.', b('desconto_tipo', peca='B', valor=1))
P(r, 'Coroação', 'Um peão promovido a rainha rende +2 moedas.', b('moedas_promocao', valor=2))
P(r, 'Retaguarda', 'As peças posicionadas nos cantos de trás começam com escudo.', esc(sel='canto', valor=1))
P(r, 'Flanco', 'Peças nas colunas das bordas ganham +1 moeda ao capturar.', cap(valor=1, borda=True))
P(r, 'Centro de Comando', 'As peças posicionadas na coluna central começam com escudo.', esc(sel='centro', valor=1))
C(r, 'Bota de Ferro', 'Uma peça à sua escolha ganha escudo nesta batalha.', 'batalha', b('escudo_alvo', valor=1), 'minha_peca')
C(r, 'Pólvora', 'Uma peça à sua escolha ganha o efeito explosivo nesta batalha.', 'batalha',
  b('efeito_alvo', efeito={'tipo': 'explodir_ao_ser_capturado'}), 'minha_peca')
C(r, 'Bolsa de Moedas', 'Ganha 4 moedas na hora.', 'qualquer', b('ganhar_moedas', valor=4))
C(r, 'Investimento', 'Ganha 2 moedas agora e mais 2 ao entrar na próxima loja.', 'qualquer', b('investimento', agora=2, loja=2))
C(r, 'Reembolso', 'Devolve metade do preço da última compra, arredondada para cima.', 'loja', b('reembolso'))
C(r, 'Remendo', 'Restaura o escudo de uma peça sua.', 'batalha', b('remendo'), 'minha_peca')
C(r, 'Munição', 'Sua próxima captura rende +3 moedas.', 'batalha', b('municao', valor=3))
X(r, 'Desfazer', 'consumivel', 'Desfaz a sua última jogada, sem gastar rodada.')
C(r, 'Respiro', 'As próximas 2 jogadas não contam como rodadas.', 'batalha', b('rodadas_gratis', valor=2))
P(r, 'Cronômetro Lento', 'O limite de rodadas por batalha aumenta em 10.', b('limite_rodadas_mais', valor=10))
P(r, 'Coletor', 'A cada 3 capturas na mesma batalha, +1 moeda.', b('moedas_a_cada_n_capturas', n=3, valor=1))
P(r, 'Sobrevivente', '+1 moeda no fim da batalha se você tiver 6 ou mais peças vivas.', b('moedas_fim_pecas_vivas', min=6, valor=1))
P(r, 'Tabuleiro Grande', '+2 moedas ao vencer em tabuleiro 7×7.', b('moedas_tabuleiro', tamanho=7, valor=2))
P(r, 'Tabuleiro Pequeno', '+2 moedas ao vencer em tabuleiro 5×5.', b('moedas_tabuleiro', tamanho=5, valor=2))
P(r, 'Lado a Lado', '+1 moeda no fim da batalha se nenhum peão seu foi capturado.', b('moedas_sem_perder', peca='P', valor=1))
P(r, 'Primeiro Sangue', '+1 moeda se a sua primeira jogada da batalha for uma captura.', b('moedas_primeira_jogada', valor=1))
P(r, 'Rainha Real', 'Rainhas ganham +1 moeda ao capturar.', cap(valor=1, peca='Q'))
P(r, 'Troca Justa', 'Ao substituir uma peça na loja, você recebe 1 moeda de volta.', b('moedas_ao_substituir', valor=1))

# INCOMUM
r = 'incomum'
P(r, 'Regateio', 'Todas as peças da loja custam 1 moeda a menos.', b('desconto_global', valor=1))
P(r, 'Pilhagem', 'Toda captura rende +1 moeda.', cap(valor=1))
P(r, 'Cavalaria', 'Cavalos começam cada batalha com escudo.', esc(sel='tipo', peca='N', valor=1))
C(r, 'Sabotagem', 'Remove uma peça inimiga aleatória.', 'combate', b('destruir_aleatorias', valor=1))
R(r, 'Sem Rede', 'Sem escudos nesta batalha, nem os seus nem os do inimigo, mas +3 moedas se vencer.', b('risco_sem_escudos', valor=3))
P(r, 'Juros', '+1 moeda a cada 4 moedas guardadas no fim da batalha.', b('juros', por=4, valor=1))
X(r, 'Balcão', 'permanente', 'A peça misteriosa mostra o tipo antes de ser comprada.')
X(r, 'Feira de Raridades', 'permanente', 'As ofertas têm 20% mais chance de serem raras.')
P(r, 'Guilda dos Peões', '+1 moeda no fim da batalha a cada 3 peões vivos.', b('moedas_fim_por_tipo', peca='P', por=3, valor=1))
P(r, 'Cavaleiro Andante', 'Cavalos ganham +2 moedas ao capturar.', cap(valor=2, peca='N'))
P(r, 'Bispo Pregador', 'Bispos ganham +2 moedas ao capturar.', cap(valor=2, peca='B'))
P(r, 'Torre de Marfim', 'Torres começam cada batalha com escudo.', esc(sel='tipo', peca='R', valor=1))
X(r, 'Falange', 'permanente', 'Peões posicionados lado a lado começam com escudo.')
P(r, 'Guarda Pessoal', 'O rei começa cada batalha com 2 escudos.', esc(sel='tipo', peca='K', valor=2))
P(r, 'Dama de Ferro', 'A rainha começa cada batalha com escudo.', esc(sel='tipo', peca='Q', valor=1))
X(r, 'Reforço Duplo', 'consumivel', 'Adiciona 2 peças comuns temporárias à sua zona nesta batalha.')
X(r, 'Emboscada', 'consumivel', 'Posiciona uma peça sua em qualquer casa vazia do tabuleiro.')
C(r, 'Cerco', 'O inimigo não move peões por 3 rodadas.', 'batalha', b('inimigo_sem_tipo', peca='P', valor=3))
C(r, 'Cegueira', 'O inimigo joga aleatoriamente por 3 rodadas.', 'batalha', b('inimigo_aleatorio', valor=3))
P(r, 'Iniciativa Dupla', 'A primeira jogada de cada batalha não conta como rodada.', b('rodadas_gratis_inicio', valor=1))
X(r, 'Escudo Reserva', 'consumivel', 'Duas peças à sua escolha ganham escudo nesta batalha.')
C(r, 'Dinamite', 'Uma peça à sua escolha ganha o efeito explosivo até o fim da run.', 'preparo',
  b('permanente_alvo', efeito={'tipo': 'explodir_ao_ser_capturado'}), 'minha_peca')
C(r, 'Ouro Instantâneo', 'Uma peça à sua escolha ganha o efeito dourado até o fim da run.', 'preparo',
  b('permanente_alvo', efeito={'tipo': 'moedas_fim_batalha', 'valor': 2}), 'minha_peca')
X(r, 'Catálogo', 'permanente', 'A primeira troca de cada loja mostra só peças que você ainda não tem na coleção.')
P(r, 'Colecionador', '+2 moedas ao comprar uma peça nova para a coleção.', b('moedas_peca_nova', valor=2))
X(r, 'Curador', 'permanente', 'A peça misteriosa é sempre nova para a coleção, quando possível.')
P(r, 'Barganha', 'Depois da primeira compra de cada loja, as próximas peças custam 1 moeda a menos.', b('barganha', valor=1))
P(r, 'Compra em Lote', 'Comprar 2 peças na mesma loja rende +2 moedas.', b('compra_lote', valor=2))
P(r, 'Sem Pressa', 'A penalidade por lentidão nunca passa de -2.', b('penalidade_max', valor=2))
P(r, 'Corrida', 'O bônus máximo por velocidade aumenta em +3.', b('bonus_velocidade_max', valor=3))
P(r, 'Saque de Guerra', 'Capturar uma rainha inimiga rende +4 moedas.', cap(valor=4, alvo='Q'))
P(r, 'Caçador de Torres', 'Capturar uma torre inimiga rende +2 moedas.', cap(valor=2, alvo='R'))
P(r, 'Recompensa pela Cabeça', 'Capturar a última peça inimiga rende +3 moedas.', b('moedas_ultima_peca', valor=3))
X(r, 'Predador', 'permanente', 'Capturas em rodadas seguidas rendem +1 moeda na segunda e +2 na terceira.')
P(r, 'Vingança', 'Quando uma peça sua é capturada, você ganha 1 moeda.', b('moedas_peca_perdida', valor=1))
P(r, 'Mártir', 'Peças suas explosivas rendem +2 moedas quando explodem.', b('moedas_explosao', valor=2))
X(r, 'Pavio Curto', 'permanente', 'A explosão de uma peça sua também destrói as peças inimigas vizinhas.')
X(r, 'Campo Minado', 'consumivel', 'Duas casas vazias da zona inimiga viram minas.')
P(r, 'Posição Avançada', 'As peças posicionadas na linha da frente começam com escudo.', esc(sel='frente', valor=1))
X(r, 'Barricada', 'consumivel', 'Bloqueia uma casa vazia do tabuleiro durante esta batalha.')
X(r, 'Troca Proibida', 'consumivel', 'Troca a posição de uma peça sua com a de uma peça inimiga.')
P(r, 'Fortuna', 'Cada vitória tem 25% de chance de dobrar o bônus de velocidade.', b('fortuna', chance=0.25))
P(r, 'Maré de Sorte', 'A troca de ofertas tem 20% de chance de ser grátis.', b('troca_gratis_chance', chance=0.2))
P(r, 'Lotérica', 'Ao entrar na loja, 30% de chance de ganhar 3 moedas.', b('loteria', chance=0.3, valor=3))
X(r, 'Fiador', 'permanente', 'Permite ficar até 3 moedas no vermelho na loja; a dívida é descontada da próxima vitória.')
P(r, 'Largada', 'A recompensa base da primeira batalha de cada run dobra.', b('recompensa_primeira_dobra'))
P(r, 'Maratonista', 'A recompensa aumenta +1 moeda por batalha já vencida na run.', b('recompensa_por_vitoria', valor=1))
X(r, 'Último Fôlego', 'permanente', 'Quando resta só 1 peça sua, ela ganha escudo.')
X(r, 'Sombra', 'consumivel', 'Uma peça sua não pode ser capturada na primeira rodada.')
P(r, 'Balanceamento', 'Se o inimigo começar com mais peças que você, +2 moedas ao vencer.', b('moedas_se_inimigo_maior', valor=2))

# RARO
r = 'rara'
P(r, 'Velocista', 'A média de rodadas esperada diminui em 2, mas o bônus por velocidade dobra.', b('media_menos', valor=2), b('bonus_velocidade_mult', valor=2))
P(r, 'Cofre', 'Cada 5 moedas guardadas rendem +1 moeda extra no fim da batalha.', b('juros', por=5, valor=1))
X(r, 'Olho Clínico', 'permanente', 'A peça misteriosa mostra a raridade antes de ser comprada.')
C(r, 'Segunda Chance', 'Revive a última peça sua capturada, na sua zona.', 'batalha', b('reviver', valor=1))
R(r, 'Desafio Dobrado', 'O inimigo ganha 2 peças, mas a recompensa da batalha dobra.', b('risco_desafio', extra=2, mult=2, escudos=False))
P(r, 'Fábrica de Moedas', '+3 moedas no fim de toda vitória.', b('moedas_fim_vitoria', valor=3))
P(r, 'Banqueiro', '+1 moeda a cada 3 moedas guardadas no fim da batalha, até 5 moedas.', b('juros', por=3, valor=1, max=5))
P(r, 'Monopólio', 'Toda peça comprada custa 2 moedas a menos, com mínimo de 1.', b('desconto_global', valor=2))
X(r, 'Leilão', 'permanente', 'Ao entrar na loja, uma das ofertas já vem 50% mais barata.')
P(r, 'Armazém', 'O custo da troca de ofertas nunca passa de 4 moedas.', b('troca_max', valor=4))
X(r, 'Reabastecimento', 'permanente', 'Toda troca de ofertas garante pelo menos uma peça rara.')
P(r, 'Mão de Midas', 'Peças douradas rendem +2 moedas extras no fim da batalha.', b('moedas_extra_fim_efeito', valor=2))
P(r, 'Saqueador de Elite', 'Peças mercenárias rendem +1 moeda extra ao capturar.', b('moedas_extra_mercenario', valor=1))
P(r, 'Aço Inquebrável', 'Todo escudo inicial seu absorve 1 captura a mais.', b('escudo_extra', valor=1))
P(r, 'Cavalaria Pesada', 'Cavalos começam com escudo e ganham +1 moeda ao capturar.', esc(sel='tipo', peca='N', valor=1), cap(valor=1, peca='N'))
P(r, 'Mestre Bispo', 'Bispos começam com escudo e ganham +1 moeda ao capturar.', esc(sel='tipo', peca='B', valor=1), cap(valor=1, peca='B'))
P(r, 'Fortaleza', 'Torres começam cada batalha com 2 escudos.', esc(sel='tipo', peca='R', valor=2))
P(r, 'Coroa', 'Rainhas começam com escudo e ganham +2 moedas ao capturar.', esc(sel='tipo', peca='Q', valor=1), cap(valor=2, peca='Q'))
P(r, 'Rei Guerreiro', 'O rei começa com escudo e ganha +2 moedas ao capturar.', esc(sel='tipo', peca='K', valor=1), cap(valor=2, peca='K'))
P(r, 'Regimento', 'Se você tiver 4 ou mais peões, todos começam com escudo.', esc(sel='tipo', peca='P', valor=1, min=4))
P(r, 'Infantaria de Ouro', 'Peões ganham o efeito dourado (+2 moedas no fim da batalha).', b('efeito_para_tipo', peca='P', efeito={'tipo': 'moedas_fim_batalha', 'valor': 2}))
X(r, 'Chuva de Fogo', 'permanente', 'A cada 3 capturas, uma peça inimiga aleatória é destruída.')
X(r, 'Reação em Cadeia', 'permanente', 'Quando uma peça sua explode, as peças vizinhas também são destruídas.')
X(r, 'Detonador', 'consumivel', 'Explode uma peça sua à escolha, destruindo as peças inimigas vizinhas.')
C(r, 'Bombardeio', 'Destrói 2 peças inimigas aleatórias.', 'combate', b('destruir_aleatorias', valor=2))
C(r, 'Raio', 'Destrói a peça inimiga de maior valor.', 'combate', b('destruir_maior'))
C(r, 'Congelamento', 'O inimigo perde 2 turnos.', 'batalha', b('inimigo_pula', valor=2))
C(r, 'Terremoto', 'Embaralha a posição de todas as peças inimigas.', 'combate', b('embaralhar_inimigas'))
X(r, 'Teleporte', 'consumivel', 'Move uma peça sua para qualquer casa vazia do tabuleiro.')
C(r, 'Peão Sagrado', 'Promove um peão seu a rainha na hora.', 'batalha', b('promover_alvo'), 'minha_peca')
X(r, 'Cavalo de Troia', 'consumivel', 'Um peão seu não é atacado pelo inimigo por 3 rodadas.')
C(r, 'Ressurreição', 'Revive 2 peças suas capturadas.', 'batalha', b('reviver', valor=2))
X(r, 'Reforços de Elite', 'consumivel', 'Adiciona 1 cavalo e 1 bispo comuns temporários à sua zona.')
P(r, 'Contra-Ataque', 'Quando uma peça sua é capturada, há 30% de chance de destruir o atacante.', b('contra_ataque', chance=0.3))
X(r, 'Sorte do Jogador', 'permanente', '15% de chance de uma captura inimiga ser absorvida, como se houvesse escudo.')
P(r, 'Escudo Coletivo', 'No início de cada batalha, uma peça sua aleatória ganha escudo.', esc(sel='aleatoria', valor=1))
P(r, 'Mestre do Tabuleiro', 'Sua zona de posicionamento ganha uma linha extra.', b('zona_extra', valor=1))
P(r, 'Redução', 'O inimigo começa cada batalha com 1 peça a menos.', b('inimigo_menos', valor=1))
P(r, 'Fraqueza', 'Peças inimigas não podem ter escudo.', b('sem_escudo_inimigo'))
P(r, 'Atrasar', 'O inimigo perde o primeiro turno de cada batalha.', b('inimigo_pula_inicio', valor=1))
P(r, 'Pressa Calculada', 'Vencer em menos da metade da média de rodadas rende +6 moedas.', b('moedas_rapido_metade', valor=6))
P(r, 'Placar', '+1 moeda por cada rodada abaixo da média, sem limite.', b('bonus_sem_limite'))
P(r, 'Prêmio de Resistência', 'Não há penalidade por lentidão, mas o bônus máximo por velocidade cai para +2.', b('sem_penalidade'), b('bonus_max_fixo', valor=2))
P(r, 'Colecionador Voraz', '+3 moedas ao comprar uma peça nova para a coleção.', b('moedas_peca_nova', valor=3))
X(r, 'Descobridor', 'permanente', 'A peça misteriosa custa 2 moedas e nunca repete peças que você já tem na coleção.')
P(r, 'Mochila', '+1 espaço de carta permanente.', b('espaco_cartas', valor=1))
X(r, 'Alquimista', 'consumivel', 'Transforma uma peça sua em outra peça aleatória do mesmo tipo, com efeito.')
C(r, 'Forja', 'Uma peça à sua escolha ganha escudo até o fim da run.', 'preparo',
  b('permanente_alvo', efeito={'tipo': 'escudo', 'valor': 1}), 'minha_peca')
R(r, 'Contrato', 'Se você vencer esta batalha com todas as peças vivas, +10 moedas.', b('risco_contrato', ganho=10))
R(r, 'Aposta', 'Aposta 5 moedas; se vencer abaixo da média de rodadas, recebe 15.', b('risco_aposta', custo=5, ganho=15))

# ÉPICO
r = 'epica'
P(r, 'Vitrine', 'A loja mostra uma oferta de peça a mais.', b('ofertas_extra', valor=1))
X(r, 'Jogada Dupla', 'consumivel', 'Você move duas vezes neste turno.')
P(r, 'Rei Midas', 'A recompensa total de cada vitória rende 50% a mais.', b('recompensa_mult', valor=1.5))
P(r, 'Cornucópia', '+5 moedas no fim de toda vitória.', b('moedas_fim_vitoria', valor=5))
P(r, 'Banco Central', '+1 moeda a cada 2 moedas guardadas no fim da batalha, até 8 moedas.', b('juros', por=2, valor=1, max=8))
P(r, 'Trilha Dourada', 'A recompensa aumenta +2 moedas por batalha já vencida na run.', b('recompensa_por_vitoria', valor=2))
P(r, 'Cartel', 'A segunda compra de peça de cada loja é grátis.', b('segunda_compra_gratis'))
P(r, 'Grande Vitrine', 'A loja mostra 2 ofertas de peça a mais.', b('ofertas_extra', valor=2))
X(r, 'Mercado Negro', 'permanente', 'Toda loja garante pelo menos uma peça de raridade épica.')
X(r, 'Misteriosa Dupla', 'permanente', 'A loja traz 2 peças misteriosas.')
P(r, 'Troca Eterna', 'A troca de ofertas custa sempre 1 moeda.', b('troca_fixo', valor=1))
X(r, 'Imortal', 'permanente', 'A primeira peça sua capturada em cada batalha volta ao tabuleiro na posição inicial.')
P(r, 'Exército Sagrado', 'Todas as suas peças começam cada batalha com escudo.', esc(sel='todas', valor=1))
P(r, 'Armadura Real', 'Rainha e rei começam cada batalha com 2 escudos.', esc(sel='tipo', peca='Q', valor=2), esc(sel='tipo', peca='K', valor=2))
X(r, 'Legião', 'permanente', 'O exército passa a ter 1 peça a mais.')
X(r, 'Frenesi Geral', 'permanente', 'Toda peça sua mercenária joga de novo após capturar.')
X(r, 'Blitz', 'consumivel', 'Você joga 3 vezes seguidas neste turno.')
C(r, 'Tempo Parado', 'O inimigo perde 4 turnos.', 'batalha', b('inimigo_pula', valor=4))
X(r, 'Reinício', 'consumivel', 'Refaz o posicionamento das suas peças no meio da batalha.')
C(r, 'Chuva de Meteoros', 'Destrói 4 peças inimigas aleatórias.', 'combate', b('destruir_aleatorias', valor=4))
C(r, 'Apocalipse', 'Destrói todos os peões inimigos.', 'combate', b('destruir_tipo', peca='P'))
C(r, 'Cataclismo', 'Destrói metade das peças inimigas, arredondada para cima.', 'combate', b('destruir_metade'))
X(r, 'Fantasma', 'consumivel', 'Uma peça sua atravessa outras peças por 3 rodadas.')
C(r, 'Promoção em Massa', '2 peões seus viram rainhas na hora.', 'batalha', b('promover_peoes', valor=2))
X(r, 'Clone', 'consumivel', 'Cria uma cópia temporária de uma peça sua nesta batalha.')
C(r, 'Ressurreição Plena', 'Revive todas as peças suas capturadas.', 'batalha', b('reviver', valor=99))
C(r, 'Contra-Feitiço', 'Remove todos os escudos das peças inimigas.', 'combate', b('remover_escudos_inimigos'))
P(r, 'Trono', 'Rainhas começam com 2 escudos e ganham +3 moedas ao capturar.', esc(sel='tipo', peca='Q', valor=2), cap(valor=3, peca='Q'))
P(r, 'Cavalaria Imperial', 'Cavalos começam com escudo, ganham +2 moedas ao capturar e explosão ao capturar.',
  esc(sel='tipo', peca='N', valor=1), cap(valor=2, peca='N'), b('efeito_para_tipo', peca='N', efeito={'tipo': 'explosao_ao_capturar'}))
P(r, 'Inquisição', 'Bispos ganham explosão ao capturar.', b('efeito_para_tipo', peca='B', efeito={'tipo': 'explosao_ao_capturar'}))
P(r, 'Cidadela', 'Torres começam com 2 escudos e ganham +2 moedas ao capturar.', esc(sel='tipo', peca='R', valor=2), cap(valor=2, peca='R'))
P(r, 'Falange de Ouro', 'Peões começam com escudo e ganham o efeito dourado.',
  esc(sel='tipo', peca='P', valor=1), b('efeito_para_tipo', peca='P', efeito={'tipo': 'moedas_fim_batalha', 'valor': 2}))
P(r, 'Pelotão Suicida', 'Todos os peões ganham o efeito explosivo.', b('efeito_para_tipo', peca='P', efeito={'tipo': 'explodir_ao_ser_capturado'}))
X(r, 'Tempestade de Fogo', 'permanente', 'A explosão ao capturar atinge peças até 2 casas de distância.')
X(r, 'Campeão', 'permanente', 'Uma peça sua aleatória, a cada batalha, ganha escudo, mercenário, explosivo e dourado.')
X(r, 'Aliança', 'permanente', 'Se 2 ou mais peças suas tiverem o mesmo efeito, todas elas ganham +1 moeda ao capturar.')
P(r, 'Arsenal', 'Cada explosão de peça sua rende +3 moedas.', b('moedas_explosao', valor=3))
P(r, 'Coleção Completa', '+1 moeda a cada 5 peças da coleção, no fim de cada batalha.', b('moedas_colecao', por=5, valor=1))
X(r, 'Herança', 'permanente', 'Você começa toda run com +10 moedas.')
X(r, 'Segunda Chance Real', 'permanente', 'Uma vez por run, uma derrota refaz a batalha do começo.')
P(r, 'Tempo é Ouro', 'Sem limite de rodadas, e a média esperada aumenta em 5.', b('sem_limite_rodadas'), b('media_mais', valor=5))
P(r, 'Estrategista Supremo', 'Sua zona de posicionamento ganha 2 linhas extras.', b('zona_extra', valor=2))
P(r, 'Desarme', 'O inimigo começa cada batalha com 2 peças a menos.', b('inimigo_menos', valor=2))
P(r, 'Cegueira Permanente', 'O inimigo joga aleatoriamente nas 3 primeiras rodadas de cada batalha.', b('inimigo_aleatorio_inicio', valor=3))
P(r, 'Aura Sagrada', 'Toda peça sua com escudo ativo ganha +1 moeda ao capturar.', cap(valor=1, com_escudo=True))
P(r, 'Colheita', 'Toda captura rende +2 moedas.', cap(valor=2))
R(r, 'Desafio Supremo', 'O inimigo ganha 3 peças com escudo, mas a recompensa triplica.', b('risco_desafio', extra=3, mult=3, escudos=True))
R(r, 'Pacto Sombrio', 'Uma peça aleatória do exército vira peão comum, e você ganha 20 moedas.', b('risco_pacto', moedas=20))
R(r, 'Tudo ou Nada', 'Vencer sem perder peças rende +25 moedas; vencer perdendo peças custa 10.', b('risco_tudo_ou_nada', ganho=25, perda=10))
X(r, 'Fusão', 'consumivel', 'Funde 2 peças suas em 1 peça de tipo superior, por exemplo 2 peões viram um cavalo.')

# LENDÁRIO
r = 'lendaria'
P(r, 'Olimpo de Ouro', '+8 moedas no fim de toda vitória.', b('moedas_fim_vitoria', valor=8))
P(r, 'Cofre Infinito', '+1 moeda a cada 2 moedas guardadas no fim da batalha, até 15 moedas.', b('juros', por=2, valor=1, max=15))
P(r, 'Toque de Midas', 'A recompensa total de cada vitória dobra.', b('recompensa_mult', valor=2))
P(r, 'Exército Imortal', 'Todas as suas peças começam cada batalha com 2 escudos.', esc(sel='todas', valor=2))
P(r, 'Rainha Suprema', 'Rainhas começam com 3 escudos e ganham +5 moedas ao capturar.', esc(sel='tipo', peca='Q', valor=3), cap(valor=5, peca='Q'))
P(r, 'Cavalaria Lendária', 'Cavalos começam com 2 escudos, ganham +4 moedas ao capturar e explosão ao capturar.',
  esc(sel='tipo', peca='N', valor=2), cap(valor=4, peca='N'), b('efeito_para_tipo', peca='N', efeito={'tipo': 'explosao_ao_capturar'}))
P(r, 'Bispo Divino', 'Bispos começam com 2 escudos, ganham +3 moedas ao capturar e explosão ao capturar.',
  esc(sel='tipo', peca='B', valor=2), cap(valor=3, peca='B'), b('efeito_para_tipo', peca='B', efeito={'tipo': 'explosao_ao_capturar'}))
P(r, 'Torre Eterna', 'Torres começam com 3 escudos e ganham +3 moedas ao capturar.', esc(sel='tipo', peca='R', valor=3), cap(valor=3, peca='R'))
P(r, 'Rei Imortal', 'O rei começa com 4 escudos e ganha +4 moedas ao capturar.', esc(sel='tipo', peca='K', valor=4), cap(valor=4, peca='K'))
P(r, 'Peões de Ouro', 'Peões começam com escudo e ganham o efeito dourado (+3 moedas no fim da batalha).',
  esc(sel='tipo', peca='P', valor=1), b('efeito_para_tipo', peca='P', efeito={'tipo': 'moedas_fim_batalha', 'valor': 3}))
C(r, 'Mate Perfeito', 'Destrói todas as peças inimigas.', 'combate', b('destruir_metade', todas=True))
C(r, 'Eclipse', 'O inimigo perde 8 turnos.', 'batalha', b('inimigo_pula', valor=8))
C(r, 'Ressurgimento', 'Revive todas as peças suas capturadas e dá escudo a todas.', 'batalha', [b('reviver', valor=99), b('escudo_todas', valor=1)])
P(r, 'Loja Infinita', 'A loja mostra 3 ofertas de peça a mais e a troca custa sempre 1 moeda.', b('ofertas_extra', valor=3), b('troca_fixo', valor=1))
P(r, 'Mercado do Rei', 'Todas as peças da loja custam 3 moedas a menos, com mínimo de 1.', b('desconto_global', valor=3))
P(r, 'Tempo Suspenso', 'Sem limite de rodadas, e as 3 primeiras jogadas de cada batalha não contam.', b('sem_limite_rodadas'), b('rodadas_gratis_inicio', valor=3))
P(r, 'Gambito da Rainha', 'Um peão promovido a rainha rende +6 moedas.', b('moedas_promocao', valor=6))
P(r, 'Visão Total', 'Marca as casas que o inimigo pode alcançar, e ele começa com 3 peças a menos.', b('mostrar_ameacas'), b('inimigo_menos', valor=3))
P(r, 'Domínio do Tabuleiro', 'Sua zona ganha 2 linhas extras e o inimigo começa com 2 peças a menos.', b('zona_extra', valor=2), b('inimigo_menos', valor=2))
C(r, 'Bênção de Caíssa', 'Ganha 30 moedas na hora.', 'qualquer', b('ganhar_moedas', valor=30))

assert len({c['id'] for c in CARTAS}) == len(CARTAS), 'ids duplicados'

def linhas(lst): return ',\n    '.join(json.dumps(x, ensure_ascii=False) for x in lst)
open('dados/cartas.json', 'w', encoding='utf-8').write('{\n  "cartas": [\n    ' + linhas(CARTAS) + '\n  ]\n}\n')

PACOTES = {
 "pacote_inicial": ("Pacote Inicial", 0, [100, 0, 0, 0, 0], False),
 "bau_do_rei": ("Baú do Rei", 4, [70, 20, 8, 1.8, 0.2], True),
 "expresso_hikaru": ("Expresso Hikaru", 5, [60, 25, 11, 3.5, 0.5], True),
 "pacote_zugzwang": ("Pacote Zugzwang", 6, [50, 28, 15, 6, 1], True),
 "registros_de_philidor": ("Registros de Philidor", 7, [42, 30, 18, 8, 2], True),
 "pacote_capablanca": ("Pacote Capablanca", 8, [35, 30, 22, 10, 3], True),
 "ataque_sovietico": ("Ataque Soviético", 9, [28, 30, 24, 13, 5], True),
 "sacrificio_de_tal": ("Sacrifício de Tal", 10, [20, 28, 27, 17, 8], True),
 "bencao_de_caissa": ("Bênção de Caíssa", 12, [15, 25, 28, 20, 12], True),
 "lembrancas_de_kasparov": ("Lembranças de Kasparov", 14, [10, 22, 28, 24, 16], True),
 "segredo_de_carlsen": ("Segredo de Carlsen", 17, [5, 15, 25, 30, 25], True),
 "pacote_imortal": ("Pacote Imortal", 20, [0, 10, 20, 30, 40], True),
}
R5 = ['comum', 'incomum', 'rara', 'epica', 'lendaria']
out = {}
for k, (nome, preco, probs, loja) in PACOTES.items():
    assert abs(sum(probs) - 100) < 1e-9, k
    out[k] = {"nome": nome, "preco": preco, "opcoes": 3, "loja": loja, "probabilidades": dict(zip(R5, probs))}
open('dados/pacotes.json', 'w', encoding='utf-8').write('{\n  ' + ',\n  '.join(f'{json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}' for k, v in out.items()) + '\n}\n')
from collections import Counter
print(Counter((c['raridade'], c['implementado']) for c in CARTAS))