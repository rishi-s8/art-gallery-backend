from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.conf import settings

class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination for API results.
    
    Returns a standardized pagination format compatible with our frontend
    and API specification.
    """
    page_size = getattr(settings, 'DEFAULT_PAGE_SIZE', 20)
    page_size_query_param = 'limit'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """
        Return a paginated response in the format:
        {
            "data": [...],
            "pagination": {
                "total": 100,
                "per_page": 20,
                "current_page": 1,
                "last_page": 5,
                "next_page_url": "https://api.example.com/items?page=2",
                "prev_page_url": null
            }
        }
        """
        return Response({
            'data': data,
            'pagination': {
                'total': self.page.paginator.count,
                'per_page': self.get_page_size(self.request),
                'current_page': self.page.number,
                'last_page': self.page.paginator.num_pages,
                'next_page_url': self.get_next_link(),
                'prev_page_url': self.get_previous_link(),
            }
        })