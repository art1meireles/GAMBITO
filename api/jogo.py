#Ponto de entrada na Vercel: recebe as ações do jogo (POST /api/jogo)
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servidor import Servidor as handler  # a Vercel procura uma classe chamada "handler"