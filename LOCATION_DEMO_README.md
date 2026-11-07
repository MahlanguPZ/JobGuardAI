# Interview Location Safety Check — Presentation Demo

Three user-provided location strings are seeded into SQLite on startup. They are **unverified demonstration records**, not confirmed incidents or allegations against building owners, tenants or businesses.

1. ILPA House, CNR Commissioner & Von Weiligh Str
2. Manchester House, CNR Von Weilligh & Pritchard Str
3. The great experience, Curthberths of Chambers Building

The second spelling variant `Weilligh` is normalised to `Weiligh`. Other matching is exact after punctuation, case and common street/corner words are normalised. This is NOT a geocoding or real-world safety verification service.

Run `pip install -r requirements.txt`, then `python app.py`. Open the dashboard and use **Interview Location Safety Check**. The API is `POST /api/location-check` with JSON `{"address":"..."}`.

For the presentation, enter one of the three addresses above and then a different address to show the match/no-match responses. Explain that neither response establishes actual safety.

On Render without a persistent disk, SQLite state may reset on redeploy; the three demo entries are re-seeded at startup. Do not use this as a production incident database. Before using real incident reports, establish evidence review, correction/removal procedures, privacy controls, and an appropriate persistent datastore.
