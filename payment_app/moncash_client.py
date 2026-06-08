import os

import httpx
from dotenv import load_dotenv
load_dotenv()


class MoncashClient:
    def __init__(self, client=None, secret=None):
        self.client = client
        self.secret = secret
        if not client:
            self.client = os.environ['MONCASH_CLIENT']

        if not secret:
            self.secret = os.environ['MONCASH_SECRET']

        self.LIVE_API_BASE = (
            "moncashbutton.digicelgroup.com/Api"
        )

        self.TEST_API_BASE = (
            "sandbox.moncashbutton.digicelgroup.com/Api"
        )

        self.LIVE_GATEWAY_BASE = (
            "https://moncashbutton.digicelgroup.com"
            "/Moncash-middleware"
        )

        self.TEST_GATEWAY_BASE = (
            "https://sandbox.moncashbutton.digicelgroup.com"
            "/Moncash-middleware"
        )

        # self.API_BASE = self.TEST_API_BASE
        # self.GATEWAY_BASE = self.TEST_GATEWAY_BASE

        self.API_BASE = self.LIVE_API_BASE
        self.GATEWAY_BASE = self.LIVE_GATEWAY_BASE


        # self.TEST_BASE = "https://sandbox.moncashbutton.digicelgroup.com/Moncash-middleware"

    def get_access_token(self):
        url = f"https://{self.API_BASE}/oauth/token"

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "scope": "read,write",
            "grant_type": "client_credentials",
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    url,
                    headers=headers,
                    data=data,
                    auth=(self.client, self.secret),
                )

            if response.status_code == 200:
                token = response.json().get("access_token")
                return token, None
            else:
                return None, f"Error {response.status_code}: {response.text}"
        except httpx.RequestError as exc:
            return None, f"Request error: {exc}"

    def create_payment(self, amount: float, order_id: str):
        url = f"https://{self.API_BASE}/v1/CreatePayment"

        access_token, _err = self.get_access_token()
        headers = {
            "Accept": "application/json",
            "authorization": f"Bearer {access_token}",
            "Content-type": "application/json"
        }

        payload = {
            "amount": int(amount),
            "orderId": order_id
        }
        print("url: ",url)
        print("$$$$$$$$$$")

        if _err:
            return None, _err

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    url,
                    headers=headers,
                    json=payload,
                )

            if response.status_code == 202:
                token = response.json()['payment_token']['token']
                return (
                    f"{self.GATEWAY_BASE}"
                    f"/Payment/Redirect?token={token}"
                ), None
            else:
                return None, response.json()

        except httpx.RequestError as exc:
            return None, exc.json()
        except Exception as exc:
            raise exc
            return None, exc.json()

    def retrieve_transaction(self, transaction_id: str):
        access_token, error = self.get_access_token()

        # print(f"ACCESS TOKEN: {access_token}")
        if error:
            return None, error

        url = f"https://{self.API_BASE}/v1/RetrieveTransactionPayment"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        payload = {"transactionId": transaction_id}
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                return response.json(), None
            return None, response.json()
        except httpx.RequestError as exc:
            return None, response.json()