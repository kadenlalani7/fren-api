from flask import Flask
from prices_api import get_purchase_data
from config import DevelopmentConfig, ProductionConfig

app = Flask(__name__)

# Configure the app based on the environment
if app.debug:
    app.config.from_object(DevelopmentConfig)
else:
    app.config.from_object(ProductionConfig)

# Define routes
@app.route('/get_purchase_data/<address>', methods=['GET'])
def get_purchase_data_route(address):
    return get_purchase_data(address)
