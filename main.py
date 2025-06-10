from flask import (
    Flask,
    render_template,
    Response,
    request,
    jsonify
)

import sys
import json
import logging
import asyncio
import websockets
import threading
from jinja2 import Template

from api import get_ai_response, get_ai_response_stream
from settings import BASE_DIR, HTTP_PORT, WS_PORT, LISTEN_ADDR

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
        
        self.system_prompt = self.read_prompt("system")
        self.elements_prompt = self.read_prompt("elements")
    
    def read_prompt(self, name):
        template = None
        with open(BASE_DIR / "prompt" / f"{name}.txt", "r", encoding = "utf-8") as fp:
            template = Template(fp.read())

        return template
    
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
    
    def ws_server(self):

        async def websocket_handler(websocket, path):
            if path == "/api/analyse":
                try:

                    self.logger.info("Recived new analyse request.")
                    message = await websocket.recv()
                    data = json.loads(message)

                    async for i in get_ai_response_stream([
                        {"role": "system", "content": self.system_prompt.render({})},
                        {"role": "user", "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": data["picture"]
                                },
                            },
                            {"type": "text", "text": self.elements_prompt.render({"elements": data["objects"]})},
                        ]}
                    ], "vison"):
                        await websocket.send(json.dumps({"status": "success", "content": i}))

                    await websocket.send(json.dumps({"status": "end", "content": ""}))

                except (websockets.exceptions.ConnectionClosedOK,websockets.exceptions.ConnectionClosedError):
                    self.logger.warning("websockets connection closed.")

        def start_websocket_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            start_server = websockets.serve(websocket_handler, LISTEN_ADDR, WS_PORT)
            loop.run_until_complete(start_server)
            loop.run_forever()

        websocket_thread = threading.Thread(target=start_websocket_server)
        websocket_thread.daemon = True
        websocket_thread.start()
        self.logger.info(f"Started WebSocket Thread in Port {WS_PORT}.")

    def web_server_runner(self):

        self.web_server()

        log = logging.getLogger('werkzeug')
        log.disabled = True
        cli = sys.modules['flask.cli']
        cli.show_server_banner = lambda *x: None
        self.logger.info(f"Start HTTP Web Server http://{LISTEN_ADDR}:{HTTP_PORT}/ .")

        self.app.run(host=LISTEN_ADDR, port=HTTP_PORT, debug=False)

sandtray = SandTray()
sandtray.ws_server()
sandtray.web_server_runner()