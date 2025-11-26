
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

	Running tests (Windows PowerShell)
	---------------------------------

	Follow these steps to run the automated test suite locally (Windows PowerShell examples):

	1. Activate the virtual environment (from the project root):

	```powershell
	python -m venv .venv
	.\.venv\Scripts\Activate.ps1
	```

	2. Install dependencies (if not already installed):

	```powershell
	pip install --upgrade pip
	pip install -r requirements.txt
	```

	3. Run tests using Django's test runner:

	- Run the whole Django test suite (verbosity for more details):

	```powershell
	.venv\Scripts\python.exe manage.py test -v2
	```

	- Run tests for specific apps (faster when iterating):

	```powershell
	.venv\Scripts\python.exe manage.py test library users -v2
	```

	- Run a single test (example):

	```powershell
	.venv\Scripts\python.exe manage.py test users.tests.test_jwt.JWTFlowTests.test_access_token_expires -v2
	```

	- Run quietly (less output):

	```powershell
	.venv\Scripts\python.exe manage.py test -q
	```

	- Save test output to a file (useful if your terminal session is interrupted):

	```powershell
	.venv\Scripts\python.exe manage.py test -v2 > test-output.txt 2>&1
	```

	4. Optionally run tests with `pytest` (if installed):

	```powershell
	python -m pytest -q
	```

	5. Run coverage (if you want coverage reports):

	```powershell
	pip install coverage
	coverage run -m pytest
	coverage report -m
	```

	Notes and tips
	- The Django test runner creates and destroys a temporary test database automatically; you do not need to run migrations before tests.
	- If a specific test is flaky because of time-based behavior (e.g., token expiry), prefer running just that single test while iterating.
	- Archived smoke scripts are available in `scripts/archived/` and can be run directly with the project virtualenv Python, for example:

	```powershell
	.venv\Scripts\python.exe scripts\archived\api_smoke_full.py
	```

	If you want, I can also add a short `Makefile` or PowerShell script to simplify these commands.
	- `GET/POST /api/v1/library/authors/`
	- `GET/POST /api/v1/library/books/` — supports filters: `?category=...&author=...&status=...`, search (`?search=...`) and ordering (`?ordering=title`)
	- `GET/POST /api/v1/library/borrowings/` — create borrowing (authenticated); POST body uses `book` (UUID) and optional `days` integer
	- `POST /api/v1/library/borrowings/{id}/return/` — mark as returned (will assign to next reservation if exists)
	- `POST /api/v1/library/borrowings/{id}/renew/` — renew borrowing (adds days); renewal blocked if another user has a reservation
	- `GET /api/v1/library/borrowings/overdue/` — list overdue borrowings
	- `GET /api/v1/library/borrowings/borrowers/` — list users who have active borrowings
	- `GET /api/v1/library/reservations/` — create/list reservations
	- `GET /api/v1/library/users/<user_id>/borrowed-books/` — list books currently borrowed by a user

