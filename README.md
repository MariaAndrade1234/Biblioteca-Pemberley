# Pemberley Library

Pemberley Library is a Django-based REST API for managing books, authors and borrowings.

This repository contains a small library management backend built with Django and Django REST Framework. It implements models for Authors, Books, Borrowings and Reservations, exposes REST endpoints, and includes business rules for borrowing (availability, limits, renewals, reservations). The project uses SQLite for persistence and JWT for authentication.

---

## Quick Start (Windows / PowerShell)

Prerequisites:
- Python 3.11+ (the project was developed and tested with Python 3.13)
- Git

1. Clone the repository and switch to the feature branch if needed:

```powershell
git clone <your-repo-url>
cd Biblioteca-Pemberley
git checkout bf-feature/library-models
```

2. Create and activate the virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

4. Run migrations and create a superuser:

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

5. Run the development server:

```powershell
python manage.py runserver
# Open http://127.0.0.1:8000/api/docs/ for API docs (Swagger)
```

---

## Tests

Run the Django test suite (unit + API tests):

```powershell
python manage.py test
```

Or run pytest (if installed):

```powershell
python -m pytest
```

---

## Authentication (JWT)

The API uses JWT authentication. Obtain a token pair with:

```bash
POST /api/v1/token/
Content-Type: application/json

{
	"username": "<username>",
	"password": "<password>"
}
```

The response contains `access` and `refresh` tokens. Use the `access` token in the `Authorization` header for protected endpoints:

```
Authorization: Bearer <access_token>
```

To refresh an access token:

```
POST /api/v1/token/refresh/
{ "refresh": "<refresh_token>" }
```

---

## Main API Endpoints (summary)

- Users
	- `GET /api/v1/users/` — list users (supports `?status=active|inactive`, pagination)
	- `POST /api/v1/users/` — create user
	- `POST /api/v1/token/` — obtain JWT
	- `POST /api/v1/token/refresh/` — refresh JWT

- Library
	- `GET/POST /api/v1/library/authors/`
	- `GET/POST /api/v1/library/books/` — supports filters: `?category=...&author=...&status=...`, search (`?search=...`) and ordering (`?ordering=title`)
	- `GET/POST /api/v1/library/borrowings/` — create borrowing (authenticated); POST body uses `book` (UUID) and optional `days` integer
	- `POST /api/v1/library/borrowings/{id}/return/` — mark as returned (will assign to next reservation if exists)
	- `POST /api/v1/library/borrowings/{id}/renew/` — renew borrowing (adds days); renewal blocked if another user has a reservation
	- `GET /api/v1/library/borrowings/overdue/` — list overdue borrowings
	- `GET /api/v1/library/borrowings/borrowers/` — list users who have active borrowings
	- `GET /api/v1/library/reservations/` — create/list reservations
	- `GET /api/v1/library/users/<user_id>/borrowed-books/` — list books currently borrowed by a user

Notes:
- Only staff users can change the `status` of a `Book`. Non-staff attempts will return an error.
- Business rules enforced:
	- Users can borrow books only if book status is `available`.
	- A user cannot have more than 5 active borrowings.
	- Inactive users cannot borrow books.
	- `return_date` must be after `borrow_date`.
	- Renewals are blocked when another user has an active reservation for the book.

---

## Development notes and architecture

- Business logic is isolated in `library/services.py` (SRP): borrowing/return/renew/reserve operations live in the service layer and use transactions for consistency.
- Serializers and ViewSets implement the API surface; `BookSerializer` and `BookViewSet` include protections so only staff can mutate `status`.
- Models are defined in `library/models.py` with UUID primary keys where requested.
- OpenAPI docs are available at `/api/schema/` and Swagger UI at `/api/docs/` (powered by drf-spectacular).

---

## Submission / reviewers

Branch for this feature: `bf-feature/library-models`.

When creating a PR, please add the following reviewers: `Jarbas` and `Robson`.

---

## License

See `LICENSE` in the repository root.

---

If you want, I can also:
- add example curl requests for the most common flows,
- enrich the OpenAPI documentation with examples and descriptions for each endpoint,
- or prepare a PR and add the reviewers.
# Biblioteca-Pemberley
Sistema de gerenciamento de livros
