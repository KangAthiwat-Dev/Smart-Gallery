# Best Shot

Best Shot is a mobile-application prototype for reviewing a photo library. It
demonstrates photo-quality scores, similar-photo grouping, best-shot selection,
and safe cleanup recommendations without deleting any files automatically.

The current version is frontend-only. Analysis results come from deterministic
mock data so the interface and user flow can be evaluated before a real image
processing backend is connected.

## Prototype flow

1. Select or drag multiple images onto the upload area.
2. Review the selected files locally in the browser.
3. Open the sample analysis to explore the gallery, similarity groups, photo
   details, and summary.

Selected files are used only for local previews. They are not uploaded, and the
sample analysis does not inspect their contents yet.

## Features

- Multiple-image selection with drag-and-drop support
- Local image previews and file-size summaries
- Gallery filtering by keep, review, and delete recommendation
- Similar-photo groups with a highlighted best shot
- Per-photo quality, sharpness, and exposure scores
- Estimated storage savings and a non-destructive cleanup summary
- Responsive layouts suitable for demonstrating a mobile app concept

## Tech stack

- Next.js 16 App Router
- React 19 and TypeScript
- Tailwind CSS 4
- Base UI and shadcn UI primitives
- Lucide icons

## Getting started

Install dependencies and start the development server:

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Quality checks

```bash
npm run check
npm run build
```

`npm run check` runs ESLint with zero warnings allowed and performs a full
TypeScript check.

## Project structure

```text
app/                  Routes, layouts, metadata, and global styles
components/           Application components
components/ui/        Generated reusable UI primitives
components/upload/    Photo-selection experience
data/                 Deterministic mock analysis data
lib/                  Shared utilities
types/                Analysis domain types
```

## Mock data and backend integration

Mock results live in `data/mock-data.ts` and follow the contracts in
`types/analysis.ts`. When a backend is introduced, replace those imports with a
data-access layer while keeping the page and component interfaces stable.

A production implementation should validate uploaded file types and sizes on
the server, run the image-analysis pipeline outside the browser, persist an
analysis session, and require explicit user confirmation before deleting any
photo.

## Current limitations

- No backend, authentication, persistence, or real image analysis
- Selected images and mock analysis results are not linked
- Remote sample images require an internet connection
- Recommendations are illustrative and must not be treated as deletion actions
