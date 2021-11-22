import os
import json
import boto3


def lambda_handler(event, context):
    # Get email form event
    body = json.loads(event.get('body', {}))
    email = body.get('email', '')

    # Setting response message to empty string
    message = ''

    # Getting environment variables
    AWS_REGION = os.getenv("REGION")

    # Check for email in SES
    ses_client = boto3.client('sesv2', AWS_REGION)

    if email:
        try:
            response = ses_client.get_email_identity(EmailIdentity=email)
            status = response.get('VerifiedForSendingStatus', '')

            if status:
                message = "Email is already verified. You can now use Text2Speech"
            elif not status:
                message = 'A mail is already sent to you long back for verification. Please check your inbox.'

        except Exception as e:
            if 'NotFoundException' in str(e):
                response = ses_client.create_email_identity(EmailIdentity=email)
                message = "Please check your Email Inbox."

    else:
        message = "Please sent request in correct format"

    return {"statusCode": 200,
            "body": json.dumps({"message": message}),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"}
            }
