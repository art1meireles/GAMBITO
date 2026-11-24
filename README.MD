# GAMBITO

Roguelike de xadrez inspirado em Balatro. Monte um pequeno exército, vença batalhas em tabuleiros pequenos, ganhe moedas e melhore suas peças e cartas na loja. A run é infinita: ela só termina quando você perde, e o objetivo é vencer o maior número de batalhas possível.

## Objetivo

Em cada batalha, **capture todas as peças inimigas**. Não existe xeque nem xeque-mate: a batalha termina quando um dos lados fica sem peças.

Você perde a run se:
- todo o seu exército for capturado;
- você ficar sem movimentos possíveis;
- o limite de rodadas da batalha acabar (40 por padrão).

Ao perder, a tela final mostra quantas batalhas você venceu e o seu recorde.

## Como funciona uma run

1. Toda run começa com **4 peças** (Torre, Bispo, Cavalo e Peão), **$5** e um **Pacote Inicial**: abra o pacote e escolha 1 entre 3 cartas.
2. Você enfrenta uma sequência de batalhas. Depois de cada vitória, passa pela loja.
3. O tamanho do tabuleiro muda a cada batalha (5×5, 6×6 ou 7×7).
4. A dificuldade sobe sozinha por estágios, sem você escolher nada no começo.

### Estágios

| Estágio | Batalhas | Inimigos | Base de recompensa |
|---|---|---|---|
| Iniciante | 1 a 5 | 4 peças | $2 |
| Fácil | 6 a 10 | 5 peças | $3 |
| Intermediário | 11 a 15 | 6 peças | $4 |
| Difícil | 16 a 30 | 6 peças | $5 |
| GM | 31 em diante | 6 peças | $6 |

Conforme o estágio sobe, os inimigos jogam melhor, aparecem peças mais fortes (torres e depois rainhas) e ganham **escudos** e **peças explosivas**. O máximo é de 6 peças inimigas por batalha.

No **GM**, a CPU joga sempre bem e considera a sua resposta antes de mover. A cada 10 batalhas ele fica ainda mais difícil: mais escudos, mais explosivas e batalhas mais longas.

### Chefes

A última batalha de cada estágio é um **chefe**, com uma composição fixa de peças mais forte que a das batalhas comuns. No GM há um chefe a cada 10 batalhas. Derrotar um chefe dá um **pacote de cartas grátis**, melhor a cada estágio.

## Batalha

### Posicionamento

As peças inimigas já aparecem reveladas. Clique numa peça sua e depois numa casa da **zona azul** (as últimas linhas do tabuleiro). Clicar numa peça já colocada a tira do tabuleiro. Há também o botão **Auto-posicionar**. Quando todas as peças estiverem no tabuleiro, clique em **Iniciar batalha**.

### Turnos

Você move uma peça por turno. Depois de 1 segundo, a CPU responde. Cada jogada sua conta como uma **rodada**.

Clique numa peça sua para ver as jogadas possíveis: pontos verdes são movimentos e anéis vermelhos são capturas.

### Movimento das peças

São os movimentos do xadrez, com algumas simplificações:

| Peça | Como anda |
|---|---|
| Peão | 1 casa para a frente (só se estiver livre) e captura na diagonal. Ao chegar à última linha, **vira Rainha** |
| Cavalo | em L, e pula as outras peças |
| Bispo | na diagonal, quantas casas quiser, até bater em algo |
| Torre | em linha reta, quantas casas quiser, até bater em algo |
| Rainha | como o bispo e a torre juntos |
| Rei | 1 casa em qualquer direção |

Não há roque, "en passant", movimento duplo do peão nem regra de xeque. O rei é uma peça comum, sem papel especial.

## Peças e efeitos

Peças da loja podem ter **efeitos**. Os blocos disponíveis são:

- **Escudo:** absorve um número de capturas. Quando a peça com escudo é atacada, o escudo se gasta e o atacante **não se move**.
- **Explosiva:** ao ser capturada, destrói também a peça que a capturou.
- **Mercenária:** ganha moedas ao capturar.
- **Dourada:** ganha moedas no fim da batalha, se sobreviver.
- **Incendiária:** ao capturar, destrói as peças inimigas vizinhas à casa de destino.

Os efeitos podem ser combinados na mesma peça. Exemplos: a Rainha Saqueadora (moedas ao capturar e escudo) e o Peão Kamikaze (explode ao ser capturado e ao capturar).

## Moedas e recompensa

Cada vitória dá moedas:

- **Base:** fixa por estágio ($2 no Iniciante, até $6 no GM).
- **Velocidade:** cada estágio tem um número médio de rodadas esperado. Vencer abaixo da média dá bônus, até um limite. Vencer acima da média gera penalidade, também limitada.
- **Capturas e efeitos:** moedas de peças mercenárias e douradas.
- **Cartas:** várias cartas dão moedas extras em situações específicas.

Terminar rápido compensa, mas nunca deixa a recompensa abaixo de $1.

## Loja

Depois de cada vitória você chega à loja, onde pode:

- **Comprar peças:** a nova peça **substitui uma do seu exército** (ele continua com o mesmo tamanho). Peças baratas aparecem com mais frequência.
- **Peça misteriosa:** uma peça aleatória, revelada só depois da compra.
- **Trocar ofertas:** sorteia novas peças. O preço da troca dobra a cada troca seguida.
- **Comprar pacotes de cartas:** veja abaixo.
- **Usar consumíveis**, antes de seguir para a próxima batalha.

## Pacotes e cartas

Um pacote mostra 3 cartas, e você **escolhe 1** (ou pula). Quanto mais caro o pacote, maior a chance de cartas raras. As cartas em si não têm preço.

**Raridades:** comum, incomum, rara, épica e lendária.

**Pacotes:** vão de $4 (Baú do Rei) a $20 (Pacote Imortal). Os mais baratos quase só trazem cartas comuns, e os mais caros chegam a 40% de chance de lendária.

**Tipos de carta:**

| Tipo | Espaços | Como funciona |
|---|---|---|
| Permanente | 3 | fica ativa até o fim da run e altera as regras (moedas, loja, batalha) |
| Consumível | 3 | uso único, no momento indicado na carta (loja, posicionamento ou batalha) |
| Risco | usa um espaço de consumível | só vale antes da batalha começar: aumenta a aposta em troca de uma recompensa maior |

Quando seus espaços estão cheios, ao escolher uma carta nova você decide qual carta antiga substituir. Há mais de 170 cartas no jogo.

## Coleção

A tela **Coleção** mostra as peças e cartas que você já descobriu (as que faltam aparecem como "???"). Ela é permanente: continua entre uma run e outra. Algumas cartas dão bônus por peças novas ou pelo tamanho da coleção. O recorde de batalhas vencidas aparece na tela de derrota.

## Dicas

- Capturas rápidas rendem mais moedas: não fique andando sem objetivo.
- O escudo protege uma peça valiosa, e peças explosivas são boas defesas contra a CPU.
- Pacotes caros valem a pena quando você já tem uma estratégia de cartas montada.
- Em chefes, o pacote grátis é um bom motivo para arriscar mais.