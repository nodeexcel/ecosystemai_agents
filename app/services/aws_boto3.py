import os 
import mimetypes
from boto3 import client

aws_client = client('s3', aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('REGION_NAME'))

ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'image/png',
    'image/jpeg',
    'image/webp',
    'video/mp4',
    'video/webm',
}

def get_upload_args(filename):
    mimetype, _ = mimetypes.guess_type(filename)

    if mimetype not in ALLOWED_MIME_TYPES:
        raise ValueError(f"File type not allowed: {mimetype}")

    content_disposition = 'attachment'
    if mimetype.startswith(('image/', 'video/')) or mimetype == 'application/pdf':
        content_disposition = 'inline'

    return {
        'ACL': 'public-read',
        'ContentType': mimetype,
        'ContentDisposition': content_disposition
    }
