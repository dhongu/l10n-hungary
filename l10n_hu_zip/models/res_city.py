# ©  2026 Terrabit
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import logging

from odoo import api, models
from odoo.tools import SQL

_logger = logging.getLogger(__name__)


class ResCity(models.Model):
    _inherit = "res.city"

    @api.model
    def _l10n_hu_unlink_old_cities(self):
        """Delete the Hungarian cities that are not in the postal list and are not used.

        Cities imported before l10n_hu_city (without postal code) stay in the selection
        next to the official ones. Once the contacts are relinked they are no longer used
        and can go. A city still referenced anywhere is kept.
        """
        official = self.env["ir.model.data"].sudo().search(
            [("module", "=", "l10n_hu_city"), ("model", "=", "res.city")]
        )
        cities = self.search([("country_id.code", "=", "HU"), ("id", "not in", official.mapped("res_id"))])
        if not cities:
            return cities
        used = set()
        fields = self.env["ir.model.fields"].sudo().search(
            [("relation", "=", "res.city"), ("ttype", "=", "many2one"), ("store", "=", True)]
        )
        for field in fields:
            model = self.env.get(field.model)
            if model is None or model._abstract or not model._auto or field.name not in model._fields:
                continue
            if not model._fields[field.name].store:
                continue
            self.env.cr.execute(
                SQL(
                    "SELECT DISTINCT %s FROM %s WHERE %s IN %s",
                    SQL.identifier(field.name),
                    SQL.identifier(model._table),
                    SQL.identifier(field.name),
                    tuple(cities.ids),
                )
            )
            used.update(row[0] for row in self.env.cr.fetchall())
        unused = cities.filtered(lambda c: c.id not in used)
        unused.unlink()
        _logger.info("l10n_hu_zip: %d old Hungarian cities deleted, %d still used kept", len(unused), len(used))
        return unused
