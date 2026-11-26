'use strict';
const SIMBOLO = { K: '♚', Q: '♛', R: '♜', B: '♝', N: '♞', P: '♟' };
const CATEGORIAS = { permanente: 'Permanente', consumivel: 'Consumível', risco: 'Risco' };
//em quais telas cada tipo de consumível pode ser usado
const MOMENTOS = {
  qualquer: ['loja', 'posicionamento', 'batalha'], loja: ['loja'], batalha: ['batalha'],
  posicionamento: ['posicionamento'], combate: ['posicionamento', 'batalha'], preparo: ['loja', 'posicionamento'],
};
//modo de teste (endereço com ?teste): usa partida e coleção separadas, que não mexem no jogo de verdade
const modoTeste = new URLSearchParams(location.search).has('teste');
const CHAVE_RUN = modoTeste ? 'gambito_teste_run' : 'gambito_run';
const CHAVE_COLECAO = modoTeste ? 'gambito_teste_colecao' : 'gambito_colecao';
const CHAVE_DUELO = modoTeste ? 'gambito_teste_duelo' : 'gambito_duelo';
let E = null;                  // estado vindo do servidor
let inspecionada = null;       //peça cujo painel de detalhes está aberto: {uid, chave}
let verAmeacas = true;         //liga e desliga o realce das casas ameaçadas
let selecionada = null;        // casa "linha,col" (batalha) ou índice do exército (posicionamento)
let comprando = null;          // compra de peça aguardando a escolha da peça a substituir
let usando = null;             // consumível aguardando a escolha de uma peça alvo
let pendenteSubstituir = null; // carta do pacote aguardando a escolha da carta a substituir
let ultimaCompra = null;
let verColecao = false;
let verComoJogar = false;
let lateralAberta = false;    //no celular: painel de cartas aberto ou fechado
let telaAnterior = null;
let larguraAnterior = window.innerWidth;

//true em telas estreitas (celular em pé), onde o menu lateral vira uma faixa no topo
function ehCelular() { return window.matchMedia('(max-width: 820px), (pointer: coarse) and (orientation: portrait)').matches; }

//no celular em pé, aumenta tudo conforme a largura da tela (1 = celular comum; maior = tela larga ou "site para computador")
function escala() { return ehCelular() ? Math.min(2.4, Math.max(1, window.innerWidth / 400)) : 1; }

//---------- sons (arquivos em /sons/) e animações de fim de batalha
const SONS = {};
['piece1', 'piece2', 'promote', 'win', 'lose'].forEach(nome => {
  SONS[nome] = new Audio('/sons/' + nome + '.wav');
  SONS[nome].preload = 'auto';
});
let mudo = lerSalvo('gambito_mudo') === true;

function tocar(nome) {
  if (mudo || !SONS[nome]) return;
  const som = SONS[nome].cloneNode();  //cópia: permite dois sons ao mesmo tempo sem cortar o anterior
  som.play().catch(() => {});  //sem arquivo ou sem permissão do navegador: segue sem som
}

function alternarMudo() {
  mudo = !mudo;
  guardar('gambito_mudo', mudo);
  atualizarBotaoSom();
}

function atualizarBotaoSom() {
  const b = document.getElementById('som');
  if (b) { b.textContent = mudo ? '🔇' : '🔊'; b.title = mudo ? 'Ligar o som' : 'Desligar o som'; }
}

//transição de fim de batalha: mostra o tabuleiro final com a animação e só então troca para a loja (ou para a derrota)
let emTransicao = false;
function resultadoDaBatalha(antes, depois) {
  if (!antes || antes.tela !== 'batalha') return null;
  if (depois.tela === 'loja') return 'win';
  if (depois.tela === 'derrota') return 'lose';
  return null;
}

function transicaoFim(venceu, real) {
  emTransicao = true;
  E = Object.assign({}, real, { tela: 'batalha', pacote: null });  //mostra o tabuleiro final, como se a batalha ainda estivesse aberta
  desenhar();
  animarFim(venceu);
  setTimeout(() => { E = real; emTransicao = false; desenhar(); }, 2400);  //com a tela coberta, troca para a loja
}

//animação de vitória (confete) ou derrota (tela escurece e treme)
function animarFim(venceu) {
  const fx = document.createElement('div');
  fx.className = 'fx-fim ' + (venceu ? 'fx-vitoria' : 'fx-derrota');
  let html = `<div class="fx-vinheta"></div><div class="fx-texto">${venceu ? 'VITÓRIA!' : 'DERROTA'}</div>`;
  if (venceu) {
    const cores = ['#f0b030', '#1d7cf2', '#e8403a', '#2f9d6a', '#f4efe2'];
    for (let i = 0; i < 40; i++) {
      html += `<i style="left:${Math.random() * 100}%; background:${cores[i % cores.length]}; animation-delay:${(Math.random() * 0.6).toFixed(2)}s; animation-duration:${(1.4 + Math.random() * 1).toFixed(2)}s"></i>`;
    }
  } else {
    const tela = document.getElementById('tela');
    tela.classList.add('tremer');
    setTimeout(() => tela.classList.remove('tremer'), 1000);
  }
  html += '<div class="fx-cortina"></div>';  //cobre a tela no meio da animação, na hora da troca
  fx.innerHTML = html;
  document.body.appendChild(fx);
  setTimeout(() => fx.remove(), 3300);
}

