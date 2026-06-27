import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from DC_DataLoader import DCDataLoader
from DC_WebApp import create_app

# Initialize the data loader
loader = DCDataLoader()

# Create the Flask app
app = create_app(loader)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
