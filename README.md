# Statistiekhub-backend-django

This repository is for the backend django part of the statistiek-hub:
a Management module for publishing statistics from the Research and Statistics Department of the municipality of Amsterdam

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