# Frontend — Social Post Preview

Primary showcase UI for AddLyft social-post R&D.

- **URL:** http://127.0.0.1:5173/
- **Proxies** `/api` → backend on port **8000**
- Generates **text post + poster** from one brief (0–3 optional reference images)

## Run

Backend must already be running on 8000 (see [`../backend/README.md`](../backend/README.md)).

```powershell
cd frontend
npm install
npm run dev
```

## Notes

- **Generate post + poster** hits both `/api/generate` and `/api/generate-image`.
- **Regenerate** updates text only.
- Standalone image UI on port 8787 is optional; day-to-day use this app only.
