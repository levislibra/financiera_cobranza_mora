# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from datetime import datetime, timedelta, date
from openerp.exceptions import UserError, ValidationError

class ExtendsFinancieraPrestamo(models.Model):
	_inherit = 'financiera.prestamo' 
	_name = 'financiera.prestamo'

	suscripto_debito_cbu = fields.Boolean('Debito por CBU', related='partner_id.suscripto_debito_cbu')
	no_debitar_cbu = fields.Boolean('No debitar por CBU')
	cobranza_externa_id = fields.Many2one('financiera.cobranza.externa', 'Cobranza externa', related='partner_id.cobranza_externa_id')

class ExtendsFinancieraPrestamoCuota(models.Model):
	_name = 'financiera.prestamo.cuota'
	_inherit = 'financiera.prestamo.cuota'

	partner_cuota_mora_id = fields.Many2one('res.partner', "Cuota en mora")