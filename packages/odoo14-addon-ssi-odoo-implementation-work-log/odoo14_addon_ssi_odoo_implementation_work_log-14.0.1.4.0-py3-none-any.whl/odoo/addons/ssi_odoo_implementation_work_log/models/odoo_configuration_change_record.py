# Copyright 2025 OpenSynergy Indonesia
# Copyright 2025 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3.0-standalone.html).

from odoo import models


class OdooConfigurationChangeRecord(models.Model):
    _name = "odoo_configuration_change_record"
    _inherit = [
        "odoo_configuration_change_record",
        "mixin.work_object",
    ]

    _work_log_create_page = True
