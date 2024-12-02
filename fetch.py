import requests

def fetch_xml():
    url = "https://pibs.nats.co.uk/operational/pibs/PIB.xml"
    response = requests.get(url)
    print(response.text)

if __name__ == "__main__":
    fetch_xml()