# Watch Atlas

An interactive watch discovery website launched with **1,244 references across 13 brands**, real product photos, source-linked specifications, and **1,230 sourced INR prices**. The catalog grows through verified weekly imports.

**Website:** https://gavriankur.github.io/watch-atlas/

## Explore

- Browse by brand and collection, or search by name and exact reference.
- Filter by INR budget, movement, case size, and style.
- Open detailed specifications and the underlying manufacturer or retailer sources.
- Compare up to six watches and save favorites on your device.
- Share individual model links or filtered catalog URLs.

### Catalog coverage at launch

| Brand | References |
| --- | ---: |
| Rolex | 30 |
| Omega | 31 |
| Rado | 358 |
| Fossil | 44 |
| Seiko | 211 |
| Casio | 31 |
| Tissot | 160 |
| Citizen | 40 |
| Titan | 79 |
| Timex | 65 |
| Hamilton | 111 |
| Longines | 58 |
| Swatch | 26 |

Counts include exact-reference variants such as different dials, materials, sizes, or straps. This is a curated snapshot rather than an exhaustive catalog of every watch.

## Run locally

Requires Python 3. No installation or build is needed to view the website.

```sh
python3 -m http.server 8080 --directory dist
```

Open http://localhost:8080/ in your browser.

## Project structure

```text
dist/
  index.html          Page structure and styles
  app.js              Search, filters, detail views, favorites, comparison
  catalog.js          Compiled browser catalog
  photos-v3/          Optimized product photographs
data/
  imports/            Source datasets with per-reference provenance
  catalog-seed-v2.json Original reference records retained by the compiler
  photo-map.json      Local photo paths and original image URLs
  import-report.json  Catalog counts and validation summary
scripts/
  build-catalog.py    Normalize, merge, and compile imported records
  cache-photos.py     Fetch and optimize product photos
.github/workflows/
  pages.yml           Publish dist/ to GitHub Pages
```

The website uses HTML, CSS, and browser JavaScript. Watch records are stored in files; there is no application server or external database service. Favorites use the visitor's browser storage and do not sync between devices.

## Update catalog data

1. Update or add source records in `data/imports/`. Preserve the exact reference, product and price sources, source-check dates, price type, specifications, and image URLs.
2. Rebuild the browser catalog:

   ```sh
   python3 prepare-catalog.py
   ```

3. For new photos, install the image-processing dependency and cache the images:

   ```sh
   python3 -m pip install -r requirements.txt
   python3 fetch-photos.py
   python3 prepare-catalog.py
   ```

4. Preview the site and commit the updated source datasets and `dist/` files.

The compiler currently recognizes the 13 listed brands. To add another brand, extend the brand and manufacturer-domain registries and display order in `scripts/build-catalog.py`.

Prices are dated snapshots from manufacturer India stores or named Indian retailers. They are not live inventory or price feeds. Manufacturer and retailer specifications are distinguished in the interface; unpublished or inconsistent fields are omitted or marked as not stated. Fourteen Swatch prices were unavailable when this snapshot was prepared. Each record shows separate price and specification check dates. A price refresh does not claim that specifications were rechecked.

## Publish updates

GitHub Pages is configured to use **GitHub Actions**. Pushing changes to `dist/` on `main` runs the `Publish Watch Atlas` workflow and updates the live website. The workflow can also be run manually from the repository's Actions tab.

The deployment publishes only `dist/`; import datasets and maintenance scripts remain available in the repository.

## Product imagery and brand names

Product photographs, trademarks, and brand names retain their respective ownership. The catalog records the product sources and original photograph URLs. No license to third-party assets is granted by this repository.

## Automatic weekly updates

The **Weekly catalog refresh** GitHub Actions workflow runs every **Sunday at 06:00 Asia/Kolkata** (`00:30 UTC`). GitHub may queue scheduled runs later than the requested time. You can also run it from the repository’s Actions tab with **Run workflow**. It runs on GitHub, even when your computer is off, and needs no API key or paid service.

Each run checks existing references against their recorded manufacturer or retailer price source. The supported sources are exact-reference Product/Offer structured data with explicit INR currency, Rado India price metadata, and India-only Shopify storefront feeds. Prices stay in rupees; the updater does not convert currencies, estimate prices, or substitute a different seller. It preserves the original check date whenever verification fails.

New-model discovery currently covers Seiko, Timex, Titan, Fossil, Tissot, and Hamilton. Omega’s retailer feed refreshes existing prices, but new Omega records require editorial review because conflicting retailer specifications were encountered. New models from the other brands remain curated imports. Each automatic addition requires a single-variant or exact-reference listing, at least eight published specification fields, a positive INR price, and a successfully cached real product photograph. Each brand is limited to 12 additions and 30 candidate inspections per run. Multi-variant retailer pages and incomplete listings are skipped.

Validation runs before publishing. Unavailable sources retain their last verified records; missing prices never become zero. Changes over 50% are quarantined for review. The run fails without publishing if fewer than 25% of existing references can be verified, if a model disappears, or if catalog/photo validation fails. Blocking or a changed source format can prevent some brands from refreshing; a successful run does not mean every price was reverified. The website displays its last successful check and verified-price count, with per-watch dates for the remaining entries.

Successful runs commit price observations, accepted new models, cached photos, and a detailed report, then deploy GitHub Pages in the same workflow. This is necessary because commits made with GitHub’s built-in workflow token do not start another push-triggered workflow. No personal access token is stored. Source imports remain intact; dated observations in `data/refresh-overrides.json` are applied after imports. Actual price changes are recorded in `data/price-history.jsonl`; run coverage, blocked sources, and quarantined observations are in `data/refresh-report.json` and the downloadable Actions artifact.

To run the same checks locally:

```sh
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests
python3 scripts/refresh-catalog.py
python3 prepare-catalog.py
python3 scripts/validate-catalog.py
```

Public-repository scheduled workflows can be disabled by GitHub after 60 days without repository activity. Check the Actions tab if weekly updates stop. No source access restrictions are bypassed.
