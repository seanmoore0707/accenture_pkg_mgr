import os

S3_BUCKET                 = os.environ.get("mywizard360-training")
S3_KEY                    = os.environ.get("AKIAJN4VIP2ULILMEOIA")
S3_SECRET                 = os.environ.get("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")
S3_LOCATION               = 'http://{}.s3.amazonaws.com/'.format(S3_BUCKET)

SECRET_KEY                = os.urandom(32)
DEBUG                     = True
PORT                      = 5000