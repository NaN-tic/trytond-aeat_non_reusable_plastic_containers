from trytond.pool import Pool, PoolMeta
from trytond.model import dualmethod, fields
from decimal import Decimal
from trytond.modules.product import round_price


plastic_account_fiscal = fields.Selection([
    (None, ''),
    ('A', ('Subjection and non-exemption Law 7/2022, of April 8,'
        'Intra-community acquisition subject and not exempt of products '
        'subject to the tax.')),
    ('B', ('Non-subjection of article 73 c) Law 7/2022, of April 8 '
        'Intra-community acquisition of paints, inks, lacquers and adhesives '
        'designed to be incorporated into taxable products.')),
    ('C', ('Non-subjection of article 73 d) Law 7/2022, of April 8,'
        'Intra-community acquisition of containers of art. 68.1a) of the Law '
        'not designed to be delivered together with the goods.')),
    ('D',('Exemption article 75 a) 1º Law 7/2022, of April 8'
         'Intra-community acquisition of containers of art. 68.1a) of the Law '
         'intended to provide its function in medicines, sanitary products, '
         'food for special medical purposes, infant formula for hospital use or'
         'hazardous waste of sanitary origin')),
    ('E', ('Exemption article 75 a) 2º Law 7/2022, of April 8 Intra-community '
        'acquisition of products of art. 68.1b) of the Law intended to obtain'
        'containers of art. 68.1a) of the Law for medicines, health products, '
        'food for special medical purposes, formulas for infants for hospital '
        'use or hazardous waste of sanitary origin.')),
    ('F', ('Exemption article 75 a) 3º Law 7/2022, of April 8, Intra-community '
        'acquisition of products of art. 68.1c) of the Law intended to allow '
        'the closing, marketing or presentation of non-reusable containers for '
        'medicines, health products, food for special medical purposes, infant '
        'formula for hospital use or hazardous waste of sanitary origin.')),
    ('G', ('Exemption article 75 b) Law 7/2022, of April 8 Intra-community '
        'acquisition of containers of art. 68.1a) of the Law that are '
        'introduced into Spanish territory providing their function in '
        'medicines, health products, food for special medical purposes, '
        'formulas for infants for hospital use or hazardous waste of sanitary '
        'origin.')),
    ('H', ('Exemption article 75 c) Law 7/2022, of April 8, Intra-community '
        'acquisition of plastic rolls used in bales or bales for silage of '
        'fodder or cereals for agricultural or livestock use')),
    ('I', ('Exemption article 75 d) Law 7/2022, of April 8,  Intra-community '
        'acquisition of products subject to the tax that, prior to the end of '
        'the period for submitting the corresponding self-assessment, are '
        'intended to be sent outside Spanish territory (directly by the '
        'intra-community acquirer, or by a third party on his behalf or on his '
        'behalf).')),
    ('J', ('Exemption article 75 e) Law 7/2022, of April 8 Intra-community '
        'acquisition of taxable products that, prior to the end of the deadline'
        ' for filing the corresponding self-assessment, have ceased to be '
        'suitable for use or have been destroyed.')),
    ('K', ('Exemption article 75 f) Law 7/2022, of April 8 Intra-community '
        'acquisition of containers of art. 68.1a) of the Law provided that the '
        'total weight of non-recycled plastic contained in said containers does'
        ' not exceed 5 kilograms in one month.')),
    ('L', ('Exemption article 75 g) 1º Law 7/2022, of April 8 Intra-community '
        'acquisition of products of art. 68.1b) of the Law when they are not '
        'going to be used to obtain containers of art. 68.1a) of the Law.')),
    ('M', ('Exemption article 75 g) 2º Law 7/2022, of April 8 Intra-community '
        'acquisition of products of article 68.1c) of the Law when they are '
        'not going to be used to allow the closing, commercialization or '
        'presentation of non-reusable containers.')),], 'Plastic Fiscal Regime')


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

        return Decimal(quantity * virginity)


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
