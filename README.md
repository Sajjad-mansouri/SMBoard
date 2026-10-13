# SMBoard

**SMBoard** is a Trello-like board management application built with Django and Django REST Framework. It provides a way to organize projects and tasks using boards, lists, and cards, with supporting features for collaboration, attachments, activity tracking, and email notifications.

The project demonstrates backend development with Django, REST API design, authentication, data modeling, automated testing, and integration with background task processing. Its frontend is built with HTML, CSS, and vanilla JavaScript.

## Live Demo

**Website:** [https://smboard.pythonanywhere.com](https://smboard.pythonanywhere.com)

The deployed version is intended as a demonstration of the project. Feature availability may depend on the deployment configuration and running background services.

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Configuration](#environment-configuration)
- [Running the Application](#running-the-application)
- [API Reference](#api-reference)
- [Authentication](#authentication)
- [Background Tasks and Notifications](#background-tasks-and-notifications)
- [Automated Testing](#automated-testing)
- [Deployment](#deployment)
- [Security and Configuration Notes](#security-and-configuration-notes)
- [License](#license)

## Features

### Board Management

- Create and manage boards.
- Support public and private board visibility.
- Customize board backgrounds and colors.
- Manage board membership.
- Watch boards for activity updates.
- Access board activity history.

### Lists and Cards

- Organize cards within board lists.
- Update list and card ordering.
- Archive lists and cards.
- Copy cards.
- Assign members to boards and cards.
- Apply labels to cards.
- Manage card-related information, including start and due dates.

### Collaboration and Attachments

- Add comments to cards.
- Create checklists and checklist items.
- Attach files and images to cards.
- Attach external links.
- Track activities associated with boards.
- Configure notification preferences.

### User Accounts and Authentication

- User registration.
- Email-based registration confirmation.
- Login and logout.
- Password reset workflows.
- JWT-based API authentication.
- Access and refresh tokens.
- User profile management.
- Account update and deletion endpoints.
- Custom authentication backend.

### REST API

- REST endpoints for boards, lists, cards, comments, checklists, labels, attachments, and memberships.
- JWT token obtain, refresh, and verification endpoints.
- Board and card search endpoints.
- Pagination support.
- Request throttling.
- Filtering support through `django-filter`.
- Dedicated API permissions and serializers.

### Email Notifications

- Immediate activity notification emails.
- Daily activity digest tasks.
- Weekly activity digest tasks.
- User-configurable notification settings.
- HTML and plain-text email templates.
- Background task processing with Celery.
- Automatic retry configuration for selected email delivery failures.

> Note: Features defined in the source code may require additional configuration or running services. In particular, Celery-based notifications depend on a configured message broker and running worker and scheduler processes.

## Technology Stack

### Backend

| Technology | Purpose |
|---|---|
| Python 3.11 | Programming language |
| Django 5.2.4 | Web framework |
| Django REST Framework 3.17.1 | REST API development |
| Django REST Framework SimpleJWT 5.5.1 | JWT authentication |
| Celery 5.6.3 | Background task processing |
| django-filter 25.2 | API filtering |

### Frontend

| Technology | Purpose |
|---|---|
| HTML5 | Page structure |
| CSS3 | Styling and layout |
| Vanilla JavaScript | Client-side interactions |

The frontend uses standard HTML, CSS, and JavaScript without a JavaScript framework.

### Database and Supporting Libraries

| Technology | Purpose |
|---|---|
| SQLite | Database configuration used for the project |
| Pillow | Image processing |
| python-decouple | Environment-based configuration |
| Django Sites framework | Site-related configuration |

### Testing

| Technology | Purpose |
|---|---|
| pytest | Test execution |
| pytest-django | Django testing integration |
| factory_boy | Test object factories |
| Faker | Test data generation |

The project uses pytest and pytest-django for automated testing.

## Project Structure

```text
smboard/
├── account/
│   ├── migrations/
│   ├── templates/
│   ├── tests/
│   ├── admin.py
│   ├── apps.py
│   ├── backends.py
│   ├── forms.py
│   ├── middleware.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
│
├── api/
│   ├── auth/
│   │   └── views.py
│   ├── board/
│   │   ├── pagination.py
│   │   ├── permissions.py
│   │   ├── serializers.py
│   │   └── views.py
│   ├── tests/
│   └── urls.py
│
├── board/
│   ├── migrations/
│   ├── templates/
│   ├── tests/
│   ├── admin.py
│   ├── apps.py
│   ├── fields.py
│   ├── signals.py
│   ├── tasks.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
│
├── config/
│   ├── asgi.py
│   ├── celery.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── media/
├── static/
├── manage.py
├── pytest.ini
└── requirements.txt
```

### Application Responsibilities

- **`account/`** — User account functionality, registration, authentication backends, forms, middleware, templates, and account views.
- **`board/`** — Core board-management functionality, data models, views, templates, signals, and Celery notification tasks.
- **`api/`** — REST API endpoints, authentication views, serializers, permissions, pagination, and API tests.
- **`config/`** — Django settings, URL configuration, WSGI and ASGI entry points, and Celery configuration.
- **`static/`** — Static frontend assets.
- **`media/`** — Uploaded media files.
- **`migrations/`** — Database schema migrations for the Django applications.
- **`tests/`** — Automated tests organized within the relevant applications.

## Getting Started

These instructions describe how to run the project in a local development environment.

### Prerequisites

- Python 3.11 or a compatible Python version.
- pip.
- Git.
- A compatible message broker if you want to execute Celery tasks.
- An SMTP service if you want to test actual email delivery.

### 1. Clone the Repository

Replace the placeholder with the actual repository URL.

```bash
git clone <your-repository-url>
cd smboard
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Linux or macOS:

```bash
source venv/bin/activate
```

On Windows:

```powershell
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root, in the same directory as `manage.py`.

See [Environment Configuration](#environment-configuration) for an example.

### 5. Apply Database Migrations

```bash
python manage.py migrate
```

### 6. Create an Administrator Account

```bash
python manage.py createsuperuser
```

### 7. Start the Development Server

```bash
python manage.py runserver
```

Open the local website at:

`http://127.0.0.1:8000/`

## Environment Configuration

The project reads configuration values from environment variables using `python-decouple`.

The following is an example for a local SQLite development setup. It contains placeholders, not working email credentials.

```dotenv
# Django
SECRET_KEY=replace_with_a_secure_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
TIME_ZONE=UTC

# Database: SQLite
DATABASAE_ENGINE=django.db.backends.sqlite3
DATABASAE_NAME=db.sqlite3
DATABASAE_USER=
DATABASAE_PASSWORD=
DATABASAE_HOST=
DATABASAE_PORT=

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_password
DEFAULT_FROM_EMAIL=your_email@example.com

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0

# Site
SITE_ADDRESS=http://localhost:8000
SITE_DOMAIN=localhost:8000
HOST_ASYNC_ABILITY=True
```

### Configuration Notes

**Database variable names**

The supplied settings use the prefix `DATABASAE_`, including the spelling shown above. These names must match the current settings code. If you correct the spelling in `settings.py`, update the environment variable names accordingly.

**SQLite**

The example configures SQLite with a database file named `db.sqlite3` in the project root. SQLite is appropriate for this project's current setup, but the database path and file permissions must be appropriate for the environment in which the application runs.

**Email**

Replace the example SMTP host and credentials with the values supplied by your email provider. Registration confirmation, password reset, and activity notifications may depend on working email configuration.

**Celery**

The example broker URL assumes Redis is installed and reachable on the local machine. A broker must be available before Celery workers can process queued tasks.

**Site URL configuration**

`SITE_ADDRESS` and `SITE_DOMAIN` are separate settings in the supplied configuration. Configure them consistently with the URLs expected by the application. Confirm that any code referencing these settings uses names actually defined in `settings.py`.

**Secrets**

Do not commit `.env` files containing real credentials, secret keys, or other sensitive configuration to Git.

## Running the Application

### Django Development Server

Start the application with:

```bash
python manage.py runserver
```

The default local address is:

`http://127.0.0.1:8000/`

### Django Administration

Create a superuser if you have not already done so:

```bash
python manage.py createsuperuser
```

The default Django administration route is:

`http://127.0.0.1:8000/admin/`

Access depends on the configured authentication and permissions.

### Celery Worker

If you have configured and started the message broker, launch a Celery worker in a separate terminal:

```bash
celery -A config worker -l info
```

### Celery Beat

To execute scheduled tasks, launch Celery Beat separately:

```bash
celery -A config beat -l info
```

Running the Django development server alone does not start Celery workers or the scheduler.

## API Reference

The API is mounted under `/api/`.

The routes below reflect the URL configuration provided for the project. Exact HTTP methods, request payloads, and permissions depend on the corresponding views and serializers.

### Authentication Endpoints

| Endpoint | Purpose |
|---|---|
| `/api/token/` | Obtain JWT tokens |
| `/api/token/refresh/` | Refresh an access token |
| `/api/token/verify/` | Verify a token |
| `/api/login/` | API login |
| `/api/logout/` | API logout |

### Router-Registered Resources

The following resources are registered through Django REST Framework's `DefaultRouter`.

| Endpoint | Resource |
|---|---|
| `/api/boards/` | Boards |
| `/api/cards/` | Cards |
| `/api/board-lists/` | Board lists |
| `/api/checklists/` | Checklists |
| `/api/checklist-items/` | Checklist items |
| `/api/comments/` | Comments |
| `/api/card-files/` | Card file attachments |
| `/api/card-images/` | Card image attachments |
| `/api/card-labels/` | Card labels |
| `/api/card-members/` | Card memberships |
| `/api/board-members/` | Board memberships |
| `/api/link-attachments/` | Link attachments |
| `/api/notification-settings/` | Notification settings |

### Additional API Routes

| Endpoint | Purpose |
|---|---|
| `/api/guest-boards/` | Guest board endpoint |
| `/api/user/` | User-related endpoint |
| `/api/current-user/` | Current-user endpoint |
| `/api/search/board/` | Board search |
| `/api/search/card/` | Card search |
| `/api/closed/` | Closed-board endpoint |
| `/api/board/<pk>/` | Board detail endpoint |
| `/api/board-list-order/` | List ordering |
| `/api/card-order/` | Card ordering |
| `/api/board-watch/` | Board watching |
| `/api/card-watch/` | Card watching |
| `/api/copy-card/<pk>/` | Card copying |
| `/api/card/update-archived/<pk>/` | Card archive status |
| `/api/list/update-archived/<pk>/` | List archive status |
| `/api/public-board-address/<pk>/` | Public board address |
| `/api/activities/<board>/` | Board activity history |
| `/api/update-profile/` | Profile update |
| `/api/update-user/` | User update |
| `/api/card-list/` | Card-list endpoint |
| `/api/delete-account/` | Account deletion |
| `/api/setting-config/` | Settings configuration |
| `/api/message/` | Message endpoint |

### Account Pages

Account-related HTML views are included under `/account/`.

| URL | Purpose |
|---|---|
| `/account/register/` | Registration |
| `/account/register/<uidb64>/<token>/` | Registration confirmation |
| `/account/register/registration_done/` | Registration completion |
| `/account/login/` | Login |
| `/account/password_reset/` | Password reset request |
| `/account/password_reset/done/` | Password reset request completion |
| `/account/reset/<uidb64>/<token>/` | Password reset confirmation |
| `/account/reset/done/` | Password reset completion |

The exact route names and behavior are determined by `account/urls.py`.

## Authentication

The application uses Django's authentication system and Django REST Framework SimpleJWT for API authentication.

The supplied configuration defines:

| Setting | Configured value |
|---|---|
| Access token lifetime | 1 minute |
| Refresh token lifetime | 1 day |
| Authentication backend | Django ModelBackend and a custom email backend |
| REST API authentication | JWT authentication |

The short access-token lifetime means clients may need to refresh tokens frequently. Refresh-token behavior depends on the SimpleJWT settings, including whether rotation is enabled.

The API also defines request throttling:

| User category | Configured limit |
|---|---|
| Anonymous users | 1,000 requests per day |
| Authenticated users | 5,000 requests per day |

These values describe the supplied settings and should not be interpreted as a guarantee of the deployed application's effective limits without verifying the active configuration.

## Background Tasks and Notifications

SMBoard includes Celery tasks for email notifications.

| Task | Purpose |
|---|---|
| `send_email_task` | Sends an individual activity notification email |
| `send_bulk_activity_email_task` | Sends a digest of recent activities |
| `daily_notification` | Dispatches tasks for daily email digest recipients |
| `weekly_notification` | Dispatches tasks for weekly email digest recipients |

The email tasks use plain-text and HTML templates and define retry behavior for selected SMTP and timeout failures.

### Scheduled Tasks

The supplied Celery Beat configuration defines the following schedules:

- **Daily notifications:** currently scheduled every minute.
- **Weekly notifications:** scheduled for Monday at 09:00.

The daily schedule is a testing-oriented configuration rather than a typical production schedule. Review it before using the application in an environment where frequent notification dispatches are undesirable.

Celery-based functionality requires the relevant broker, worker, and scheduler to be configured and running. The presence of task definitions in the repository does not establish that these services are active on the deployed website.

## Automated Testing

The project uses pytest and pytest-django.

Run the tests from the project root:

```bash
pytest
```

To run tests for an individual application:

```bash
pytest account/tests/
pytest board/tests/
pytest api/tests/
```

These commands assume the test directories contain tests discoverable by pytest.

The latest reported test run collected **890 test items**. The available output did not include the final test summary, so the number of passing tests has not been confirmed here.

For an accurate portfolio description, update this section after a successful test run with the final passing, failing, and skipped counts.

## Deployment

The live demonstration is hosted on PythonAnywhere:

**[https://smboard.pythonanywhere.com](https://smboard.pythonanywhere.com)**

The project uses SQLite for its current database configuration. Deployment configuration may differ from local development, especially for environment variables, file paths, email settings, and background tasks.

Before deploying or updating the application, verify the following:

- Environment variables are configured in the hosting environment.
- `SECRET_KEY` is private and `DEBUG` is disabled for production use.
- `ALLOWED_HOSTS` includes the deployed hostname.
- Database paths and permissions are correct.
- Static files are configured and served appropriately.
- Media uploads use a suitable writable location.
- Email credentials are configured securely.
- Any required Celery broker, worker, and scheduler are actually available.

Do not assume that optional background services are active merely because their configuration and task definitions exist in the codebase.

## Security and Configuration Notes

- Keep secret keys, SMTP credentials, and other secrets out of version control.
- Do not expose sensitive environment values in logs.
- Avoid printing email credentials or other secrets during application startup.
- Review public-board access and membership permissions before deployment.
- Verify file upload validation and media storage configuration.
- Review token lifetimes and refresh-token behavior against the application's security requirements.
- Confirm that production settings are loaded by the deployed WSGI application.
- Keep dependencies updated and test changes before deploying them.

## License

No license has been specified in this README.

If you plan to distribute the project or explicitly grant others permission to reuse its code, add an appropriate `LICENSE` file and update this section to match it.
