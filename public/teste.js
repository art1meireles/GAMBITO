//Modo de teste: tela para montar um cenário (peças suas e inimigas no tabuleiro) e testar os efeitos. Só aparece com ?teste no endereço
//As funções daqui são chamadas pelo app.js; este arquivo carrega antes dele, então nada roda fora de função

let cenario = null;   //{n, pecas: [{lado, id, linha, col}], parado, nivel (posição em E.niveis_ia)}
let paleta = { busca: '', tipo: '', escolhida: 'Q:comum', lado: 'j' };

function garantirCenario() {
  if (cenario) return;
  const salvo = lerSalvo('gambito_teste_cenario');
  cenario = salvo && Array.isArray(salvo.pecas) ? salvo : {
    n: 6, parado: false, nivel: 1,
    pecas: [{ lado: 'j', id: 'Q:comum', linha: 5, col: 2 }, { lado: 'j', id: 'N:comum', linha: 5, col: 4 },
            { lado: 'i', id: 'P:comum', linha: 1, col: 1 }, { lado: 'i', id: 'P:comum', linha: 1, col: 3 }, { lado: 'i', id: 'N:comum', linha: 0, col: 2 }],
  };
}

function nivelValido() {
  if (typeof cenario.nivel !== 'number' || cenario.nivel < 0 || cenario.nivel >= E.niveis_ia.length) cenario.nivel = 1;
  return cenario.nivel;
}

function salvarCenario() { guardar('gambito_teste_cenario', cenario); }

function nomeDaCasa(linha, col, n) { return 'abcdefg'[col] + (n - linha); }

//---------- editor do cenário
function telaEditorTeste(tela) {
  garantirCenario();
  const tipos = ['', 'P', 'N', 'B', 'R', 'Q', 'K'];
  tela.innerHTML = `<div class="teste">
    <div class="faixa-teste">MODO DE TESTE · nada aqui mexe na sua partida nem na sua coleção</div>
    <div class="teste-colunas">
      <div class="caixa teste-paleta">
        <h3>1. Escolha a peça</h3>
        <input id="t-busca" class="teste-busca" placeholder="Buscar por nome ou efeito..." value="${paleta.busca}" oninput="paleta.busca=this.value;redesenharPaleta()">
        <div class="lista teste-tipos" id="t-tipos"></div>
        <div id="t-lista" class="teste-lista"></div>
      </div>
      <div class="teste-editor">
        <h3>2. Monte o cenário</h3>
        <div class="lista centro" id="t-opcoes"></div>
        <div id="t-nivel" class="dica"></div>
        <div id="t-escolhida" class="dica"></div>
        <div id="t-tabuleiro"></div>
        <p class="dica">Clique numa casa vazia para colocar a peça escolhida. Clique numa peça para tirá-la.</p>
        <div class="lista centro">
          <label class="teste-check"><input type="checkbox" ${cenario.parado ? 'checked' : ''} onchange="cenario.parado=this.checked;salvarCenario()"> Inimigo parado (não joga)</label>
        </div>
        <div class="lista centro">
          <button class="bt azul" onclick="comecarTeste()">Começar teste</button>
          <button class="bt cinza" onclick="limparCenario()">Limpar tabuleiro</button>
        </div>
      </div>
    </div></div>`;
  redesenharOpcoes();
  redesenharPaleta();
  redesenharTabuleiroTeste();
}

