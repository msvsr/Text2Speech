import os
import boto3


# Need to configure asynchronous invocations  Retry attempts:0


def lambda_handler(event, context):
    # Getting environment variables.
    BUCKET_NAME = os.getenv('BUCKET_NAME')
    QUEUE_URL = os.getenv('QUEUE_URL')
    AWS_REGION = os.getenv('REGION')
    SENDER_EMAIL = os.getenv('SENDER_EMAIL')  # This need to be already verified.

    # Getting message from Queue
    sqs_message = event.get('Records', [])
    if sqs_message:
        sqs_message = sqs_message[0]
        receiptHandle = sqs_message.get('receiptHandle', '')
        s3_object_uri = sqs_message.get('messageAttributes', {}).get('s3objecturi', {}).get('stringValue', '')
        s3_object = s3_object_uri.split('/')[4]
        email = sqs_message.get('messageAttributes', {}).get('email', {}).get('stringValue', '')

        if s3_object and email:
            # Modify S3 object permissions
            s3_client = boto3.client('s3', AWS_REGION)
            waiter = s3_client.get_waiter('object_exists')
            waiter.wait(Bucket=BUCKET_NAME, Key=s3_object)
            s3_client.put_object_acl(ACL='public-read', Bucket=BUCKET_NAME, Key=s3_object)

            # Send email
            ses_client = boto3.client('sesv2', AWS_REGION)
            ses_client.send_email(
                FromEmailAddress=SENDER_EMAIL,
                Destination={'ToAddresses': [email]},
                Content={
                    'Simple':
                        {'Subject':
                             {'Data': 'Text2Speech'},
                         'Body':
                             {'Text':
                                  {'Data': s3_object_uri}
                              }
                         }
                }
            )

            # Delete message from Queue
            sqs_client = boto3.client('sqs', AWS_REGION)
            try:
                sqs_client.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=receiptHandle)
            except Exception as e:
                print(str(e))
