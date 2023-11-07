# djano-import-export-celery
instead of installing from pypy django-import-export-celery
copied django-app from https://github.com/auto-mat/django-import-export-celery 

added the following requirements to requirements.txt:
django-author

Adjustments to original code:
- Changed the admin to only IMPORT -> removed ALL export code
- removed export-job because not used
- set "file" as readonly so can't change after job is made
- fixed error if in_stream == bytes then decode to string
- applied linting
- adjusted job-formats to statistiek_hub import formats
- create html in tasks.py with template




