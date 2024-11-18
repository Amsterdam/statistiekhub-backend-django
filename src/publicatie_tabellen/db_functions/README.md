## When the function code is changed

Unmigrate the db_function migration - like `0002_db_functions migration` - in the app `publicatie_tabellen` and then migrate again.


1. Go back 1 migration before the one we want to rerun.

    In this example we have 2 migrations in the app `publicatie_tabellen`
    * 0001_initial
    * 0002_db_functions

    Go back to the first migration before the one to rerun. This will unmigrate all the above, in our case drop all custom created functions.

    ```bash
    python manage.py migrate publicatie_tabellen 0001_initial
    ```

2. Then rerun the above migrations including the one that creates the functions.

    ```bash
    python manage.py migrate
    ```
