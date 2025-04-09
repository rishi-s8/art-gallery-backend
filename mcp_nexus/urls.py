from django.contrib import admin
from django.urls import URLResolver, path, include, URLPattern
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from django.http import HttpResponse
from django.http import HttpRequest


def home_view(_: HttpRequest):
    return HttpResponse("""
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1.0'>
        <title>Welcome</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                margin: 0;
                padding: 0;
                background-color: #f4f4f9;
                color: #333;
            }
            header {
                padding: 20px;
                background-color: #6200ea;
                color: white;
            }
            a {
                color: #6200ea;
                text-decoration: none;
                font-weight: bold;
            }
            a:hover {
                text-decoration: underline;
            }
            main {
                padding: 20px;
            }
        </style>
    </head>
    <body>
        <header>
            <h1>Welcome to the Art Gallery Backend</h1>
        </header>
        <main>
            <p>Welcome to the backend server of the Art Gallery project. Here are some useful links:</p>
            <ul>
                <li><a href='/admin/'>Admin Panel</a></li>
                <li><a href='/api/v1/'>API v1</a></li>
                <li><a href='/api/docs/'>API Documentation (Swagger)</a></li>
                <li><a href='/api/redoc/'>API Documentation (ReDoc)</a></li>
            </ul>
        </main>
    </body>
    </html>
    """)

api_v1_patterns = [
    path('auth/', include('authentication.urls')),
    path('servers/', include('servers.urls')),
    path('discovery/', include('discovery.urls')),
    path('verification/', include('verification.urls')),
    path('analytics/', include('analytics.urls')),
    path('webhooks/', include('webhooks.urls')),
]

urlpatterns: list[URLPattern | URLResolver] = [
    path('', home_view),
    path('admin/', admin.site.urls),

    # API v1 URLs
    path('api/v1/', include(api_v1_patterns)),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]