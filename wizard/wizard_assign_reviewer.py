from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError

class AssignReviewer(models.TransientModel):
	_name = 'assign.reviewer'

	reviewer_id = fields.Many2one('res.users', string='Reviewer')

	def assign_to_reviewer(self):
		# context = self._context
		pengajuan = self.env['pengajuan'].browse(self.env.context.get('active_ids'))
		for rec in pengajuan:
			rec.reviewer_id = self.reviewer_id.id
			print('pengajuan:::',pengajuan.id)
		# print('ctx:::',context)
		# pengajuan = self.env['pengajuan']