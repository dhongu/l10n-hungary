# ©  2026 Terrabit
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import logging
import re
import unicodedata

import psycopg2

from odoo import api, models
from odoo.service.model import PG_CONCURRENCY_ERRORS_TO_RETRY

_logger = logging.getLogger(__name__)

RELINK_PARAM = "l10n_hu_zip.relink_last_partner_id"
RELINK_BATCH = 5000


def _normalize_city(name):
    """Compare city names without accents, punctuation and case ("Budapest, XXII." = "Budapest XXII")."""
    name = unicodedata.normalize("NFKD", name or "")
    name = "".join(c for c in name if not unicodedata.combining(c)).casefold()
    return " ".join(re.sub(r"[^\w]+", " ", name).split())


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
            needle = _normalize_city(city_name)
            same_name = cities.filtered(lambda c: _normalize_city(c.name) == needle)
            if len(same_name) == 1:
                cities = same_name
            else:
                # the main locality of the postal code, whose name starts the others
                # ("Budapest XXII" and "Budapest XXII - Budafok"), when the typed name is it
                main = cities.filtered(
                    lambda c: all(_normalize_city(o.name).startswith(_normalize_city(c.name)) for o in cities)
                )
                if len(main) == 1 and needle.startswith(_normalize_city(main.name).split()[0]):
                    cities = main
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
        """Link the Hungarian contacts to the city of their postal code.

        The contacts getting the same values are written together: on a large database
        this runs on tens of thousands of contacts.
        """
        cache = {}
        to_write = {}
        for partner in self:
            if partner.country_id.code != "HU" or not partner.zip:
                continue
            zip_code = partner.zip.replace(" ", "")
            if partner.city_id.zipcode == zip_code:
                continue
            key = (zip_code, _normalize_city(partner.city))
            if key not in cache:
                cache[key] = self._l10n_hu_city_from_zip(zip_code, partner.city)
            city, state = cache[key]
            if city:
                values = (("city_id", city.id), ("city", city.name), ("state_id", city.state_id.id))
            elif state and partner.state_id != state:
                values = (("state_id", state.id),)
            else:
                continue
            to_write.setdefault(values, self.browse())
            to_write[values] |= partner
        fixed = self.browse()
        for values, partners in to_write.items():
            fixed |= partners._l10n_hu_write_skipping_errors(dict(values))
        if fixed:
            _logger.info("l10n_hu_zip: city set from the postal code on %d contacts", len(fixed))
        return fixed

    def _l10n_hu_write_skipping_errors(self, values):
        """Write the values on the contacts; return those written.

        A contact that cannot be written (a constraint of another module on data that was
        already wrong) is logged and left as it is, instead of stopping the whole batch:
        otherwise the relink stops for good on the first such contact.
        """
        try:
            with self.env.cr.savepoint():
                self.write(values)
            return self
        except psycopg2.Error as error:
            if error.pgcode in PG_CONCURRENCY_ERRORS_TO_RETRY:
                raise  # the batch is retried as a whole
            if len(self) == 1:
                _logger.warning("l10n_hu_zip: contact %s (id %s) not relinked: %s", self.display_name, self.id, error)
                return self.browse()
        except Exception:  # noqa: BLE001
            if len(self) == 1:
                _logger.warning(
                    "l10n_hu_zip: contact %s (id %s) not relinked to city %s", self.display_name, self.id, values,
                    exc_info=True,
                )
                return self.browse()
        written = self.browse()
        for partner in self:
            written |= partner._l10n_hu_write_skipping_errors(values)
        return written

    @api.model
    def _l10n_hu_relink_domain(self):
        return [("country_id.code", "=", "HU"), ("zip", "!=", False)]

    @api.model
    def _l10n_hu_relink_batch(self, last_id, limit=RELINK_BATCH):
        """Relink the next batch of contacts after ``last_id``; return (last id, count)."""
        # no chatter message for each of the tens of thousands of contacts relinked, and no
        # VAT check: only the address changes, a wrong VAT entered before must not stop it
        partners = self.with_context(active_test=False, tracking_disable=True, no_vat_validation=True).search(
            self._l10n_hu_relink_domain() + [("id", ">", last_id)], order="id", limit=limit
        )
        # a contact of type "contact" takes the address of its parent: writing it would copy
        # its own address on the parent (upstream sync). It is relinked through its parent,
        # and left as it is when its address differs from the parent's.
        partners.filtered(lambda p: not (p.parent_id and p.type == "contact")).l10n_hu_fix_city_from_zip()
        return (partners[-1].id if partners else last_id), len(partners)

    @api.model
    def _cron_l10n_hu_relink_partners(self):
        """Relink all the Hungarian contacts, in batches, then deactivate the cron."""
        params = self.env["ir.config_parameter"].sudo()
        cron = self.env["ir.cron"]
        last_id = int(params.get_param(RELINK_PARAM, 0))
        remaining = self.with_context(active_test=False).search_count(
            self._l10n_hu_relink_domain() + [("id", ">", last_id)]
        )
        while True:
            last_id, count = self._l10n_hu_relink_batch(last_id)
            if not count:
                params.set_param(RELINK_PARAM, 0)
                cron._commit_progress(remaining=0, deactivate=True)
                return
            params.set_param(RELINK_PARAM, last_id)
            remaining = max(remaining - count, 0)
            if cron._commit_progress(count, remaining=remaining) <= 0:
                return
