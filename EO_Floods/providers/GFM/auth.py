import getpass
import requests


def GFM_authenticate() -> dict:
    print(
        "To authenticate to the GFM API please enter your email and your password in the following prompts"
    )
    email = input()
    password = getpass.getpass()
    url = "https://api.gfm.eodc.eu/v1/auth/login"
    r = requests.post(url=url, json={"email": email, "password": password})
    if r.status_code == 200:
        print("Successfully authenticated to the GFM API")
        return r.json()
    else:
        raise r.raise_for_status()
