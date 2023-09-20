from odoo import api, fields, tools, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError

class PengajuanJudul(models.Model):
    _name = 'pengajuan.judul'

    name = fields.Char('Judul PKM')
    pkm_id = fields.Many2one('jenis.pkm', string='Bidang PKM')
    pengajuan_id = fields.Many2one('pengajuan', string='Pengajuan')
    creator_id = fields.Many2one('res.users', string='Nama Pengajuan')
    deskripsi_pkm = fields.Char('Deskripsi PKM', help="Deskripsi Dari PKM")
    bidang_ilmu = fields.Char('Bidang Ilmu')
    perguruan_tinggi = fields.Char('Perguruan Tinggi')
    program_studi = fields.Char('Program Studi')
    catatan = fields.Text('Catatan')
    state = fields.Selection([
        ('pengajuan', 'Pengajuan'),
        ('diterima', 'Diterima'),
        ('ditolak', 'Ditolak'),
        ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='pengajuan')
    dospem_id = fields.Many2one('res.users', string='Dosen Pembimbing')
    pengajuan_count = fields.Integer('# Pengajuan', compute='_compute_pengajuan_count')

    def _compute_pengajuan_count(self):
        for rec in self:
            rec.pengajuan_count = self.env['pengajuan'].search_count([('judul_pkm', '=', rec.name)])

    def action_view_pengajuan(self):
        result = self.env["ir.actions.actions"]._for_xml_id('pkm_custom.action_pengajuan')
        context = result['context'] = {'default_creator_id': self.creator_id.id, 'default_judul_pkm': self.name}
        return {
            'type': 'ir.actions.act_window',
            'name': 'Pengajuan',
            'view_mode': 'tree,form',
            'res_model': 'pengajuan',
            'domain' : [('judul_pkm', '=', self.name)],
            'context': context
        }

    @api.model
    def create(self, vals):
        if not vals.get('creator_id'):
            vals['creator_id'] = self.env.user.id
        result = super(PengajuanJudul, self).create(vals)

        return result
    
    def action_terima(self):
        if self.env.user.id != self.dospem_id.id:
            raise UserError(_('Anda Bukan Termasuk Dosen Pembimbing Judul PKM ini.'))
        self.state = 'diterima'
        values = {
            'creator_id' : self.creator_id.id,
            'judul_pkm' : self.name,
            'bidang_ilmu' : self.bidang_ilmu,
            'pkm_id' : self.pkm_id.id,
            'program_studi' : self.program_studi,
            'dospem_id' : self.dospem_id.id,
            
        }
        pengajuan = self.env['pengajuan'].sudo().create(values)
        self.pengajuan_id = pengajuan

    def write(self, values):
        if self.env.user.has_group('pkm_custom.group_pkm_mahasiswa'):
            if self.env.user.id != self.creator_id.id:
                raise ValidationError("Tidak dapat mengubah data orang lain")

        result = super(PengajuanJudul, self).write(values)
        return result
    
    def unlink(self):
        for data in self:
            user = self.env.user
            if not user.has_group('base.group_system'):
                if user.id != data.creator_id.id:
                    raise UserError(_('Anda Tidak Bisa Menghapus Data Orang Lain.'))
            
        return super(PengajuanJudul, self).unlink()