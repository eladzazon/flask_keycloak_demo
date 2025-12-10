<img width="895" height="324" alt="image" src="https://github.com/user-attachments/assets/e320dbee-b9b0-45b6-ac4b-0240177f190d" /># Flask Keycloak Integration Guide

This guide provides step-by-step instructions to set up a Flask application with Keycloak authentication from scratch, including setting up Keycloak locally using Docker.

## 1. Environment Setup (Docker)

We use `docker-compose` to spin up a Keycloak instance backed by a PostgreSQL database.

1.  **Create/Verify `docker-compose.yaml`**:
    Ensure your `docker-compose.yaml` is in the root directory with the following content:
    ```yaml
    version: '3.8'
    services:
      postgres:
        image: postgres:15
        container_name: keycloak-db
        environment:
          POSTGRES_DB: keycloak
          POSTGRES_USER: keycloak
          POSTGRES_PASSWORD: password
        volumes:
          - postgres_data:/var/lib/postgresql/data
        healthcheck:
          test: ["CMD-SHELL", "pg_isready -U keycloak"]
          interval: 10s
          timeout: 5s
          retries: 5
      keycloak:
        image: quay.io/keycloak/keycloak:latest
        container_name: keycloak-app
        command: start-dev
        environment:
          KEYCLOAK_ADMIN: admin
          KEYCLOAK_ADMIN_PASSWORD: admin
          KC_DB: postgres
          KC_DB_URL: jdbc:postgresql://postgres:5432/keycloak
          KC_DB_USERNAME: keycloak
          KC_DB_PASSWORD: password
        ports:
          - "8080:8080" # Maps local port 8080 to container port 8080
        depends_on:
          postgres:
            condition: service_healthy
    volumes:
      postgres_data:
    ```

