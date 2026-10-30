# -*- coding: utf-8 -*-
{
    "name": "Hungarian City Database - Official Postal List",
    "version": "19.0.1.1.0",
    "icon": "static/description/l10n.png",
    "images": [
        "static/description/hungarian_city_list_screenshot.png",
        "static/description/hu_city.png",
        "static/description/hu_city_2.png",
        "static/description/hu_city_3.png",
        "static/description/hu_city_4.png",
    ],
    'website': 'https://www.dotech.hu/kiegeszito-funkciok',
    "category": "DO Tech/Localization",
    "author": "DO Tech (OdooTech Zrt.)",
    'summary': "Official Magyar Posta city and postal code database with automatic partner migration.",
    'description': """
Hungarian City Database - Official Postal List
===============================================
* Ships with the complete, official city database from Magyar Posta.
* Pre-loaded with postal codes, city names, and counties (states).
* Automatically migrates and links existing Hungarian partners upon installation.
    """,
    "depends": ["base_address_extended"],
    "data": [
        "data/res_state_data.xml",
        "data/res_city_data.xml",
        "data/res_country_data.xml",
    ],
    "pre_init_hook": "_pre_init_hook",
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    "auto_install": False,
    "cloc_exclude": ["**/*"],
}
