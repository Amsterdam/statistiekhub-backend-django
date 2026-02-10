from django.core.exceptions import ValidationError
from django.db import models


class TimeStampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AddErrorFuncion(models.Model):
    @classmethod
    def add_error(cls, errors, new_errors):
        for err_code, err_value in new_errors.items():
            if err_value is None:
                continue

            if err_code in errors.keys():
                if isinstance(errors[err_code], ValidationError):
                    errors.update({err_code: [errors[err_code], err_value]})
                elif isinstance(errors[err_code], list):
                    errors[err_code].append(err_value)
            else:
                errors.update(new_errors)
        return errors

    class Meta:
        abstract = True
