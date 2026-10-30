# l10n-hungary

Localizare Odoo pentru Ungaria (Terrabit).

## Module

- `l10n_hu_city` — județele (megye, cu coduri ISO 3166-2:HU) și localitățile din lista
  oficială Magyar Posta, cu codul poștal. Preluat din modulul „Hungarian City Database -
  Official Postal List” al DO Tech (OdooTech Zrt.), versiunea `19.0.1.0.20260506`, licență
  LGPL-3. Autorul și licența rămân ale DO Tech. Datele sunt nemodificate; față de original:
  - depinde doar de `base_address_extended`, nu de `l10n_hu` (care ar instala automat
    e-Factura NAV și rapoartele HU într-o bază fără companie maghiară);
  - înainte de instalare preia județele maghiare deja existente (după nume, fără diacritice)
    și unește dublurile, ca să nu apară încă un set de județe;
  - legarea partenerilor de localitate nu se mai face la instalare: o face `l10n_hu_zip`,
    pe loturi.
- `l10n_hu_zip` — completează localitatea și județul din codul poștal (în Budapesta,
  districtul) și corectează contactele legate de altă localitate decât cea a codului poștal:
  la instalare, direct pe o bază mică sau printr-o acțiune programată, pe loturi, pe una mare.
  Acțiunea „Hungary: delete unused cities not in the postal list” (pe orașe) șterge apoi
  orașele maghiare importate înainte, rămase nefolosite.

## Surse oficiale

- Lista codurilor poștale Magyar Posta:
  https://net.posta.hu/dashboard/public/dashboard-ui/iranyitoszam-kereso/download-as-table
