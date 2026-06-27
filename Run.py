from DC_DataLoader import DCDataLoader
from DC_WebApp import run_server

if __name__ == '__main__':
    import os
    loader = DCDataLoader()
    # The loader is now aware of config.ini and PyInstaller APP_DIR
    port = int(os.environ.get("PORT", 5000))
    run_server(loader, host="0.0.0.0", port=port, open_browser=False)
