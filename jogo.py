"""Como rodar:   python3 jogo.py     e abra   http://localhost:8000

Onde fica cada coisa:
  dados/        arquivos JSON que você edita (peças, efeitos, estágios, inimigos, configurações)
  dados.py      carrega e confere os JSON
  efeitos.py    o que cada bloco de efeito faz
  xadrez.py     movimentos, capturas e IA do inimigo
  run.py        batalhas, posicionamento, recompensas
  loja.py       loja e compras
  colecao.py    coleção permanente (guardada no navegador)
  servidor.py   ligação com o navegador
  public/       a página (index.html, style.css, app.js)
"""
import servidor

if __name__ == '__main__':
    servidor.iniciar()