from rest_framework.pagination import PageNumberPagination


class CustomLimitPagination(PageNumberPagination):
    page_size = 6

    def get_page_size(self, request):

        limit = request.query_params.get('limit')
        if limit:
            try:
                return int(limit)
            except ValueError:
                pass
        return super().get_page_size(request)
