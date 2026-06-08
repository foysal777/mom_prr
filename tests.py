import subprocess
import re
import json

from movie_series.vdocipher_client import VdocipherClient

# client = VdocipherClient()


# print(client.get_playlist_info("33816a28fe754fa389da142b8a85b072"))


# print(client.delete_videos(["xvxcv", "007bac5f9cb5f67835f5cdd1eed63d94"]))


from payment_app.moncash_client import MoncashClient

transaction_id = "2038363142"

client = MoncashClient()
# response, _err = client.create_payment(20, "abc")
response, _err = client.retrieve_transaction(transaction_id)
# response, _err = client.get_access_token()
print(json.dumps(response, indent=2))
print(json.dumps(_err, indent=2))