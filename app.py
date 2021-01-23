import os
from flask import Flask
from flask import request

app = Flask(__name__)


@app.route('/', methods=['OPTIONS'])
def options():
    return {}, 200


@app.route('/hello', methods=['POST'])
def main():
    print('\nHello World')
    return {'response': 'hello'}, 200
