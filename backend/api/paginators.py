from rest_framework.pagination import PageNumberPagination


class LimitPagination(PageNumberPagination):
    """Пагинатор."""
    page_size_query_param = "limit"
