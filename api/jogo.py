#Ponto de entrada na Vercel: recebe as ações do jogo (POST /api/jogo)
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import servidor


class handler(BaseHTTPRequestHandler):  # a Vercel procura uma classe com este nome
    def _responder(self, codigo, conteudo):
        corpo = json.dumps(conteudo, ensure_ascii=False).encode('utf-8')
        self.send_response(codigo)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        self._responder(200, {'ok': True})  # só para conferir no navegador que a função está no ar

    def do_POST(self):
        tamanho = int(self.headers.get('Content-Length') or 0)
        codigo, resposta = servidor.tratar_pedido(self.rfile.read(tamanho))
        self._responder(codigo, resposta)