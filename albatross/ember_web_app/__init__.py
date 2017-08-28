"""
This app provides a url and accompanying view to serve your
Ember web app from S3. To use it install **django-storages**
and add the following to your top-level app's settings::

    # Django Storages Settings

    AWS_ACCESS_KEY_ID = os.environ.get('S3_API_KEY')

    from boto.s3.connection import OrdinaryCallingFormat
    AWS_S3_CALLING_FORMAT = OrdinaryCallingFormat()

    AWS_S3_HOST = 's3.amazonaws.com'

    AWS_S3_REGION_NAME = 'us-east-1'

    AWS_SECRET_ACCESS_KEY = os.environ.get('S3_API_SECRET')

    AWS_STORAGE_BUCKET_NAME = os.environ.get('S3_WEB_APP_ASSETS_BUCKET')

    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

    S3_USE_SIGV4 = True
"""