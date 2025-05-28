from flask import (
    Flask,
    render_template,
    Response,
    request,
    jsonify
)

import settings

import sys
import json
import pathlib
import logging

BASE_DIR = pathlib.Path(__file__).parent

class SandTray:

    def __init__(self):
        
        self.app = Flask(__name__)

        self.logger = logging.getLogger("sand_tray")
        self.logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(asctime)s](%(module)s)[%(levelname)s] %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        with open(BASE_DIR / "data" / "element.json", "r") as fp:
            self.elements = json.loads(fp.read())
    
    def web_server(self):

        @self.app.route('/')
        def index():
            return render_template('index.html')

        @self.app.route('/play/')
        def play():
            return render_template('play.html')

        @self.app.route('/api/get_elements')
        def get_elements():
            return jsonify(self.elements)

    def web_server_runner(self):

        self.web_server()

        log = logging.getLogger('werkzeug')
        log.disabled = True
        cli = sys.modules['flask.cli']
        cli.show_server_banner = lambda *x: None
        self.logger.info(f"Start HTTP Web Server http://{settings.LISTEN_ADDR}:{settings.HTTP_PORT}/ .")

        self.app.run(host=settings.LISTEN_ADDR, port=settings.HTTP_PORT, debug=True)

SandTray().web_server_runner()
