# ©  2026 Terrabit
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo.tests import Form, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCityFromZip(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hungary = cls.env.ref("base.hu")
        cls.budapest = cls.env.ref("l10n_hu_city.BU")

    def _hu_city(self, zip_code, name):
        return self.env["res.city"].search(
            [("country_id", "=", self.hungary.id), ("zipcode", "=", zip_code), ("name", "=", name)]
        )

    def test_budapest_district(self):
        for zip_code, name in (("1025", "Budapest II"), ("1061", "Budapest VI"), ("1124", "Budapest XII")):
            city, state = self.env["res.partner"]._l10n_hu_city_from_zip(zip_code, "Budapest")
            self.assertEqual(city, self._hu_city(zip_code, name))
            self.assertEqual(state, self.budapest)

    def test_shared_zip(self):
        # 1007 is both "Budapest" and "Budapest Margitsziget": only the county is known
        city, state = self.env["res.partner"]._l10n_hu_city_from_zip("1007")
        self.assertFalse(city)
        self.assertEqual(state, self.budapest)
        # the city name picks the locality
        city, state = self.env["res.partner"]._l10n_hu_city_from_zip("1007", "budapest margitsziget")
        self.assertEqual(city, self._hu_city("1007", "Budapest Margitsziget"))

    def test_onchange_zip(self):
        with Form(self.env["res.partner"]) as partner_form:
            partner_form.name = "Kánya Zoltán"
            partner_form.country_id = self.hungary
            partner_form.zip = "1124"
            self.assertEqual(partner_form.city_id, self._hu_city("1124", "Budapest XII"))
            self.assertEqual(partner_form.city, "Budapest XII")
            self.assertEqual(partner_form.state_id, self.budapest)

    def test_fix_wrong_city(self):
        district_1 = self._hu_city("1011", "Budapest I")
        partner = self.env["res.partner"].create(
            {
                "name": "Kánya Zoltán",
                "country_id": self.hungary.id,
                "city_id": district_1.id,
                "city": district_1.name,
                "state_id": self.budapest.id,
                "zip": "1124",
            }
        )
        self.assertEqual(partner.l10n_hu_fix_city_from_zip(), partner)
        self.assertEqual(partner.city_id, self._hu_city("1124", "Budapest XII"))
        self.assertEqual(partner.city, "Budapest XII")
        # nothing left to fix
        self.assertFalse(partner.l10n_hu_fix_city_from_zip())

    def test_other_country_untouched(self):
        partner = self.env["res.partner"].create(
            {"name": "Test RO", "country_id": self.env.ref("base.ro").id, "zip": "1124", "city": "Oradea"}
        )
        self.assertFalse(partner.l10n_hu_fix_city_from_zip())
        self.assertFalse(partner.city_id)
