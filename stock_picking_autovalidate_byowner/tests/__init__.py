# command run test module
# odoo-bin -d <demo database> -i <module technical name> --test-tags=<module technical name> -c file configuration
# --test-tags stop the test case execution after module installation
# from odoo.tests.common import tagged import tagged for running only test case module
from . import test_onchange_owner
from . import test_sale_order
