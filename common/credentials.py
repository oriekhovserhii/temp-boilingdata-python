import boto3
from warrant import Cognito
from common.aws_credentials import AWSCredentials

IDP_REGION = "eu-west-1"
UserPoolId = "eu-west-1_0GLV9KO1p"
Logins = f"cognito-idp.{IDP_REGION}.amazonaws.com/{UserPoolId}"
IdentityPoolId = "eu-west-1:bce21571-e3a6-47a4-8032-fd015213405f"
pool_data = {'UserPoolId': UserPoolId, 'ClientId': "6timr8knllr4frovfvq8r2o6oo"}

def get_id_token(username: str, password: str) -> str:
    u = Cognito(pool_data['UserPoolId'], pool_data['ClientId'], user_pool_region=IDP_REGION, username=username)
    u.authenticate(password)
    id_token = u.id_token
    return id_token


def refresh_creds_with_token(id_token: str) -> dict:
    cognito_identity = boto3.client('cognito-identity', region_name=IDP_REGION)
    response = cognito_identity.get_id(
        IdentityPoolId=IdentityPoolId,
        Logins={
            Logins: id_token
        },
    )
    identity_id = response['IdentityId']

    response = cognito_identity.get_credentials_for_identity(
        IdentityId=identity_id,
        Logins={
            Logins: id_token
        },
    )
    return response['Credentials']


async def swap_bd_creds_for_aws_creds(username: str, password: str) -> AWSCredentials:
    
    id_token = get_id_token(username, password)
    creds = refresh_creds_with_token(id_token)

    access_key_id = creds['AccessKeyId']
    secret_access_key = creds['SecretKey']
    session_token = creds['SessionToken']

    if not access_key_id or not secret_access_key:
        raise Exception("Missing credentials (after refresh)!")

    aws_credentials = AWSCredentials(access_key_id, secret_access_key, session_token)

    return aws_credentials
    
