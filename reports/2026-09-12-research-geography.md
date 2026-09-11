# Research — NT geography layer (communities, roads, distances)

Checked 2026-09-12. Scope: notes.md research items 1 and 2. Primary sources only; blog and
aggregator hits were used as leads and are not cited as facts.

---

## 1. Community locations and populations

### Claim A — BushTel exposes community data through a public, unauthenticated JSON API
**Verdict: confirmed (undocumented API, verified by direct call 2026-09-12).**
- List: `GET https://bushtel.nt.gov.au/api/Community?community=&boundary=0` -> HTTP 200, 797 records.
  Per record: `Id`, `DefaultName`, alias names, `Point{Latitude,Longitude}`, `CommunityTypeName`,
  `ElectorateName`, `LocalGovernmentWardName`. **No population in the list response.**
- Detail: `GET https://bushtel.nt.gov.au/api/Community/{id}` -> adds `Population`,
  `PopulationSource` ("Based on ABS 2021 Census SA1"), `Sa1Code`, `NTRegionName`,
  `Capabilities.RoadAccess`, a `Services` entry `Accessible by road` with free-text comments, and a
  prose `Description` that usually states km and drive time to the nearest town. Example (Wugularr,
  id 581): pop 636, -14.5548 / 133.1142, BIG RIVERS, "approximately 118 km south east of Katherine
  ... around 1.5 hours drive".
- Type mix across the 797: Family Outstation 635, **Major 59**, Town Camp 45, **Minor 37**,
  Village 13, Town 6, City 2.
- I pulled the detail record for all 96 Major+Minor communities on 2026-09-12: **89 carry a
  population figure, 84 carry a km distance in the description, 23 mention wet season or flooding.**
  Regions: Central Australia 26, Big Rivers 23, East Arnhem 18, Top End 17, Barkly 12.
- Endpoint found by reading `https://bushtel.nt.gov.au/public/dist/bundle.js?v=2.5.26`; the parameter
  set quoted in a 2017 GovHack page (`?communityTerm=&lotTerm=...`) now returns 404.
- **What it changes:** this is the seed source. Major+Minor = 96 communities, trims to 60-80 by
  population or region; coordinates, population, region and a town distance all arrive together.
  Fetch once, freeze to a CSV in the repo — do not call the API at demo time.

### Claim B — BushTel data is released under an open licence
**Verdict: unknown — TBD, needs validation.** The site footer says only "Copyright © 2026 Northern
Territory Government" and links `https://nt.gov.au/copyright-disclaimer-and-privacy`, which returns
403 behind Cloudflare to automated fetches (checked 2026-09-12). The data.nt.gov.au portal's own
attribution terms do not extend to BushTel. **What would settle it:** reading that copyright page in
a browser, or emailing opendata@nt.gov.au. Until then, cite BushTel with attribution and do not
claim a CC licence in the report.

### Claim C — data.nt.gov.au publishes a CC-BY dataset of remote communities with coordinates
**Verdict: confirmed, but no population.** "Remote Communities with 3G/4G Mobile Coverage 2021"
(https://data.nt.gov.au/dataset/remote-communities-with-mobile-coverage): XLSX plus a PDF data
quality statement, GPS coordinates, licence stated as Creative Commons Attribution, published
18 Mar 2021, last updated 30 Jun 2022, excludes Darwin/Palmerston/Tennant Creek/Katherine/
Alice Springs/Nhulunbuy. Portal attribution format at https://data.nt.gov.au/about (CC version not
stated there).
**What it changes:** the licence-clean cross-check for BushTel coordinates, and a second citable
source for the datasets judging criterion.

### Claim D — ABS gives an open-licensed geography for Aboriginal communities
**Verdict: confirmed for boundaries; population needs a separate download.** ILOC 2021 (ASGS Ed. 3,
Jul 2021 - Jun 2026), 1,139 ILOCs nationally, minimum about 90 people, built from whole SA1s;
GeoPackage and ESRI Shapefile, published 6 Oct 2021, **CC BY 4.0**
(https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-3-july-2021-june-2026/access-and-downloads/digital-boundary-files).
Also mirrored as "ILOC (2021) – ASGS Ed. 3" on the Digital Atlas of Australia.
**Contradiction to record, not resolve:** BushTel populations are SA1-based, ABS publishes
ILOC-based counts; the two will not agree for the same named place. **TBD:** which exact ABS Census
product gives ILOC population counts as a downloadable CSV — not verified today.
**What it changes:** polygons for the map and a licence-clean citation; not the seed table.

---

## 2. Roads, closures, distances

