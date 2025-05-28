from flask import (
    Flask,
    render_template,
    Response,
    request,
    jsonify
)

import settings

import sys
import logging

app = Flask(__name__)

logger = logging.getLogger("sand_tray")
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s](%(module)s)[%(levelname)s] %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)



@app.route('/')
def index():
    return render_template('index.html')

log = logging.getLogger('werkzeug')
log.disabled = True
cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: None
logger.info(f"Start HTTP Web Server http://{settings.LISTEN_ADDR}:{settings.HTTP_PORT}/ .")

app.run(host=settings.LISTEN_ADDR, port=settings.HTTP_PORT, debug=True)