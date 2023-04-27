import botocore.auth
import botocore.awsrequest

def get_ws_api_domain(region: str) -> str:
    return f"{region}.api.boilingdata.com"

def get_signer(region, credentials):
    service = "execute-api"
    signer = botocore.auth.SigV4QueryAuth(credentials, service, region, 300)
    return signer

async def get_signed_wss_url(credentials, region: str = "eu-west-1", protocol: str = "wss", path: str = "/dev") -> str:
    host = get_ws_api_domain(region)
    request = botocore.awsrequest.AWSRequest(
        method='GET',
        url=f"{protocol}://{host}{path}",
        headers={'host': host}
    )

    signer = get_signer(region, credentials)
    signer.add_auth(request)

    return request.url
