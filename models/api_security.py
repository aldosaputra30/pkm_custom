from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
import random
import string

class ApiSecurity(models.Model):
    _name = 'api.security'

    name = fields.Char('API Key Token')

    def Config(self):
        api = self.env[self._name].sudo().search([], limit=1)
        return api

    def auto_change_api_key(self):
        api_security = self.env[self._name].sudo().search([], limit=1)
        letters = string.ascii_lowercase
        api_key = ''
        for data in range(4):
            result_str = ''.join(random.choice(letters) for i in range(4))
            if not api_key: 
                api_key = result_str
            else:
                api_key += '-'+ result_str
        api_security.name = api_key  