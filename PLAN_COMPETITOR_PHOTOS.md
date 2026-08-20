# Plan: Add Real Competitor Photos to Comparison Filmstrip

## Current State
- **AQUA products**: Real photos from `assets/produk/` (works ✓)
- **Competitors (LG, Midea, Polytron, Samsung, Sharp)**: Inline SVG placeholders (data:image/svg+xml) — user sees "kosong"

## Root Cause
`site/data/kompetitor.json` has NO image fields for any competitor model (50+ models across 5 brands).

## Options

| Option | Effort | Quality | Notes |
|--------|--------|---------|-------|
| **A. Manual curate** — find/download 50+ product photos, add `image_url` to JSON | High (2-3 hrs) | Best — controlled, consistent | Need to source from brand sites / GD / assets |
| **B. Scrape from `source_url`** — each model has manufacturer page URL | Medium (30 min script) | Variable — some pages block, layout differs | `source_url` exists for most models |
| **C. Map to local assets** — check if photos exist in `assets/produk/` or `assets/kompetitor/` | Low (if photos exist) | Good — if we have them | Need to audit asset folders |
| **D. Reliable placeholder service** — use `via.placeholder.com` with proper CORS or `dummyimage.com` | Low | OK for now — but user wants real | Not "real photos" |

## Recommended: Hybrid A + C + B fallback

1. **Audit local assets first** — check `assets/produk/`, `assets/`, `D:\AI\projects\mtms-aqua-haier-kb-foto\` for existing competitor photos
2. **Add `image` field to kompetitor.json** for models where we have photos
3. **For missing**: write quick scraper using `source_url` to extract `og:image` or main product image
4. **Fallback**: inline SVG (current) for any still missing

## Implementation Steps

### Step 1: Asset Audit (5 min)
```bash
# Check local folders for competitor brand photos
ls assets/produk/ | grep -iE "LG|MIDEA|POLYTRON|SAMSUNG|SHARP"
ls D:\AI\projects\mtms-aqua-haier-kb-foto\ | head -20
```

### Step 2: Add `image` field to kompetitor.json (15 min)
- For models with local assets: `image: "assets/produk/LG_GC-L257CQEL.jpg"`
- For models without: leave empty, will use fallback

### Step 3: Update `buildCompetitorFilmstrip()` (5 min)
```javascript
image: best.image || makePlaceholderImage(b.brand, best.model)
```

### Step 4: Optional — Scraper for missing (30 min)
- Use `source_url` to fetch page
- Extract `og:image` or first product image
- Update JSON

## Definition of Done
- [ ] All 6 cards in Top Mount filmstrip show real photos (not SVG)
- [ ] Bottom Mount (AQUA + LG + Samsung) shows real photos
- [ ] No console errors for image loading
- [ ] Visual check: cards look consistent, properly sized

## Next Session
Run asset audit → add images to JSON → deploy → verify visually.