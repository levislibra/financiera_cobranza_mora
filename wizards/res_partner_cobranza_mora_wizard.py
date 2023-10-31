# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime, timedelta
from dateutil import relativedelta
from openerp.exceptions import UserError, ValidationError
import time
import math

class ResPartnerCobranzaMoraWizard(models.TransientModel):
	_name = 'res.partner.cobranza.mora.wizard'
	
	@api.multi
	def actualizar_mora(self):
		context = dict(self._context or {})
		active_ids = context.get('active_ids')
		for _id in active_ids:
			partner_id = self.env['res.partner'].browse(_id)
			partner_id.actualizar_deuda_partner()
