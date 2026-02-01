import requests

url = "https://v1.american-football.api-sports.io/leagues"

payload={}
headers = {
  'x-rapidapi-key': 'XxXxXxXxXxXxXxXxXxXxXxXx',
  'x-rapidapi-host': 'v1.american-football.api-sports.io'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)