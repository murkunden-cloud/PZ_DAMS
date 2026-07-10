import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import traceback

try:
    from DC_DataLoader import DCDataLoader
    from DC_WebApp import create_app
    loader = DCDataLoader()
    success = True
except Exception as e:
    err_str = traceback.format_exc()
    success = False

if success:
    app = create_app(loader)
else:
    from flask import Flask
    app = Flask(__name__)
    
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def catch_all(path):
        return f"<pre>Initialization Error:\n{err_str}</pre>", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
