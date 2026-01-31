import jwt
import time
import requests
import json
import urllib.parse
from datetime import datetime, timedelta

class ZitadelTokenProvider:
    def __init__(self, key_file_path: str, issuer_url: str, project_id: str, ssl_ca_cert: str = None):
        self.key_file_path = key_file_path
        self.issuer_url = issuer_url
        self.project_id = project_id
        
        with open(key_file_path, 'r') as f:
            self.key_data = json.load(f)
            
        self.access_token = None
        self.expiry = 0

    def get_token(self) -> str:
        if self.access_token and time.time() < self.expiry:
            return self.access_token

        now = int(time.time())
        # Create JWT assertion
        claims = {
            "iss": self.key_data["userId"],
            "sub": self.key_data["userId"],
            "aud": self.issuer_url,
            "exp": now + 3600,
            "iat": now,
        }
        
        encoded_jwt = jwt.encode(
            claims, 
            self.key_data["key"], 
            algorithm="RS256", 
            headers={"kid": self.key_data["keyId"]}
        )

        # Exchange for access token
        # Build scopes matching the Go SDK implementation
        scopes = [
            "openid",
            "profile",
            "urn:zitadel:iam:user:resourceowner",
            "urn:zitadel:iam:org:projects:roles",
            f"urn:zitadel:iam:org:project:id:{self.project_id}:aud",
        ]
        scope = " ".join(scopes)
        
        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": encoded_jwt,
            "scope": scope
        }
        
        response = requests.post(f"{self.issuer_url}/oauth/v2/token", data=data)
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data["access_token"]
        self.expiry = now + token_data["expires_in"] - 60 # buffer
        
        return self.access_token
