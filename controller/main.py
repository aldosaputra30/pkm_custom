# -*- coding: utf-8 -*- 
import time
import string
import urllib
import io
import tempfile
import csv
import xlrd
import re
import sys

import os
from openpyxl import Workbook  
from openpyxl.styles import Border, Side, PatternFill, Font, GradientFill, Alignment, NamedStyle

import werkzeug
from werkzeug.urls import url_encode

import json
import logging
import base64
import datetime
import odoo
import odoo.modules.registry
from odoo.tools.translate import _
from odoo.tools.safe_eval import safe_eval
from odoo import http 
from odoo.exceptions import AccessError, UserError
import ast
from odoo.tools import float_is_zero, ustr
from odoo.http import content_disposition, dispatch_rpc, request, \
    serialize_exception as _serialize_exception, Response

import mimetypes
from odoo.tools.mimetypes import guess_mimetype
from dateutil.parser import parse
from operator import itemgetter

# from odoo.addons.web.controllers.main import Home as HomeLogin
from odoo.addons.website.controllers.main import Website
from odoo.addons.web.controllers.main import Home, ensure_db
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager 

class Pengajuan(http.Controller):
    def check_required_fields(self, required_fields,post={}):
        env = request.env(user=odoo.SUPERUSER_ID)
        has_error = []
        is_valid = True
        for field in required_fields:
            if field not in post:
                has_error +=[field]
        if has_error:
            is_valid = False

        return is_valid

    def check_validation_token(self, config, post={}):
        is_valid = False
        env = request.env(user=odoo.SUPERUSER_ID)
        token = post.get('token',False)
        print('token :::',token,config.name)
        if config.name:
            if token == config.name:
                return True
        return is_valid


    @http.route(['/api/get/pengajuan'], auth='public', type='json', methods=['GET','POST'],csrf=False)
    def get_pengajuan(self, **post):
        env = request.env(user=odoo.SUPERUSER_ID)
        config = env['api.security'].Config()
        
        has_error = []
        required_fields = ['token','username','password']
        login = post.get('username')
        password = post.get('password')
        is_valid_fields = self.check_required_fields(required_fields,post=post)
        if not is_valid_fields:
            has_error += ['is_valid_fields']
            response = {"error" : 400, "description" : "InvalidRequest"}

        if not has_error:
            is_valid_token = self.check_validation_token(config=config, post=post)
            if not is_valid_token:
                has_error += ['is_valid_token']
                response = {"error" : 400, "description" : "InvalidRequest"}
        
        if not has_error:
            user_id = request.session.authenticate(request.session.db, login, password)
            if not user_id:
                has_error += ['user_id']
                response = {"error" : 400, "description" : "Wrong Login or Password"}

            pengajuan_obj = env['pengajuan'].sudo().search([])
            pengajuan = []
            for data in pengajuan_obj:
                vals = {"id":data.id,'name': data.name,'judul_pkm': data.judul_pkm}
                pengajuan.append(vals)
            response = {'status_code': 200, 'message':'Success' ,'pengajuan': pengajuan}
            headers = {'Access-Control-Allow-Origin': '*'}
            body = response
        return response
    @http.route(['/api/get/token'], auth='public', type='json', methods=['GET','POST'],csrf=False)
    def get_token(self, **post):
        env = request.env(user=odoo.SUPERUSER_ID)
        config = env['api.security'].Config()
        
        has_error = []
        required_fields = ['username','password']
        login = post.get('username')
        password = post.get('password')
        is_valid_fields = self.check_required_fields(required_fields,post=post)
        if not is_valid_fields:
            has_error += ['is_valid_fields']
            response = {"error" : 400, "description" : "InvalidRequest"}

        if not has_error:
            user_id = request.session.authenticate(request.session.db, login, password)
            if not user_id:
                has_error += ['user_id']
                response = {"error" : 400, "description" : "Wrong Login or Password"}
            if not has_error:
                response = {'status_code': 200, 'message':'Success' ,'token': config.name}
                headers = {'Access-Control-Allow-Origin': '*'}
                body = response
        return response

    @http.route(['/api/get/pengajuan-http'], auth='public', type='http', methods=['GET','POST'],csrf=False)
    def get_pengajuan(self, **post):
        env = request.env(user=odoo.SUPERUSER_ID)
        pengajuan_obj = env['pengajuan'].sudo().search([])
        pengajuan = []
        for data in pengajuan_obj:
            vals = {"id":data.id,'name': data.name,'judul_pkm': data.judul_pkm or ''}
            pengajuan.append(vals)
        response = {'status_code': 200, 'message':'Success' ,'pengajuan': pengajuan}
        headers = {'Access-Control-Allow-Origin': '*'}
        body = response
        return Response(json.dumps(pengajuan), headers=headers)

    @http.route(['/api/get/dospem-http'], auth='public', type='http', methods=['GET','POST'],csrf=False)
    def get_dospem_http(self, **post):
        env = request.env(user=odoo.SUPERUSER_ID)
        dospem_ids = request.env['res.users'].sudo().search([('role','=','dosen_pembimbing')])
        dosen_pembimbing = []
        for data in dospem_ids:
            vals = {"id":data.id,'nama_dosen': data.name}
            dosen_pembimbing.append(vals)
        response = {'status_code': 200, 'message':'Success' ,'dosen_pembimbing': dosen_pembimbing}
        headers = {'Access-Control-Allow-Origin': '*'}
        body = response
        return Response(json.dumps(dosen_pembimbing), headers=headers)
    
    @http.route(['/api/get/jenis-pkm-http'], auth='public', type='http', methods=['GET','POST'],csrf=False)
    def get_jenis_pkm_http(self, **post):
        env = request.env(user=odoo.SUPERUSER_ID)
        jenis_pkm = env['jenis.pkm'].sudo().search([])
        pkm_ids = []
        for data in jenis_pkm:
            vals = {'id':data.id,'name': data.name}
            pkm_ids.append(vals)
        response = {'status_code': 200, 'message':'Success' ,'pkm_ids': pkm_ids}
        headers = {'Access-Control-Allow-Origin': '*'}
        body = response
        return Response(json.dumps(pkm_ids), headers=headers)
    
    @http.route(['/api/post/jenis-pkm-http'], auth='public', type='http', methods=['GET','POST'],csrf=False)
    def post_jenis_pkm_http(self, **post):
        env = request.env(user=odoo.SUPERUSER_ID)
        has_error = []
        required_fields = ['name']
        name = post.get('name')
        is_valid_fields = self.check_required_fields(required_fields,post=post)
        if not is_valid_fields:
            has_error += ['is_valid_fields']
            response = {"error" : 400, "description" : "InvalidRequest"}
        if not has_error:
            check_pkm = env['jenis.pkm'].search([('name','=',name)],limit=1)
            if check_pkm:
                has_error += ['pkm_exist']
                response = {"error" : 400, "description" : "Jenis PKM sudah ada"}
        if not has_error:
            new_jenis_pkm = env['jenis.pkm'].create({'name':name})
            response = {'status_code': 200, 'message':'Success', 'jenis_pkm_id': new_jenis_pkm.id}
        headers = {'Access-Control-Allow-Origin': '*'}
        body = response
        return Response(json.dumps(body), headers=headers)
    
    @http.route(['/api/get/dospem'], auth='public', type='json', methods=['GET','POST'],csrf=False)
    def get_dospem(self, **post):
        env = request.env(user=odoo.SUPERUSER_ID)
        config = env['api.security'].Config()
        has_error = []
        required_fields = ['token','username','password']
        login = post.get('username')
        password = post.get('password')

        is_valid_fields = self.check_required_fields(required_fields,post=post)
        if not is_valid_fields:
            has_error += ['is_valid_fields']
            response = {"error" : 400, "description" : "InvalidRequest"}

        if not has_error:
            is_valid_token = self.check_validation_token(config=config, post=post)
            if not is_valid_token:
                has_error += ['is_valid_token']
                response = {"error" : 400, "description" : "InvalidRequest"}
        
        if not has_error:
            user_id = request.session.authenticate(request.session.db, login, password)
            if not user_id:
                has_error += ['user_id']
                response = {"error" : 400, "description" : "Wrong Login or Password"}
                    
            dospem_ids = request.env['res.users'].sudo().search([('role','=','dosen_pembimbing')])
            dosen_pembimbing = []
            for data in dospem_ids:
                vals = {"id":data.id,'nama_dosen': data.name}
                dosen_pembimbing.append(vals)
            response = {'status_code': 200, 'message':'Success' ,'dosen_pembimbing': dosen_pembimbing}
            headers = {'Access-Control-Allow-Origin': '*'}
            body = response
        return response

    @http.route(['/api/get/pengajuan_data'], auth='public', type='json', methods=['GET','POST'],csrf=False)
    def get_pengajuan_data(self, **post):
        env = request.env(user=odoo.SUPERUSER_ID)
        config = env['api.security'].Config()
        
        has_error = []
        required_fields = ['token','username','password']
        login = post.get('username')
        password = post.get('password')
        is_valid_fields = self.check_required_fields(required_fields,post=post)
        if not is_valid_fields:
            has_error += ['is_valid_fields']
            response = {"error" : 400, "description" : "InvalidRequest"}

        if not has_error:
            is_valid_token = self.check_validation_token(config=config, post=post)
            if not is_valid_token:
                has_error += ['is_valid_token']
                response = {"error" : 400, "description" : "InvalidRequest"}
        
        if not has_error:
            user_id = request.session.authenticate(request.session.db, login, password)
            if not user_id:
                has_error += ['user_id']
                response = {"error" : 400, "description" : "Wrong Login or Password"}

            pengajuan_obj = env['pengajuan'].sudo().search([])
            pengajuan = []
            for data in pengajuan_obj:
                vals = {"id":data.id,'name': data.name,'judul_pkm': data.judul_pkm}
                pengajuan.append(vals)
            response = {'status_code': 200, 'message':'Success' ,'pengajuan': pengajuan}
            headers = {'Access-Control-Allow-Origin': '*'}
            body = response
        return response

    @http.route(['/api/insert-json/pengajuan'], type='json', auth="public", methods=['GET','POST'], csrf=False)
    def api_insert_json_pengajuan(self, **post): 
        cr, uid, pool, context = request.cr, odoo.SUPERUSER_ID, request.registry, request.context
        response = {}
        env = request.env(user=odoo.SUPERUSER_ID)
        config = env['api.security'].Config()
        request.uid = odoo.SUPERUSER_ID
        has_error = []
        required_fields = ['token','username','password']
        login = post.get('username')
        password = post.get('password')
        is_valid_fields = self.check_required_fields(required_fields,post=post)
        if not is_valid_fields:
            has_error += ['is_valid_fields']
            response = {"error" : 400, "description" : "InvalidRequest"}

        if not has_error:
            is_valid_token = self.check_validation_token(config=config, post=post)
            if not is_valid_token:
                has_error += ['is_valid_token']
                response = {"error" : 400, "description" : "InvalidRequest"}
        
        if not has_error:
            user_id = request.session.authenticate(request.session.db, login, password)
            if not user_id:
                has_error += ['user_id']
                response = {"error" : 400, "description" : "Wrong Login or Password"}
            judul_kegiatan = post.get('judul_kegiatan','')
            jenis_pkm = post.get('jenis_pkm','')
            bidang_ilmu = post.get('bidang_ilmu','')
            program_studi = post.get('program_studi','')
            dospem_id = post.get('dospem_id','')
            
            if jenis_pkm:
                pkm_id = env['jenis.pkm'].search([('name','ilike',jenis_pkm)],limit=1)
            
            if not has_error:
                values = {
                    'creator_id':user_id,
                    'judul_pkm': judul_kegiatan,
                    'pkm_id': pkm_id.id,
                    'bidang_ilmu':bidang_ilmu,
                    'program_studi':program_studi,
                    'dospem_id':int(dospem_id),
                }
                pengajuan = env['pengajuan'].create(values)

                response = {
                    'status_code': 200,
                    'status_desc': 'Success',
                    'pkm_id': pengajuan.id,
                }

            print("responseresponse",response)
            headers = {'Access-Control-Allow-Origin': '*'}
            body = response
        return response

    @http.route(['/api/delete-json/pengajuan'], type='json', auth="public", methods=['GET','POST'], csrf=False)
    def api_delete_json_pengajuan(self, **post): 
        cr, uid, pool, context = request.cr, odoo.SUPERUSER_ID, request.registry, request.context
        response = {}
        env = request.env(user=odoo.SUPERUSER_ID)
        config = env['api.security'].Config()
        request.uid = odoo.SUPERUSER_ID
        has_error = []
        required_fields = ['token','username','password']
        login = post.get('username')
        password = post.get('password')
        is_valid_fields = self.check_required_fields(required_fields,post=post)
        if not is_valid_fields:
            has_error += ['is_valid_fields']
            response = {"error" : 400, "description" : "InvalidRequest"}

        if not has_error:
            is_valid_token = self.check_validation_token(config=config, post=post)
            if not is_valid_token:
                has_error += ['is_valid_token']
                response = {"error" : 400, "description" : "InvalidRequest"}
        
        if not has_error:
            user_id = request.session.authenticate(request.session.db, login, password)
            if not user_id:
                has_error += ['user_id']
                response = {"error" : 400, "description" : "Wrong Login or Password"}

            pkm_id = post.get('pkm_id','')
            
            if pkm_id:
                pkm_id = env['pengajuan'].search([('id','=',pkm_id)],limit=1)
                if not pkm_id:
                    has_error += ['no_pkm']
                    response = {"error" : 400, "description" : "Data PKM Tidak Ditemukan"}
                if pkm_id.creator_id.id == user_id:
                    has_error += ['user_id']
                    response = {"error" : 400, "description" : "Tidak Bisa Menghapus Data Orang lain"}
            
            if not has_error:
                delete_pkm = pkm_id.sudo().unlink()

                response = {
                    'status_code': 200,
                    'status_desc': 'Success',
                    'message' : 'Data Berhasil Dihapus',
                }

            headers = {'Access-Control-Allow-Origin': '*'}
            body = response
        return response

    @http.route(['/api/update-json/pengajuan'], type='json', auth="public", methods=['GET','POST'], csrf=False)
    def api_update_json_pengajuan(self, **post): 
        cr, uid, pool, context = request.cr, odoo.SUPERUSER_ID, request.registry, request.context
        response = {}
        env = request.env(user=odoo.SUPERUSER_ID)
        config = env['api.security'].Config()
        request.uid = odoo.SUPERUSER_ID
        has_error = []
        required_fields = ['token','username','password']
        login = post.get('username')
        password = post.get('password')
        is_valid_fields = self.check_required_fields(required_fields,post=post)
        if not is_valid_fields:
            has_error += ['is_valid_fields']
            response = {"error" : 400, "description" : "InvalidRequest"}

        if not has_error:
            is_valid_token = self.check_validation_token(config=config, post=post)
            if not is_valid_token:
                has_error += ['is_valid_token']
                response = {"error" : 400, "description" : "InvalidRequest"}
        
        if not has_error:
            user_id = request.session.authenticate(request.session.db, login, password)
            if not user_id:
                has_error += ['user_id']
                response = {"error" : 400, "description" : "Wrong Login or Password"}

            pkm_id = post.get('pkm_id','')
            
            if pkm_id:
                pengajuan = env['pengajuan'].search([('id','=',pkm_id)],limit=1)
                if not pengajuan:
                    has_error += ['pengajuan']
                    response = {"error" : 400, "description" : "Data PKM Tidak Ditemukan"}    
                if pengajuan.creator_id.id != user_id:
                    has_error += ['user_id']
                    response = {"error" : 400, "description" : "Tidak Bisa Mengubah Data Orang lain"}
                
            
            if not has_error:
                jenis_pkm = post.get('jenis_pkm','')
                judul_kegiatan = post.get('judul_kegiatan','')
                bidang_ilmu = post.get('bidang_ilmu','')
                dospem_id = post.get('dospem_id','')
                program_studi = post.get('program_studi','')
                if jenis_pkm:
                    jenis_pkm = env['jenis.pkm'].search([('name','ilike',jenis_pkm)],limit=1)
                values = {
                    # 'creator_id':user_id,
                    'judul_pkm': judul_kegiatan,
                    'pkm_id': jenis_pkm.id or False,
                    'bidang_ilmu':bidang_ilmu,
                    'program_studi':program_studi,
                    'dospem_id':int(dospem_id),
                }
                try:
                    edit_pengajuan = pengajuan.sudo().write(values)
                except Exception as e:
                    print('Ex',e)
                response = {
                    'status_code': 200,
                    'status_desc': 'Success',
                    'message' : 'Data Berhasil Di Update',
                }

            headers = {'Access-Control-Allow-Origin': '*'}
            body = response
        return response

    @http.route(['/api/insert/pengajuan'], type='http', auth="public", methods=['GET','POST'], csrf=False)
    def api_insert_pengajuan(self, **post): 
        cr, uid, pool, context = request.cr, odoo.SUPERUSER_ID, request.registry, request.context
        response = {}
        env = request.env(user=odoo.SUPERUSER_ID)
        request.uid = odoo.SUPERUSER_ID

        has_error = []
        user_id = False
        username = post.get('username','')
        if not has_error:
            if username:
                user = env['res.users'].search([('login','=',username)], limit=1)
                user_id = user and user.id or False
                print('user_id::::',user_id)
                if not user_id:
                    has_error += ['user_id']
                    response = {"error" : 400, "description" : "InvalidRequest"}

            if not username:
                has_error += ['username']
                response = {"error" : 400, "description" : "InvalidRequest"}

        judul_kegiatan = post.get('judul_kegiatan','')
        jenis_pkm = post.get('jenis_pkm','')
        bidang_ilmu = post.get('bidang_ilmu','')
        program_studi = post.get('program_studi','')
        dospem_id = post.get('dospem_id','')
        
        if jenis_pkm:
            pkm_id = env['jenis.pkm'].search([('name','ilike',jenis_pkm)],limit=1)
           
        if not has_error:
            values = {
                'creator_id':user_id,
                'judul_pkm': judul_kegiatan,
                'pkm_id': pkm_id.id,
                'bidang_ilmu':bidang_ilmu,
                'program_studi':program_studi,
                'dospem_id':int(dospem_id),
            }
            pengajuan = env['pengajuan'].create(values)

            response = {
                'status_code': 200,
                'status_desc': 'Success',
                'pkm_id': pengajuan.id,
            }

        headers = {'Access-Control-Allow-Origin': '*'}
        body = response
        return Response(json.dumps(body), headers=headers)