//compara o estado antes e depois da ação para decidir qual som tocar
function efeitosDaAcao(acao, antes, depois) {
  const fim = resultadoDaBatalha(antes, depois);
  if (fim) { tocar(fim); return; }
  if (antes && antes.batalha && depois.batalha) {
    const tipos = {};
    antes.batalha.pecas.forEach(p => tipos[p.uid] = p.tipo);
    if (depois.batalha.pecas.some(p => tipos[p.uid] === 'P' && p.tipo === 'Q')) tocar('promote');
  }
  if (acao === 'mover') tocar('piece1');
  if (acao === 'vez_inimigo' && depois.batalha) {
    const log = depois.batalha.log;
    if (!['O inimigo perdeu o turno.', 'Inimigo parado (modo de teste).'].includes(log[log.length - 1])) tocar('piece2');
  }
}

function simbolo(tipo) { return SIMBOLO[tipo] + '︎'; } // ︎ evita virar emoji

function iconesDosEfeitos(efeitos, escudo) {
  let icones = efeitos.filter(e => e.tipo !== 'escudo').map(e => E.efeitos[e.tipo].icone).join('');
  if (escudo === undefined) escudo = efeitos.some(e => e.tipo === 'escudo') ? 1 : 0;
  if (escudo > 0) icones = E.efeitos.escudo.icone + (escudo > 1 ? escudo : '') + icones;
  return icones;
}

//---------- detalhes e sinais das peças
const NOME_TIPO = { K: 'Rei', Q: 'Rainha', R: 'Torre', B: 'Bispo', N: 'Cavalo', P: 'Peão' };

function textoDoEfeito(e) {
  const d = E.efeitos[e.tipo];
  return d.desc.replace(/\{(\w+)\}/g, (_, k) => (e[k] !== undefined ? e[k] : ''));
}

//Marcadores de estado dentro da peça: nível, recarga da troca e habilidade de uso único já gasta
function marcadoresDaPeca(p) {
  const tem = t => p.efeitos.some(e => e.tipo === t);
  let m = '';
  if (tem('berserker') && p.nivel) m += `<span class="marca m-nivel" title="Nível do Berserker">Nv${p.nivel}</span>`;
  if (p.espera > 0) m += `<span class="marca m-espera" title="Troca de lugar em ${p.espera} turno(s)">⏳${p.espera}</span>`;
  if ((tem('troca_qualquer') && p.usou_troca) || (tem('errante') && p.usou_errante)) m += '<span class="marca m-usada" title="Habilidade de uso único já usada">✕</span>';
  if (p.copia) m += `<span class="marca m-copia" title="Anda como ${NOME_TIPO[p.copia]} no próximo movimento">☣</span>`;
  return m;
}

//Painel com nome, descrição e efeitos da peça tocada (a sua ou a do inimigo)
function painelDaPeca(pecas, achar, rotulo) {
  const p = inspecionada && achar(inspecionada);
  if (!p) return '';
  const cat = E.catalogo[p.id];
  const nome = cat ? cat.nome : NOME_TIPO[p.tipo];
  const lado = rotulo ? rotulo(p) : (p.lado === 'j' ? 'Sua peça' : 'Peça inimiga');
  const efs = p.efeitos.map(e => `<div class="ef"><span class="ef-icone">${E.efeitos[e.tipo].icone}</span><span>${textoDoEfeito(e)}</span></div>`).join('')
    || '<div class="ef"><span>Peça comum, sem habilidade.</span></div>';
  const estado = [];
  if (p.escudo > 0) estado.push(`Escudo: ${p.escudo}`);
  if (p.espera > 0) estado.push(`Troca disponível em ${p.espera} turno(s)`);
  if (p.nivel) estado.push(`Nível: ${p.nivel}`);
  if (p.copia) estado.push(`Próximo movimento como ${NOME_TIPO[p.copia]}`);
  return `<div class="caixa detalhe"><div class="detalhe-topo"><span class="peca-${p.lado} detalhe-peca">${simbolo(p.copia || p.tipo)}</span>
    <div><b>${nome}</b><small>${lado} · ${NOME_TIPO[p.tipo]}</small></div>
    <button class="bt cinza mini-bt" onclick="inspecionada=null;desenhar()">Fechar</button></div>
    ${efs}${estado.length ? `<div class="ef-estado">${estado.join(' · ')}</div>` : ''}</div>`;
}

//No computador o painel de detalhes fica numa coluna ao lado do tabuleiro (largura sempre reservada, para o tabuleiro não se mexer); no celular fica embaixo
function larguraDetalhe() { return ehCelular() ? 0 : (window.innerHeight <= 520 ? 220 : 300); }
function comDetalhe(tabuleiro, painel) {
  const w = larguraDetalhe();
  if (!w) return `<div>${tabuleiro}</div>${painel}`;
  return `<div class="com-detalhe"><div>${tabuleiro}</div><div class="coluna-detalhe" style="width:${w}px">${painel}</div></div>`;
}

//depois da jogada do jogador, a CPU joga 1 segundo depois
let esperandoInimigo = false;
function esperarInimigo() {
  if (esperandoInimigo || E.tela !== 'batalha' || !E.batalha || E.batalha.vez !== 'inimigo') return;
  esperandoInimigo = true;
  setTimeout(async () => { esperandoInimigo = false; await chamar('vez_inimigo'); }, 1000);
}

//A partida e a coleção ficam guardadas no navegador (localStorage) e viajam com cada ação.
function lerSalvo(chave) {
  try { return JSON.parse(localStorage.getItem(chave)); } catch (e) { return null; }
}
function guardar(chave, valor) {
  try {
    if (valor === null || valor === undefined) localStorage.removeItem(chave);
    else localStorage.setItem(chave, JSON.stringify(valor));
  } catch (e) { /* navegador sem armazenamento: o jogo segue, mas não salva */ }
}