### Claim E — roadreport.nt.gov.au has a machine-readable feed
**Verdict: confirmed (undocumented), for current conditions only.**
`GET https://roadreport.nt.gov.au/api/Obstruction/GetAll` -> HTTP 200 JSON, **80 records, every one
`status: "CURRENT"`** (checked 2026-09-12). Fields: `roadName`, `obstructionType`, `restrictionType`,
`dateFrom` / `dateTo` / `dateActive` / `dateLastUpdated`, `startPoint` and `endPoint` lat-lon,
`comment`, `locationComment`. Type counts today: Roadworks 25, "Maximum GVM 4.5 Tonne, Light Vehicles
Only" 15, Changing Surface Conditions 15, Road Damage 11, Flooding 3. Some `dateFrom` values go back
to 2018, so records are long-lived, but the feed is a snapshot, not a history.
Endpoint found in `https://roadreport.nt.gov.au/main.47bd91e6a1a678ce.js`. Licence: the app links the
same Cloudflare-blocked nt.gov.au copyright page — **TBD**; the DITRDCSA catalogue entry for
"Road Report Northern Territory" says "Licence not specified" and lists only an HTML map.
**What it changes:** a real, dated closure snapshot can seed the synthetic road-status field and can
be shown live in the demo. Any historical closure series must be synthetic and labelled as such.

### Claim F — there is an open dataset of NT unsealed roads or seasonal access
**Verdict: contradicted / not found.** A `road` search on data.nt.gov.au (50 results, 2026-09-12)
returns "NT Government Controlled Roads" (KMZ, Creative Commons Attribution, last updated
23 Jun 2021, custodian Department of Logistics and Infrastructure; **no surface-type field documented
on the page**), "Darwin Road Maintenance Area", a PRP listing, and bike counts. No closure,
seasonal-access or sealed/unsealed dataset. OpenStreetMap (via the `ogc.ntlis.nt.gov.au` basemap or a
direct extract) carries a `surface` tag and is the remaining option — **TBD, not verified today.**
**What it changes:** wet-season vulnerability per community must be modelled, not sourced. The 23 of
96 BushTel road-access comments mentioning wet season or flooding are the defensible anchor.

### Claim G — an official Darwin / Katherine / Tennant Creek / Alice Springs to community distance table exists
**Verdict: unknown, none found.** Only tourism distance charts between major centres. The BushTel
`Description` km figure (84 of 96 communities) is the only per-community, government-published
distance located. **What would settle it:** an NT DLI freight or road-distance schedule; not found.

### Claim H — a free routing option is usable without an API key
**Verdict: confirmed with conditions, all three options.**
- **OSRM demo server** (`router.project-osrm.org`): no key. Policy page last edited 17 Dec 2020
  (https://github.com/Project-OSRM/osrm-backend/wiki/Api-usage-policy): reasonable non-commercial use,
  maximum about 1 request per second, must display ODbL and OSRM attribution, valid User-Agent, no
  uptime guarantee, access withdrawable without reason. Fine for a one-off offline pre-computation of
  a 96x4 matrix, not for demo-time calls.
- **OpenRouteService**: API key required (free account). Documented per-request limits
  (https://openrouteservice.org/restrictions/, checked 2026-09-12): Matrix 3,500 location pairs per
  request, Directions maximum 6,000 km. **Daily and per-minute quotas TBD:** the plans page is
  JS-rendered and returned no figures; secondary sources claim 2,000 directions/day with 40/minute,
  and another claims 2,500/day — contradictory, both unverified.
- **Haversine**: no terms, no network, deterministic. Correct default here; road distance is
  systematically longer, so document the fallback as a stated limitation.
**What it changes:** compute a frozen distance matrix once (OSRM, respecting 1 request/second) and
ship the CSV; haversine as the documented in-code fallback. No routing call at demo time.

---

## Recommended sources for the PRD

1. **BushTel community API** — seed table: name, lat/lon, population (ABS 2021 SA1), NT region,
   community type, road access, km to nearest town. Licence TBD; attribute explicitly.
2. **data.nt.gov.au — Remote Communities with 3G/4G Mobile Coverage 2021** (XLSX, CC Attribution,
   updated 30 Jun 2022) — licence-clean coordinate cross-check.
3. **ABS ILOC 2021 boundaries** (GeoPackage / Shapefile, CC BY 4.0, 6 Oct 2021) — map polygons.
4. **roadreport.nt.gov.au `/api/Obstruction/GetAll`** — dated current-closure snapshot; licence TBD.
5. **data.nt.gov.au — NT Government Controlled Roads** (KMZ, CC Attribution, 23 Jun 2021).
6. **OSRM demo server** under its usage policy, for a one-off frozen distance matrix; **haversine**
   as the documented fallback.

## Where this belongs

PRD data section (sources 1-5, with licence status and the "frozen snapshot, synthetic history"
rule); CLAUDE.md Part 2 only for the routing/distance decision (source 6) and the "no network calls
at demo time" constraint.