function redesenharOpcoes() {
  const botao = (rotulo, ativo, acao) => `<button class="bt ${ativo ? 'azul' : 'cinza'} mini-bt" onclick="${acao}">${rotulo}</button>`;
  document.getElementById('t-opcoes').innerHTML =
    '<span class="rotulo">Tabuleiro</span>' + [5, 6, 7].map(n => botao(n + '×' + n, cenario.n === n, `mudarTamanho(${n})`)).join('') +
    '<span class="rotulo">Colocar como</span>' + botao('Minha peça', paleta.lado === 'j', "paleta.lado='j';redesenharOpcoes();redesenharTabuleiroTeste()") +
    botao('Peça inimiga', paleta.lado === 'i', "paleta.lado='i';redesenharOpcoes();redesenharTabuleiroTeste()") +
    '<br><span class="rotulo">Dificuldade da máquina</span>' +
    E.niveis_ia.map((nv, i) => botao(nv.nome, nivelValido() === i, `mudarNivel(${i})`)).join('');
  document.getElementById('t-nivel').innerHTML = (n => `${n.nome}: ${n.inteligencia === 0 ? 'captura quando pode e, senão, anda ao acaso' :
    Math.round(n.inteligencia * 100) + '% das jogadas são escolhidas com cuidado' + (n.olhar >= 2 ? ', olhando 2 jogadas à frente' : '')}.`)(E.niveis_ia[nivelValido()]);
}

function redesenharPaleta() {
  const tipos = ['', 'P', 'N', 'B', 'R', 'Q', 'K'];
  document.getElementById('t-tipos').innerHTML = tipos.map(t =>
    `<button class="bt ${paleta.tipo === t ? 'azul' : 'cinza'} mini-bt" onclick="paleta.tipo='${t}';redesenharPaleta()">${t ? simbolo(t) : 'Todas'}</button>`).join('');
  const busca = paleta.busca.trim().toLowerCase();
  const ids = Object.keys(E.catalogo).filter(id => {
    const p = E.catalogo[id];
    if (paleta.tipo && p.tipo !== paleta.tipo) return false;
    return !busca || (p.nome + ' ' + p.desc).toLowerCase().includes(busca);
  });
  document.getElementById('t-lista').innerHTML = (ids.map(id => {
    const p = E.catalogo[id];
    return `<div class="teste-item ${id === paleta.escolhida ? 'sel' : ''}" onclick="escolherPecaTeste('${id}')">
      <b>${simbolo(p.tipo)} ${p.nome}</b> <small>$${p.preco}</small><small>${p.desc}</small></div>`;
  }).join('')) || '<p class="dica">Nenhuma peça encontrada.</p>';
  const atual = E.catalogo[paleta.escolhida];
  document.getElementById('t-escolhida').innerHTML = `Peça escolhida: <b>${atual.nome}</b> · ${atual.desc}`;
}

function escolherPecaTeste(id) { paleta.escolhida = id; redesenharPaleta(); }

function redesenharTabuleiroTeste() {
  const n = cenario.n;
  const tam = Math.floor(Math.min(520, Math.max(240, window.innerWidth - 60)) / n);
  const mapa = {};
  cenario.pecas.forEach(p => mapa[p.linha + ',' + p.col] = p);
  let html = `<div class="tabuleiro" style="grid-template-columns: repeat(${n}, ${tam}px); width:${tam * n}px">`;
  for (let l = 0; l < n; l++) {
    for (let c = 0; c < n; c++) {
      const p = mapa[l + ',' + c];
      let conteudo = '';
      if (p) {
        const m = E.catalogo[p.id];
        const selo = iconesDosEfeitos(m.efeitos);
        conteudo = `<div class="peca"><span class="peca-${p.lado}" style="font-size:${tam * 0.75}px; line-height:1">${simbolo(m.tipo)}</span>`
                 + (selo ? `<span class="selo">${selo}</span>` : '') + '</div>';
      }
      html += `<div class="casa ${(l + c) % 2 ? 'escura' : 'clara'} clicavel" style="height:${tam}px" title="${p ? E.catalogo[p.id].nome : nomeDaCasa(l, c, n)}" onclick="editarCasa(${l},${c})">${conteudo}</div>`;
    }
  }
  document.getElementById('t-tabuleiro').innerHTML = html + '</div>';
}

function editarCasa(linha, col) {
  const i = cenario.pecas.findIndex(p => p.linha === linha && p.col === col);
  if (i >= 0) cenario.pecas.splice(i, 1);
  else cenario.pecas.push({ lado: paleta.lado, id: paleta.escolhida, linha: linha, col: col });
  salvarCenario();
  redesenharTabuleiroTeste();
}