async function chamar(acao, dados) {
  const pedido = { acao: acao, dados: dados || {}, run: lerSalvo(CHAVE_RUN), colecao: lerSalvo(CHAVE_COLECAO), duelo: lerSalvo(CHAVE_DUELO) };
  let resp;
  try {
    resp = await fetch('/api/jogo', { method: 'POST', body: JSON.stringify(pedido) });
  } catch (e) { avisar('Sem conexão com o servidor.'); return false; }
  const json = await resp.json();
  if (!resp.ok) { avisar(json.erro); return false; }
  guardar(CHAVE_RUN, json._run);
  guardar(CHAVE_COLECAO, json.colecao);
  guardar(CHAVE_DUELO, json._duelo);
  delete json._run;
  delete json._duelo;
  if (json.tela !== telaAnterior) lateralAberta = false;  //mudou de tela: fecha o painel de cartas
  telaAnterior = json.tela;
  const antes = E;
  E = json;
  efeitosDaAcao(acao, antes, json);
  efeitosDoDuelo(acao, antes, json);  //sons do modo duelo (duelo.js)
  const fim = resultadoDaBatalha(antes, json);
  if (fim && json.batalha) { transicaoFim(fim === 'win', json); return true; }
  desenhar();
  esperarInimigo();
  return true;
}

function avisar(texto) {
  const a = document.getElementById('aviso');
  a.textContent = texto; a.style.display = 'block';
  setTimeout(() => a.style.display = 'none', 2800);
}

//---------- tabuleiro
function desenharTabuleiro(b) {
  const n = b.n;
  const posicionando = b.fase === 'posicionando';
  let largura;
  const z = escala();
  if (ehCelular()) largura = Math.max(240, Math.min(window.innerWidth - 16, window.innerHeight - (posicionando ? 350 : 210) * z, 900) / z);
  else if (window.innerHeight <= 520) largura = Math.max(220, Math.min(window.innerWidth - 330 - larguraDetalhe() - 16, window.innerHeight - (posicionando ? 200 : 110), 760));  //celular deitado
  else largura = Math.max(280, Math.min(window.innerWidth - 380 - larguraDetalhe() - 16, window.innerHeight - (posicionando ? 300 : 150), 760));
  const tam = largura / n;
  const mapa = {};
  b.pecas.forEach(p => mapa[p.linha + ',' + p.col] = p);
  const destinos = selecionada && b.jogadas ? (b.jogadas[selecionada] || []).map(d => d.join(',')) : [];
  const ameacas = new Set(verAmeacas ? b.ameacas.map(a => a.join(',')) : []);
  let html = `<div class="tabuleiro" style="grid-template-columns: repeat(${n}, ${tam}px); width:${largura}px">`;
  for (let l = 0; l < n; l++) {
    for (let c = 0; c < n; c++) {
      const chave = l + ',' + c, p = mapa[chave];
      let cls = 'casa ' + ((l + c) % 2 ? 'escura' : 'clara');
      if (b.fase === 'posicionando' && l >= b.zona_inicio) cls += ' minha-zona';
      if (chave === selecionada) cls += ' selecionada';
      if (destinos.includes(chave)) cls += ' destino' + (p ? (p.lado === 'j' ? ' troca' : ' captura') : '');  //casa de aliado = troca de lugar
      if (ameacas.has(chave)) cls += ' ameaca';
      let clicavel = false;
      if (E.tela === 'posicionamento') clicavel = l >= b.zona_inicio;
      else if (usando !== null) clicavel = !!p && p.lado === 'j';
      else clicavel = !!b.jogadas[chave] || destinos.includes(chave);
      if (clicavel) cls += ' clicavel';
      let conteudo = '';
      if (p) {
        const selo = iconesDosEfeitos(p.efeitos, p.escudo);
        conteudo = `<div class="peca" data-uid="${p.uid}" data-l="${l}" data-c="${c}" data-lado="${p.lado}">
          <span class="peca-${p.lado}" style="font-size:${tam * 0.75}px; line-height:1">${simbolo(p.copia || p.tipo)}</span>`
                 + (selo ? `<span class="selo">${selo}</span>` : '') + marcadoresDaPeca(p) + '</div>';
      }
      const lerPeca = !!p && usando === null && (E.tela === 'batalha' || E.tela === 'posicionamento');  //tocar numa peça abre os detalhes
      html += `<div class="${cls}" style="height:${tam}px" ${clicavel || lerPeca ? `onclick="clicouCasa(${l},${c})"` : ''}>${conteudo}</div>`;
    }
  }
  return html + '</div>';
}

function cartaExercito(chave, i, extra) {
  const p = E.catalogo[chave];
  const efeitosExtras = (E.extras[i] || []);
  const marcado = efeitosExtras.length ? ' ★' : '';
  return `<div class="carta ${extra || ''}" onclick="clicouCarta(${i})" title="${p.desc}">
    <div class="icone">${simbolo(p.tipo)}</div>${p.nome}${marcado}<small class="so-celular">${p.desc}</small></div>`;
}

//---------- cartas (permanentes e consumíveis)
function cartaMini(id, botao) {
  const c = E.cartas_catalogo[id];
  return `<div class="carta mini r-${c.raridade}" title="${c.desc}"><b>${c.nome}</b>
    <small>${E.raridades[c.raridade]} · ${CATEGORIAS[c.categoria]}</small><small>${c.desc}</small>${botao || ''}</div>`;
}

function slotCarta(id, botao) {
  const c = E.cartas_catalogo[id];
  return `<div class="slot r-${c.raridade}" title="${c.desc}"><b>${c.nome}</b><small>${c.desc}</small>${botao || ''}</div>`;
}

