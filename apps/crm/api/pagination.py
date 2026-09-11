from django.core.paginator import Paginator


def paginate(queryset, page: int, page_size: int):
    """
    Mirrors hiveforest-api's app/modules/health_care_professional/utils.py
    paginate_queryset() exactly, so the JSON shape hiveforest-api expects
    (page, page_size, total_items, total_pages, has_next, has_previous) is
    produced here instead, now that hiveforest-api no longer holds a live
    queryset to paginate itself.
    """
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    meta = {
        "page": page_obj.number,
        "page_size": page_size,
        "total_items": paginator.count,
        "total_pages": paginator.num_pages,
        "has_next": page_obj.has_next(),
        "has_previous": page_obj.has_previous(),
    }
    return page_obj.object_list, meta
