# -*- coding: utf-8 -*-
# Terrabit: replaces the post-install partner migration of DO Tech. The partners are
# linked to their city by l10n_hu_zip, in batches, which also corrects a wrong city.
import logging
import unicodedata

from odoo.tools import SQL

_logger = logging.getLogger(__name__)

# xml id, name of the county as loaded by data/res_state_data.xml
COUNTIES = [
    ("BU", "Budapest"),
    ("BK", "Bács-Kiskun"),
    ("BA", "Baranya"),
    ("BE", "Békés"),
    ("BZ", "Borsod-Abaúj-Zemplén"),
    ("CS", "Csongrád-Csanád"),
    ("FE", "Fejér"),
    ("GS", "Győr-Moson-Sopron"),
    ("HB", "Hajdú-Bihar"),
    ("HE", "Heves"),
    ("JN", "Jász-Nagykun-Szolnok"),
    ("KE", "Komárom-Esztergom"),
    ("NO", "Nógrád"),
    ("PE", "Pest"),
    ("SO", "Somogy"),
    ("SZ", "Szabolcs-Szatmár-Bereg"),
    ("TO", "Tolna"),
    ("VA", "Vas"),
    ("VE", "Veszprém"),
    ("ZA", "Zala"),
]


def _normalize(name):
    name = unicodedata.normalize("NFKD", name or "")
    return "".join(c for c in name if not unicodedata.combining(c)).strip().casefold()


def _matches(existing_name, county_name):
    # "Csongrád" is the name of Csongrád-Csanád before 2020
    existing, county = _normalize(existing_name), _normalize(county_name)
    return existing == county or county.startswith(existing + "-")


def _state_references(env):
    """Stored many2one columns pointing to res.country.state, as (table, column)."""
    fields = env["ir.model.fields"].sudo().search(
        [("relation", "=", "res.country.state"), ("ttype", "=", "many2one"), ("store", "=", True)]
    )
    references = []
    for field in fields:
        model = env.get(field.model)
        if model is None or model._abstract or not model._auto or field.name not in model._fields:
            continue
        if not model._fields[field.name].store or model._fields[field.name].company_dependent:
            continue
        references.append((model._table, field.name))
    return references


def _usage(env, references, state_id):
    total = 0
    for table, column in references:
        env.cr.execute(
            SQL("SELECT COUNT(*) FROM %s WHERE %s = %s", SQL.identifier(table), SQL.identifier(column), state_id)
        )
        total += env.cr.fetchone()[0]
    return total


def _adopt_existing_counties(env):
    """Reuse the Hungarian counties already in the database.

    Without it, a database that already has the counties (imported by hand, often
    twice) gets one more copy of each. For every county of the module, the most used
    existing county of the same name gets the xml id of the module, so that loading
    the data updates it; its duplicates are merged into it.
    """
    hungary = env.ref("base.hu", raise_if_not_found=False)
    if not hungary:
        return
    states = env["res.country.state"].with_context(active_test=False).search([("country_id", "=", hungary.id)])
    if not states:
        return
    references = _state_references(env)
    data = env["ir.model.data"].sudo()
    for xml_id, county_name in COUNTIES:
        if data.search_count([("module", "=", "l10n_hu_city"), ("name", "=", xml_id)]):
            continue
        candidates = states.filtered(lambda s, n=county_name: _matches(s.name, n))
        if not candidates:
            continue
        keep = max(candidates, key=lambda s: (_usage(env, references, s.id), -s.id))
        for duplicate in candidates - keep:
            for table, column in references:
                env.cr.execute(
                    SQL(
                        "UPDATE %s SET %s = %s WHERE %s = %s",
                        SQL.identifier(table),
                        SQL.identifier(column),
                        keep.id,
                        SQL.identifier(column),
                        duplicate.id,
                    )
                )
            _logger.info("l10n_hu_city: county %s (id %s) merged into id %s", duplicate.name, duplicate.id, keep.id)
        env.invalidate_all()
        (candidates - keep).unlink()
        data.create(
            {"module": "l10n_hu_city", "name": xml_id, "model": "res.country.state", "res_id": keep.id}
        )
        _logger.info("l10n_hu_city: existing county %s (id %s) reused as %s", keep.name, keep.id, xml_id)
        states -= candidates


def _pre_init_hook(env):
    _adopt_existing_counties(env)
