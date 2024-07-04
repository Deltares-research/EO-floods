import getpass
import requests


def GFM_authenticate() -> dict:
    print(
        "To authenticate to the GFM API please enter your email and your password in the following prompts"
    )
    email = input(prompt="Enter your email")
    password = getpass.getpass(prompt="Enter your password")
    url = "https://api.gfm.eodc.eu/v2/auth/login"
    r = requests.post(url=url, json={"email": email, "password": password})
    if r.status_code == 200:
        print("Successfully authenticated to the GFM API")
        return r.json()
    else:
        raise r.raise_for_status()
