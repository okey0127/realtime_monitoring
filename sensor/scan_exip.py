import requests
URL = 'https://icanhazip.com'
respons = requests.get(URL)
print(respons.text)