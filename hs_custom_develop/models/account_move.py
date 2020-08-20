# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


import logging
_logger = logging.getLogger(__name__)

class AccountMovelineInherit(models.Model):
	_inherit = 'account.move.line'


	def create_refund_payment(self, payments):
		"""Crea automaticamente un pago a proveedor para cancelar el pago
		registrado del fondo. Esto con el objetivo que el fondo no tengo 
		saldo a favor

		Args:
			invoice ([type]): [description]
		"""
		if payments:
			for payment in payments:
				payment.cancel()
					
				#return
				"""
				refund = self.env['account.payment'].sudo().with_context(
					default_payment_type = 'outbound', 
					default_partner_type = 'supplier',
					default_payment_date = fields.Date.today()
				)
				payment_method_name = 'account.account_payment_method_manual_out'
				payment_method = self.env.ref(payment_method_name)
				if not payment_method:
					raise exceptions.ValidationError('Account configuration '
					'module - Default journal Strifund is empty.')
				
				payment_refund = refund.create({
					'payment_method_id': payment_method.id,
					'partner_id': payment.partner_id.id,
					'amount': payment.amount,
					'journal_id': payment.journal_id.id,
					'communication': 'Cancel payment %s' % (payment.name)
				})
				payment_refund.post()
				"""


	@api.multi
	def remove_move_reconcile(self):
		"""Controlamos que la funcion UNRECONCILE en la factura solo pueda
		ser usada por usurios que tengan ciertos privilegios; tambien que la
		regla solo se aplique a clientes regulares. 

		Raises:
			exceptions.ValidationError: [description]

		Returns:
			[type]: [description]
		"""
		invoice_id = self.env.context.get('invoice_id')
		if invoice_id:
			invoice = self.env['account.invoice'].browse(invoice_id)
			if invoice.partner_id.customer_type == "regular":
				user = self.env.user
				group_manager = self.env.ref('account.group_account_user')
				if user in group_manager.users:
					raise exceptions.ValidationError('No cuenta con los \
						permisos necesarios para realizar esta acción.')
				return super(AccountMovelineInherit, self).remove_move_reconcile()
			else:
				payments = invoice.payment_ids
				unreconcile = super(AccountMovelineInherit, self).remove_move_reconcile()
				self.create_refund_payment(payments)
				return unreconcile
		
		return super(AccountMovelineInherit, self).remove_move_reconcile()