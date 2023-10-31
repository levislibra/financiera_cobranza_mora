# -*- coding: utf-8 -*-

from openerp import models, fields, api
import time
from datetime import datetime, timedelta
from dateutil import relativedelta
from openerp.exceptions import UserError, ValidationError
import time
import numpy as np


class ExtendsResPartner(models.Model):
	_name = 'res.partner'
	_inherit = 'res.partner'

	cuota_mora_ids = fields.One2many('financiera.prestamo.cuota', 'partner_cuota_mora_id', 'Cuotas en mora')
	proxima_cuota_id = fields.Many2one('financiera.prestamo.cuota', 'Proxima cuota a pagar')
	cuota_proximo_vencimiento = fields.Date('Proximo vencimiento')
	cuota_proxima_numero = fields.Char('Proximo nro de cuota')
	cuota_proxima_original_saldo = fields.Float('Saldo original', digits=(16, 2))
	cuota_proxima_monto = fields.Float('Saldo actual', digits=(16, 2))
	# pagos_360_checkout_url = fields.Char('Pagos360 - Url de pago online', compute='_compute_link_pagos_360')
	# pagos_360_pdf_url = fields.Char('Pagos360 - Url de cupon de pago en pdf', compute='_compute_link_pagos_360')
	referido_1_nombre = fields.Char('Referido 1')
	referido_1_celular = fields.Char('Referido 1 celular')
	referido_2_nombre = fields.Char('Referido 2')
	referido_2_celular = fields.Char('Referido 2 celular')
	saldo_mora = fields.Float('Deuda en mora', digits=(16, 2))
	saldo_total = fields.Float('Deuda total', digits=(16, 2))
	cobranza_historial_conversacion_ids = fields.One2many('cobranza.historial.conversacion', 'partner_id', 'Historial de conversacion')
	cobranza_disponible = fields.Boolean('Disponible', default=True)
	suscripto_debito_cbu = fields.Boolean('Debito por CBU')
	no_debitar_cbu = fields.Boolean('No debitar por CBU')
	# Estado actual
	cobranza_estado_id = fields.Many2one('cobranza.historial.conversacion.estado', 'Estado')
	cobranza_proxima_accion_id = fields.Many2one('cobranza.historial.conversacion.accion', 'Proxima accion')
	cobranza_proxima_accion_fecha = fields.Datetime('Fecha proxima accion')
	# Estado de mora
	dias_en_mora = fields.Integer('Dias en mora')
	mora_id = fields.Many2one('res.partner.mora', 'Segmento')
	# Notificaiones
	notificacion_ids = fields.One2many('financiera.cobranza.notificacion', 'partner_id', 'Notificaciones')
	# Estudio de cobranza externa
	cobranza_externa_id = fields.Many2one('financiera.cobranza.externa', 'Cobranza externa')
	# actualizacion mora
	fecha_actualizacion_mora = fields.Date('Fecha actualizacion mora')

	@api.one
	def compute_proxima_cuota_a_pagar(self, cuota_id):
		self.write({
			'cuota_proximo_vencimiento': cuota_id.fecha_vencimiento,
			'cuota_proxima_numero': cuota_id.numero_cuota,
			'cuota_proxima_original_saldo': cuota_id.cuota_original_saldo,
			'cuota_proxima_monto': cuota_id.saldo,
		})
	
	@api.one
	def actualizar_deuda_partner(self):
		fecha_actual = datetime.now()
		partner_saldo = self.saldo
		self.write({
			'saldo_total': partner_saldo,
			'mora_id': False,
			'proxima_cuota_id': False,
		})
		# Buscamos las cuotas activas del cliente
		cuota_obj = self.pool.get('financiera.prestamo.cuota')
		cuota_ids = cuota_obj.search(self.env.cr, self.env.uid, [
			('partner_id', '=', self.id),
			('state','in', ['activa', 'judicial','incobrable'])
		], order='fecha_vencimiento asc')
		cuota_id = None
		flag_primer_cuota_activa_procesada = False
		cuota_mora_ids = []
		saldo_mora = 0
		dias_en_mora = 0
		for _id in cuota_ids:
			cuota_id = cuota_obj.browse(self.env.cr, self.env.uid, _id)
			fecha_vencimiento = datetime.strptime(cuota_id.fecha_vencimiento, "%Y-%m-%d")
			if not flag_primer_cuota_activa_procesada:
				self.proxima_cuota_id = cuota_id.id
				self.compute_proxima_cuota_a_pagar(cuota_id)
				# Calculamos los dias de la primer cuota activa
				diferencia = fecha_actual - fecha_vencimiento
				dias = diferencia.days
				if fecha_vencimiento < fecha_actual:
					dias_en_mora = abs(dias)
				self.dias_en_mora = dias_en_mora
				self.mora_id = self.env['res.partner.mora'].get_mora_partner(self)
				flag_primer_cuota_activa_procesada = True
			if fecha_vencimiento < fecha_actual:
				saldo_mora += cuota_id.saldo
				cuota_mora_ids.append(cuota_id.id)
		self.cuota_mora_ids = cuota_mora_ids
		self.write({
			'saldo_mora': saldo_mora,
			'dias_en_mora': dias_en_mora,
			'fecha_actualizacion_mora': fecha_actual,
		})

	# @api.one
	# def compute_referidos(self):
	# 	len_contactos = len(self.contacto_ids)
	# 	values = {}
	# 	if len_contactos > 1:
	# 		values['referido_2_nombre'] = self.contacto_ids[1].name
	# 		values['referido_2_celular'] = self.contacto_ids[1].movil
	# 	if len_contactos > 0:
	# 		values['referido_1_nombre'] = self.contacto_ids[0].name
	# 		values['referido_1_celular'] = self.contacto_ids[0].movil
	# 		self.write(values)

	@api.model
	def cobranza_siguiente_deudor(self):
		cr = self.env.cr
		uid = self.env.uid
		current_user = self.env['res.users'].browse(uid)
		ret_deudor_id = None
		deudor_obj = self.pool.get('res.partner')
		deudor_primera_accion_ids = deudor_obj.search(cr, uid, [
			('saldo_mora', '>', 0),
			('cobranza_disponible', '=', True),
			('cobranza_proxima_accion_fecha', '=', False),
			('cobranza_externa_id', '=', False),
			('company_id', '=', current_user.company_id.id),
		])
		if len(deudor_primera_accion_ids) > 0:
			ret_deudor_id = deudor_obj.browse(cr, uid, deudor_primera_accion_ids[0])
			ret_deudor_id.cobranza_disponible = False
		else:
			date_now = datetime.now()
			deudor_ids = deudor_obj.search(cr, uid, [
				('saldo_mora', '>', 0),
				('cobranza_disponible', '=', True),
				('cobranza_externa_id', '=', False),
				('company_id', '=', current_user.company_id.id),
				('cobranza_proxima_accion_fecha', '<=', str(date_now))
			], order='cobranza_proxima_accion_fecha asc', limit=1)
			if len(deudor_ids) > 0:
				partner_id = deudor_obj.browse(cr, uid, deudor_ids[0])
				ret_deudor_id = partner_id
				ret_deudor_id.cobranza_disponible = False
		return ret_deudor_id

	@api.multi
	def carta_documento_report(self):
		self.ensure_one()
		if len(self.company_id.cobranza_config_id) > 0:
			return self.env['report'].get_action(self, "financiera_cobranza_mora.carta_documento_report_view")
		else:
			raise UserError("Modulo cobranza no esta contartado.")

