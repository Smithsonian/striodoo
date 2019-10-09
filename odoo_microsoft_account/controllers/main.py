# See LICENSE file for full copyright and licensing details.

import logging
import json
import odoo
import http.client as httplib
import simplejson
import werkzeug.utils
from odoo import http
from odoo.http import request
from odoo.addons.auth_oauth.controllers.main import OAuthLogin as Home
from odoo.addons.web.controllers.main import\
    set_cookie_and_redirect, login_and_redirect
from odoo.addons.auth_oauth.controllers.main import\
    fragment_to_query_string

_logger = logging.getLogger(__name__)


class OAuthLogin(Home):

    def list_providers(self):
        try:
            providers = request.env['auth.oauth.provider'].sudo().search_read(
                [('enabled', '=', True)])
            _logger.info("providers " + str(providers))
        except Exception:
            providers = []
        provider_microsoft = request.env.ref(
            'odoo_microsoft_account.provider_microsoft')
        _logger.info("provider_microsoft " + str(provider_microsoft))
        base_url = request.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        _logger.info("base_url " + str(base_url))
        for provider in providers:
            if provider.get('id') == provider_microsoft.id:
                return_url = base_url + '/auth_oauth/microsoft/signin'
                params = dict(
                    client_id=provider['client_id'],
                    response_type='code',
                    redirect_uri=return_url,
                    prompt='select_account',
                    scope=provider['scope'],
                )
                _logger.info("params " + str(params))
            else:
                return_url = base_url + '/auth_oauth/signin'
                state = self.get_state(provider)
                _logger.info("state " + str(state))
                params = dict(
                    response_type='token',
                    client_id=provider['client_id'],
                    redirect_uri=return_url,
                    scope=provider['scope'],
                    state=json.dumps(state),
                )
                _logger.info("params " + str(params))
            provider['auth_link'] = "%s?%s" % (provider['auth_endpoint'],
                                               werkzeug.url_encode(params))
        return providers


class OAuthController(http.Controller):

    @http.route('/auth_oauth/microsoft/signin',
                type='http',
                auth='none',
                csrf=False)
    @fragment_to_query_string
    def microsoft_signin(self, **kw):
        pool = request.env
        root_url = request.env['ir.config_parameter'].sudo().get_param(
            'web.base.url') + '/'
        _logger.info("root_url " + str(root_url))
        _logger.info("kw " + str(kw))
        oauth_provider_rec =\
            pool['ir.model.data'].sudo().get_object_reference(
                'odoo_microsoft_account',
                'provider_microsoft')[1]
        _logger.info("oauth_provider_rec " + str(oauth_provider_rec))
        provider = \
            pool['auth.oauth.provider'].sudo().browse(oauth_provider_rec)
        _logger.info("provider " + str(provider))  
        authorization_data = \
            pool['auth.oauth.provider'].sudo().oauth_token(
                'authorization_code',
                provider,
                kw.get('code'),
                refresh_token=None)
        _logger.info("authorization_data " + str(authorization_data))
        access_token = authorization_data.get('access_token')
        _logger.info("access_token " + str(access_token))
        refresh_token = authorization_data.get('refresh_token')
        _logger.info("refresh_token " + str(refresh_token))
        try:
            conn = httplib.HTTPSConnection(provider.data_endpoint)
            _logger.info("conn " + str(conn))
            conn.request("GET", "/adfs/userinfo", "", {
                'Authorization': 'Bearer '+access_token,
            })
            response = conn.getresponse()
            _logger.info("response.status_code" + str(response.status_code))
            _logger.info("response" + str(response))
            content = response.read().decode('utf-8')
            _logger.info("content" + str(content))
            _logger.info("El valor de response.read() es" + str(content))
            data = simplejson.loads(content)
            _logger.info("data" + str(data))
            displayName = data.get('displayName')
            _logger.info("displayName" + str(displayName))
            mail = data.get('userPrincipalName')
            _logger.info("mail" + str(mail))
            user_id = data.get('id')
            _logger.info("user_id" + str(user_id))
            _logger.info("El valor de data es " + str(data))
            _logger.info("El valor de displayName es " + str(displayName))
            _logger.info("El valor de mail es " + str(mail))
            _logger.info("El valor de user_id es " + str(user_id))
            conn.close()
        except Exception as e:
            _logger.exception("OAuth2: %s" % str(e))
            print(e)
        try:
            credentials = pool['res.users'].sudo().microsoft_auth_oauth(
                provider.id, {
                    'access_token': access_token,
                    'user_id': user_id,
                    'email': mail,
                    'name': displayName,
                    'microsoft_refresh_token': refresh_token
                })
            request.cr.commit()
            return login_and_redirect(*credentials,
                                      redirect_url=root_url + 'web?')
        except AttributeError:
            _logger.error(
                "auth_signup not installed on"
                " database %s: oauth sign up cancelled." % (
                    request.cr.dbname))
            url = "/web/login?oauth_error=1"
        except odoo.exceptions.AccessDenied:
            _logger.info(
                'OAuth2: access denied,'
                ' redirect to main page in case a valid'
                ' session exists, without setting cookies')
            url = "/web/login?oauth_error=3"
            redirect = werkzeug.utils.redirect(url, 303)
            redirect.autocorrect_location_header = False
            return redirect
        except Exception as e:
            _logger.exception("OAuth2: %s" % str(e))
            url = "/web/login?oauth_error=2"
        return set_cookie_and_redirect(root_url + url)
