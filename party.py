from trytond.model import fields
from trytond.pool import PoolMeta


class Party(metaclass=PoolMeta):
    __name__ = 'party.party'

    show_plastic_detail = fields.Boolean('Show Plastic Detail')

    @staticmethod
    def default_show_plastic_detail():
        return False
