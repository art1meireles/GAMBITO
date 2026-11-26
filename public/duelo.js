//Modo DUELO: dois jogadores no mesmo aparelho (azul e vermelho), um match de 10 batalhas
//Fluxo: sorteio > banimentos > draft > (montagem > batalha > resultado) x 10 > fim. As regras ficam no servidor (duelo.py)
//As funções daqui são chamadas pelo app.js; este arquivo carrega antes dele, então nada roda fora de função

let dPal = { busca: '', tipo: '', sel: null };  //paleta de banimentos e draft: busca, filtro de tipo e peça selecionada
let dSel = null;                                //montagem: índice da peça do exército; batalha: casa "linha,col"

const cl = j => (j === 'a' ? 'c-a' : 'c-v');    //classe de cor do jogador
const nomeJ = j => E.duelo.nomes[j];
const meio = p => (p % 1 ? Math.floor(p) + '½' : String(p));  //4.5 vira 4½

function telaDuelo(tela) {
  const v = E.duelo;
  document.body.className = 'run';
  document.getElementById('topo').innerHTML = '';
  let corpo;
  if (v.fase === 'sorteio') corpo = dSorteio(v);
  else if (v.fase === 'banimentos' || v.fase === 'draft') corpo = dPaleta(v);
  else if (v.fase === 'fim') corpo = dFim(v);
  else corpo = dBatalha(v);
  tela.innerHTML = `<div class="duelo">${dPlacar(v)}${corpo}</div>`;
  if (v.fase === 'banimentos' || v.fase === 'draft') dRedesenharLista();
}

async function dSair() {
  if (!confirm('Sair do duelo? O match será perdido.')) return;
  dSel = null; dPal = { busca: '', tipo: '', sel: null };
  await chamar('duelo_sair');
}

function dPlacar(v) {
  const meioTexto = { sorteio: 'Sorteio', banimentos: 'Banimentos', draft: 'Draft', fim: 'Resultado final' }[v.fase]
    || `Batalha ${v.partida + 1} de ${v.total}`;
  return `<div class="d-placar"><div class="d-lado c-a">AZUL <b>${meio(v.pontos.a)}</b></div>
    <div class="d-centro">${meioTexto}</div>
    <div class="d-lado c-v"><b>${meio(v.pontos.v)}</b> VERMELHO</div>
    <button class="bt cinza mini-bt" onclick="dSair()">Sair</button></div>`;
}

//---------- sorteio
function dSorteio(v) {
  const chips = v.ordem.map((j, i) => `<div class="d-chip revela ${cl(j)}" style="--i:${i + 1}"><small>Batalha ${i + 1}</small><b>${nomeJ(j)}</b></div>`).join('');
  return `<div class="caixa d-caixa"><h2 class="grande-titulo">SORTEIO</h2>
    <div class="d-grande revela ${cl(v.abre)}" style="--i:0"><small>Bane primeiro e escolhe por último no draft</small><b>${nomeJ(v.abre)}</b></div>
    <h3>Quem monta primeiro (e joga primeiro) em cada batalha</h3>
    <div class="d-ordem">${chips}</div>
    <p class="dica">Quem monta primeiro usa 3/5, 4/6 ou 5/7 do tabuleiro e faz o primeiro movimento. Quem monta depois vê o tabuleiro do outro e usa as 2 últimas linhas do seu lado.</p>
    <button class="bt verde grande-bt" onclick="chamar('duelo_avancar')">Continuar para os banimentos</button></div>`;
}