function painelCartas() {
  const vazios = Math.max(0, E.espacos - E.cartas.length);
  let html = `<div class="painel"><div class="rotulo">Cartas ${E.cartas.length}/${E.espacos}</div>`;
  html += E.cartas.map((id, i) => slotCarta(id, botaoVenda(false, i))).join('');
  html += Array(vazios).fill('<div class="slot vazio">vazio</div>').join('');
  html += `<div class="rotulo">Consumíveis ${E.consumiveis.length}/${E.config.max_consumiveis}</div>`;
  html += E.consumiveis.map((id, i) => {
    const c = E.cartas_catalogo[id];
    const ok = MOMENTOS[c.quando].includes(E.tela) && !(c.categoria === 'risco' && !(E.batalha && E.batalha.fase === 'posicionando'));
    const rotulo = usando === i ? 'Escolha a peça...' : 'Usar';
    return slotCarta(id, `<button class="bt laranja mini-bt" ${ok ? '' : 'disabled'} onclick="usarCarta(${i})">${rotulo}</button>` + botaoVenda(true, i));
  }).join('') || '<div class="slot vazio">nenhum</div>';
  if (usando !== null) html += '<div class="aviso-uso">Clique na peça que receberá o efeito. <button class="bt cinza mini-bt" onclick="usando=null;desenhar()">Cancelar</button></div>';
  return html + '</div>';
}

//venda (só na loja): devolve metade do preço original
function botaoVenda(consumivel, i) {
  if (E.tela !== 'loja' || !E.venda) return '';
  const valor = (consumivel ? E.venda.consumiveis : E.venda.cartas)[i];
  return `<button class="bt cinza mini-bt" ${E.pacote ? 'disabled' : ''} onclick="vender('${consumivel ? 'consumivel' : 'carta'}',${i})">Vender $${valor}</button>`;
}

async function vender(tipo, i) {
  usando = null;
  if (tipo === 'peca') await chamar('vender_peca', { indice: i });
  else await chamar('vender_carta', { consumivel: tipo === 'consumivel', indice: i });
}

//com vaga livre no exército a peça entra direto; sem vaga, você escolhe qual substituir
async function iniciarCompra(slot) {
  if (E.exercito.length < E.config.tamanho_exercito) {
    const ok = await chamar('comprar', { slot: slot, substituir: -1 });
    if (ok) { ultimaCompra = E.exercito[E.exercito.length - 1]; desenhar(); }
    return;
  }
  comprando = slot;
  desenhar();
}

async function usarCarta(i) {
  const c = E.cartas_catalogo[E.consumiveis[i]];
  lateralAberta = false;  //no celular, fecha o painel para você tocar na peça
  if (c.alvo === 'minha_peca') { usando = (usando === i ? null : i); return desenhar(); }
  await chamar('usar_carta', { indice: i });
}

//---------- menu lateral (parecido com o do Balatro)
function lateral(titulo, info) {
  return `<aside class="lateral${lateralAberta ? ' aberto' : ''}">
    <div class="lat-titulo">${titulo}</div>
    <div class="painel info">${info}</div>
    <div class="painel moedas"><span class="cifrao">$</span><span>${E.moedas}</span></div>
    <button class="bt azul peq lat-toggle" onclick="alternarLateral()">Cartas ${E.cartas.length + E.consumiveis.length}</button>
    <div class="lat-corpo">
      <div class="lat-botoes">
        <button class="bt laranja peq" onclick="verColecao=true;desenhar()">Coleção</button>
        <button class="bt vermelho peq" onclick="abandonar()">Abandonar</button>
      </div>
      ${painelCartas()}
    </div></aside>`;
}

//abre ou fecha o painel de cartas (só aparece no celular)
function alternarLateral() {
  lateralAberta = !lateralAberta;
  const l = document.querySelector('.lateral');
  if (l) l.classList.toggle('aberto', lateralAberta);
}

function infoGeral() { return `${E.estagio.nome} · Batalha ${E.num}${E.estagio.chefe ? ' · CHEFE' : ''}`; }

function comLateral(titulo, info, principal) {
  //no celular o painel de cartas fica fechado, então o aviso de "escolha uma peça" aparece aqui também
  const avisoUso = usando !== null ? `<div class="aviso-uso topo-uso">Toque na peça que receberá o efeito. <button class="bt cinza mini-bt" onclick="usando=null;desenhar()">Cancelar</button></div>` : '';
  return `<div class="layout">${lateral(titulo, info)}<main class="central">${avisoUso}${principal}</main></div>`;
}

//---------- telas
function desenhar() {
  document.documentElement.style.setProperty('--z', escala());
  if (E.tela === 'duelo') return telaDuelo(document.getElementById('tela'));  //modo duelo (duelo.js)
  if (modoTeste && (E.tela === 'menu' || E.tela === 'loja' || E.tela === 'derrota')) {  //telas do modo de teste (teste.js)
    document.body.className = '';
    document.getElementById('topo').innerHTML = '';
    return E.tela === 'menu' ? telaEditorTeste(document.getElementById('tela')) : telaResultadoTeste(document.getElementById('tela'));
  }
  const topo = document.getElementById('topo');
  const tela = document.getElementById('tela');
  const noMenu = E.tela === 'menu' && !verColecao && !verComoJogar;
  const fim = E.tela === 'derrota';
  document.body.className = noMenu ? 'menu' : (verColecao || fim ? '' : 'run');
  const comoJogar = E.tela === 'menu' && verComoJogar && !verColecao;
  if (comoJogar) document.body.className = '';
  topo.innerHTML = (verColecao || comoJogar) ? '<h2>GAMBITO</h2>' : '';

  if (comoJogar) return telaComoJogar(tela);
  if (verColecao) return telaColecao(tela);
  if (E.tela === 'menu') return telaMenu(tela);
  if (E.pacote) return telaPacote(tela);
  if (E.tela === 'posicionamento') return telaPosicionamento(tela);
  if (E.tela === 'batalha') return telaBatalha(tela);
  if (E.tela === 'loja') return telaLoja(tela);
  if (fim) return telaFim(tela);
}

