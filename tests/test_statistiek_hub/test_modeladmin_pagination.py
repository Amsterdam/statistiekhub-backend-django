from statistiek_hub.modeladmins.pagination import LimitedPaginator, PageLimitExceeded


def test_page_limit_exceeded_exception():
    requested_page = 10
    max_pages = 5

    exception = PageLimitExceeded(requested_page, max_pages)

    assert exception.requested_page == requested_page
    assert exception.max_pages == max_pages
    assert str(exception) == f"Page {requested_page} exceeds maximum of {max_pages}"


def test_limited_paginator_valid_page():
    object_list = range(1000)  # Example object list
    per_page = 10
    max_offset = 500

    paginator = LimitedPaginator(object_list, per_page, max_offset=max_offset)

    page = paginator.page(1)

    assert list(page.object_list) == list(range(10))
