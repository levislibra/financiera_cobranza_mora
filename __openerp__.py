# -*- coding: utf-8 -*-
{
    'name': "Financiera - Cobranza Mora",

    'summary': """
        Gestion de cobranza - historial de conversasion con el deudor.""",

    'description': """
        Gestion de cobranza - historial de conversasion con el deudor.
    """,

    'author': "Librasoft",
    'website': "https://www.libra-soft.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'finance',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'financiera_prestamos', 'financiera_pagos_360', 'financiera_mobbex','financiera_sms'],

    # always loaded
    'data': [
		'security/user_groups.xml',
		'security/ir.model.access.csv',
		'security/security.xml',
		'views/cobranza_config.xml',
		'views/cobranza_cbu_config.xml',
		'views/cobranza_cbu.xml',
		'views/cobranza_externa.xml',
		'views/cobranza_historial_conversacion.xml',
		'views/cobranza_sesion.xml',
		'views/cobranza_notificacion.xml',
		'views/extends_res_partner.xml',
		'views/extends_res_company.xml',
		'views/res_bank_bna_code.xml',
		'views/extends_financiera_prestamo.xml',
		'views/views.xml',
		'wizards/res_partner_debt_to_bank_file_wizard.xml',
		'wizards/res_partner_cobranza_externa_wizard.xml',
		'wizards/res_partner_cobranza_mora_wizard.xml',
		'reports/generic_reports.xml',
		'data/ir_cron.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}