function telaMenu(tela) {
  const titulo = `<div class="titulo"><span>GAMB</span><div class="carta-titulo"><i>♟\uFE0E</i></div><span>TO</span></div>`;
  const meio = `<div class="barra-botoes">
      <button class="bt azul grande-bt" onclick="chamar('novo')">JOGAR</button>
      <button class="bt laranja grande-bt" onclick="verComoJogar=true;desenhar()">COMO JOGAR</button>
      <button class="bt verde grande-bt" onclick="verColecao=true;desenhar()">COLEÇÃO</button>
      <button class="bt vermelho grande-bt" onclick="chamar('duelo_novo')">DUELO</button></div>`;
  tela.innerHTML = `<div class="menu-conteudo">${titulo}${meio}</div>`;
}

function telaComoJogar(tela) {
  tela.innerHTML = `<div class="como-jogar"><button class="bt cinza" onclick="verComoJogar=false;desenhar()">← Voltar</button>
    <div class="caixa"><h2 class="grande-titulo">Como jogar</h2>
    <h3>Objetivo</h3>
    <p>Gambito é um roguelike de xadrez. Em cada batalha você precisa <b>capturar todas as peças inimigas</b>. Não existe xeque-mate nem rei especial: a batalha termina quando um dos lados fica sem peças.
    Você perde a run se todas as suas peças forem capturadas, se ficar sem movimentos ou se estourar o limite de rodadas.</p>
    <h3>Uma run</h3>
    <ul><li>A run é <b>infinita</b>: você enfrenta batalhas em sequência até perder. O resultado é o número de batalhas vencidas.</li>
    <li>A dificuldade sobe sozinha por estágios: <b>Iniciante</b> (1–5), <b>Fácil</b> (6–10), <b>Intermediário</b> (11–15), <b>Difícil</b> (16–30) e <b>GM</b> (31 em diante, sem fim).</li>
    <li>A última batalha de cada estágio é um <b>chefe</b> (no GM, um a cada 10 batalhas). Derrotá-lo dá um <b>pacote de cartas grátis</b>.</li>
    <li>Os inimigos ficam mais espertos e ganham mais peças fortes, escudos e peças explosivas a cada estágio, até no máximo 6 peças.</li>
    <li>Todo começo de run traz um <b>Pacote Inicial</b>: escolha 1 entre 3 cartas.</li>
    <li>Seu exército tem sempre <b>4 peças</b>. O tabuleiro muda de tamanho (5×5, 6×6 ou 7×7) a cada batalha.</li></ul>
    <h3>Posicionamento</h3>
    <p>As peças inimigas já aparecem reveladas. Clique numa peça sua e depois numa casa da <b>zona azul</b> (as últimas linhas do tabuleiro). Clicar numa peça já colocada a tira do tabuleiro. Quando todas estiverem posicionadas, inicie a batalha.</p>
    <h3>Batalha</h3>
    <ul><li>Você move uma peça por turno; depois de 1 segundo, o inimigo responde.</li>
    <li>Os movimentos são os do xadrez: o <b>peão</b> anda 1 casa para a frente e captura na diagonal; o <b>cavalo</b> anda em L; o <b>bispo</b> na diagonal; a <b>torre</b> em linha reta; a <b>rainha</b> como bispo e torre juntos; o <b>rei</b> 1 casa em qualquer direção.</li>
    <li>Clique numa peça para ver as jogadas: pontos verdes são movimentos e anéis vermelhos são capturas.</li>
    <li>Cada jogada sua conta uma <b>rodada</b>. Quanto mais rápido você vencer, mais moedas ganha.</li></ul>
    <h3>Moedas e recompensa</h3>
    <p>Cada vitória dá uma base que cresce com o estágio ($2 no Iniciante, até $6 no GM), mais bônus: terminar abaixo da rodada média, capturas que dão moedas, efeitos de peças e cartas. Terminar acima da média gera penalidade.</p>
    <h3>Loja</h3>
    <ul><li><b>Peças:</b> comprar uma peça substitui uma do seu exército (o tamanho nunca muda).</li>
    <li><b>Peça misteriosa:</b> uma peça aleatória, revelada só depois da compra.</li>
    <li><b>Trocar ofertas:</b> sorteia novas peças, e o preço dobra se você trocar várias vezes seguidas.</li>
    <li><b>Pacotes de cartas:</b> ao abrir, você escolhe 1 entre as opções. Pacotes mais caros têm mais chance de cartas raras, épicas e lendárias. As cartas em si não têm preço.</li></ul>
    <h3>Cartas</h3>
    <ul><li><b>Permanentes</b> (3 espaços): ficam ativas até o fim da run.</li>
    <li><b>Consumíveis</b> (3 espaços): uso único, quando você quiser (dentro do momento indicado na carta).</li>
    <li><b>Risco:</b> só podem ser usadas no posicionamento; arriscam algo em troca de uma recompensa maior.</li>
    <li>Se os espaços estiverem cheios, você escolhe qual carta substituir.</li></ul>
    <h3>Efeitos de peças</h3>
    <p>Algumas peças têm efeitos, mostrados por um símbolo no canto delas: escudo (absorve uma captura), explosão ao ser capturada, moedas ao capturar e mais. Passe o mouse sobre uma peça na loja para ler a descrição.</p>
    <h3>Fim da run e coleção</h3>
    <p>Ao perder, as peças e cartas da run são perdidas. A <b>coleção</b> guarda tudo o que você já descobriu.</p>
    <button class="bt cinza" onclick="verComoJogar=false;desenhar()">← Voltar</button></div></div>`;
}

