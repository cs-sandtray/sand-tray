import shutil
import yaml
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SETTING = None
yaml_path = BASE_DIR / 'setting.yaml'
example_path = BASE_DIR / 'setting.yaml.example'

if not yaml_path.exists():
    shutil.copyfile(example_path, yaml_path)

with open(yaml_path, 'r', encoding='utf-8') as fp:
    SETTING = yaml.safe_load(fp)

BASE_DIR = BASE_DIR
LISTEN_ADDR = SETTING["listen-addr"]
HTTP_PORT = SETTING["http-port"]
WS_PORT = SETTING["ws-port"]

PROXY_WS_PORT = SETTING.get("proxy-ws-port", WS_PORT)
PROXY_LISTEN_ADDR = SETTING.get("proxy-listen-addr", LISTEN_ADDR)

API_KEY_TEXT = SETTING["api-key-text"]
BASE_URL_TEXT = SETTING["base-url-text"]
MODEL_NAME_TEXT = SETTING["model-name-text"]

API_KEY_VISION = SETTING["api-key-vision"]
BASE_URL_VISION = SETTING["base-url-vision"]
MODEL_NAME_VISION = SETTING["model-name-vision"]
