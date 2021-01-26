from helpers import config
from requests.api import request
from urllib.parse import urlencode
import requests
import secrets
import string
import logging
import json
import os
from flask import (
    abort,
    Flask,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from datetime import datetime, timedelta, timezone as datetime_timezone


app = Flask(__name__)
app.secret_key = secrets.token_hex(config.SESSION_SECRET_KEY_LENGTH)


def _create_future_timestamp_from_seconds(seconds_from_current_time):
    current_timestamp = datetime.utcnow().replace(
        tzinfo=datetime_timezone.utc)
    future_timestamp = current_timestamp + \
        timedelta(seconds=seconds_from_current_time)
    return future_timestamp


@app.route('/', methods=['OPTIONS'])
def options():
    return {}, 200


@app.route('/login', methods=['GET'])
def login():
    auth_state = ''.join(secrets.choice(
        string.ascii_letters + string.digits) for i in range(config.RANDOM_STRING_STATE_LENGTH))
    payload = {
        'client_id': config.CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': config.REDIRECT_URI,
        'scope': config.LOGIN_SCOPE,
        'state': auth_state,
        'show_dialog': True
    }
    response = make_response(
        redirect(f'{config.SPOTIFY_LOGIN_URL}/?{urlencode(payload)}'))
    response.set_cookie(config.SPOTIFY_STATE_COOKIE_NAME, auth_state)
    app.logger.info('\nlogin url response: ', response)
    return response

    # response = requests.get(
    #     url=config.SPOTIFY_LOGIN_URL + '/?' + urlencode(req_params))
    # print('\nspotify login url call resp: ', response.next)
    # return response.text, 200


@app.route('/callback', methods=['GET'])
def callback():
    '''OAuth Callback'''

    error = request.args.get('error')
    code = request.args.get('code')
    state = request.args.get('state')
    stored_state = request.cookies.get(config.SPOTIFY_STATE_COOKIE_NAME)

    if state is None or state != stored_state:
        app.logger.error('Error message: ', repr(error))
        return {'error': error}, 400

    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': config.REDIRECT_URI,
    }
    response = requests.post(url=config.SPOTIFY_TOKEN_URL, data=payload, auth=(
        config.CLIENT_ID, config.CLIENT_SECRET))
    response_data = response.json()

    if response.status_code != 200 or response_data.get('error'):
        app.logger.error(
            'Failed to receive token: ', response_data.get('error'))
        return {'error': response_data.get('error')}, response.status_code

    app.logger.info('\ntoken url response: ', response_data)

    session['tokens'] = {
        'access_token': response_data.get('access_token'),
        'refresh_token': response_data.get('refresh_token'),
        'token_expiry_timestamp': _create_future_timestamp_from_seconds(response_data.get('expires_in'))
    }

    return 'Success', 200


@app.route('/refresh')
def refresh():
    '''Refresh access token.'''

    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': session.get('tokens').get('refresh_token'),
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.post(url=config.SPOTIFY_TOKEN_URL, data=payload, auth=(
        config.CLIENT_ID, config.CLIENT_SECRET), headers=headers)
    response_data = response.json()
    app.logger.info('\nrefresh url response: ', response_data)

    session['tokens']['access_token'] = response_data.get('access_token')
    if response_data.get('refresh_token') is not None and response_data.get('refresh_token') != session['tokens'].get('refresh_token'):
        session['tokens']['refresh_token'] = response_data.get('refresh_token')
        session['tokens']['token_expiry_timestamp'] = _create_future_timestamp_from_seconds(
            response_data.get('expires_in'))

    return json.dumps(session['tokens'])
