# -*- coding: utf-8 -*-

import requests

from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient


import logging
_logger = logging.getLogger(__name__)


class RestAPI:
	def __init__(self):
		self.url = 'https://stri-pruebasclasscode-1373171.dev.odoo.co'
		self.client_id = 'r1er4U1Gm4UwteXvsKmfEM93X4oNev'
		self.client_secret = '11cYHtKNcTHTfsRyCY0Stz9Pxjtg0F'
		self.client = BackendApplicationClient(client_id=self.client_id)
		self.oauth = OAuth2Session(client=self.client)

	def route(self, url):
		if url.startswith('/'):
			url = "%s%s" % (self.url, url)
		return url

	def authenticate(self):
		self.oauth.fetch_token(
			token_url=self.route('/api/authentication/oauth2/token'),
			client_id=self.client_id, client_secret=self.client_secret
		)

	def execute(self, enpoint, type="GET", data={}):
		if type == "POST":
			response = self.oauth.post(self.route(enpoint), data=data)
		elif type == "PUT":
			response = self.oauth.put(self.route(enpoint), data=data)
		elif type == "DELETE":
			response = self.oauth.delete(self.route(enpoint), data=data)
		else:
			response = self.oauth.get(self.route(enpoint), data=data)
		if response.status_code != 200:
			raise Exception(logging.info(str(response.json())))
		else:
			return response.json()