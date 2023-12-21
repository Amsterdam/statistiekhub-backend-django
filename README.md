# Statistiekhub-backend-django

This repository is for the backend django part of the statistiek-hub.

## Install instructions

### Development environment

See the Makefile in this project for the description of relevant commands.

1. From the root directory run:

   ```bash
   make build
   ```

   **Note:** If you get the error:
   > Got permission denied while trying to connect to the Docker daemon socket

   Try one of these options:

    1. Manage docker as a non-root user:

       Create the docker group:

        ```bash
        sudo groupadd docker
        ```

       Add your user to the docker group

        ```bash
        sudo usermod -aG docker $USER
        ```

       Log out and in so that your group membership is re-evaluated.

    2. or set read-write permissions to `docker.sock`:

        ```bash
        sudo chmod 666 /var/run/docker.sock
        ```

2. Apply migrations:

   ```bash
   make migrate
   ```

   **Note:** If you get the warning that database structure is out-of-date, then first make migrations before applying them:

   ```bash
   make migrations
   ```

3. Check if the build worked

   ```bash
   make dev
   ```

4. When you confirm the successful build, stop the running container with `Ctrl-C` and fill the database with testdata

   ```bash
    make load_fixtures 
   ```

5. Last, when you want to add a super-user for django admin, go to the terminal of the backend docker container

   ```bash
   python manage.py createsuperuser
   ```

6. Now all is set and you can run the Composer

   ```bash
   make dev
   ```

Test your development environment on [localhost:8000/admin](http://localhost:8000/admin).

### Acceptance environment

1. Rename `.example.env` to `.acc.env`:

   ```bash
   mv .example.env .acc.env
   ```

2. Replace example variable values with proper remote database values:

   ```conf
   DB_HOST=<remote_url>
   DB_PORT=5432
   DB_NAME=<postgre_database_name>
   DB_SCHEMA=<postgre_database_schema>
   DB_USER=<postgre_database_user>
   DB_PASS=<postgre_database_password>
   ```

3. Build Docker images:

   ```bash
   make build
   ```

4. Launch Django localy with the remote database:

   ```bash
   make app
   ```

5. Login on http://127.0.0.1:80/admin/ or just http://127.0.0.1/admin/

6. If it asks for admin user, make one with:

   ```bash
   docker compose -f docker-compose-acc.yml run --rm app sh -c "python manage.py createsuperuser"
   ```
   
### Known issues

1. If you encounter a problem with the cache table, go to the terminal of the backend docker container
   ```bash
   python manage.py createcachetable
   ```

2. If you encounter a problem with the postgresql database, which mapped to the ip-adres / port
   ```bash
   sudo service postgresql stop
   ```