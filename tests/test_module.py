# This file is part aeat_non_reusable_plastic_containers module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase


class AeatNonReusablePlasticContainersTestCase(ModuleTestCase):
    'Test Aeat Non Reusable Plastic Containers module'
    module = 'aeat_non_reusable_plastic_containers'


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        AeatNonReusablePlasticContainersTestCase))
    return suite