function telaPacote(tela) {
  const p = E.pacote, info = E.pacotes[p.id];
  const odds = E.ordem_raridades.filter(r => info.probabilidades[r] > 0)
    .map(r => `<span class="r-${r}-txt">${E.raridades[r]} ${info.probabilidades[r]}%</span>`).join(' · ');
  let html = `<h2 class="grande-titulo">${info.nome}</h2><p>Escolha <b>1</b> das ${p.opcoes.length} cartas · ${odds}</p><div class="lista centro">`;
  p.opcoes.forEach((id, i) => {
    const c = E.cartas_catalogo[id];
    html += `<div class="carta grande r-${c.raridade}"><b>${c.nome}</b><span class="rar r-${c.raridade}-txt">${E.raridades[c.raridade]}</span>
      <small>${CATEGORIAS[c.categoria]}</small><small>${c.desc}</small>
      <button class="bt azul mini-bt" onclick="escolherOpcao(${i})">Escolher</button></div>`;
  });
  html += '</div>';
  if (pendenteSubstituir !== null) {
    const c = E.cartas_catalogo[p.opcoes[pendenteSubstituir]];
    const perm = c.categoria === 'permanente';
    const lista = perm ? E.cartas : E.consumiveis;
    html += `<div class="caixa"><b>Seus espaços estão cheios.</b> Clique na carta que será <b>substituída</b> por ${c.nome}:
      <div class="lista centro">${lista.map((id, i) => `<div onclick="confirmarSubstituicao(${i})" style="cursor:pointer">${cartaMini(id)}</div>`).join('')}</div>
      <button class="bt cinza mini-bt" onclick="pendenteSubstituir=null;desenhar()">Cancelar</button></div>`;
  }
  html += `<button class="bt cinza" onclick="pendenteSubstituir=null;chamar('pular_pacote')">Pular pacote</button>`;
  tela.innerHTML = comLateral('Pacote', infoGeral(), `<div class="pacote-tela">${html}</div>`);
}

async function escolherOpcao(i) {
  const c = E.cartas_catalogo[E.pacote.opcoes[i]];
  const perm = c.categoria === 'permanente';
  const lista = perm ? E.cartas : E.consumiveis;
  const limite = perm ? E.espacos : E.config.max_consumiveis;
  if (lista.length < limite) { await chamar('escolher_carta', { opcao: i }); return; }
  pendenteSubstituir = i; desenhar();
}

async function confirmarSubstituicao(posicao) {
  const i = pendenteSubstituir; pendenteSubstituir = null;
  await chamar('escolher_carta', { opcao: i, substituir: posicao });
}

function telaPosicionamento(tela) {
  const b = E.batalha;
  const colocadas = Object.keys(b.posicoes).length;
  const cartas = E.exercito.map((k, i) => {
    const usada = b.posicoes[i] ? 'usada' : '';
    return cartaExercito(k, i, usada + (selecionada === i ? ' escolhida' : '') + (usando !== null ? ' alvo' : ''));
  }).join('');
  const principal = `<h3>Posicione seu exército (${colocadas}/${E.exercito.length})</h3>
    ${comDetalhe(desenharTabuleiro(b), painelDaPeca(b.pecas, i => b.pecas.find(p => p.linha + ',' + p.col === i.chave)))}
    <div class="lista centro">${cartas}</div>
    <p class="dica">Clique numa peça e depois numa casa da zona azul. Clique numa peça já usada para tirá-la.</p>
    <div class="lista centro"><button class="bt cinza" onclick="chamar('auto')">Auto-posicionar</button>
    <button class="bt azul" ${colocadas < E.exercito.length ? 'disabled' : ''} onclick="selecionada=null;chamar('iniciar')">Iniciar batalha</button></div>`;
  tela.innerHTML = comLateral('Posicionamento', infoGeral(), principal);
}

function telaBatalha(tela) {
  const b = E.batalha;
  const inimigas = b.pecas.filter(p => p.lado === 'i').length;
  const minhas = b.pecas.filter(p => p.lado === 'j').length;
  const cor = b.rodadas > E.estagio.media ? '#ff7a70' : '#7be08f';
  const info = `${infoGeral()}<div class="grande-num" style="color:${cor}">Rodada ${b.rodadas}</div>
    <small>Média ${E.estagio.media} · Limite ${b.limite || 'nenhum'}</small><br>
    <span class="azul-txt">Suas peças: ${minhas}</span> · <span class="verm-txt">Inimigas: ${inimigas}</span>
    <div class="log">${b.log.map(l => '<div>' + l + '</div>').join('')}</div>`;
  const botaoAmeaca = b.ameacas.length ? ` <button class="bt cinza mini-bt" onclick="verAmeacas=!verAmeacas;desenhar()">${verAmeacas ? 'Esconder' : 'Mostrar'} alcance inimigo</button>` : '';
  const principal = `${comDetalhe(desenharTabuleiro(b), painelDaPeca(b.pecas, i => b.pecas.find(p => p.uid === i.uid)))}
    <p class="dica">Verde = mover · anel vermelho = capturar · toque numa peça para ver os detalhes${b.ameacas.length ? ' · casas avermelhadas = alcance inimigo' : ''}${botaoAmeaca}</p>`;
  tela.innerHTML = comLateral(E.estagio.chefe ? `CHEFE · Batalha ${E.num}` : `Batalha ${E.num}`, info, principal + (modoTeste ? painelTeste() : ''));
  const box = document.querySelector('.log'); if (box) box.scrollTop = box.scrollHeight;
}

