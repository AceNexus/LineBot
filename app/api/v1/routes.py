from flask import Blueprint, jsonify

api_v1_blueprint = Blueprint('api_v1', __name__)


@api_v1_blueprint.route('/hello', methods=['GET'])
def hello_world():
    return jsonify({"message": "Hello World V1!"}), 200
