# PictApp – Image Upload

Simple Flask web application with user authentication and image upload functionality.

## Features
- User registration, login, logout
- Upload images for authenticated users
- List and delete user images
- Image files are stored on disk (synced folder)
- PostgreSQL stores image metadata only (no binary data)

## Storage
Uploaded images are stored on disk under a shared directory:

/var/lib/pictapp/uploads/

Each user has a separate subdirectory.
The same path is used on all application VMs.

## Database
PostgreSQL stores metadata only:
- user_id
- original filename
- stored filename
- file path
- creation timestamp

## Run locally
1. Create and activate a virtual environment
2. Install dependencies from "requirements.txt"
3. Set required environment variables:
- `FLASK_SECRET_KEY` (any random string)
- `DATABASE_URL` (SQLAlchemy URL), e.g.:
    ```text
    postgresql+psycopg2://pictapp_user@192.168.56.13:5432/pictapp
    ```
    The database password should be stored in `~/.pgpass` to avoid exposing credentials.
4. Start the application:
    ```bash
    python app.py
    ```
5. Open the app in a browser:
    ```text
    http//localhost:5000
    ```

## Notes
- The application fails fast on startup if required DB tables (`users`, `images`) are missing.
- In our setup, the DB schema is applied via Jenkins/Ansible from the infrastructure repository (`ansible/roles/db/files/schema.sql`).
- In a deployed environment the app is accessed via load balancer or directly via VM IP
- `UPLOAD_ROOT` can be overridden via an environment variable in deployed environments.

