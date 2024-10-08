from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from .feed import LatestPostsFeed

urlpatterns = [
    path('admin/', admin.site.urls),
    path('nimdatatau/', admin.site.urls),
    path('accounts/login/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('feed/', LatestPostsFeed(), name='latest_feed'),
    path('', include('app.urls')),
    path('robots.txt', lambda x: HttpResponse("Sitemap: https://datatau.net/sitemap.xml \nUser-agent:* \nDisallow: ",
                                              content_type="text/plain"),
         name="robots_file")
]
