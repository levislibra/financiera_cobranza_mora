# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime, timedelta

class FinancieraCobranzaConfig(models.Model):
	_name = 'financiera.cobranza.config'

	name = fields.Char("Nombre")
	fecha = fields.Datetime("Fecha ultima actualizacion")
	id_cobranza_cbu = fields.Integer('Id cobranza CBU')
	mora_ids = fields.One2many('res.partner.mora', "config_id", "Segmentos")
	company_id = fields.Many2one('res.company', 'Empresa', required=False, default=lambda self: self.env['res.company']._company_default_get('financiera.cobranza.config'))
	# Carta Documento
	cd_logo_1 = fields.Binary('CD Logo 1 - carta documento')
	cd_logo_2 = fields.Binary('CD Logo 2 - carta documento')
	cd_logo_3 = fields.Binary('CD Logo 3 - carta documento')
	cd_titulo = fields.Char('CD titulo')
	cd_texto = fields.Text('CD texto')
	cd_saludo = fields.Char('CD saludo')
	# Archivo BNA
	bna_sucursal = fields.Char('BNA cuenta recaudadora sucursal')
	bna_cuenta = fields.Char('BNA cuenta recaudadora numero')
	bna_tipo_moneda = fields.Char('BNA cuenta recaudadora tipo y moneda')
	bna_moneda_movimientos = fields.Char('BNA moneda de movimientos')
	bna_indicador_empleados_bna = fields.Char('BNA indicador empleados BNA')
	# Configuracion Adsus
	# Archivo BAPRO
	bapro_file_name_pre = fields.Char('BAPRO - Pre nombre de archivo')
	bapro_file_name_pos = fields.Char('BAPRO - Pos nombre de archivo')
	bapro_denominacion_pre = fields.Char('BAPRO - Pre deniminacion')
	# Generales
	codigo_servicio_epico = fields.Char('Codigo de servicio Itau/BBVA/Ciudad')
	adsus_template_id = fields.Many2one('mail.template', 'Plantilla de email ADSUS')
	# Archivo BBVA
	codigo_referencia_bbva = fields.Char('Codigo referencia ADSUS')
	
	@api.model
	def _cron_actualizar_deudores(self):
		print("Cron actualizar deudores")
		company_obj = self.pool.get('res.company')
		comapny_ids = company_obj.search(self.env.cr, self.env.uid, [])
		for _id in comapny_ids:
			company_id = company_obj.browse(self.env.cr, self.env.uid, _id)
			print("company_id: ", str(company_id.name))
			if len(company_id.cobranza_config_id) > 0:
				company_id.cobranza_config_id.actualizar_deudores()
				company_id.cobranza_config_id.fecha = datetime.now()
				company_id.fecha_actualizacion_deudores = datetime.now()

	def get_id_cobranza_cbu(self):
		self.id_cobranza_cbu += 1
		return self.id_cobranza_cbu

	# reset fecha_actualizacion_mora all partners
	@api.one
	def reset_fecha_actualizacion_mora(self):
		partner_obj = self.pool.get('res.partner')
		partner_ids = partner_obj.search(self.env.cr, self.env.uid, [
			('company_id', '=', self.company_id.id),
		])
		partner_obj_ids = partner_obj.browse(self.env.cr, self.env.uid, partner_ids)
		partner_obj_ids.write({'fecha_actualizacion_mora': False})

	@api.one
	def actualizar_deudores(self):
		print("Actualizacion de deuda de partner iniciada")
		partner_obj = self.pool.get('res.partner')
		total = 0
		procesados = 0
		today = datetime.now().date()
		today_menos_10 = today - timedelta(days=120)
		while True:
			partner_ids = partner_obj.search(self.env.cr, self.env.uid, [
				('company_id', '=', self.company_id.id),
				('cuota_ids.state', '=', 'activa'),
				'|', ('fecha_actualizacion_mora', '<', str(today)), ('fecha_actualizacion_mora', '=', False),
			], limit=300)
			# Buscamos partner que tengan cuotas con pagos en los ultimos 10 dias y sin cuotas activas
			partner_pagos_recientes_ids = partner_obj.search(self.env.cr, self.env.uid, [
				('active', '=', True),
				('company_id.id', '=', self.id),
				('cuota_ids.state', '!=', 'activa'),
				('cuota_ids.payment_ids.create_date', '>', str(today_menos_10)),
				'|', ('fecha_actualizacion_mora', '=', False), ('fecha_actualizacion_mora', '<', str(today)),
			], limit=200)
			# unir listas
			partner_ids = partner_ids + partner_pagos_recientes_ids
			print("partner_ids: ", partner_ids)
			print("partner_ids todos: ", partner_ids)
			if not partner_ids:
				break
			try:
				total += len(partner_ids)
				partner_obj_ids = partner_obj.browse(self.env.cr, self.env.uid, partner_ids)
				for partner_id in partner_obj_ids:
					print("Procesando partner: ", partner_id.name)
					partner_id.actualizar_deuda_partner()
					procesados += 1
					print("Procesados / Total:", str(procesados), str(total))
				partner_obj_ids.write({'fecha_actualizacion_mora': today})
				self.env.cr.commit()
			except Exception as e:
				print("Error: ", e)
				self.env.cr.rollback()
		self.fecha = datetime.now()
		self.company_id.fecha_actualizacion_deudores = datetime.now()

	# @api.one
	# def actualizar_deudores(self):
	# 	self.fecha = datetime.now()
	# 	partners_len = 0
	# 	partners_procesados = 0
	# 	# inicializacion
	# 	mora_en_memoria_ids = []
	# 	for mora_id in self.mora_ids:
	# 		mora_en_memoria_ids.append({
	# 			'activo': mora_id.activo,
	# 			'dia_inicial_impago': mora_id.dia_inicial_impago,
	# 			'dia_final_impago':mora_id.dia_final_impago,
	# 			'monto': 0,
	# 			'partner_cantidad': 0,
	# 			'ids': [],
	# 		})
	# 		mora_id.write({
	# 			'monto': 0,
	# 			'partner_cantidad': 0,
	# 			'partner_ids': [(6,0,[])]
	# 		})
	# 	partner_obj = self.pool.get('res.partner')
	# 	partner_ids = partner_obj.search(self.env.cr, self.env.uid, [
	# 		('company_id', '=', self.company_id.id),
	# 		# ('state','in', ['confirm','validated']),
	# 		('cuota_ids.state','in', ['activa', 'judicial','incobrable'])
	# 	])
	# 	partners_len = len(partner_ids)
	# 	print("Procesando %s deudores" % str(partners_len))
	# 	fecha_actual = datetime.now()
	# 	deuda_total = 0.0
	# 	for _id in partner_ids:
	# 		partner_id = partner_obj.browse(self.env.cr, self.env.uid, _id)
	# 		partner_saldo = partner_id.saldo
	# 		partner_id.write({
	# 			'saldo_total': partner_saldo,
	# 			'mora_id': False,
	# 			'proxima_cuota_id': False,
	# 		})
	# 		# Buscamos las cuotas activas del cliente
	# 		cuota_obj = self.pool.get('financiera.prestamo.cuota')
	# 		cuota_ids = cuota_obj.search(self.env.cr, self.env.uid, [
	# 			('partner_id', '=', partner_id.id),
	# 			('state','in', ['activa', 'judicial','incobrable'])
	# 		], order='fecha_vencimiento asc')
	# 		cuota_id = None
	# 		flag_primer_cuota_activa_procesada = False
	# 		cuota_mora_ids = []
	# 		saldo_mora = 0
	# 		dias_en_mora = 0
	# 		for _id in cuota_ids:
	# 			cuota_id = cuota_obj.browse(self.env.cr, self.env.uid, _id)
	# 			fecha_vencimiento = datetime.strptime(cuota_id.fecha_vencimiento, "%Y-%m-%d")
	# 			if not flag_primer_cuota_activa_procesada:
	# 				partner_id.proxima_cuota_id = cuota_id.id
	# 				partner_id.compute_proxima_cuota_a_pagar(cuota_id)
	# 				# Calculamos los dias de la primer cuota activa
	# 				diferencia = fecha_actual - fecha_vencimiento
	# 				dias = diferencia.days
	# 				if fecha_vencimiento < fecha_actual:
	# 					dias_en_mora = abs(dias)
	# 				for mora_id in mora_en_memoria_ids:
	# 					if mora_id['activo'] and dias >= mora_id['dia_inicial_impago'] and dias <= mora_id['dia_final_impago']:
	# 						deuda_total += partner_saldo
	# 						mora_id['monto'] = mora_id['monto'] + partner_saldo
	# 						mora_id['partner_cantidad'] = mora_id['partner_cantidad'] + 1
	# 						mora_id['ids'].append(partner_id.id)
	# 						break
	# 				flag_primer_cuota_activa_procesada = True
	# 			if fecha_vencimiento < fecha_actual:
	# 				saldo_mora += cuota_id.saldo
	# 				cuota_mora_ids.append(cuota_id.id)
	# 		partner_id.compute_referidos()
	# 		partner_id.cuota_mora_ids = cuota_mora_ids
	# 		partner_id.write({
	# 			'saldo_mora': saldo_mora,
	# 			'dias_en_mora': dias_en_mora,
	# 		})
	# 		partners_procesados += 1
	# 		print("Partners procesados: %s%%" % str((float(partners_procesados)/float(partners_len))*100))
	# 	i = 0
	# 	for mora_id in self.mora_ids:
	# 		mora_id.write({
	# 			'monto': mora_en_memoria_ids[i]['monto'],
	# 			'partner_cantidad': mora_en_memoria_ids[i]['partner_cantidad'],
	# 			'partner_ids': [(6,0, mora_en_memoria_ids[i]['ids'])]
	# 		})
	# 		i = i + 1
	# 		if deuda_total > 0:
	# 			mora_id.porcentaje = (mora_id.monto / deuda_total) * 100

class ExtendsResCompany(models.Model):
	_name = 'res.company'
	_inherit = 'res.company'

	cobranza_config_id = fields.Many2one('financiera.cobranza.config', 'Configuracion Cobranza y seguimiento')
	fecha_actualizacion_deudores = fields.Datetime("Fecha ultima actualizacion de deudores")