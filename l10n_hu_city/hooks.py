# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def _migrate_hungarian_city_ids(env):
    hungary = env.ref("base.hu", raise_if_not_found=False)
    if not hungary:
        _logger.warning(
            "l10n_hu_city: base.hu country record not found, skipping migration."
        )
        return

    # Build lookup indexes from res.city so we hit the DB only once
    all_hu_cities = env["res.city"].search([("country_id", "=", hungary.id)])

    # zip -> city  (a zip can theoretically map to multiple cities, e.g. Budapest districts)
    zip_index: dict[str, list] = {}
    name_index: dict[str, list] = {}

    for city in all_hu_cities:
        if city.zipcode:
            zip_index.setdefault(city.zipcode.strip(), []).append(city)
        if city.name:
            name_index.setdefault(city.name.strip().lower(), []).append(city)

    def _resolve_city(zip_code, city_name):
        """Return (res.city record, match_type) or (None, None)."""
        if zip_code:
            candidates = zip_index.get(zip_code.strip())
            if candidates:
                if len(candidates) == 1:
                    return candidates[0], "zip"
                if city_name:
                    needle = city_name.strip().lower()
                    for c in candidates:
                        if c.name.strip().lower() == needle:
                            return c, "zip+name"
                # Multiple candidates, no name to narrow — return first
                return candidates[0], "zip"

        # Fallback: city name only
        if city_name:
            candidates = name_index.get(city_name.strip().lower())
            if candidates:
                return candidates[0], "name"

        return None, None

    # Migrate res.partner
    partners = env["res.partner"].search([
        ("country_id", "=", hungary.id),
        ("city_id", "=", False),     # skip already-resolved records
    ])
    _logger.info(
        "l10n_hu_city: processing %d Hungarian res.partner records.", len(partners)
    )

    partner_ok = partner_warn = 0
    for partner in partners:
        city_rec, match_type = _resolve_city(partner.zip, partner.city)
        if city_rec:
            partner.write({
                "city_id": city_rec.id,
                "city": city_rec.name,
                "state_id": city_rec.state_id.id,
            })
            partner_ok += 1
        else:
            _logger.warning(
                "l10n_hu_city: could not resolve city for res.partner id=%d "
                "name=%r zip=%r city=%r",
                partner.id, partner.name, partner.zip, partner.city,
            )
            partner_warn += 1

    _logger.info(
        "l10n_hu_city: res.partner migration done — "
        "matched: %d, unresolved: %d",
        partner_ok, partner_warn,
    )


def _post_init_hook(env):
    _migrate_hungarian_city_ids(env)