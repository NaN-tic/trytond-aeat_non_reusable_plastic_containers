from trytond.model import fields
from trytond.pool import PoolMeta


class Configuration(metaclass=PoolMeta):
    __name__ = 'account.configuration'

    tax_plastic_product = fields.Many2One('product.product',
        'Tax Plastic Product')
