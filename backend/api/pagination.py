from rest_framework.pagination import PageNumberPagination

from foodgram.settings import DEFAULT_PAGE_SIZE


class CustomLimitPagination(PageNumberPagination):
    """Кастомная пагинация с лимитом на количество элементов."""
    page_size = DEFAULT_PAGE_SIZE

    def get_page_size(self, request):
        """Получает размер страницы из параметров запроса."""

        limit = request.query_params.get('limit')
        if limit:
            try:
                return int(limit)
            except ValueError:
                pass
        return super().get_page_size(request)
