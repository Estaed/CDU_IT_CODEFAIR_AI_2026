# Historical housing context

Source: Northern Territory Government, Department of Housing, Local Government and Community Development,
[Urban Public Housing Wait Times, Wait List and Allocations December 2020](https://data.nt.gov.au/dataset/urban-public-housing-wait-times-wait-list-and-allocations-december-2020).

- CSV: [31 December 2020 resource](https://data.nt.gov.au/dataset/2dcfe0b7-6b4d-4633-9761-cc6128d1bbfb/resource/3e6fef35-1eb4-4387-ab06-80e422652ab5/download/open-data-urban-public-housing-wait-times-wait-list-and-allocations-31-december-2020.csv), saved verbatim as `urban-public-housing-2020-12.csv`.
- Licence checked at the dataset source on 3 October 2026: **Creative Commons Attribution (CC BY)**. Its licence link points to [the CC BY licence family](https://opendefinition.org/licenses/cc-by/); the source does not specify a version.
- Period: estimated wait times and applicant counts as at **31 December 2020**; allocations cover **1 January–31 December 2020**. The portal lists publication as 31 March 2021.
- Source and CSV read/downloaded: **3 October 2026**.

The source has no priority-specific wait-time figure. The case header therefore shows the
Darwin/Casuarina **general urban housing** estimate for **2–3 bedrooms: 2–4 years**. Both bedroom
columns report the same range, so they are combined without averaging or implying a precise
wait. This is a regional housing-size context for a family application, not a determination of
the applicant's bedroom entitlement. The source reports a range, not a mean or median.

The header credits NT open data, states December 2020, and labels the estimate historical and
not priority-specific. It is over five years old on the date read, not a current wait-time
prediction. This local CSV is served offline through `/api/context`; it is never added to the
pipeline view, checks, flags, outcomes or decision record. Attribution is retained in this
README and linked on the case header. The downloaded CSV's original bytes are unchanged.
