# This file is part aeat_non_reusable_plastic_containers module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import product
from . import purchase
from . import invoice
from . import configuration
from . import party

def register():
    Pool.register(
        configuration.Configuration,
        product.Product,
        party.Party,
        invoice.PlasticFiscalRegime,
        module='aeat_non_reusable_plastic_containers', type_='model')
    Pool.register(
        purchase.Purchase,
        purchase.PurchaseLine,
        depends=['purchase'],
        module='aeat_non_reusable_plastic_containers', type_='model')
    Pool.register(
        invoice.AccountInvoice,
        invoice.AccountInvoiceLine,
        depends=['account_invoice'],
        module='aeat_non_reusable_plastic_containers', type_='model')
