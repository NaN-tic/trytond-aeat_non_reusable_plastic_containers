# This file is part aeat_non_reusable_plastic_containers module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.

try:
    from trytond.modules.aeat_non_reusable_plastic_contaires.test_module import suite
except ImportError:
    from .test_module import suite


__all__ = ['suite']
