"""
Bot Freedom - obatatoide
Posta piadas aleatórias do blog 'Tempo de Secura' (2005 a 2010)
na rede Freedom (https://freedom-0yku.onrender.com/).
"""

import os
import sys
import time
import json
import random
import hashlib
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from html import unescape
import requests
from bs4 import BeautifulSoup

# Configurações de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('obatatoide')

# Constantes
BASE_URL = os.environ.get('FREEDOM_URL', 'https://freedom-0yku.onrender.com').rstrip('/')
NICKNAME = os.environ.get('FREEDOM_NICKNAME', 'obatatoide')
POST_INTERVAL_SECONDS = int(os.environ.get('POST_INTERVAL', 120))  # 2 minutos
BLOG_YEARS = [2005, 2006, 2007, 2008, 2009, 2010]
POST_MAX_LENGTH = 500

DIR_PATH = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(DIR_PATH, 'jokes_cache.json')
HISTORY_FILE = os.path.join(DIR_PATH, 'posted_history.json')


def clean_text(raw_html):
    """Limpa e formata o texto da piada removendo tags indesejadas mantendo quebras de linha."""
    soup = BeautifulSoup(raw_html, 'html.parser')

    # Substitui <br> por quebras de linha
    for br in soup.find_all('br'):
        br.replace_with('\n')

    # Substitui links/parágrafos por texto
    text = soup.get_text()
    text = unescape(text)

    # Limpeza de linhas em branco repetidas
    lines = [line.strip() for line in text.split('\n')]
    cleaned_lines = []
    prev_blank = False
    for line in lines:
        if not line:
            if not prev_blank:
                cleaned_lines.append('')
                prev_blank = True
        else:
            cleaned_lines.append(line)
            prev_blank = False

    cleaned_text = '\n'.join(cleaned_lines).strip()
    return cleaned_text


def fetch_jokes_from_blog():
    """Baixa e extrai piadas de todos os anos (2005 a 2010)."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    jokes = []
    seen_hashes = set()

    logger.info("Coletando piadas do blog Tempo de Secura (2005 a 2010)...")
    for year in BLOG_YEARS:
        url = f"https://tempo-de-secura.blogspot.com/{year}/"
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.status_code != 200:
                logger.warning(f"Erro ao acessar ano {year}: HTTP {resp.status_code}")
                continue

            soup = BeautifulSoup(resp.text, 'html.parser')
            posts = soup.select('div.post-body')

            year_count = 0
            for post in posts:
                text = clean_text(str(post))

                # Ignora posts vazios, apenas pontuação ou sem conteúdo
                if not text or len(text) < 15:
                    continue

                # Ignora avisos administrativos do blog
                if 'administrador de um blog' in text.lower() or 'termina por opção pessoal' in text.lower():
                    continue

                # Garante que respeita o limite do Freedom (500 chars)
                if len(text) > POST_MAX_LENGTH:
                    continue

                # Hash do conteúdo para evitar repetições
                h = hashlib.sha256(text.encode('utf-8')).hexdigest()
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    jokes.append({
                        'hash': h,
                        'text': text,
                        'year': year
                    })
                    year_count += 1

            logger.info(f"Ano {year}: {year_count} piadas válidas extraídas.")
        except Exception as e:
            logger.error(f"Falha ao processar ano {year}: {e}")

    logger.info(f"Total de piadas coletadas: {len(jokes)}")
    return jokes


def load_cache():
    """Carrega piadas do cache local ou baixa novas se o cache não existir ou estiver vazio."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                jokes = json.load(f)
            if jokes and len(jokes) > 0:
                logger.info(f"Carregadas {len(jokes)} piadas do cache ({CACHE_FILE}).")
                return jokes
        except Exception as e:
            logger.warning(f"Erro ao carregar cache local: {e}")

    jokes = fetch_jokes_from_blog()
    if jokes:
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(jokes, f, ensure_ascii=False, indent=2)
            logger.info(f"Cache de piadas salvo em {CACHE_FILE}.")
        except Exception as e:
            logger.warning(f"Não foi possível salvar cache: {e}")

    return jokes


