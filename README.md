# Watch Atlas

An interactive watch discovery website with **1,244 references across 13 brands**, real product photos, source-linked specifications, and **1,230 sourced INR prices**.

**Website:** https://gavriankur.github.io/watch-atlas/

## Explore

- Browse by brand and collection, or search by name and exact reference.
- Filter by INR budget, movement, case size, and style.
- Open detailed specifications and the underlying manufacturer or retailer sources.
- Compare up to six watches and save favorites on your device.
- Share individual model links or filtered catalog URLs.

### Catalog coverage

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

Prices are dated snapshots from manufacturer India stores or named Indian retailers. They are not live inventory or price feeds. Manufacturer and retailer specifications are distinguished in the interface; unpublished or inconsistent fields are omitted or marked as not stated. Fourteen Swatch prices were unavailable when this snapshot was prepared. Price and specification source checks are dated 13–14 October 2026 on individual entries.

## Publish updates

GitHub Pages is configured to use **GitHub Actions**. Pushing changes to `dist/` on `main` runs the `Publish Watch Atlas` workflow and updates the live website. The workflow can also be run manually from the repository's Actions tab.

The deployment publishes only `dist/`; import datasets and maintenance scripts remain available in the repository.

## Product imagery and brand names

Product photographs, trademarks, and brand names retain their respective ownership. The catalog records the product sources and original photograph URLs. No license to third-party assets is granted by this repository.