function mudarTamanho(n) {
  cenario.n = n;
  cenario.pecas = cenario.pecas.filter(p => p.linha < n && p.col < n);  //tira o que ficou fora do tabuleiro menor
  salvarCenario();
  redesenharOpcoes();
  redesenharTabuleiroTeste();
}

function mudarNivel(i) { cenario.nivel = i; salvarCenario(); redesenharOpcoes(); }

function limparCenario() { cenario.pecas = []; salvarCenario(); redesenharTabuleiroTeste(); }

//---------- iniciar e repetir
async function comecarTeste() {
  garantirCenario();
  salvarCenario();
  if (!(await chamar('teste_montar', { n: cenario.n, pecas: cenario.pecas, nivel: nivelValido() }))) return;
  if (cenario.parado) await chamar('teste_parado', { valor: true });
}

async function repetirTeste() { selecionada = null; usando = null; await comecarTeste(); }

async function voltarAoEditor() { selecionada = null; usando = null; await chamar('abandonar'); }

//---------- durante a batalha (aparece embaixo do tabuleiro)
function painelTeste() {
  garantirCenario();
  const t = E.teste || { bonus: 0, serie: 0, turnos: 0, parado: false };
  const b = E.batalha;
  const linhas = b.pecas.map(p => {
    const m = p.id && E.catalogo[p.id];
    const nome = m ? m.nome : (SIMBOLO[p.tipo] + ' ' + p.tipo);
    return `<tr><td class="${p.lado === 'j' ? 'azul-txt' : 'verm-txt'}">${p.lado === 'j' ? 'Minha' : 'Inimiga'}</td>
      <td><b>${nome}</b> <small>${m ? m.desc : ''}</small></td><td>${nomeDaCasa(p.linha, p.col, b.n)}</td><td>${p.escudo}</td></tr>`;
  }).join('');
  return `<div class="caixa teste-painel">
    <div class="faixa-teste">MODO DE TESTE</div>
    <div class="lista centro">
      <button class="bt cinza mini-bt" onclick="repetirTeste()">Repetir cenário</button>
      <button class="bt cinza mini-bt" onclick="voltarAoEditor()">Voltar ao editor</button>
      <button class="bt laranja mini-bt" onclick="chamar('teste_avancar',{n:1})">Avançar 1 rodada</button>
      <button class="bt laranja mini-bt" onclick="chamar('teste_avancar',{n:3})">Avançar 3 rodadas</button>
      <label class="teste-check"><input type="checkbox" ${t.parado ? 'checked' : ''} onchange="chamar('teste_parado',{valor:this.checked})"> Inimigo parado</label>
    </div>
    <div class="teste-resumo">Moedas ganhas nesta batalha: <b>${t.bonus}</b> · Capturas seguidas: <b>${t.serie}</b> · Turnos: <b>${t.turnos}</b> · Máquina: <b>${t.nivel}</b></div>
    <table class="teste-tabela"><tr><th>Lado</th><th>Peça</th><th>Casa</th><th>Escudo</th></tr>${linhas}</table></div>`;
}

//---------- resultado (a batalha acabou)
function telaResultadoTeste(tela) {
  const venceu = E.tela === 'loja';
  const corpo = venceu ? reportHTML(E.relatorio) : `<div class="caixa fim"><h2 class="grande-titulo">Derrota</h2><p>${E.relatorio.motivo}</p></div>`;
  tela.innerHTML = `<div class="teste"><div class="faixa-teste">MODO DE TESTE</div>
    <div class="teste-resultado">${corpo}
      <div class="lista centro"><button class="bt azul" onclick="repetirTeste()">Repetir cenário</button>
      <button class="bt cinza" onclick="voltarAoEditor()">Voltar ao editor</button></div></div></div>`;
}