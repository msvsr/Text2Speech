import os
import json
import boto3


def lambda_handler(event, context):
    # Getting email and text
    body = json.loads(event.get('body', {}))
    email, text = body.get("email", ''), body.get("text", "No text found here")
    message = ''

    # Getting s3 bucket name and queue url from environment variables
    BUCKET_NAME = os.getenv("BUCKET_NAME")
    QUEUE_URL = os.getenv("QUEUE_URL")
    AWS_REGION = os.getenv("REGION")

    # Check for email in SES
    ses_client = boto3.client('sesv2', AWS_REGION)
    if email:
        try:
            response = ses_client.get_email_identity(EmailIdentity=email)
            status = response.get('VerifiedForSendingStatus', '')

            if status:
                # Creating audio using polly
                polly_client = boto3.client('polly', AWS_REGION)
                audio = polly_client.start_speech_synthesis_task(Engine='standard', LanguageCode='en-US',
                                                                 VoiceId='Aditi',
                                                                 OutputFormat='mp3', Text=text,
                                                                 OutputS3BucketName=BUCKET_NAME)

                s3_object_uri = audio.get('SynthesisTask', '').get('OutputUri', '')

                sqs_client = boto3.client('sqs', AWS_REGION)
                sqs_client.send_message(
                    QueueUrl=QUEUE_URL,
                    MessageBody='Please process this message',
                    MessageAttributes={
                        's3objecturi': {'StringValue': s3_object_uri, 'DataType': 'String'},
                        'email': {'StringValue': email, 'DataType': 'String'},

                    }
                )
                message = "Please check your email. You will receive a mail with link to your audio"
            else:
                message = 'Please verify your email with verifyemail API and then try to proceed with Text2Speech API'

        except Exception as e:
            if 'NotFoundException' in str(e):
                message = "Please verify your email with verifyemail API and then try to proceed with Text2Speech API"
    else:
        message = "Please send email in the request body"

    return {"statusCode": 200,
            "body": json.dumps({"message": message}),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"}
            }
