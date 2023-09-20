from dataclasses import field
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError

class ResUsers(models.Model):
    _inherit = 'res.users'

    role = fields.Selection([('mahasiswa', 'Mahasiswa'),('reviewer', 'Reviewer'),('dosen_pembimbing', 'Dosen Pembimbing'),('admin', 'Admin')])    
    jenis_kelamin = fields.Selection([('laki_laki', 'Laki-Laki'),('perempuan', 'Perempuan')])
    create_new_pass = fields.Char(string="Create New Password", default='') 

    # is_mahasiswa = fields.Boolean(compute='_compute_role',store=True)
    # is_admin = fields.Boolean(compute='_compute_role',store=True)
    # is_reviewer = fields.Boolean(compute='_compute_role',store=True)
    # is_dospem = fields.Boolean(compute='_compute_role',store=True)

    def remove_mahasiswa_group(self):
        commission_group = self.env.ref('pkm_custom.group_pkm_mahasiswa')
        # users = self.env['res.users'].search([])
        # for data in users:
        #     data.write({'lang' : 'id_ID'})
        print("commission_group::::",commission_group.users, self.env.user.id)
        # for data in commission_group.users:
        #     if data.id == self.env.user.id:
        #         print("remove")
        #         commission_group.write({'users': False})
        # # commission_group.write({'users': [(4, 20)]}) 
        # print("commission_group::::",commission_group.users)
        
        # commission_group.write({'users': [(4, False)]})

    def set_mahasiswa_group(self, user):
        commission_group = self.env.ref('pkm_custom.group_pkm_mahasiswa')
        commission_group.write({'users': [(4, user.id)]})
        # user.write({'role': 'mahasiswa'})
        # return True

    def set_reviewer_group(self, user):
        commission_group = self.env.ref('pkm_custom.group_pkm_reviewer')
        commission_group.write({'users': [(4, user.id)]})
        # user.write({'role': 'reviewer'})
        # return True

    def set_admin_group(self, user):
        commission_group = self.env.ref('pkm_custom.group_pkm_admin')
        commission_group.write({'users': [(4, user.id)]})
        commission_group_admin = self.env.ref('base.group_system')
        print("commission_group_admin:::",commission_group_admin)
        commission_group_admin.write({'users': [(4, user.id)]})
        # user.write({'role': 'admin'})
        # return True

    def set_dospem_group(self, user):
        commission_group = self.env.ref('pkm_custom.group_pkm_dospem')
        commission_group.write({'users': [(4, user.id)]})
        # user.write({'role': 'dosen_pembimbing'})
        # return True

    @api.model
    def create(self, values):
        user = super(ResUsers, self).create(values)

        if values.get('create_new_pass'):
            self.create_new_password(user_id=user, new_passwd=values['create_new_pass'])
        user.write({'create_new_pass': '####'}) 
        # context = self._context and self._context.copy() or {}
        user.write({'lang' : 'id_ID'})
        print(user.password)
        if user.role == 'mahasiswa':
            user.set_mahasiswa_group(user)
        elif user.role == 'reviewer':
            user.set_reviewer_group(user)
        elif user.role == 'admin':
            user.set_admin_group(user)
        elif user.role == 'dosen_pembimbing':
            user.set_dospem_group(user)
        return user

    def create_new_password(self, user_id, new_passwd):
        print("test_print")
        if new_passwd:
            # use self.env.user here, because it has uid=SUPERUSER_ID
            user_id.write({'password': new_passwd})
            return user_id
        raise UserError(_("Setting empty passwords is not allowed for security reasons!"))

    # @api.depends('role')
    # def _compute_role(self):
    #     # user = self.env.user
    #     for user in self:
    #         print("user:::",user)
    #         if user.role == 'mahasiswa':
    #             user.is_mahasiswa = True
    #             user.set_mahasiswa_group(user)
    #             user.write({'role': 'mahasiswa'})
    #         elif user.role == 'reviewer':
    #             user.is_reviewer = True
    #             user.set_reviewer_group(user)
    #             user.write({'role': 'reviewer'})
    #         elif user.role == 'admin':
    #             user.is_admin = True
    #             user.set_admin_group(user)
    #             user.write({'role': 'admin'})
    #         elif user.role == 'dosen_pembimbing':
    #             user.is_dospem = True
    #             user.set_dospem_group(user)
    #             user.write({'role': 'dosen_pembimbing'})
    #         else:
    #             user.is_admin = False
    #             user.is_mahasiswa = False
    #             user.is_reviewer = False
    #             user.is_dospem = False

