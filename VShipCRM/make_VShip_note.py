import requests

from VShipCRM.signInVShipCRM import get_valid_token

REQUEST_TIMEOUT = (10, 30)

def post_note(booking_id, note: str, token: str) -> requests.Response:
    return requests.post(
        f"https://vship2000-prod-api.azurewebsites.net/api/Bookings/{booking_id}/comments",
        json={
            "comment": note,
            "commentType": 1,
        },
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            'sec-ch-ua': '"Chromium";v="143", "Not A(Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "Referer": "https://vshipcrm.com/"},
        timeout=REQUEST_TIMEOUT,
        )