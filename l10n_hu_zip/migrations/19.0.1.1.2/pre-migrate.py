# ©  2026 Terrabit
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).


def migrate(cr, version):
    # the cron used to be updatable: mark it noupdate before the data is loaded, so this
    # update already keeps it active when a relink is in progress
    cr.execute(
        """
        UPDATE ir_model_data SET noupdate = TRUE
         WHERE module = 'l10n_hu_zip' AND name = 'ir_cron_relink_partners'
        """
    )
