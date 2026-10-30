# ©  2026 Terrabit
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from .models.res_partner import RELINK_BATCH


def post_init_hook(env):
    # link the Hungarian contacts to the city of their postal code; a large database
    # is left to the cron, in batches, so that the install does not time out
    Partner = env["res.partner"].with_context(active_test=False)
    domain = Partner._l10n_hu_relink_domain()
    if Partner.search_count(domain) <= RELINK_BATCH:
        Partner._l10n_hu_relink_batch(0)
        return
    cron = env.ref("l10n_hu_zip.ir_cron_relink_partners")
    cron.active = True
    cron._trigger()
