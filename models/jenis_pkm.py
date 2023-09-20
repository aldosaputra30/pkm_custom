from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError

class JenisPkm(models.Model):
	_name = 'jenis.pkm'

	name = fields.Char('Jenis PKM')
	# kode_pkm = fields.Char('Kode PKM')