function reportHTML(r) {
  const sinal = v => (v >= 0 ? '+' : '') + v;
  return `<div class="caixa relatorio"><b class="grande-titulo">Vitória!</b>
    <span>Base +${r.base}</span>
    <span>${r.rodadas} rodadas (média ${r.media}): <b style="color:${r.tempo >= 0 ? '#7be08f' : '#ff7a70'}">${sinal(r.tempo)}</b></span>
    <span>Capturas +${r.capturas}</span><span>Peças vivas +${r.fim_de_batalha}</span><span>Cartas ${sinal(r.cartas)}</span>
    ${r.mult !== 1 ? `<span>Multiplicador ×${r.mult}</span>` : ''}
    <b class="preco">Total +${r.total}${r.loja ? ` (+${r.loja} ao entrar na loja)` : ''}</b>
    ${r.chefe ? `<b class="preco">Chefe derrotado! Pacote grátis: ${r.pacote_chefe}</b>` : ''}</div>`;
}

function oddsCurtas(info) {
  return E.ordem_raridades.filter(r => info.probabilidades[r] > 0)
    .map(r => `<span class="r-${r}-txt">${E.raridades[r].slice(0, 3)} ${info.probabilidades[r]}%</span>`).join(' · ');
}

function telaLoja(tela) {
  const r = E.relatorio, loja = E.loja, pr = E.precos;
  let html = reportHTML(r);
  if (ultimaCompra) html += `<div class="dica">Você comprou: <b>${E.catalogo[ultimaCompra].nome}</b></div>`;
  if (E.cupom) html += `<div class="dica">Cupom ativo: sua próxima peça custa ${E.cupom} a menos.</div>`;

  //área do exército (como a área dos coringas do Balatro)
  const podeVender = E.exercito.length > 1 && comprando === null && !E.pacote;
  html += `<div class="area-exercito"><div class="rotulo">Seu exército ${E.exercito.length}/${E.config.tamanho_exercito}
    ${comprando !== null ? ' — clique na peça que será SUBSTITUÍDA' : ' — ★ = peça com efeito de carta'}</div>
    <div class="lista centro">${E.exercito.map((k, i) => `<div class="item">${cartaExercito(k, i, comprando !== null || usando !== null ? 'escolhida' : '')}
      <button class="bt cinza mini-bt" ${podeVender ? '' : 'disabled'} onclick="vender('peca',${i})">Vender $${E.venda.pecas[i]}</button></div>`).join('')}</div></div>`;

  //peças à venda
  let pecas = loja.ofertas.map((k, i) => {
    const p = E.catalogo[k], vendida = loja.vendidas[i], preco = pr.ofertas[i];
    const original = p.preco !== preco ? ` <s>${p.preco}</s>` : '';
    return `<div class="item ${vendida ? 'vendido' : ''}"><div class="etiqueta">$${preco}${original}</div>
      <div class="carta" onclick="${vendida || E.moedas < preco ? '' : `iniciarCompra('${i}')`}">
      <div class="icone">${simbolo(p.tipo)}</div><b>${p.nome}</b><small>${p.desc}</small></div>
      <button class="bt laranja mini-bt" ${vendida || E.moedas < preco ? 'disabled' : ''} onclick="iniciarCompra('${i}')">${vendida ? 'Comprada' : 'Comprar'}</button></div>`;
  }).join('');
  const mv = loja.misteriosa_vendida;
  pecas += `<div class="item ${mv ? 'vendido' : ''}"><div class="etiqueta">$${pr.misteriosa}</div>
    <div class="carta" onclick="${mv || E.moedas < pr.misteriosa ? '' : `iniciarCompra('misteriosa')`}">
    <div class="icone">?</div><b>Peça misteriosa</b><small>Uma peça aleatória. Só descobre ao comprar!</small></div>
    <button class="bt laranja mini-bt" ${mv || E.moedas < pr.misteriosa ? 'disabled' : ''} onclick="iniciarCompra('misteriosa')">${mv ? 'Comprada' : 'Comprar'}</button></div>`;

  //pacotes
  const pacs = loja.pacotes.map((id, i) => {
    const info = E.pacotes[id], vendido = loja.pacotes_vendidos[i];
    return `<div class="item ${vendido ? 'vendido' : ''}"><div class="etiqueta">$${info.preco}</div>
      <div class="pacote-visual" onclick="${vendido || E.moedas < info.preco ? '' : `chamar('comprar_pacote', {slot:${i}})`}">
        <b>${info.nome}</b><small>${oddsCurtas(info)}</small></div>
      <button class="bt laranja mini-bt" ${vendido || E.moedas < info.preco ? 'disabled' : ''} onclick="chamar('comprar_pacote', {slot:${i}})">${vendido ? 'Aberto' : 'Abrir'}</button></div>`;
  }).join('');

  html += `<div class="loja-painel">
    <div class="loja-botoes">
      <button class="bt vermelho" onclick="ultimaCompra=null;comprando=null;usando=null;chamar('proxima')">Próxima batalha</button>
      <button class="bt verde" ${E.moedas < pr.troca ? 'disabled' : ''} onclick="ultimaCompra=null;chamar('trocar')">Trocar ofertas<br><span class="preco">$${pr.troca}</span></button>
      ${comprando !== null ? '<button class="bt cinza" onclick="comprando=null;desenhar()">Cancelar compra</button>' : ''}
    </div>
    <div class="loja-direita">
      <div class="loja-secao"><div class="rotulo">Peças</div><div class="lista centro">${pecas}</div></div>
      <div class="loja-secao"><div class="rotulo">Pacotes de cartas</div><div class="lista centro">${pacs}</div></div>
    </div></div>`;
  tela.innerHTML = comLateral('LOJA', `${infoGeral()}<br><small>Melhore seu exército!</small>`, html)
    .replace('class="lat-titulo"', 'class="lat-titulo placa"');
}

