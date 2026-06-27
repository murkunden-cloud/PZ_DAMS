from DC_DataLoader import DCDataLoader
from DC_WebApp import run_server

if __name__ == '__main__':
    loader = DCDataLoader()
    # The loader is now aware of config.ini and PyInstaller APP_DIR
    run_server(loader, host="127.0.0.1", port=5000, open_browser=True)
