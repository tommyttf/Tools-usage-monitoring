import os
import json

from connexion import FlaskApp
from connexion.lifecycle import ConnexionRequest, ConnexionResponse

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

load_dotenv()


def not_found() -> ConnexionResponse:
    return ConnexionResponse(status_code=404, body=json.dumps({"error": "Not Found"}))


def duplicate_key(request: ConnexionRequest, exc: Exception) -> ConnexionResponse:
    return ConnexionResponse(status_code=409, body=json.dumps({"error": "Duplicate Key", "detail": exc.args}))


def unprocessable_entity(request: ConnexionRequest, exc: Exception) -> ConnexionResponse:
    return ConnexionResponse(status_code=422, body=json.dumps({"error": "Unprocessable Entity", "detail": exc.args}))


# setup server app
app = FlaskApp(__name__, specification_dir="./", strict_validation=True)
app.add_api("swagger.yml", strict_validation=True)
app.add_error_handler(FileNotFoundError, not_found)
app.add_error_handler(404, not_found)
app.add_error_handler(DuplicateKeyError, duplicate_key)
app.add_error_handler(ValueError, unprocessable_entity)


#  setup mongodb
client = MongoClient(os.getenv("MONGO_URI"))
db = client.get_default_database()
logs = db.get_collection("logs")

if __name__ == "__main__":
    app.run(port=int(os.getenv('PORT', 8000)))
