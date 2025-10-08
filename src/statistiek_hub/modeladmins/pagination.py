from django.core.paginator import Paginator


class PageLimitExceeded(Exception):
    def __init__(self, requested_page, max_pages):
        self.requested_page = requested_page
        self.max_pages = max_pages
        super().__init__(f"Page {requested_page} exceeds maximum of {max_pages}")


class LimitedPaginator(Paginator):
    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True, max_offset=5000):
        super().__init__(object_list, per_page, orphans, allow_empty_first_page)
        self.max_offset = max_offset

    @property
    def max_pages(self):
        return self.max_offset // self.per_page

    def page(self, number):
        number = self.validate_number(number)
        if number > self.max_pages:
            raise PageLimitExceeded(number, self.max_pages)
        return super().page(number)
