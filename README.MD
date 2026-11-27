# GAMBITO

Gambito é um roguelike de xadrez inspirado em Balatro. O jogador monta um pequeno exército, vence batalhas em tabuleiros pequenos, ganha moedas e melhora peças e cartas na loja. A run é infinita: só termina quando o jogador perde, e o objetivo é vencer o maior número de batalhas possível.

**Versão online:** [gambitochesss.vercel.app](https://gambitochesss.vercel.app)

O jogo funciona no computador e no celular, e tem efeitos sonoros (o botão de som fica no canto da tela).

## Sobre o projeto

A ideia une a estratégia do xadrez com a construção de combinações de cartas e peças que ficam cada vez mais fortes, como em Balatro. Não existe xeque nem xeque-mate: o que importa é capturar tudo o que o inimigo tem, e rápido, porque a velocidade rende mais moedas.

O projeto usa apenas Python, sem pacotes externos, e uma página em HTML, CSS e JavaScript. Quase tudo que altera o jogo (peças, cartas, preços e dificuldade) fica em arquivos JSON, separado do código.

## Objetivo

Em cada batalha, o objetivo é **capturar todas as peças inimigas**. A batalha termina quando um dos lados fica sem peças.

A run termina em derrota quando:
- todo o exército é capturado;
- não há movimentos possíveis;
- o limite de rodadas da batalha acaba (40 por padrão).

A tela final mostra quantas batalhas foram vencidas e o recorde.

## Como funciona uma run

1. Toda run começa com **4 peças** (Torre, Bispo, Cavalo e Peão), **$5** e um **Pacote Inicial**, do qual se escolhe 1 entre 3 cartas.
2. Segue uma sequência de batalhas, com uma passagem pela loja depois de cada vitória.
3. O tamanho do tabuleiro muda a cada batalha (5×5, 6×6 ou 7×7).
4. A dificuldade sobe sozinha por estágios.

### Estágios

| Estágio | Batalhas | Inimigos | Base de recompensa | Inimigos com movimento especial |
|---|---|---|---|---|
| Iniciante | 1 a 5 | 4 peças | $2 | 0% |
| Fácil | 6 a 10 | 5 peças | $3 | 5% |
| Intermediário | 11 a 15 | 6 peças | $4 | 10% |
| Difícil | 16 a 30 | 6 peças | $5 | 15% |
| GM | 31 em diante | 6 peças | $6 | 20% |

Conforme o estágio sobe, os inimigos jogam melhor, aparecem peças mais fortes (torres e depois rainhas) e surgem **escudos**, **peças explosivas** e, às vezes, **movimentos especiais**. O máximo é de 6 peças inimigas por batalha.

No **GM**, a CPU joga sempre bem e considera a resposta do jogador antes de mover. A cada 10 batalhas a dificuldade aumenta de novo: mais escudos, mais peças explosivas e batalhas mais longas.

### Chefes

A última batalha de cada estágio é um **chefe**, com composição fixa e mais forte que a das batalhas comuns. No GM há um chefe a cada 10 batalhas. Derrotar um chefe dá um **pacote de cartas grátis**, melhor a cada estágio.

## Batalha

### Posicionamento

As peças inimigas aparecem reveladas. As peças do jogador são colocadas na **zona azul** (as últimas linhas do tabuleiro), uma a uma, ou todas de uma vez pelo botão **Auto-posicionar**. Com todas no tabuleiro, o botão **Iniciar batalha** começa o combate.

### Turnos

Quem monta primeiro joga primeiro. Como o campo inimigo já está montado quando o jogador posiciona o exército, a CPU abre cada batalha. Depois o jogador move uma peça por turno, e a CPU responde 1 segundo depois. Cada jogada do jogador conta como uma **rodada**. Quem não tem jogadas perde a vez (a vez perdida também conta como rodada), e a batalha só termina por falta de movimentos se nenhum dos lados puder jogar.

Ao selecionar uma peça, o tabuleiro mostra as jogadas possíveis:
- ponto verde: movimento;
- anel vermelho: captura;
- anel azul tracejado: **troca de lugar** com um aliado.

Tocar em qualquer peça, da própria ou do inimigo, abre um painel com o nome, a descrição e os efeitos dela. Marcadores dentro da peça indicam o estado atual: nível do Berserker (Nv), recarga da troca de lugar (⏳), habilidade de uso único já gasta (✕) e movimento copiado pelo Parasita (☣). As casas que o inimigo pode alcançar ficam avermelhadas na run (com a carta Casas Ameaçadas), no modo de teste e no Duelo, e um botão liga e desliga o realce.

No fim da batalha, uma animação de vitória ou derrota faz a transição para a loja ou para a tela final.

### Movimento das peças

São os movimentos do xadrez, com algumas simplificações:

| Peça | Como anda |
|---|---|
| Peão | 1 casa para a frente (só se estiver livre) e captura na diagonal. Ao chegar à última linha, **vira Rainha** |
| Cavalo | em L, pulando as outras peças |
| Bispo | na diagonal, quantas casas quiser, até bater em algo |
| Torre | em linha reta, quantas casas quiser, até bater em algo |
| Rainha | como o bispo e a torre juntos |
| Rei | 1 casa em qualquer direção |

Não há roque, "en passant", movimento duplo do peão nem regra de xeque. O rei é uma peça comum, sem papel especial. Algumas peças especiais alteram essas regras (veja abaixo).

## Peças e efeitos

O jogo tem **195 peças na loja**. Cada peça é um tipo (Peão, Cavalo, Bispo, Torre, Rainha ou Rei) mais uma lista de **efeitos**, que podem ser combinados. As famílias de efeitos são:

- **Escudo:** absorve capturas. Quando a peça com escudo é atacada, o escudo se gasta e o atacante **não se move**. Há escudos que protegem aliados, que se renovam e que quebram o escudo do alvo.
- **Explosões:** ao ser capturada (ou ao capturar), a peça destrói outras ao redor, em cruz, em diagonais ou em área, ou leva o atacante junto.
- **Moedas:** ganhos ao capturar, ao sobreviver até o fim da batalha, por série de capturas, por tipo de alvo, por posição no tabuleiro e outras condições.
- **Sobrevivência:** peças imortais e peças com chance de escapar de uma captura.
- **Mutante:** recebe uma habilidade sorteada no começo da batalha.
- **Movimento especial:** altera como a peça anda (tabela abaixo).

### Peças de movimento especial

| Peça | O que faz |
|---|---|
| Berserker (Peão, Cavalo, Rei) | a cada captura (até 3 vezes) ganha alcance: o Peão avança mais casas, o Cavalo ganha saltos 3+2, depois 4+3 e 5+4, o Rei anda mais casas em linha reta |
| Bispo Errante | uma vez por batalha, dá um passo reto para uma casa vazia (muda de cor de casa) |
| Bispo Suporte | troca de lugar com um aliado na mesma diagonal (uma vez a cada 3 turnos) |
| Rei Viajante | uma vez por batalha, troca de lugar com qualquer aliado |
| Peão Saltador | se a casa da frente estiver ocupada, pula para a seguinte |
| Peão Independente | passa por cima de um aliado que esteja na frente |
| Peão Pacifista | nunca captura, mas passa por cima de um inimigo na frente. Ao promover, perde o efeito |
| Bispo Independente | atravessa uma peça aliada em cada diagonal |
| Rei Ausente | pula por cima de uma peça ao lado e cai 2 casas adiante |
| Parasita (Cavalo, Bispo, Torre, Rainha, Rei) | ao capturar, no próximo movimento anda como a peça capturada (sem copiar habilidades) |

Trocas de lugar contam como jogada. Alguns inimigos também recebem Berserker, Parasita, Peão Saltador, Peão Independente e Bispo Independente.

## Moedas e recompensa

Cada vitória dá moedas:

- **Base:** fixa por estágio ($2 no Iniciante, até $6 no GM).
- **Velocidade:** cada estágio tem um número médio de rodadas esperado. Vencer abaixo da média dá bônus, até um limite. Vencer acima da média gera penalidade, também limitada.
- **Capturas e efeitos:** moedas das peças com efeito de moeda.
- **Cartas:** várias cartas dão moedas extras em situações específicas.

Terminar rápido compensa, mas a recompensa nunca fica abaixo de $1.

## Loja

Depois de cada vitória, a loja oferece:

- **Peças:** a peça comprada **substitui uma do exército**. Quando o exército tem menos de 4 peças (por causa de uma venda), ela entra direto na vaga livre. Peças baratas aparecem com mais frequência.
- **Peça misteriosa:** uma peça aleatória, revelada só depois da compra.
- **Troca de ofertas:** sorteia novas peças. O preço da troca dobra a cada troca seguida.
- **Pacotes de cartas:** descritos abaixo.
- **Venda de peças e cartas:** devolve **metade do preço original**, arredondando para baixo, com mínimo de $1. Uma peça de $9 vende por $4. O exército precisa manter pelo menos 1 peça, e a venda fica bloqueada enquanto há um pacote aberto.
- **Consumíveis:** podem ser usados antes de seguir para a próxima batalha.

As cartas não têm preço de compra. Para a venda, o valor base depende da raridade: comum $4, incomum $6, rara $8, épica $11 e lendária $15 (campo `preco_cartas` em `dados/config.json`).

## Pacotes e cartas

Cada pacote mostra 3 cartas, e o jogador **escolhe 1** (ou pula). Quanto mais caro o pacote, maior a chance de cartas raras.

**Raridades:** comum, incomum, rara, épica e lendária.

**Pacotes:** vão de $4 (Baú do Rei) a $20 (Pacote Imortal). Os mais baratos quase só trazem cartas comuns, e os mais caros chegam a 40% de chance de lendária.

**Tipos de carta:**

| Tipo | Espaços | Como funciona |
|---|---|---|
| Permanente | 3 | fica ativa até o fim da run e altera as regras (moedas, loja, batalha) |
| Consumível | 3 | uso único, no momento indicado na carta (loja, posicionamento ou batalha) |
| Risco | usa um espaço de consumível | só vale antes da batalha começar: aumenta a aposta em troca de uma recompensa maior |

Com os espaços cheios, a escolha de uma carta nova exige trocar por uma antiga. Há 171 cartas que saem nos pacotes, e outras 49 ainda estão em desenvolvimento.

## Coleção

A tela **Coleção** mostra as peças e cartas já descobertas (as que faltam aparecem como "???"). Ela continua entre uma run e outra. Algumas cartas dão bônus por peças novas ou pelo tamanho da coleção. O recorde de batalhas vencidas aparece na tela de derrota.

**Onde fica o progresso:** a run e a coleção ficam guardadas no navegador (`localStorage`), e o servidor não guarda nada. Por isso cada navegador, cada aba anônima e cada endereço do site tem o seu próprio progresso, e limpar os dados do site zera tudo.

## Modo Duelo

O botão **DUELO** do menu abre uma partida para dois jogadores no mesmo aparelho ou contra a máquina: **Azul** (embaixo) e **Vermelho** (em cima). O match tem 10 batalhas e não usa cartas nem moedas.

- **Sorteio:** no início do match, 10 sorteios definem quem monta primeiro em cada batalha, e outro sorteio define quem bane primeiro. Quem monta primeiro usa 3/5, 4/6 ou 5/7 do tabuleiro (conforme o tamanho 5×5, 6×6 ou 7×7), monta sem ver o adversário e faz o primeiro movimento. Quem monta depois vê as peças do outro e usa as 2 últimas linhas do seu lado.
- **Banimentos:** cada jogador bane até 5 peças, alternando e de forma pública. As peças banidas ficam fora do draft.
- **Draft:** cada jogador tem 40 moedas e escolhe peças alternadamente, sem repetir peças, até 4 por exército. Quem baniu primeiro escolhe por último. Peças com efeito de moedas não aparecem. O exército vale para o match inteiro, e as peças perdidas voltam a cada batalha.
- **Pontuação:** vitória vale 1 ponto e empate vale meio ponto para cada. Quem não tem jogada perde a vez, e se nenhum dos dois puder jogar ou o limite de 40 rodadas for atingido, a batalha empata. Vence o match quem tiver mais pontos, e a igualdade termina em empate.

**Contra a máquina:** o jogador fica com o Azul e a máquina com o Vermelho, em três níveis (Fácil, Médio e Difícil). A máquina bane as peças mais fortes, escolhe um exército que cabe nas 40 moedas, monta o tabuleiro e joga com a mesma inteligência dos inimigos da run: o nível define a chance de jogar bem e quanto ela olha à frente. As duas últimas casas movimentadas ficam destacadas no tabuleiro, e a revanche mantém o modo e o nível.

O match fica salvo no navegador e continua se a aba for fechada.

## Execução local

O jogo roda localmente apenas com Python 3, sem pacotes externos:

```
python3 jogo.py
```

O servidor local responde em `http://localhost:8000`.

### Modo de teste

O endereço `http://localhost:8000/?teste` abre um modo para testar peças sem jogar uma run. A tela tem uma paleta com todas as peças da loja e um editor de tabuleiro (5×5, 6×6 ou 7×7), com dois lados, escolha da **dificuldade da máquina** (Básica ou a de cada estágio, do Iniciante ao GM) e opções para **parar o inimigo** e **avançar turnos**. O modo de teste não altera a run nem a coleção.

## Estrutura do projeto

```
gambito/
├── jogo.py              inicia o servidor local
├── servidor.py          recebe os cliques do navegador e devolve o estado
├── run.py               a run: batalhas, posicionamento, recompensas, modo de teste
├── duelo.py             o modo Duelo: sorteio, banimentos, draft e batalhas
├── xadrez.py            movimentos, capturas e IA do inimigo
├── efeitos.py           o que cada bloco de efeito faz
├── cartas.py            efeitos das cartas permanentes, recompensa e preços
├── consumiveis.py       cartas consumíveis e de risco
├── pacotes.py           abrir pacotes e escolher cartas
├── loja.py              compras, troca de ofertas e vendas
├── colecao.py           coleção de peças e cartas
├── dados.py             carrega e confere os arquivos JSON
├── estado.py            guarda a run em memória durante cada pedido
├── api/jogo.py          entrada do servidor na hospedagem
├── vercel.json          configuração da hospedagem
├── dados/               arquivos JSON que definem o jogo
│   ├── pecas.json       as peças da loja
│   ├── efeitos.json     os blocos de efeito (ícone e descrição)
│   ├── cartas.json      todas as cartas
│   ├── pacotes.json     pacotes: preço e chance de cada raridade
│   ├── estagios.json    dificuldade por estágio e chefes
│   ├── inimigos.json    limite de ocupação do campo inimigo
│   ├── tipos.json       nome e valor de cada tipo de peça
│   └── config.json      moedas, preços, tamanho do exército, espaços
├── public/              a página do jogo
│   ├── index.html
│   ├── app.js           a interface
│   ├── teste.js         o modo de teste (?teste)
│   ├── duelo.js         as telas do modo Duelo
│   ├── style.css
│   ├── favicon.*        ícone do site (a carta com o peão)
│   └── sons/            piece1, piece2, promote, win e lose
└── tools/               ferramentas de teste e balanceamento
    ├── testar_cartas.py       testa todas as cartas
    ├── simular_economia.py    robô que joga centenas de runs e mede o dinheiro
    └── simular_inimigos.py    compara batalhas com e sem efeitos nos inimigos
```

## Como o jogo é configurado

Quase tudo é definido nos arquivos de `dados/`. O jogo confere esses arquivos ao iniciar e avisa quando algo está errado, como uma vírgula faltando, um id repetido ou um efeito inexistente.

**Peças:** cada peça é uma linha em `dados/pecas.json`:

```json
{"id": "N:saqueador", "nome": "Cavalo Saqueador", "tipo": "N",
 "efeitos": [{"tipo": "moedas_ao_capturar", "valor": 2}, {"tipo": "escudo", "valor": 1}],
 "preco": 7, "loja": true}
```

- `id`: nome único da peça, no formato `TIPO:nome`.
- `tipo`: P, N, B, R, Q ou K.
- `efeitos`: lista de blocos definidos em `dados/efeitos.json`, que podem ser combinados.
- `preco`: custo na loja. Com `loja: true` a peça aparece nela.
- A descrição é montada sozinha a partir dos efeitos, ou definida em `"desc"`.

**Efeitos:** cada efeito tem nome, ícone e descrição em `dados/efeitos.json`, e a lógica fica em `efeitos.py` (ou em `xadrez.movimentos`, quando o efeito altera o movimento).

**Outros arquivos:** `config.json` (moedas iniciais, preços, espaços de cartas), `estagios.json` (dificuldade e chefes), `pacotes.json` (preços e chances) e `cartas.json` (com `"implementado": false`, a carta fica fora dos pacotes).

### Testes e simulações

- **Cartas:** `tools/testar_cartas.py` testa todas.
- **Economia:** `tools/simular_economia.py` roda um robô que joga centenas de runs com uma política de compra (`aleatorio`, `moeda` ou `caro`), uma semente de sorteio (a mesma semente repete o resultado) e um número de runs. O robô joga pior que uma pessoa e morre por volta da batalha 5, então as fases finais têm poucas amostras.
- **Inimigos:** `tools/simular_inimigos.py` compara a taxa de vitória com e sem efeitos de movimento nos inimigos.