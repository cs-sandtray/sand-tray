from flask import (
    Flask,
    render_template,
    Response,
    request,
    jsonify
)

import os
import re
import sys
import json
import time
import uuid
import base64
import logging
import asyncio
import websockets
import threading
from jinja2 import Template

from api import get_ai_response, get_ai_response_stream
from settings import BASE_DIR, HTTP_PORT, WS_PORT, LISTEN_ADDR, PROXY_LISTEN_ADDR, PROXY_WS_PORT

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

        self.elements_psychological = {}
        for i in self.elements.values():
            for j in i:
                self.elements_psychological[j["pic_name"]] = j["psychological"]

        self.system_prompt = self.read_prompt("system")
        self.elements_prompt = self.read_prompt("elements")

        self.img_cache = {}
    
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
            return render_template('play.html', WS_PORT = PROXY_WS_PORT, LISTEN_ADDR = PROXY_LISTEN_ADDR)

        @self.app.route('/api/get_elements')
        def get_elements():
            return jsonify(self.elements)
        
        @self.app.route('/api/upload_img', methods=['POST'])
        def upload_img():
            img_data = request.get_json().get('img_data')
            uid = uuid.uuid4().__str__()
            self.img_cache[uid] = img_data
            return jsonify({"uid": uid})
        
        @self.app.route('/api/suggest', methods=['POST'])
        def suggest():
            data = request.get_json()
            fname = str(time.time())
            os.mkdir(BASE_DIR / "user_data" / fname)

            with open(BASE_DIR / "user_data" / fname / "elements.json", "w+") as fp:
                fp.write(json.dumps(data["objects"]))

            with open(BASE_DIR / "user_data" / fname / "suggestion.txt", "w+") as fp:
                fp.write(data["content"])

            with open(BASE_DIR / "user_data" / fname / "airesponse.txt", "w+") as fp:
                fp.write(data["airesponse"])
            
            match = re.match(r'data:image/(?P<ext>.*?);base64,(?P<data>.*)', data["img_data"], re.DOTALL)
            if match:
                ext = match.group('ext')
                data = match.group('data')
                img_data = base64.b64decode(data)

                filename = f"output_image.{ext}"
                with open(BASE_DIR / "user_data" / fname / filename, 'wb+') as f:
                    f.write(img_data)
            
            return jsonify({"status": "success"})
    
    def ws_server(self):

        async def websocket_handler(websocket, path):
            if path == "/api/analyse":
                try:

                    self.logger.info("Recived new analyse request.")
                    message = await websocket.recv()
                    data = json.loads(message)

                    self.logger.debug("Recived data from client: {message}")

                    # Bound the element name and psychological
                    for i in data["objects"]:
                        i["psychological"] = self.elements_psychological[i["pic_name"]]

                    async for i in get_ai_response_stream([
                        {"role": "system", "content": self.system_prompt.render({})},
                        {"role": "user", "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": self.img_cache[data["picture"]]
                                },
                            },
                            {"type": "text", "text": self.elements_prompt.render({"elements": data["objects"]})},
                        ]}
                    ], "vison"):
                        await websocket.send(json.dumps({"status": "success", "content": i}))

                    await websocket.send(json.dumps({"status": "end", "content": ""}))
                    del self.img_cache[data["picture"]]

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