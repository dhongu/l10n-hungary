Fills in the city and the county of Hungarian addresses from the postal code, using the
official Magyar Posta list loaded by `l10n_hu_city`.

- On the contact form, typing the postal code of a Hungarian address sets the city and the
  county. In Budapest the postal code gives the district (e.g. 1124 → Budapest XII).
- A postal code shared by several localities sets only the county; the city name, when it
  matches one of them, picks the locality.
- The action *Hungary: set city from ZIP* on contacts relinks the contacts whose city does
  not match their postal code. City names are compared without accents and punctuation
  ("Budapest, XXII." is "Budapest XXII").
- At install, the Hungarian contacts are relinked: directly on a small database, by the
  scheduled action *Hungary: link contacts to the city of their ZIP* in batches on a large one
  (it deactivates itself when done).
- The action *Hungary: delete unused cities not in the postal list* on cities deletes the
  Hungarian cities imported before (without postal code) that nothing uses any more.
