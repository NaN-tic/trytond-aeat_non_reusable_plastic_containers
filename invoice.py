from trytond.pool import Pool, PoolMeta
from trytond.model import dualmethod, fields
from decimal import Decimal
from trytond.modules.product import round_price


plastic_account_fiscal = fields.Selection([
    (None, ''),
    ('A', 'A'),
    ('B', 'B'),
    ('C', 'B'),
    ('D', 'D'),
    ('E', 'E'),
    ('F', 'F'),
    ('G', 'G'),
    ('H', 'H'),
    ('I', 'I'),
    ('J', 'J'),
    ('K', 'K'),
    ('L', "L"),
    ('M', 'M'),], 'Plastic Fiscal Regime')

class PlasticTaxMixin(object):
    __slots__ = ()

    def set_plastic_cost(self):
        pool = Pool()
        Configuration = pool.get('account.configuration')
        configuration = Configuration(1)

        plastic_product = configuration.tax_plastic_product

        removed = []
        lines = list(self.lines or [])
        plastic_kgs = self.get_plastic_kg_ipnr()
        for line in lines:
            if line.type == 'line' and line.product == plastic_product:
                lines.remove(line)
                removed.append(line)

        for ipnr, plastic_kg in plastic_kgs.items():
            plastic_line = self.get_plastic_line(plastic_kg, ipnr)
            plastic_line.save()
            lines.append(plastic_line)

        self.lines = lines
        return removed

    def get_plastic_kg_ipnr(self):
        res = {}
        for line in self.lines:
            if (line.type == 'line' and line.product and line.product.ipnr):
                if not res.get(line.product.ipnr):
                    res[line.product.ipnr] = 0
                res[line.product.ipnr] += line.get_plastic_base_quantity()

        return res

    def get_plastic_line(self, quantity, unit_price):
        pass


class PlasticTaxLineMixin(object):
    __slots__ = ()

    def get_plastic_base_quantity(self):
        pool = Pool()
        Uom = pool.get('product.uom')
        Configuration = pool.get('account.configuration')
        configuration = Configuration(1)
        kg = configuration.tax_plastic_product.default_uom

        quantity = None

        if not self.unit:
            return Decimal('0')

        if kg.category == self.unit.category:
            quantity = Uom.compute_qty(self.unit, self.quantity or 0, kg)

        if (hasattr(self, 'show_info_unit') and self.show_info_unit
                and self.info_unit.category == kg.category):
            quantity = Uom.compute_qty(self.info_unit, self.info_quantity or 0,
                kg, round=True)
            quantity = Decimal(quantity)

        if not quantity:
            return Decimal('0')

        if self.plastic_account_fiscal and (
                self.plastic_account_fiscal not in ('A')):
            quantity = 0

        virginity = Decimal(self.product and self.product.ipnr_virginity
            or 0) / 100

        return Decimal(quantity * virginity).quantize(10**-3)

    @fields.depends('product')
    def on_change_with_plastic_account_fiscal(self):
        if self.product and self.product.plastic_account_fiscal:
            return self.product.plastic_account_fiscal



class AccountInvoice(PlasticTaxMixin, metaclass=PoolMeta):
    __name__ = 'account.invoice'

    show_plastic_detail = fields.Boolean('Show Plastic Detail')

    @dualmethod
    def update_taxes(cls, invoices, exception=False):
        pool = Pool()
        InvoiceLine = pool.get('account.invoice.line')
        removed = []
        for invoice in invoices:
            if (invoice.state in ('posted', 'paid', 'cancelled')
                    or invoice.type == 'out'):
                continue
            removed.extend(invoice.set_plastic_cost())

        if removed:
            InvoiceLine.delete(removed)

        invoices = cls.browse(invoices)
        super().update_taxes(invoices, exception)

    def get_plastic_line(self, quantity, unit_price):
        pool = Pool()
        InvoiceLine = pool.get('account.invoice.line')

        Configuration = pool.get('account.configuration')
        configuration = Configuration(1)
        plastic_product = configuration.tax_plastic_product

        sequence = None
        if self.lines:
            last_line = self.lines[-1]
            if last_line.sequence is not None:
                sequence = last_line.sequence + 1

        plastic_line = InvoiceLine(
            invoice=self,
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

    def on_change_party(self):
        super().on_change_party()
        if self.party:
            self.show_plastic_detail = self.party.show_plastic_detail


class AccountInvoiceLine(PlasticTaxLineMixin, metaclass=PoolMeta):
    __name__ = 'account.invoice.line'

    plastic_account_fiscal = plastic_account_fiscal