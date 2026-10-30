# ©  2026 Terrabit
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
{
    "name": "Hungary - City from ZIP",
    "summary": "Fill in the Hungarian city and county from the postal code",
    "version": "19.0.1.1.2",
    "author": "Terrabit",
    "website": "https://www.terrabit.ro",
    "category": "Localization",
    "countries": ["hu"],
    "license": "LGPL-3",
    "depends": ["l10n_hu_city"],
    "data": [
        "data/ir_actions_server.xml",
        "data/ir_cron.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "maintainers": ["dhongu"],
}