function telaFim(tela) {
  tela.innerHTML = `<div class="centralizado"><div class="caixa fim"><h2 class="grande-titulo">Derrota</h2>
    <p>${E.relatorio.motivo}</p>
    <p>Batalhas vencidas: <b>${E.relatorio.vencidas}</b> · Recorde: <b>${E.colecao.melhor}</b></p>
    <p>As peças e cartas desta run foram perdidas, mas a coleção continua.</p>
    <button class="bt azul" onclick="chamar('abandonar')">Voltar ao menu</button></div></div>`;
}

function telaColecao(tela) {
  const chaves = E.loja_chaves;
  const tenho = Object.keys(E.colecao.pecas).length;
  let html = `<button class="bt cinza" onclick="verColecao=false;desenhar()">← Voltar</button>
    <h3>Peças: ${tenho}/${chaves.length} descobertas</h3><div class="lista">`;
  chaves.forEach(k => {
    const p = E.catalogo[k], qtd = E.colecao.pecas[k];
    if (qtd) html += `<div class="carta" style="cursor:default"><div class="icone">${simbolo(p.tipo)}</div><b>${p.nome}</b><small>${p.desc}</small>Comprada ${qtd}x</div>`;
    else html += `<div class="carta trancada"><div class="icone">${simbolo(p.tipo)}</div><b>???</b><small>Ainda não descoberta</small></div>`;
  });
  html += '</div>';
  const todas = Object.values(E.cartas_catalogo);
  const impl = todas.filter(c => c.implementado);
  const achadas = impl.filter(c => E.colecao.cartas[c.id]).length;
  html += `<h3>Cartas: ${achadas}/${impl.length} descobertas</h3>
    <p class="sub">${todas.length - impl.length} cartas ainda estão em desenvolvimento e não saem nos pacotes.</p>`;
  E.ordem_raridades.forEach(r => {
    const lista = impl.filter(c => c.raridade === r);
    const n = lista.filter(c => E.colecao.cartas[c.id]).length;
    html += `<h4 class="r-${r}-txt">${E.raridades[r]} — ${n}/${lista.length}</h4><div class="lista">`;
    html += lista.map(c => E.colecao.cartas[c.id]
      ? `<div class="carta mini r-${c.raridade}" style="cursor:default"><b>${c.nome}</b><small>${CATEGORIAS[c.categoria]}</small><small>${c.desc}</small><small>Escolhida ${E.colecao.cartas[c.id]}x</small></div>`
      : `<div class="carta mini vazia">???</div>`).join('');
    html += '</div>';
  });
  tela.innerHTML = html;
}

//---------- cliques
async function clicouCasa(l, c) {
  const chave = l + ',' + c;
  const b = E.batalha;
  const peca = b.pecas.find(p => p.linha === l && p.col === c);
  if (usando !== null) {  // escolhendo o alvo de uma carta
    if (peca && peca.lado === 'j') {
      const i = usando; usando = null;
      await chamar('usar_carta', { indice: i, alvo: peca.indice });
    }
    return;
  }
  inspecionada = peca ? { uid: peca.uid, chave: chave } : null;
  if (E.tela === 'posicionamento') {
    if (peca && peca.lado === 'j' && selecionada === null) { selecionada = peca.indice; return desenhar(); }
    if (peca && peca.lado === 'i') return desenhar();  //peça inimiga: só mostra os detalhes
    if (selecionada !== null) {
      const i = selecionada; selecionada = null;
      await chamar('colocar', { indice: i, linha: l, col: c });
    } else desenhar();
  } else if (E.tela === 'batalha') {
    if (selecionada && (b.jogadas[selecionada] || []).some(d => d.join(',') === chave)) {
      const de = selecionada.split(',').map(Number);
      selecionada = null;
      await chamar('mover', { de: de, para: [l, c] });
    } else {
      selecionada = b.jogadas[chave] ? chave : null;
      desenhar();
    }
  }
}

async function clicouCarta(i) {
  if (usando !== null) {  // usando uma carta em uma peça do exército (posicionamento ou loja)
    const carta = usando; usando = null;
    await chamar('usar_carta', { indice: carta, alvo: i });
    return;
  }
  if (E.tela === 'posicionamento') {
    if (E.batalha.posicoes[i]) { selecionada = null; await chamar('tirar', { indice: i }); }
    else { selecionada = (selecionada === i ? null : i); desenhar(); }
  } else if (E.tela === 'loja' && comprando !== null) {
    const slot = comprando; comprando = null;
    const ok = await chamar('comprar', { slot: slot, substituir: i });
    if (ok) { ultimaCompra = E.exercito[i]; desenhar(); }
  }
}

async function abandonar() {
  if (confirm('Abandonar a run? As peças e cartas serão perdidas.')) {
    selecionada = null; inspecionada = null; comprando = null; usando = null; pendenteSubstituir = null; verColecao = false; verComoJogar = false;
    await chamar('abandonar');
  }
}

async function iniciar() {
  if (!(await chamar('estado'))) {  // partida salva com problema: começa do menu
    guardar(CHAVE_RUN, null);
    await chamar('estado');
  }
}
//refaz o tabuleiro quando a largura muda (girar o celular, redimensionar a janela)
window.addEventListener('resize', () => {
  if (window.innerWidth === larguraAnterior) return;  //só a barra do navegador mudou de altura
  larguraAnterior = window.innerWidth;
  if (E && (E.batalha || E.duelo)) desenhar();
});
//botão de som (liga e desliga)
const botaoSom = document.createElement('button');
botaoSom.id = 'som';
botaoSom.onclick = alternarMudo;
document.body.appendChild(botaoSom);
atualizarBotaoSom();
iniciar();