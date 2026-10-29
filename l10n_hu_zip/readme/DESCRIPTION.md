Fills in the city and the county of Hungarian addresses from the postal code, using the
official Magyar Posta list loaded by `l10n_hu_city`.

- On the contact form, typing the postal code of a Hungarian address sets the city and the
  county. In Budapest the postal code gives the district (e.g. 1124 → Budapest XII).
- A postal code shared by several localities sets only the county; the city name, when it
  matches one of them, picks the locality.
- The action *Hungary: set city from ZIP* on contacts relinks the contacts whose city does
  not match their postal code. It also runs once when the module is installed.
