# Course Catalog API

Backend на FastAPI с каталогом курсов (Pydantic-модель, фильтрация, сортировка, пагинация через Depends).

## Как запустить

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
fastapi dev main.py
```

Сервер: http://127.0.0.1:8000, документация: http://127.0.0.1:8000/docs

## What was verified (Lab 4)

| Request | Result |
| --- | --- |
| `/` | `{"message": "Course Catalog API is running"}` |
| `/courses` | 6 courses, `ai-integration` first (32 likes), `api-design` last (11) |
| `/courses/web-security` | one course |
| `/courses/nope` | 404, `{"detail": "Course not found"}` |
| `/courses?is_elective=true` | 2 courses: ai-integration, api-design |
| `/courses?is_elective=false` | 4 courses: modern-frontend, web-security, backend-fastapi, databases-postgresql |
| `/courses?sort=title` | 6 courses alphabetically: ai-integration, api-design, backend-fastapi, modern-frontend, databases-postgresql, web-security |
| `/courses?page=1&page_size=2` | ai-integration, modern-frontend |
| `/courses?page=2&page_size=2` | web-security, backend-fastapi |
| `/courses?page=3&page_size=2` | databases-postgresql, api-design |
| `/courses?page=4&page_size=2` | `[]` |

## What changed (Lab 5)

- **CORS**: `CORSMiddleware` allows the origin `http://localhost:3000` (scheme + host + port, no trailing slash).
  It is needed because the browser (Client Components on the Next.js page) calls this API directly from another origin.
  Requests from Next.js Server Components do not need CORS.
- **camelCase in JSON**: models inherit from `CamelModel` (`alias_generator=to_camel`, `validate_by_name=True`,
  `validate_by_alias=True`), so `is_elective` is sent as `isElective`. Query parameters keep their names (`?is_elective=true`).
- **New routes**:
  - `POST /courses/{course_id}/like` → `200`, e.g. `{"id": "web-security", ..., "likes": 22}`; unknown id → `404`
  - `POST /enrollments` with body `{"courseId": "web-security", "studentName": "Aigerim"}` →
    `201` `{"courseId": "web-security", "studentName": "Aigerim", "id": 1}`; name shorter than 2 chars → `422`; unknown course → `404`
  - `GET /enrollments` → list of enrollments (in memory, reset on restart)
