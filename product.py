from trytond.model import fields
from trytond.pool import PoolMeta
from .invoice import plastic_fiscal_regime


class Product(metaclass=PoolMeta):
    __name__ = 'product.product'

    ipnr_virginity = fields.Numeric('IPNR Virginity', digits=(16, 2))
    ipnr = fields.Numeric('IPNR', digits=(16, 2))
    plastic_fiscal_regime = plastic_fiscal_regime
    plastic_key = fields.Selection([
        (None, ''),
        ('A', 'Non-reusable container that contains plastic',),
        ('B', ('semi-finished plastic product intended for obtaining '
            'non-reusable containers that contain plastic')),
        ('C', ('Plastic product intended to allow the closure, sale or '
            'presentation of non-reusable plastic containers containing '
            'plastic')),], 'PLastic Key')





