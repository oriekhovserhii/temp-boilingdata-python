class AWSCredentials:
    def __init__(self, access_key, secret_key, session_token):
        self.access_key = access_key
        self.secret_key = secret_key
        self.token = session_token