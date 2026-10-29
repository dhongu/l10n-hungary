# ©  2026 Terrabit
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _l10n_hu_city_from_zip(self, zip_code, city_name=None):
        """Return (city, state) for a Hungarian postal code.

        A postal code can be shared by several localities: the city is returned only
        when it is unique, or when the city name picks one of them; the county is
        returned when all the localities of the postal code are in the same county.
        """
        City = self.env["res.city"]
        zip_code = (zip_code or "").replace(" ", "")
        if not zip_code:
            return City, self.env["res.country.state"]
        cities = City.search([("country_id.code", "=", "HU"), ("zipcode", "=", zip_code)])
        if len(cities) > 1 and city_name:
            needle = city_name.strip().casefold()
            same_name = cities.filtered(lambda c: c.name.casefold() == needle)
            if len(same_name) == 1:
                cities = same_name
        state = cities.state_id if len(cities.state_id) == 1 else cities.state_id.browse()
        return (cities if len(cities) == 1 else City), state

    @api.onchange("zip")
    def _onchange_zip_l10n_hu(self):
        if self.country_id.code != "HU" or not self.zip:
            return
        if self.city_id.zipcode == self.zip.replace(" ", ""):
            return
        city, state = self._l10n_hu_city_from_zip(self.zip, self.city)
        if city:
            self.city_id = city
            self.city = city.name
            self.state_id = city.state_id
        elif state:
            self.state_id = state

    def l10n_hu_fix_city_from_zip(self):
        """Link the Hungarian contacts to the city of their postal code."""
        fixed = self.browse()
        for partner in self:
            if partner.country_id.code != "HU" or not partner.zip:
                continue
            if partner.city_id.zipcode == partner.zip.replace(" ", ""):
                continue
            city, state = self._l10n_hu_city_from_zip(partner.zip, partner.city)
            if city:
                values = {"city_id": city.id, "city": city.name, "state_id": city.state_id.id}
            elif state and partner.state_id != state:
                values = {"state_id": state.id}
            else:
                continue
            partner.write(values)
            fixed |= partner
        if fixed:
            _logger.info("l10n_hu_zip: city set from the postal code on %d contacts", len(fixed))
        return fixed
