import uuid
import jwt

import requests

from config.settings import SECRETS_FULL

UP_BIT_KEY = SECRETS_FULL['UP_BIT_KEY']
access_key = UP_BIT_KEY['access_key']
secret_key = UP_BIT_KEY['secret_key']

server_url = 'https://api.upbit.com'
payload = {
    'access_key': access_key,
    'nonce': str(uuid.uuid4()),
}
jwt_token = jwt.encode(payload, secret_key)
authorize_token = 'Bearer {}'.format(jwt_token)
headers = {"Authorization": authorize_token}
res = requests.get(server_url + "/v1/status/wallet", headers=headers)
print(res.status_code)
print('withdraw api ', res.text)