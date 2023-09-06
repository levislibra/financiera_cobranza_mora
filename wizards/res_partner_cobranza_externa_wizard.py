# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime, timedelta
from dateutil import relativedelta
from openerp.exceptions import UserError, ValidationError
import time
import math

class ResPartnerCobranzaExternaWizard(models.TransientModel):
	_name = 'res.partner.cobranza.externa.wizard'

	cobranza_externa_id = fields.Many2one('financiera.cobranza.externa', 'Cobranza externa')
	
	@api.multi
	def asignar_cobranza_externa(self):
		context = dict(self._context or {})
		active_ids = context.get('active_ids')
		for _id in active_ids:
			partner_id = self.env['res.partner'].browse(_id)
			partner_id.cobranza_externa_id = self.cobranza_externa_id.id if self.cobranza_externa_id else False
