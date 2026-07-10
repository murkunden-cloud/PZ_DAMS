import os
import sys
import traceback

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def initialize_app():
    try:
        from DC_DataLoader import DCDataLoader
        from DC_WebApp import create_app

        # Initialize the data loader
        loader = DCDataLoader()

        # Create the Flask app
        return create_app(loader)
    except Exception as e:
        err_str = traceback.format_exc()
        from flask import Flask
        error_app = Flask(__name__)
        
        @error_app.route("/", defaults={"path": ""})
        @error_app.route("/<path:path>")
        def catch_all(path):
            return f"<pre>Initialization Error:\n{err_str}</pre>", 500
        return error_app

# Top-level assignment for Vercel's strict builder
app = initialize_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