//---------- banimentos e draft (mesma paleta)
function dPaleta(v) {
  const ban = v.fase === 'banimentos';
  const j = v.vez;
  const banner = ban
    ? `Vez do <b>${nomeJ(j)}</b>: banir peças (${v.bans[j].length} de ${v.max_bans})`
    : `Vez do <b>${nomeJ(j)}</b>: escolher uma peça · restam <b>$${v.restante[j]}</b> de $${v.orcamento}`;
  const painel = jg => {
    const lista = ban
      ? v.bans[jg].map(id => `<div class="d-peca ${cl(jg)} banida"><span>${simbolo(E.catalogo[id].tipo)} ${E.catalogo[id].nome}</span></div>`).join('')
      : v.exercitos[jg].map(id => `<div class="d-peca ${cl(jg)}"><span>${simbolo(E.catalogo[id].tipo)} ${E.catalogo[id].nome}</span><small>$${E.catalogo[id].preco}</small></div>`).join('');
    const status = !ban && v.encerrado[jg] ? ' · terminou' : '';
    const info = ban ? `Banidas ${v.bans[jg].length}/${v.max_bans}` : `Exército ${v.exercitos[jg].length}/${v.max_pecas} · gasto $${v.gasto[jg]}${status}`;
    return `<div class="caixa d-jogador ${cl(jg)}"><div class="d-titulo">${nomeJ(jg)}</div><small>${info}</small>${lista || '<small>nenhuma ainda</small>'}</div>`;
  };
  return `<div class="d-banner ${cl(j)}">${banner}</div>
    <div class="d-colunas">
      <div class="caixa teste-paleta d-paleta">
        <input id="d-busca" class="teste-busca" placeholder="Buscar por nome ou efeito..." value="${dPal.busca}" oninput="dPal.busca=this.value;dRedesenharLista()">
        <div class="lista teste-tipos" id="d-tipos"></div>
        <div id="d-lista" class="teste-lista"></div>
      </div>
      <div class="d-lateral"><div id="d-acao"></div>${painel('a')}${painel('v')}</div>
    </div>`;
}

function dRedesenharLista() {
  const v = E.duelo;
  const ban = v.fase === 'banimentos';
  const tipos = ['', 'P', 'N', 'B', 'R', 'Q', 'K'];
  document.getElementById('d-tipos').innerHTML = tipos.map(t =>
    `<button class="bt ${dPal.tipo === t ? 'azul' : 'cinza'} mini-bt" onclick="dPal.tipo='${t}';dRedesenharLista()">${t ? simbolo(t) : 'Todas'}</button>`).join('');
  const banidas = new Set([...v.bans.a, ...v.bans.v]);
  const base = ban ? v.elegiveis.filter(id => !banidas.has(id)) : v.disponiveis;
  const busca = dPal.busca.trim().toLowerCase();
  const ids = base.filter(id => {
    const p = E.catalogo[id];
    if (dPal.tipo && p.tipo !== dPal.tipo) return false;
    return !busca || (p.nome + ' ' + p.desc).toLowerCase().includes(busca);
  });
  if (dPal.sel && !base.includes(dPal.sel)) dPal.sel = null;
  document.getElementById('d-lista').innerHTML = (ids.map(id => {
    const p = E.catalogo[id];
    const caro = !ban && p.preco > v.restante[v.vez];
    return `<div class="teste-item ${id === dPal.sel ? 'sel' : ''} ${caro ? 'caro' : ''}" onclick="dPal.sel='${id}';dRedesenharLista()">
      <b>${simbolo(p.tipo)} ${p.nome}</b> <small>$${p.preco}</small><small>${p.desc}</small></div>`;
  }).join('')) || '<p class="dica">Nenhuma peça encontrada.</p>';
  //botões de ação
  const j = v.vez;
  let acao = '';
  if (ban) {
    const p = dPal.sel && E.catalogo[dPal.sel];
    acao = (p ? `<div class="dica">Selecionada: <b>${p.nome}</b></div><button class="bt vermelho" onclick="dBanir()">Banir ${p.nome}</button>` : '<div class="dica">Clique numa peça para selecioná-la.</div>')
      + `<button class="bt cinza" onclick="dSel=null;dPal.sel=null;chamar('duelo_fim_bans')">Terminar meus banimentos</button>`;
  } else {
    const p = dPal.sel && E.catalogo[dPal.sel];
    const cheio = v.exercitos[j].length >= v.max_pecas;
    const pode = p && p.preco <= v.restante[j] && !cheio;
    acao = (p ? `<div class="dica">Selecionada: <b>${p.nome}</b> · custa $${p.preco}</div>` : '<div class="dica">Clique numa peça para selecioná-la.</div>')
      + `<button class="bt verde" ${pode ? '' : 'disabled'} onclick="dEscolher()">${p ? `Escolher por $${p.preco}` : 'Escolher'}</button>
         <button class="bt cinza" ${v.exercitos[j].length ? '' : 'disabled'} onclick="dPal.sel=null;chamar('duelo_parar')">Parar e ficar com este exército</button>`;
  }
  document.getElementById('d-acao').innerHTML = `<div class="caixa d-acao ${cl(j)}">${acao}</div>`;
}

