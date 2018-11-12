# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime, timedelta
from dateutil import relativedelta
from openerp.exceptions import UserError, ValidationError
import time
import numpy as np


class ExtendsResPartner(models.Model):
	_name = 'res.partner'
	_inherit = 'res.partner'

	cuota_mora_ids = fields.One2many('financiera.prestamo.cuota', 'partner_cuota_mora_id', 'Cuotas en mora')
	saldo_mora = fields.Float('Saldo en mora', digits=(16, 2))
	cobranza_historial_conversacion_ids = fields.One2many('cobranza.historial.conversacion', 'partner_id', 'Historial de conversacion')
	cobranza_disponible = fields.Boolean('Disponible', default=True)
	cobranza_proxima_accion_fecha = fields.Datetime('Fecha')

	@api.model
	def cron_cuotas_mora(self):
		print "SE EJECUTOOOOOOOO **************--------------------"
		print "SE EJECUTOOOOOOOO **************--------------------"
		print "SE EJECUTOOOOOOOO **************--------------------"
		cr = self.env.cr
		uid = self.env.uid
		partner_obj = self.pool.get('res.partner')
		partner_ids = partner_obj.search(cr, uid, [])
		for _id in partner_ids:
			partner_id = partner_obj.browse(cr, uid, _id)
			partner_id.compute_cuotas_mora()

	@api.one
	def compute_cuotas_mora(self):
		cr = self.env.cr
		uid = self.env.uid
		self.cuota_mora_ids = None
		cuota_obj = self.pool.get('financiera.prestamo.cuota')
		cuota_ids = cuota_obj.search(cr, uid, [
			('cliente_id', '=', self.id),
			('state_mora', '!=', 'normal'),
			('state', 'in', ('activa', 'facturado')),
		])
		self.cuota_mora_ids = cuota_ids
		self._saldo_mora()


	@api.one
	def _saldo_mora(self):
		saldo = 0
		for cuota_id in self.cuota_mora_ids:
			saldo += cuota_id.saldo
		self.saldo_mora = saldo

	@api.model
	def cobranza_siguiente_deudor(self):
		cr = self.env.cr
		uid = self.env.uid
		ret_dudor_id = None
		deudor_obj = self.pool.get('res.partner')
		deudor_primera_accion_ids = deudor_obj.search(cr, uid, [
			('saldo_mora', '>', 0),
			('cobranza_proxima_accion_fecha', '=', False)
		])
		print "deudores primera accion"
		print deudor_primera_accion_ids
		if len(deudor_primera_accion_ids) > 0:
			print "dudor primera accion"
			print deudor_primera_accion_ids[0]
			ret_dudor_id = deudor_obj.browse(cr, uid, deudor_primera_accion_ids[0])
			ret_dudor_id.cobranza_disponible = False
			print ret_dudor_id
		else:
			deudor_ids = deudor_obj.search(cr, uid, [
				('saldo_mora', '>', 0),
				('cobranza_disponible', '=', True),
			], order='cobranza_proxima_accion_fecha asc', limit=1)
			print deudor_ids
			if len(deudor_ids) > 0:
				partner_id = deudor_obj.browse(cr, uid, deudor_ids[0])
				print partner_id
				if partner_id.cobranza_proxima_accion_fecha <= datetime.now():
					ret_dudor_id = partner_id
				else:
					proxima_fecha = partner_id.cobranza_proxima_accion_fecha
		return ret_dudor_id

	# @api.one
	# def actualizar_deudor(self):
		

class ExtendsFinancieraPrestamoCuota(models.Model):
	_name = 'financiera.prestamo.cuota'
	_inherit = 'financiera.prestamo.cuota'

	partner_cuota_mora_id = fields.Many2one('res.partner', "Cuota en mora")

	@api.one
	def confirmar_cobrar_cuota(self):
		rec = super(ExtendsFinancieraPrestamoCuota, self).confirmar_cobrar_cuota()
		self.cliente_id.compute_cuotas_mora()