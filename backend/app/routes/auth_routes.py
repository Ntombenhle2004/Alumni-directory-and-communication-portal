from flask import Blueprint, request, jsonify

auth = Blueprint('auth', __name__)

@auth.route("/test")
def test():
    return jsonify({"message": "Auth routes working"})