function dBanir() { const id = dPal.sel; dPal.sel = null; chamar('duelo_banir', { id: id }); }
function dEscolher() { const id = dPal.sel; dPal.sel = null; chamar('duelo_escolher', { id: id }); }

//---------- montagem, batalha e resultado (mesmo tabuleiro)
function dLargura() {
  const z = escala();
  if (ehCelular()) return Math.max(240, Math.min(window.innerWidth - 16, window.innerHeight - 340 * z, 900) / z);
  return Math.max(280, Math.min(window.innerWidth - 470, window.innerHeight - 260, 720));
}

function dBatalha(v) {
  const b = v.batalha;
  let banner = '', lateral = '';
  if (v.fase === 'montagem') {
    const j = b.montando, z = b.zonas[j], linhas = z[1] - z[0];
    const regra = j === b.primeiro ? 'Monta primeiro (sem ver o outro lado) e joga primeiro.' : `Monta depois, já vendo o tabuleiro do ${nomeJ(b.primeiro)}.`;
    banner = `<div class="d-banner ${cl(j)}"><b>${nomeJ(j)}</b> monta o seu lado: ${linhas} de ${b.n} linhas. ${regra}</div>`;
    const pecas = v.exercitos[j].map((id, i) => {
      const p = E.catalogo[id], colocada = b.posicoes[j][String(i)];
      return `<div class="d-peca ${cl(j)} ${dSel === i ? 'sel' : ''} ${colocada ? 'colocada' : ''}" onclick="dEscolherPeca(${i})" title="${p.desc}">
        <span>${simbolo(p.tipo)} ${p.nome}</span><small>${colocada ? 'no tabuleiro' : 'clique e escolha a casa'}</small></div>`;
    }).join('');
    const faltam = v.exercitos[j].length - Object.keys(b.posicoes[j]).length;
    lateral = `<div class="caixa d-jogador ${cl(j)}"><div class="d-titulo">Peças do ${nomeJ(j)}</div>${pecas}
      <div class="lista centro"><button class="bt cinza mini-bt" onclick="dSel=null;chamar('duelo_auto')">Auto-posicionar</button>
      <button class="bt verde" ${faltam ? 'disabled' : ''} onclick="dSel=null;chamar('duelo_pronto')">Pronto</button></div>
      <small>Clique numa peça já colocada para tirá-la.</small></div>`;
  } else if (v.fase === 'batalha') {
    banner = `<div class="d-banner ${cl(b.vez)}">Vez do <b>${nomeJ(b.vez)}</b> · rodada ${b.rodadas + 1} de ${v.limite}</div>`;
    lateral = `<div class="caixa"><div class="rotulo">Esta batalha</div><small>${nomeJ(b.primeiro)} montou e joga primeiro · tabuleiro ${b.n}×${b.n}</small>
      <div class="rotulo">Legenda</div><small>● movimento · ○ vermelho: captura · ○ azul tracejado: troca de lugar</small>
      <div class="rotulo">Registro</div><div class="log">${b.log.slice().reverse().map(l => `<div>${l}</div>`).join('')}</div></div>`;
  } else {  //resultado da batalha
    const r = b.resultado, ultima = v.partida + 1 >= v.total;
    banner = r.vencedor
      ? `<div class="d-banner d-resultado ${cl(r.vencedor)}"><h2>${nomeJ(r.vencedor).toUpperCase()} VENCEU A BATALHA ${v.partida + 1}</h2>${r.motivo} +1 ponto.</div>`
      : `<div class="d-banner d-resultado c-e"><h2>EMPATE NA BATALHA ${v.partida + 1}</h2>${r.motivo} Meio ponto para cada.</div>`;
    lateral = `<div class="caixa"><div class="rotulo">Placar</div><div class="d-grandepontos"><span class="c-a">${meio(v.pontos.a)}</span> x <span class="c-v">${meio(v.pontos.v)}</span></div>
      <div class="log">${b.log.slice().reverse().map(l => `<div>${l}</div>`).join('')}</div>
      <button class="bt verde grande-bt" onclick="chamar('duelo_proxima')">${ultima ? 'Ver resultado final' : 'Próxima batalha'}</button></div>`;
  }
  const detalhe = painelDaPeca(b.pecas, i => b.pecas.find(p => (v.fase === 'montagem' ? p.linha + ',' + p.col === i.chave : p.uid === i.uid)),
    p => 'Peça do ' + nomeJ(p.lado === 'j' ? 'a' : 'v'));
  const alcance = v.fase === 'batalha' ? `<button class="bt cinza mini-bt" onclick="verAmeacas=!verAmeacas;desenhar()">${verAmeacas ? 'Esconder' : 'Mostrar'} alcance do adversário</button>` : '';
  return `${banner}<div class="d-corpo"><div class="d-tabuleiro">${dTabuleiro(v)}<div class="d-sob">${alcance}</div>${larguraDetalhe() ? '' : detalhe}</div><div class="d-lateral">${lateral}${larguraDetalhe() ? detalhe : ''}</div></div>`;
}

