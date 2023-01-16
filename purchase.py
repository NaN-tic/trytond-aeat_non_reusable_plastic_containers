from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from .invoice import (PlasticTaxMixin, PlasticTaxLineMixin,
    plastic_account_fiscal)
from trytond.modules.product import round_price
from trytond.model import fields
from trytond.pyson import Eval


class Purchase(PlasticTaxMixin, metaclass=PoolMeta):
    __name__ = 'purchase.purchase'

    @classmethod
    def write(cls, *args):
        actions = iter(args)
        all_purchases = []
        for purchases, values in zip(actions, actions):
            if 'lines' in values:
                all_purchases += purchases
        update_purchases = [i for i in all_purchases if i.state == 'draft']
        super().write(*args)
        if update_purchases:
            cls.update_plastic_tax_line(update_purchases)

    @classmethod
    def copy(cls, purchases, default=None):
        if default is None:
            default = {}
        default = default.copy()
        copy_purchases = super().copy(purchases, default=default)
        cls.update_plastic_tax_line(copy_purchases)
        return copy_purchases

    @classmethod
    def update_plastic_tax_line(cls, purchases):
        pool = Pool()
        PurchaseLine = pool.get('purchase.line')
        removed = []
        for purchase in purchases:
            if purchase.state in ('posted', 'paid', 'cancelled'):
                continue
            removed.extend(purchase.set_plastic_cost())

        if removed:
            PurchaseLine.delete(removed)
        purchases = cls.browse(purchases)

    def get_plastic_line(self, quantity, unit_price):
        pool = Pool()
        PurchaseLine = pool.get('purchase.line')
        Configuration = pool.get('account.configuration')
        configuration = Configuration(1)
        plastic_product = configuration.tax_plastic_product

        sequence = None
        if self.lines:
            last_line = self.lines[-1]
            if last_line.sequence is not None:
                sequence = last_line.sequence + 1

        plastic_line = PurchaseLine(
            purchase=self,
            sequence=sequence,
            type='line',
            product=plastic_product,
            quantity=quantity,
            unit=plastic_product.default_uom
        )
        plastic_line.on_change_product()
        if unit_price is not None:
            plastic_line.unit_price = round_price(unit_price)

        plastic_line.amount = plastic_line.on_change_with_amount()
        return plastic_line

    def create_invoice(self):
        with Transaction().set_context(no_ipnr=True):
            return super().create_invoice()

class PurchaseLine(PlasticTaxLineMixin, metaclass=PoolMeta):
    __name__ = 'purchase.line'

    plastic_account_fiscal = plastic_account_fiscal
    manual_kg = fields.Float('Manual Kg',
        digits=(16, Eval('unit_digits', 2)),
        states={
            'invisible': Eval('type') != 'line',
            'readonly': Eval('purchase_state') != 'draft',
        },
        depends=['type', 'unit_digits', 'purchase_state'])

    @fields.depends('quantity', 'manual_kg', methods=['on_change_with_amount'])
    def on_change_manual_kg(self):
        self.quantity = self.manual_kg
        self.amount = self.on_change_with_amount()

    def get_invoice_line(self):
        pool = Pool()
        Configuration = pool.get('account.configuration')
        configuration = Configuration(1)
        plastic_product = configuration.tax_plastic_product

        if self.product == plastic_product:
            return []

        return super().get_invoice_line()