2.  **Start the Services**:
    Open a terminal in the project root and run:
    ```bash
    docker-compose up -d
    ```
    Wait for Keycloak to start. You can check logs with `docker logs -f keycloak-app`. Once it says "Listening on: 0.0.0.0:8080", it's ready.

    **Access Keycloak**: [http://localhost:8080](http://localhost:8080)

## 2. Keycloak Configuration

You need to configure a Realm, Client, and Users manually.

1.  **Login to Admin Console**:
    *   URL: [http://localhost:8080/admin](http://localhost:8080/admin)
    *   Username: `admin`
    *   Password: `admin`

2.  **Create a Realm**:
    *   Hover over the dropdown in the top-left corner (currently says **Master**).
    *   Click **Create Realm**.
    *   Name: `my-realm`
    *   Click **Create**.

3.  **Create a Client** (The Flask App):
    *   Go to **Clients** in the left menu.
    *   Click **Create client**.
    *   **Settings**:
        *   Client type: `OpenID Connect` (default)
        *   Client ID: `my-flask-app`
        *   Click **Next**.
    *   **Capability Config**:
        *   **Client authentication**: **ON** (This enables the Client Secret).
        *   Click **Next**.
    *   **Access Settings**:
        *   Valid redirect URIs: `http://localhost:5000/*`
        *   Post logout redirect URIs: `http://localhost:5000/*`
        *   Click **Save**.

4.  **Get Client Secret**:
    *   In the **my-flask-app** client details, go to the **Credentials** tab.
    *   Copy the **Client secret**. You will need this for the `.env` file.

5.  **Configure Group Mapper** (Crucial for seeing groups in Flask):
    *   **Click separate "Clients" menu**: Go to **Clients** in the left-hand sidebar (NOT "Client scopes").
    *   **Select your client**: Click on `my-flask-app` in the list to open its settings.
    *   **Go to the Tab**: Inside `my-flask-app` settings, click the **Client scopes** tab at the top of the page.
    *   **Click the Dedicated Scope**: You will see a list of assigned scopes. Click the blue link text that says **`my-flask-app-dedicated`** (Description usually: "Dedicated scope and mappers for this client").
    *   Click **Add mapper** -> **By configuration**.
    *   Select **Group Membership**.
    *   **Name**: `groups`
    *   **Token Claim Name**: `groups`
    *   **Full group path**: `OFF` (Uncheck this to get just group names like "group-a", otherwise you get "/group-a").
    *   **Add to ID token**: `On`
    *   **Add to access token**: `On`
    *   **Add to lightweight access token**: `Off`
    *   **Add to userinfo**: `On`
    *   **Add to token introspection**: `On` (Optional, good for verification).
    *   Click **Save**.

6.  **Create Groups**:
    *   Go to **Groups** in the left menu.
    *   Click **Create group**.
    *   Name: `group-a`.
    *   Click **Create**.

7.  **Create a User & Assign Group**:
    *   **Create**:
        *   Go to **Users** in the left menu.
        *   Click **Create new user**.
        *   Username: `testuser`
        *   **Email**: `testuser@example.com`
        *   **First name**: `Test`
        *   **Last name**: `User`
        *   Email verified: `On`
        *   Click **Create**.
    *   **Join Group** (Immediately after creating):
        *   Click the **Groups** tab (at the top of the user page).
        *   Click **Join Group**.
        *   Check the box for `group-a` and click **Join**.
    *   **Set Password**:
        *   Click the **Credentials** tab.
        *   Click **Set password**.
        *   Password: `password` (and confirm).
        *   Temporary: `Off`.
        *   Click **Save**.

## 3. Flask Project Setup

1.  **Configure Environment Variables**:
    Create or edit the `.env` file in `flask_keycloak_demo/.env`.
    
    ```properties
    # Keycloak URL (Note port 8080 matches docker-compose)
    OIDC_ISSUER=http://localhost:8080/realms/my-realm
    
    # Client ID from Step 2.3
    OIDC_CLIENT_ID=my-flask-app
    
    # Client Secret from Step 2.4
    OIDC_CLIENT_SECRET=PASTE_YOUR_SECRET_HERE
    
    # Flask Security
    FLASK_SECRET_KEY=dev_secret_key_change_this_in_prod
    ```

2.  **Install Dependencies**:
    Open a terminal in the project root.
    ```bash
    pip install -r flask_keycloak_demo/requirements.txt
    ```
    
    The project relies on the following key libraries:
    *   **Flask**: The web framework.
    *   **Authlib**: Handles OpenID Connect (OIDC) integration securely.
    *   **requests**: Standard HTTP library.
    *   **python-dotenv**: Loads configuration from `.env` file.

## 4. Running the Project

1.  **Start the Flask App**:
    ```bash
    python flask_keycloak_demo/app.py
    ```

2.  **Verify**:
    *   Open your browser to [http://localhost:5000](http://localhost:5000).
    *   Click **Login**.
    *   You should be redirected to the Keycloak login page.
    *   Log in with `testuser` / `password`.
    *   You should be redirected back to the **Profile** page.

3.  **Check Data**:
    *   **Identity**: should show "Test User", "testuser", and "testuser@example.com".
    *   **Groups**: should show a list containing `group-a`.

## 5. Screenshots

1. **Main Page (Without login)**:
<img width="895" height="324" alt="image" src="https://github.com/user-attachments/assets/d33c83d7-f4db-437c-ad41-72d6167fd2e7" />

2. **Keycloak Login Page**:
<img width="771" height="555" alt="image" src="https://github.com/user-attachments/assets/bf8fa677-5861-4cce-8823-eebcbe7f5e3d" />

3. **Profile Page (After login)**:
<img width="1144" height="911" alt="image" src="https://github.com/user-attachments/assets/e04b46ed-910a-4b11-afb6-2467b7c66426" />

4. **Main Page (After login)**:
<img width="578" height="344" alt="image" src="https://github.com/user-attachments/assets/6566ddc9-8060-4e95-957c-474003759174" />