function dTabuleiro(v) {
  const b = v.batalha, n = b.n;
  const tam = dLargura() / n;
  const mapa = {};
  b.pecas.forEach(p => mapa[p.linha + ',' + p.col] = p);
  const destinos = v.fase === 'batalha' && dSel ? (b.jogadas[dSel] || []).map(d => d.join(',')) : [];
  const zona = v.fase === 'montagem' ? b.zonas[b.montando] : null;
  const ameacas = new Set(verAmeacas && v.fase === 'batalha' ? b.ameacas.map(a => a.join(',')) : []);
  let html = `<div class="tabuleiro" style="grid-template-columns: repeat(${n}, ${tam}px); width:${tam * n}px">`;
  for (let l = 0; l < n; l++) {
    for (let c = 0; c < n; c++) {
      const chave = l + ',' + c, p = mapa[chave];
      let cls = 'casa ' + ((l + c) % 2 ? 'escura' : 'clara');
      let clicavel = false;
      if (zona && l >= zona[0] && l < zona[1]) { cls += ' zona-' + b.montando; clicavel = true; }
      if (v.fase === 'batalha') {
        if (chave === dSel) cls += ' selecionada';
        if (destinos.includes(chave)) cls += ' destino' + (p ? (p.lado === (b.vez === 'a' ? 'j' : 'i') ? ' troca' : ' captura') : '');
        if (ameacas.has(chave)) cls += ' ameaca';
        clicavel = !!b.jogadas[chave] || destinos.includes(chave);
      }
      if (clicavel) cls += ' clicavel';
      let conteudo = '';
      if (p) {
        const selo = iconesDosEfeitos(p.efeitos, p.escudo);
        conteudo = `<div class="peca"><span class="peca-${p.lado}" style="font-size:${tam * 0.75}px; line-height:1">${simbolo(p.copia || p.tipo)}</span>`
                 + (selo ? `<span class="selo">${selo}</span>` : '') + marcadoresDaPeca(p) + '</div>';
      }
      const titulo = p && p.id && E.catalogo[p.id] ? `${E.catalogo[p.id].nome}: ${E.catalogo[p.id].desc}` : '';
      html += `<div class="${cls}" style="height:${tam}px" title="${titulo}" ${clicavel || p ? `onclick="dClicouCasa(${l},${c})"` : ''}>${conteudo}</div>`;
    }
  }
  return html + '</div>';
}

