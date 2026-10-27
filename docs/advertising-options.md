# Advertising options

The current advertising integration uses Google AdSense:

- **Google AdSense** — general display advertising; the site is currently
  under Google review.
- **Carbon Ads** — contextual advertising for developer and technology
  audiences.
- **EthicalAds** — privacy-conscious contextual advertising.
- **Microsoft Advertising** — a general-purpose alternative network.
- **Affiliate links** — commissions from relevant gaming equipment or
  software recommendations.
- **Direct sponsorships** — paid placements negotiated with a gaming brand or
  community.

## Integration rules

Only add a provider after checking its current terms and Vercel's commercial
use rules. Keep each provider in a separate, clearly identified ad slot; do
not load multiple networks in the same slot. Never incentivize clicks,
redirect users unexpectedly, or add intrusive pop-ups.

Before enabling personalized advertising, add the required privacy policy and
consent flow for the visitors' jurisdictions. The project currently keeps
AdSense conditional on the publisher ID in `web/index.html`.
