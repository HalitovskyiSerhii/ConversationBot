import logging
from uuid import uuid4

import boto3
from botocore.client import Config

from actions.config import cfg

logger = logging.getLogger(__name__)

class _Storage:

    def __init__(self):
        self.s3 = boto3.resource('s3',
                                 endpoint_url=cfg.storage_url,
                                 aws_access_key_id=cfg.storage_access_key,
                                 aws_secret_access_key=cfg.storage_secret_key,
                                 config=Config(signature_version='s3v4'),
                                 region_name='us-east-1')

        self.client = boto3.client('s3',
                                   endpoint_url=cfg.storage_url,
                                   aws_access_key_id=cfg.storage_access_key,
                                   aws_secret_access_key=cfg.storage_secret_key,
                                   config=Config(signature_version='s3v4'),
                                   region_name='us-east-1'
                                   )
        self.bucket = self.s3.Bucket(cfg.storage_files_bucket)

    def _get_url(self, key, name):
        return self.client.generate_presigned_url(
            'get_object',
            ExpiresIn=28800,
            Params={
                'Bucket': cfg.storage_files_bucket,
                'Key': key,
                'ResponseContentDisposition': f'attachment; filename= {name}'
            }
        )

    def save_obj(self, obj, get_url=False):
        key = str(uuid4())
        self.bucket.upload_fileobj(obj, key)
        if get_url:
            return self._get_url(key, obj.name)