def load_history():
    """Carrega o histórico de hashes das piadas já postadas."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data)
        except Exception as e:
            logger.warning(f"Erro ao ler histórico: {e}")
    return set()


def save_history(history_set):
    """Salva o histórico de hashes postados."""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(history_set), f, indent=2)
    except Exception as e:
        logger.error(f"Erro ao salvar histórico: {e}")


class FreedomBot:
    def __init__(self, base_url, nickname):
        self.base_url = base_url
        self.nickname = nickname
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FreedomJokeBot/1.0 (obatatoide)',
            'Content-Type': 'application/json'
        })
        self.session_token = None

    def login(self):
        """Autentica na plataforma Freedom usando quick-nickname."""
        login_url = f"{self.base_url}/api/auth/quick-nickname"
        payload = {"nickname": self.nickname}

        try:
            logger.info(f"Tentando login como '{self.nickname}' em {self.base_url}...")
            res = self.session.post(login_url, json=payload, timeout=25)

            if res.status_code == 200:
                data = res.json()
                self.session_token = data.get('sessionToken')
                if self.session_token:
                    self.session.headers['Authorization'] = f"Bearer {self.session_token}"
                logger.info(f"Login realizado com sucesso! Usuário: {data.get('user', {}).get('nickname')}")
                return True
            else:
                logger.error(f"Erro no login ({res.status_code}): {res.text}")
                return False
        except Exception as e:
            logger.error(f"Falha de conexão no login: {e}")
            return False

    def post_message(self, content):
        """Publica uma mensagem no feed do Freedom."""
        post_url = f"{self.base_url}/api/posts"
        payload = {"content": content}

        try:
            res = self.session.post(post_url, json=payload, timeout=25)
            if res.status_code in (200, 201):
                logger.info("Postagem publicada com sucesso!")
                return True
            elif res.status_code == 401:
                logger.warning("Sessão expirada ou não autenticada. Tentando relogar...")
                if self.login():
                    retry_res = self.session.post(post_url, json=payload, timeout=25)
                    return retry_res.status_code in (200, 201)
            else:
                logger.error(f"Erro ao postar ({res.status_code}): {res.text}")
                return False
        except Exception as e:
            logger.error(f"Falha ao enviar post: {e}")
            return False


def start_health_server():
    """Sobe um servidor HTTP mínimo para satisfazer o health check do Koyeb."""
    port = int(os.environ.get('PORT', 8000))

    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')

        def log_message(self, format, *args):  # silencia logs do HTTP
            pass

    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    logger.info(f"Health-check server rodando na porta {port}")
    server.serve_forever()


def run():
    logger.info("=== Iniciando Bot Freedom - obatatoide ===")
    logger.info(f"Servidor: {BASE_URL}")
    logger.info(f"Usuário: {NICKNAME}")
    logger.info(f"Intervalo: {POST_INTERVAL_SECONDS} segundos ({POST_INTERVAL_SECONDS / 60:.1f} minutos)")

    # Inicia o servidor de health-check em background (necessário pro Koyeb)
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    jokes = load_cache()
    if not jokes:
        logger.error("Nenhuma piada disponível. Encerrando bot.")
        return

    posted_history = load_history()
    logger.info(f"Histórico: {len(posted_history)} piadas já postadas anteriormente.")

    bot = FreedomBot(BASE_URL, NICKNAME)
    while not bot.login():
        logger.info("Tentando login novamente em 15 segundos...")
        time.sleep(15)

    while True:
        # Encontra piadas que ainda não foram postadas
        available_jokes = [j for j in jokes if j['hash'] not in posted_history]

        if not available_jokes:
            logger.info("Todas as piadas da lista já foram postadas! Resetando histórico para reiniciar o ciclo...")
            posted_history.clear()
            save_history(posted_history)
            available_jokes = jokes

        # Escolhe aleatoriamente uma piada nunca postada no ciclo
        selected_joke = random.choice(available_jokes)
        joke_text = selected_joke['text']
        joke_hash = selected_joke['hash']

        logger.info(f"\n--- Preparando post (Ano {selected_joke.get('year')}, {len(joke_text)} caracteres) ---")
        preview = joke_text.replace('\n', ' ')
        if len(preview) > 80:
            preview = preview[:77] + '...'
        logger.info(f"Prévia: {preview}")

        success = bot.post_message(joke_text)
        if success:
            posted_history.add(joke_hash)
            save_history(posted_history)
            logger.info(f"Piada registrada no histórico ({len(posted_history)}/{len(jokes)} postadas).")
        else:
            logger.warning("Não foi possível enviar a piada nesta tentativa. Tentará novamente no próximo ciclo.")

        logger.info(f"Aguardando {POST_INTERVAL_SECONDS} segundos até a próxima postagem...\n")
        time.sleep(POST_INTERVAL_SECONDS)


if __name__ == '__main__':
    run()
