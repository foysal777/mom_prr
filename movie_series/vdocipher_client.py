import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()


class VdocipherClient:
    def __init__(self, api_key=os.environ['VDOCIPHER_API_KEY']):
        assert api_key is not None
        self.api_key = api_key

    def get_video_detail(self, video_id):
        url = f"https://www.vdocipher.com/api/videos/{video_id}"
        result = httpx.get(
            url,
            headers={
                'Authorization': f"Apisecret {self.api_key}",
            }
        )
        if result.status_code != 200:
            return None, result.json()

        return result.json(), None

    def get_playlist_info(self, video_id):
        print(">>>>>>> play cREATE <<<<<<")
        print(">>>>>>> play cREATE <<<<<<")
        print(">>>>>>> play cREATE <<<<<<")
        print(">>>>>>> play cREATE <<<<<<")
        print(">>>>>>> play cREATE <<<<<<")
        url = f"https://dev.vdocipher.com/api/videos/{video_id}/otp"

        payload = json.dumps({
            "annotate": json.dumps([{
                'type': 'rtext', 'text': 'name',
                'alpha': '0.60', 'color': '0xFF0000',
                'size': '15', 'interval': '5000'
            }]),
            "ttl": 300,
          # "licenseRules": {
          #   "canPersist": True,
          #   "rentalDuration": 15 * 24 * 3600,
          # }
        })
        headers = {
            'Authorization': f"Apisecret {self.api_key}",
        }

        result = httpx.post(
            url,
            headers=headers,
            data=payload,
        )

        if result.status_code != 200:
            return None, result.json()
        return result.json(), None
        pass


    def get_offline_playlist(self, video_id):
        url = f"https://dev.vdocipher.com/api/videos/{video_id}/otp"

        headers = {
            "Accept": "application/json",
            "Authorization": f"Apisecret {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "licenseRules": '{"canPersist": true, "rentalDuration": 1296000}'
        }

        result = httpx.post(url, headers=headers, json=data)

        if result.status_code != 200:
            return None, result.json()
        return result.json(), None
        pass

    def delete_videos(self, video_ids):
        assert isinstance(video_ids, list)
        url = (
            f"https://www.vdocipher.com/api/videos"
            f"?videos={','.join(video_ids)}"
        )
        headers = {
            'Authorization': f"Apisecret {self.api_key}",
        }

        result = httpx.delete(
            url,
            headers=headers,
        )

        if result.status_code != 200:
            return None, result.json()
        return result.json(), None
        pass

