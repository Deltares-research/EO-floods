import getpass
import requests


def GFM_authenticate(email=None, pwd=None) -> dict:
    if not all([email, pwd]):
        print(
            "To authenticate to the GFM API please enter your email and your password in the following prompts"
        )
        email = input(prompt="Enter your email")
        pwd = getpass.getpass(prompt="Enter your password")
    url = "https://api.gfm.eodc.eu/v2/auth/login"
    r = requests.post(url=url, json={"email": email, "password": pwd})
    if r.status_code == 200:
        print("Successfully authenticated to the GFM API")
        return r.json()
    elif r.status_code == 400:
        print("Incorrect email or password, please try again")
        return GFM_authenticate()
    else:
        raise r.raise_for_status()


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r
