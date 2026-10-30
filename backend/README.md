# Smart Gallery FastAPI service

Run from this directory:

<!-- MacOS -->
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
<!-- WindowOS -->
```bash
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Health: http://127.0.0.1:8000/health
- OpenAPI UI: http://127.0.0.1:8000/docs

## Deploy on Render

Commit and push the backend sources and configuration to the connected GitHub
branch before deploying. Create a **Web Service** with these settings:

| Setting | Value |
| --- | --- |
| Root Directory | `backend` |
| Language | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |

Select Free compute for the demo and a region close to your users. The service's
`.python-version` selects Python 3.13, matching the version used for local testing.
If `PYTHON_VERSION` is already set in Render, it overrides that file; remove the
override or set a compatible fully qualified 3.13 version.

Once the service is live, check `https://<service>.onrender.com/health`.
Set the backend's `CORS_ORIGINS` to the frontend's exact HTTPS origin.
On Vercel, set `NEXT_PUBLIC_API_URL` to the backend's HTTPS base URL and redeploy
the frontend. Browser uploads go directly to the backend.

## API and image processing

`POST /analyze` accepts multipart `files` and a JSON string `manifest`.
The manifest must have one entry per file in the same upload order:

```json
[{ "id": "client-generated-id", "relativePath": "folder/photo.jpg" }]
```

IDs must be unique. Responses include the same IDs, source-relative paths,
JPEG data-URL previews, score/classification fields, EXIF capture time,
recommendations, `bestShotNeedsReview`, summary, skipped-file issues, and the parameters used.
`exposureMetrics` contains the existing `brightnessMean`, `darkClippingRatio`
and `highlightClippingRatio` measurements for the light indicator. They are
display data; exposing them does not change scores or decision thresholds.
File paths from the manifest are display metadata, never filesystem targets.

Limits: 200 files, 30 MiB per file, 200 MiB total. Decoding happens server-side;
corrupt images are skipped and identified by ID. All-invalid requests return 422
with issue details. Manifest errors return 400; size violations return 413.

Images are processed in a temporary directory that is deleted after each
request. There is no server-side persistent photo store.

The pipeline is based on the core functions in `presentation_results.ipynb`,
with the demo's `similarity.strategy: "exif_time_or_phash"` extension:
EXIF orientation → RGB/1024 resize → quality scores → separate time/pHash pools
→ provisional Best Shot / near-tie review → quality-gap recommendations.
Timed photos first use capture-time differences with complete linkage in
seconds. Each original group's span cannot exceed `exif_time_window_seconds`.
Then `timed_phash_threshold` may join whole time groups/singletons for matches
outside the window. Untimed photos use `phash_threshold` and configured `linkage`.
The two pHash thresholds are independent; changing the untimed threshold never
affects timed grouping.
SSIM is removed from this version. Its old strategy and non-null threshold
are rejected. The internal pair table compares photos only within their own
timestamp pool. Time matches are labelled `exif_time` (no Hamming distance),
beyond-window comparisons `timed_phash`, and untimed comparisons `phash`.
Pair decisions are not final membership.
Timestamp extraction also reads the nested Exif IFD used by phone/camera files.

`sharpnessLabel` predicts `sharp` or `blur`. The experimental dataset has four
types (Sharp, Slight Blur, Motion Blur, Defocus Blur; 30 images each); the three
blur types all map to `blur` during evaluation. The classifier does not predict
blur subtypes. `exposureLabel` predicts all three dataset classes: `normal`,
`underexposed`, `overexposed` (30 images each in the experiment).
`similarityGroup` identifies a predicted cluster, not an image class. The
similarity dataset has 20 groups of 5; inference discovers groups in each upload
without requiring that count. See `../colab/` for evaluation by original blur
type, confusion matrices, pairwise grouping scores and ARI.

The demo adds an optional missing-timestamp fallback beyond the notebook.
`similarity.missing_exif_policy` controls it:

- `"phash"`: if both timestamps are missing/unreadable, compare pHash alone using
  `phash_threshold`. This is enabled in the current runtime JSON. Timed photos
  never group with untimed photos, even if their images are identical.
- `"strict"`: missing timestamps exclude a pair, as in the notebook. This is
  the backward-compatible default if the setting is omitted.

Pairs with only one valid timestamp never group together. Both pools use the
existing quality and recommendation rules. The current strategy skips the
notebook's pHash-based rescue/merge stages and their guards, using its own timed
pHash step instead. Time matches never have to pass pHash. Whole time groups
merge only if every cross pair passes time OR the timed pHash threshold, using
complete linkage. The pHash step cannot split existing time groups or chain
incompatible groups together. It has no additional time cap.

`similarity.timed_phash_threshold` accepts integers `0`–`64`; larger is looser.
It starts at `29` in the runtime JSON. Omit it or set it to `null` for time-only
grouping. Reasons distinguish time-only groups from those joined through pHash.
The health response, analysis parameters and missing-EXIF reasons report the
active policy. Recorded notebook metrics and `selection` metadata describe the
original strict experiment, not the fallback's accuracy.

Settings in `config/best_parameters.json` are validated and loaded at startup;
restart the service and analyze again after changing them. Do not silently substitute notebook
fallback values or use development metric fields as image-quality scores.
This update adds only `similarity.timed_phash_threshold`, preserving existing
thresholds and weights. Missing linkage and tie margin
use the notebook's defaults: `complete` and `2.0`. Add `similarity.linkage`
and `recommendation.best_shot_tie_margin` explicitly when testing selected values.
Rescue/merge need a finite non-negative `exif_time_window_seconds`.

To compare against the original notebook, use `strategy: "exif_phash"` and
`missing_exif_policy: "strict"`. Only this legacy mode uses EXIF+pHash for timed
photos and enables the notebook's refinements/guards.
`run_core_pipeline(..., use_rescue=False)` disables both refinements in legacy mode.
Use `use_group_merge=False` with rescue enabled for rescue-only experiments.
These toggles are Python comparison tools, not browser controls. The health
endpoint reports whether legacy refinements are active.

Configure allowed frontend origins with `CORS_ORIGINS`, comma-separated.
Defaults: `http://localhost:3000,http://127.0.0.1:3000`.

Tests:

```bash
pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
PYTHONPATH=. python tests/check_notebook_parity.py --notebook /path/to/presentation_results.ipynb
```

See the root README for the full frontend/demo workflow.
The notebook comparison runs in legacy strict mode; separate regression tests
cover time-first groups, separate pHash thresholds, beyond-window matches,
preservation of original time groups, fallback groups, separation
of mixed timestamp batches, quality decisions and API reporting.
