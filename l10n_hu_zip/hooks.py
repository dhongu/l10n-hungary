# ©  2026 Terrabit
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).


def post_init_hook(env):
    # relink the Hungarian contacts whose city does not match their postal code
    # (l10n_hu_city only links the contacts that have no city at all)
    partners = env["res.partner"].with_context(active_test=False).search(
        [("country_id.code", "=", "HU"), ("zip", "!=", False)]
    )
    partners.l10n_hu_fix_city_from_zip()
