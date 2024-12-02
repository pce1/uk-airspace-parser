import requests
import xml.etree.ElementTree as ET

def fetch_restrictions():
    url = "https://pibs.nats.co.uk/operational/pibs/PIB.xml"
    response = requests.get(url)
    return parse_restrictions(response.text)

def parse_restrictions(xml_text):
    root = ET.fromstring(xml_text)
    restrictions = []
    
    for notam in root.findall('.//NOTAM'):
        code23 = notam.find('.//Code23')
        if code23 is None or code23.text not in ['RD', 'RT']:
            continue
            
        restrictions.append({
            'id': f"{notam.find('Series').text}{notam.find('Number').text}/{notam.find('Year').text}",
            'type': code23.text,
            'coordinates': notam.find('Coordinates').text,
            'radius': notam.find('Radius').text if notam.find('Radius') is not None else None,
            'description': notam.find('ItemE').text,
            'lower': notam.find('ItemF').text,
            'upper': notam.find('ItemG').text
        })
    
    return restrictions

if __name__ == "__main__":
    restrictions = fetch_restrictions()
    print(f"Found {len(restrictions)} restrictions:")
    for r in restrictions:
        print(f"\n{r['type']} - {r['id']}")
        print(f"Location: {r['coordinates']}")
        if r['radius']:
            print(f"Radius: {r['radius']}nm")
        print(f"Altitude: {r['lower']} to {r['upper']}")