function dEscolherPeca(i) { dSel = (dSel === i ? null : i); desenhar(); }

async function dClicouCasa(l, c) {
  const v = E.duelo, b = v.batalha, chave = l + ',' + c;
  const p = b.pecas.find(q => q.linha === l && q.col === c);
  inspecionada = p ? { uid: p.uid, chave: chave } : null;
  if (v.fase === 'montagem') {
    if (p && p.dono === b.montando) { dSel = null; return chamar('duelo_tirar', { indice: p.indice }); }
    if (p) return desenhar();  //peça do outro jogador: só mostra os detalhes
    if (dSel !== null) {
      const i = dSel;
      if (await chamar('duelo_colocar', { indice: i, linha: l, col: c })) dSel = null;
    }
    return;
  }
  if (v.fase === 'batalha') {
    if (dSel && (b.jogadas[dSel] || []).some(d => d.join(',') === chave)) {
      const de = dSel.split(',').map(Number);
      dSel = null;
      return chamar('duelo_mover', { de: de, para: [l, c] });
    }
    dSel = b.jogadas[chave] ? chave : null;
    desenhar();
  }
}

//---------- fim do match
function dFim(v) {
  const a = v.pontos.a, vm = v.pontos.v;
  const ganhador = a > vm ? 'a' : (vm > a ? 'v' : null);
  const banner = ganhador
    ? `<div class="d-banner d-resultado ${cl(ganhador)}"><h2>${nomeJ(ganhador).toUpperCase()} VENCEU O MATCH</h2>${meio(a)} x ${meio(vm)}</div>`
    : `<div class="d-banner d-resultado c-e"><h2>O MATCH TERMINOU EMPATADO</h2>${meio(a)} x ${meio(vm)}</div>`;
  const linhas = v.resultados.map(r => `<tr><td>${r.partida + 1}</td><td>${r.n}×${r.n}</td><td class="${cl(r.primeiro)}">${nomeJ(r.primeiro)}</td>
    <td class="${r.vencedor ? cl(r.vencedor) : ''}">${r.vencedor ? nomeJ(r.vencedor) : 'Empate'}</td></tr>`).join('');
  return `${banner}<div class="caixa d-caixa"><table class="teste-tabela"><tr><th>Batalha</th><th>Tabuleiro</th><th>Montou primeiro</th><th>Resultado</th></tr>${linhas}</table>
    <button class="bt azul grande-bt" onclick="dSel=null;chamar('duelo_sair')">Voltar ao menu</button></div>`;
}

//---------- sons (chamado pelo app.js depois de cada ação)
function efeitosDoDuelo(acao, antes, depois) {
  const a = antes && antes.duelo, d = depois.duelo;
  if (!d) return;
  if (acao === 'duelo_mover' && a) {
    tocar(a.vez === 'a' ? 'piece1' : 'piece2');  //som de peça diferente para cada jogador
    if (a.batalha && d.batalha) {
      const tipos = {};
      a.batalha.pecas.forEach(p => tipos[p.uid] = p.tipo);
      if (d.batalha.pecas.some(p => tipos[p.uid] === 'P' && p.tipo === 'Q')) setTimeout(() => tocar('promote'), 250);
    }
  }
  if (a && a.fase === 'batalha' && d.fase === 'resultado' && d.batalha.resultado.vencedor) setTimeout(() => tocar('win'), 400);
  if (a && a.fase !== 'fim' && d.fase === 'fim') setTimeout(() => tocar('win'), 400);
}