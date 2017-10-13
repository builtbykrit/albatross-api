import django.middleware.csrf

from django.conf import settings
from django.core.files.storage import default_storage
from django.http import Http404, HttpResponse


def ember_web_app_view(request):
    """
    get:
    Renders index.html for the Ember Web App deployed to the
    S3 bucket in your Django Storages settings.
    """
    index_name = 'index.html'
    revision = request.GET.get('revision')
    if revision:
        index_name += ':{}'.format(revision)
    try:
        if not default_storage.exists(index_name):
            raise Http404()
        index_file = default_storage.open(index_name, 'r')
        index_as_bytes = index_file.read()
        index_file.close()
        index_html = index_as_bytes.decode()

        if ('django.middleware.csrf.CsrfViewMiddleware'
                in settings.MIDDLEWARE_CLASSES):
            start = index_html.index('</head>')
            meta = '<meta name="X-CSRFToken" content="{}">'.format(
                django.middleware.csrf.get_token(request))
            index_html = index_html[:start] + meta + index_html[start:]
        return HttpResponse(index_html, content_type='text/html')
    except Exception as e:
        raise Http404()
