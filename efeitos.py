"""Os BLOCOS DE EFEITO. Cada função abaixo é um momento do jogo em que efeitos podem agir.

Para criar um efeito novo:
  1) adicione o nome dele em dados/efeitos.json (ícone e descrição);
  2) escreva o que ele faz na função do momento certo aqui (um novo "if");
  3) use o nome dele no campo "efeitos" de qualquer peça em dados/pecas.json.
"""


def valor_total(lista_de_efeitos, tipo):
    #Soma o 'valor' de todos os efeitos de um tipo (0 se a peça não tiver)
    return sum(e.get('valor', 1) for e in lista_de_efeitos if e['tipo'] == tipo)


def tem(peca, tipo):
    return any(e['tipo'] == tipo for e in peca['efeitos'])


# Momento 1: a peça vai ser capturada. Devolve True se o golpe foi absorvido.
def ao_receber_golpe(alvo):
    if alvo['escudo'] > 0:          # efeito "escudo"
        alvo['escudo'] -= 1
        return True
    return False


# Momento 2: a peça foi capturada. Devolve True se o atacante deve morrer junto.
def ao_ser_capturado(alvo):
    return tem(alvo, 'explodir_ao_ser_capturado')


#  Momento 3: a peça acabou de capturar. Devolve (moedas ganhas, peças destruídas).
def ao_capturar(atacante, linha, col, pecas):
    moedas = 0
    destruidas = []
    if atacante['lado'] == 'j':     # moedas só valem para o jogador
        moedas += valor_total(atacante['efeitos'], 'moedas_ao_capturar')
    if tem(atacante, 'explosao_ao_capturar'):
        for p in list(pecas):
            vizinha = abs(p['linha'] - linha) <= 1 and abs(p['col'] - col) <= 1
            if vizinha and p['lado'] != atacante['lado']:
                pecas.remove(p)
                destruidas.append(p)
    return moedas, destruidas


# Momento 4: a batalha acabou (vitória). Devolve as moedas das peças que sobreviveram.
def moedas_no_fim_da_batalha(pecas):
    total = 0
    for p in pecas:
        if p['lado'] == 'j':
            total += valor_total(p['efeitos'], 'moedas_fim_batalha')
    return total