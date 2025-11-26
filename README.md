
Pemberley Library is a Django-based REST API for managing books, authors and borrowings.

This repository contains a small library management backend built with Django and Django REST Framework. It implements models for Authors, Books, Borrowings and Reservations, exposes REST endpoints, and includes business rules for borrowing (availability, limits, renewals, reservations). The project uses SQLite for persistence and JWT for authentication.

---


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
```

---


Run the Django test suite (unit + API tests):

```powershell
python manage.py test
```

Or run pytest (if installed):

```powershell
python -m pytest
```

---


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


Replace placeholders like <ACCESS_TOKEN>, <BOOK_UUID>, <BORROWING_ID> and <USER_ID> before running the commands.

1) Obtain JWT tokens (login):

```bash
curl -X POST http://127.0.0.1:8000/api/v1/token/ \
	-H "Content-Type: application/json" \
	-d '{"username":"apiuser","password":"Password123"}'
```

2) Create an author (authenticated):

```bash
curl -X POST http://127.0.0.1:8000/api/v1/library/authors/ \
	-H "Authorization: Bearer <ACCESS_TOKEN>" \
	-H "Content-Type: application/json" \
	-d '{"name":"Test Author","biography":"Bio","birth_date":"1980-01-01","nationality":"BR"}'
```

3) Create a book (authenticated):

```bash
curl -X POST http://127.0.0.1:8000/api/v1/library/books/ \
	-H "Authorization: Bearer <ACCESS_TOKEN>" \
	-H "Content-Type: application/json" \
	-d '{"title":"Test Book","author_id":"<AUTHOR_UUID>","book_description":"Desc","category":"Fiction","publisher":"Pemberley Press","publication_date":"2020-01-01","ISBN":"ISBN-EXAMPLE-1234","page_count":123,"last_edition":"2023-01-01","language":"EN","cover_url":"http://example.com/cover.jpg"}'
```

4) Borrow a book (authenticated):

```bash
curl -X POST http://127.0.0.1:8000/api/v1/library/borrowings/ \
	-H "Authorization: Bearer <ACCESS_TOKEN>" \
	-H "Content-Type: application/json" \
	-d '{"book":"<BOOK_UUID>", "days":7}'
```

5) Renew a borrowing (authenticated):

```bash
curl -X POST http://127.0.0.1:8000/api/v1/library/borrowings/<BORROWING_ID>/renew/ \
	-H "Authorization: Bearer <ACCESS_TOKEN>" \
	-H "Content-Type: application/json" \
	-d '{"extra_days":7}'
```

6) Return a borrowed book (authenticated):

```bash
curl -X POST http://127.0.0.1:8000/api/v1/library/borrowings/<BORROWING_ID>/return/ \
	-H "Authorization: Bearer <ACCESS_TOKEN>"
```

7) List overdue borrowings (authenticated):

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/library/borrowings/overdue/?user_id=<USER_ID>" \
	-H "Authorization: Bearer <ACCESS_TOKEN>"
```

8) List books currently borrowed by a user (anyone):

```bash
curl -X GET http://127.0.0.1:8000/api/v1/library/users/<USER_ID>/borrowed-books/ \
	-H "Authorization: Bearer <ACCESS_TOKEN>"
```

These examples use the local development server at `http://127.0.0.1:8000/` and assume you already created a user and obtained a JWT access token. For PowerShell, you may need to adjust quoting or use the `--%` operator if curl is aliased.



- Business logic is isolated in `library/services.py` (SRP): borrowing/return/renew/reserve operations live in the service layer and use transactions for consistency.
- Serializers and ViewSets implement the API surface; `BookSerializer` and `BookViewSet` include protections so only staff can mutate `status`.
- Models are defined in `library/models.py` with UUID primary keys where requested.
- OpenAPI docs are available at `/api/schema/` and Swagger UI at `/api/docs/` (powered by drf-spectacular).

---


Branch: use the current feature branch (for example `bf-refactor/serializer-meta-and-tests`) or `main`.

When creating a PR, please add the following reviewers: `Jarbas` and `Robson`.

---


See `LICENSE` in the repository root.

---
A Django REST API for managing books, authors and borrowings.
