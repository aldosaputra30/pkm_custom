from odoo import api, fields, tools, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
import os
import shutil

class Pengajuan(models.Model):
    _name = 'pengajuan'

    name = fields.Char(string='Kode PKM', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    pkm_id = fields.Many2one('jenis.pkm', string='Bidang PKM')
    creator_id = fields.Many2one('res.users', string='Nama Pengajuan')
    judul_pkm = fields.Char('Judul Kegiatan')
    deskripsi_pkm = fields.Char('Deskripsi PKM', help="Deskripsi Dari PKM")
    line_pengajuan = fields.One2many('pengajuan.line', 'pengajuan_id', 'Tim Pengajuan')
    line_penilaian = fields.One2many('penilaian.bobot', 'pengajuan_id', 'Penilaian')
    bidang_ilmu = fields.Char('Bidang Ilmu')
    perguruan_tinggi = fields.Char('Perguruan Tinggi')
    file = fields.Binary(string="Proposal",attachment=True)
    file_preview = fields.Binary(string="Proposal",attachment=True)
    file_name = fields.Char('Proposal')
    file_revisi = fields.Binary(string="Proposal Revisi",attachment=True)
    file_name_revisi = fields.Char('Proposal Revisi')
    program_studi = fields.Char('Program Studi')
    catatan = fields.Text('Catatan')
    state = fields.Selection([
        ('pengajuan', 'Pengajuan'),
        ('proses', 'Proses'),
        ('diterima', 'Diterima'),
        ('ditolak', 'Ditolak'),
        ('revisi', 'Revisi'),
        ('batal', 'Batal Pengajuan'),
        ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='pengajuan')

    is_done = fields.Boolean('Diterima',copy=False)
    is_reject = fields.Boolean('Ditolak',copy=False)
    is_cancel = fields.Boolean('Batal',copy=False)
    is_revisi = fields.Boolean('Revisi',copy=False)
    dospem_id = fields.Many2one('res.users', string='Dosen Pembimbing')
    reviewer_id = fields.Many2one('res.users', string='Reviewer')

    # def unlink(self):
    #     for data in self:
    #         user = self.env.user
    #         if not user.has_group('base.group_system'):
    #             if user.id != data.creator_id.id:
    #                 raise UserError(_('Anda Tidak Bisa Menghapus Data Orang Lain.'))
            
    #     return super(Pengajuan, self).unlink()
    
    def action_assign_reviewer(self):
        return {'type': 'ir.actions.act_window',
                    'name': _('Tugaskan Kepada Reviewer'),
                    'res_model': 'whatsapp.wizard',
                    'target': 'new',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'context': {
                        'default_template_id': self.env.ref('odoo_whatsapp_integration.whatsapp_purchase_template').id},
                    }

    def action_proses(self):
        for data in self:
            if not data.file:
                raise ValidationError("Masukkan Proposal Terlebih Dahulu")

            if not self.env.user.has_group('base.group_system'):
                if self.env.user.id == data.creator_id.id:
                    data.state = 'proses'
                else:
                    raise ValidationError("Tidak Bisa Mengajukan Data Orang Lain")
            else:
                data.state = 'proses'
    def action_batal(self):
        for data in self:
            if not self.env.user.has_group('base.group_system'):
                if self.env.user.id == data.creator_id.id:
                    data.state = 'batal'
                    data.is_cancel = True
                else:
                    raise ValidationError("Tidak Bisa Membatalkan Pengajuan Orang Lain")
            else:
                data.state = 'batal'
                data.is_cancel = True
                
    def action_terima(self):
        for data in self:
            data.state = 'diterima'
            data.is_done = True
            data.is_cancel = False
            data.is_reject = False
            data.is_revisi = False
            data.inbox_message()

    def action_tolak(self):
        for data in self:
            data.state = 'ditolak'
            data.is_reject = True

    def action_revisi(self):
        for data in self:
            if not data.catatan:
                raise ValidationError("Silahlan Isi Catatan Untuk Revisi")

            data.state = 'revisi'
            data.is_revisi = True

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        # print("data:::",self.context)
        # if self.env.ref('pkm_custom.action_my_pengajuan'):    
        #     args += [('create_uid','=',self.env.user.id)]
        return super(Pengajuan, self).search(args, offset=offset, limit=limit, order=order, count=count)
    
    def inbox_message(self):
        # construct the message that is to be sent to the user
        message_text = f'<strong>Pengajuan ' + self.name + '</strong>'\
                        f'<p>Selamat Pengajuan Anda Diterima</p>'

        # odoo runbot
        odoobot_id = self.env['ir.model.data'].sudo().xmlid_to_res_id("base.partner_root")

        # find if a channel was opened for this user before
        channel = self.env['mail.channel'].sudo().search([
        ('name', '=', 'Pengajuan ' + self.name),
        ('channel_partner_ids', 'in', [self.create_uid.partner_id.id])
        ],
        limit=1,
        )

        if not channel:
            # create a new channel
            channel = self.env['mail.channel'].with_context(mail_create_nosubscribe=True).sudo().create({
            'channel_partner_ids': [(4, odoobot_id), (4, self.create_uid.partner_id.id)],
            'public': 'private',
            'channel_type': 'chat',
            'email_send': False,
            'name': f'Pengajuan ' + self.name,
            'display_name': f'Pengajuan ' + self.name,
            })

        # send a message to the related user
        channel.sudo().message_post(
        body=message_text,
        author_id=odoobot_id,
        message_type="comment",
        subtype_xmlid="mail.mt_comment",
        )
        print("chanell:::::",channel)
    
    def save_samba_folder(self):
        if self.file_preview:
            pdf_name = 'Proposal PKM %s' %self.name
            samba_dir = "/home/administrator/write-able"
            if samba_dir:
                full_path = os.path.join(samba_dir, pdf_name)
                with open(full_path, 'wb') as samba_file:
                    samba_file.write(self.file_preview)


    @api.constrains('file')
    def _check_file(self):
        if self.file and str(self.file_name.split(".")[-1]) != 'pdf' :
            raise ValidationError("Tidak dapat mengunggah file yang berbeda dari file .pdf")

        if self.file_revisi and str(self.file_name_revisi.split(".")[-1]) != 'pdf' :
            raise ValidationError("Tidak dapat mengunggah file yang berbeda dari file .pdf")
        for rec in self:            
            rec.file_preview = rec.file

    # @api.onchange('file')
    # def _check_pdf(self):
    #     if self.file and str(self.file_name.split(".")[-1]) != 'pdf' :
    #         raise ValidationError("Tidak dapat mengunggah file yang berbeda dari file .pdf")

    #     if self.file_revisi and str(self.file_name_revisi.split(".")[-1]) != 'pdf' :
    #         raise ValidationError("Tidak dapat mengunggah file yang berbeda dari file .pdf")
        
    @api.constrains('file_revisi')
    def _check_pdf_revisi(self):
        if self.file_revisi and str(self.file_name_revisi.split(".")[-1]) != 'pdf' :
            raise ValidationError("Tidak dapat mengunggah file yang berbeda dari file .pdf")
        for rec in self:            
            rec.file_preview = rec.file_revisi

    def write(self, values):
        if self.env.user.has_group('pkm_custom.group_pkm_mahasiswa'):
            if self.env.user.id != self.creator_id.id:
                raise ValidationError("Tidak dapat mengubah data orang lain")

        result = super(Pengajuan, self).write(values)
        return result

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('pengajuan') or _('New')
        if not vals.get('creator_id'):
            vals['creator_id'] = self.env.user.id
        result = super(Pengajuan, self).create(vals)
        if result.pkm_id.name == 'PKM Artikel Ilmiah (PKM-AI)':
            result.line_penilaian.create({
            'pengajuan_id': result.id,
            'no' : "1",
            'kriteria': "JUDUL: Kesesuaian isi dan judul artikel.",
            'bobot': "5",
            })
            result.line_penilaian.create({
            'pengajuan_id': result.id,
            'no' : "2",
            'kriteria': "ABSTRAK/ABSTRACT: Latar belakang, Tujuan, Metode, Hasil,Kesimpulan, Kata kunci.",
            'bobot': "10",
            })
            result.line_penilaian.create({
            'pengajuan_id': result.id,
            'no' : "3",
            'kriteria': "PENDAHULUAN: Persoalan yang mendasari pelaksanaan dan uraian dasar keilmuan yang mendukung kemutakhiran substansi kajian.",
            'bobot': "10",
            })
            result.line_penilaian.create({
            'pengajuan_id': result.id,
            'no' : "4",
            'kriteria': "METODE: Kesesuaian dengan persoalan yang telah diselesaikan, Pengembangan metode baru, Penggunaan metode yang sudah ada.",
            'bobot': "25",
            })
            result.line_penilaian.create({
            'pengajuan_id': result.id,
            'no' : "5",
            'kriteria': "HASIL DAN PEMBAHASAN: Kumpulan dan kejelasan penampilan data Proses/teknik pengolahan data, Ketajaman analisis dan sintesis data, Perbandingan hasil dengan hipotesis atau hasil sejenis sebelumnya",
            'bobot': "30",
            })
            result.line_penilaian.create({
            'pengajuan_id': result.id,
            'no' : "6",
            'kriteria': "KESIMPULAN: Tingkat ketercapaian hasil dengan tujuan.",
            'bobot': "10",
            })
            result.line_penilaian.create({
            'pengajuan_id': result.id,
            'no' : "7",
            'kriteria': "DAFTAR PUSTAKA: Ditulis dengan sistem Harvard (nama,tahun), Sesuai dengan uraian sitasi, Kemutakhiran Pustaka.",
            'bobot': "5",
            })
        elif result.pkm_id.name == 'PKM Artikel Ilmiah (PKM-AI)':
            result.line_penilaian.create({
            'pengajuan_id': result.id,
            'no' : "1",
            'kriteria': "Format Artikel: a. Tata tulis: ukuran kertas, tipografi, kerapihan ketik, tata letak, jumlah halaman.  b. Penggunaan Bahasa Indonesia yang baik dan benar.  c. Kesesuaian format penulisan.",
            'bobot': "10",
            })
            result.line_penilaian.create({
            'pengajuan_id': result.id,
            'no' : "2",
            'kriteria': "Gagasan: a. Kreativitas gagasan (visioner/ futuristik, unik, manfaat dan dampak sistemik).  b. Kelayakan realisasi.  c. Ruang lingkup/skala permasalahan yang ditangani.",
            'bobot': "35",
            })
            result.line_penilaian.create({
            'pengajuan_id': result.id,
            'no' : "3",
            'kriteria': "Tahapan solusi yang ditawarkan dan prediksi keberhasilan. a. Ketepatan solusi. b. Pemanfaatan iptek.  c. Keterlibatan pihak terkait.",
            'bobot': "30",
            })
            result.line_penilaian.create({
            'pengajuan_id': result.id,
            'no' : "4",
            'kriteria': "Sumber informasi: a. Kesesuaian sumber informasi dengan gagasan yang ditawarkan.  b. Akurasi dan kemutakhiran sumber informasi.",
            'bobot': "15",
            })
            result.line_penilaian.create({
            'pengajuan_id': result.id,
            'no' : "5",
            'kriteria': "Kesimpulan: Prediksi dampak terealisasikannya gagasan",
            'bobot': "10",
            })            

        elif result.pkm_id.name == 'PKM Kewirausahaan (PKM-K)':
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'kriteria': "Kreativitas",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "1",
                'kriteria': "Gagasan Usaha (analisis peluang pasar, dukungan sumber data yang berkualitas)",
                'bobot': "15",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'kriteria': "Keunggulan Produk (berbasis iptek, unik, dan bermanfaat)",
                'bobot': "20",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "2",
                'kriteria': "Rancangan Usaha",
                'bobot': "20",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'kriteria': "Potensi Program",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "3",
                'kriteria': "Potensi Pelaksanaan dan Perolehan Profit",
                'bobot': "20",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'kriteria': "Potensi Keberlanjutan Usaha",
                'bobot': "15",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "4",
                'kriteria': "Penjadwalan Kegiatan dan Personalia (lengkap,jelas,waktu dan personalianya sesuai)",
                'bobot': "5",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "5",
                'kriteria': "Penyusun Anggaran Biaya (lengkap,rinci, wajar dan jelas peruntukannya)",
                'bobot': "5",
                })
        elif result.pkm_id.name == 'PKM Karsa Cipta (PKM-KC)':
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'kriteria': "Kreativitas",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "1",
                'kriteria': "Gagasan (orisinalitas, unik dan manfaat masa depan)",
                'bobot': "20",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'kriteria': "Kemutakhiran Iptek yang Diadopsi",
                'bobot': "20",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "2",
                'kriteria': "Kesesuaian Tahap Pelaksanaan",
                'bobot': "15",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'kriteria': "Potensi Program:",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "3",
                'kriteria': "Kontribusi Produk Luaran Terhadap Perkembangan Iptek",
                'bobot': "25",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'kriteria': "Potensi Publikasi Artikel Ilmiah/KI",
                'bobot': "10",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "4",
                'kriteria': "Penjadwalan Kegiatan dan Personalia (lengkap, jelas, waktu, dan personalianya sesuai)",
                'bobot': "5",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "5",
                'kriteria': "Penyusunan Anggaran Biaya (lengkap, rinci, wajar dan jelas peruntukannya)",
                'bobot': "5",
                })
        elif result.pkm_id.name == 'PKM Karya Inovatif (PKM-KI)':
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'kriteria': "Kreativitas:",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "1",
                'kriteria': "Urgensi Permasalahan, Cakupan Pengguna",
                'bobot': "15",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'kriteria': "Kreativitas Gagasan Solusi (orisinalitas, problem based, specific, measurable)",
                'bobot': "25",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "2",
                'kriteria': "Kesesuaian Tahap Pelaksanaan",
                'bobot': "15",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'kriteria': "Potensi Produk (dampak ekonomi nasional)",
                'bobot': "10",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "3",
                'kriteria': "Ketepatan Iptek, Standar, Regulasi dan Metode yang Digunakan ",
                'bobot': "25",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "4",
                'kriteria': "Penjadwalan Kegiatan dan Personalia (lengkap, jelas, dan personalianya sesuai)",
                'bobot': "5",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "5",
                'kriteria': "Penyusunan Anggaran Biaya (lengkap, rinci, wajar dan jelas peruntukannya)",
                'bobot': "5",
                })
        elif result.pkm_id.name == 'PKM Penerapan IPTEK (PKM-PI)':
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'kriteria': "Kreativitas:",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "1",
                'kriteria': "Identifikasi Permasalahan atau Kebutuhan Mitra",
                'bobot': "10",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'kriteria': "Ketepatan Solusi yang Ditawarkan",
                'bobot': "20",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "2",
                'kriteria': "Ketepatan Mitra Program",
                'bobot': "15",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'kriteria': "Potensi Program:",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "3",
                'kriteria': "Potensi Nilai Tambah untuk Mitra Program",
                'bobot': "25",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'kriteria': "Potensi Keberlanjutan Program",
                'bobot': "20",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "4",
                'kriteria': "Penjadwalan Kegiatan dan Personalia (lengkap, jelas, waktu, dan personalianya sesuai)",
                'bobot': "5",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "5",
                'kriteria': "Penyusunan Anggaran Biaya (lengkap, rinci, wajar dan jelas peruntukannya)",
                'bobot': "5",
                })
        elif result.pkm_id.name == 'PKM Pengabdian Masyarakat(PKM-PM)':
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'kriteria': "Kreativitas:",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "1",
                'kriteria': "Perumusan Masalah",
                'bobot': "10",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'kriteria': "Ketepatan Solusi (fokus dan atraktif)",
                'bobot': "20",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "2",
                'kriteria': "Ketepatan Masyarakat Mitra dan Kondisi Existing Mitra",
                'bobot': "15",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'kriteria': "Potensi Program:",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "3",
                'kriteria': "Potensi Nilai Tambah untuk Mitra Program",
                'bobot': "25",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'kriteria': "Potensi Keberlanjutan Program",
                'bobot': "20",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "4",
                'kriteria': "Penjadwalan Kegiatan dan Personalia (lengkap, jelas, waktu, dan personalianya sesuai)",
                'bobot': "5",
                })
            result.line_penilaian.create({
                'pengajuan_id': result.id,
                'no': "5",
                'kriteria': "Penyusunan Anggaran Biaya (lengkap, rinci, wajar dan jelas peruntukannya)",
                'bobot': "5",
                })

        return result

class PengajuanLine(models.Model):
    _name = 'pengajuan.line'

    pengajuan_id = fields.Many2one('pengajuan')
    nama_anggota = fields.Char('Nama Anggota')
    kelas = fields.Char('Kelas')
    jurusan = fields.Char('Jurusan')
    nim = fields.Integer('Nim')
    nomor_hp = fields.Char('Nomor Handphone')

class PenilaianBobot(models.Model):
    _name = 'penilaian.bobot'

    pengajuan_id = fields.Many2one('pengajuan')
    no = fields.Char('No')
    kriteria = fields.Char('Kriteria')
    bobot = fields.Char('Bobot')
    skor = fields.Char('Skor')
    nilai = fields.Char('Nilai')
    # nomor_hp = fields.Char('Nomor Handphone')