import requests
import xml.etree.ElementTree as ET
from datetime import datetime

def fetch_nats_pib():
    """Fetch the NATS PIB XML file"""
    url = "https://pibs.nats.co.uk/operational/pibs/PIB.xml"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching XML: {e}")
        return None

def parse_coordinates(coord_str):
    """Parse coordinates from format like '5152N00049E'"""
    if not coord_str or len(coord_str) < 11:
        return None
    
    try:
        lat_deg = int(coord_str[0:2])
        lat_min = int(coord_str[2:4])
        lat_dir = coord_str[4]
        lon_deg = int(coord_str[5:8])
        lon_min = int(coord_str[8:10])
        lon_dir = coord_str[10]
        
        lat = lat_deg + lat_min/60
        if lat_dir == 'S':
            lat = -lat
            
        lon = lon_deg + lon_min/60
        if lon_dir == 'W':
            lon = -lon
            
        return (lat, lon)
    except (ValueError, IndexError):
        return None

def parse_polygon_coords(text):
    """Parse polygon coordinates from ItemE text"""
    # Look for coordinate sequences
    coords = []
    parts = text.split('-')
    for part in parts:
        part = part.strip()
        if len(part) >= 11:  # Min length for coordinate format
            try:
                coord_part = part.split()[0]  # Get first "word" which should be coordinate
                coord = parse_coordinates(coord_part.replace(' ', ''))
                if coord:
                    coords.append(coord)
            except:
                continue
    return coords if coords else None

def get_area_restrictions():
    """Get all Danger Areas and Restricted Areas"""
    xml_text = fetch_nats_pib()
    if not xml_text:
        return []
    
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return []
    
    restrictions = []
    
    for notam in root.findall('.//NOTAM'):
        try:
            # Get Q-code to identify restriction type
            code23 = notam.find('.//QLine/Code23').text if notam.find('.//QLine/Code23') is not None else None
            
            # Only process Danger Areas (RD) and Restricted Areas (RT)
            if code23 not in ['RD', 'RT']:
                continue
                
            restriction = {
                'id': f"{notam.find('Series').text}{notam.find('Number').text}/{notam.find('Year').text}",
                'type': 'Danger Area' if code23 == 'RD' else 'Restricted Area',
                'valid_from': notam.find('StartValidity').text,
                'valid_to': notam.find('EndValidity').text,
                'lower_limit': notam.find('ItemF').text,
                'upper_limit': notam.find('ItemG').text,
                'description': notam.find('ItemE').text
            }
            
            # Check for polygon coordinates in ItemE
            polygon_coords = parse_polygon_coords(restriction['description'])
            if polygon_coords:
                restriction['shape'] = 'polygon'
                restriction['coordinates'] = polygon_coords
            else:
                # Try to get center coordinates and radius
                coords_elem = notam.find('Coordinates')
                radius_elem = notam.find('Radius')
                
                if coords_elem is not None and radius_elem is not None:
                    center_coords = parse_coordinates(coords_elem.text)
                    if center_coords:
                        restriction['shape'] = 'circle'
                        restriction['center'] = center_coords
                        restriction['radius'] = float(radius_elem.text)
                        
            restrictions.append(restriction)
                
        except Exception as e:
            print(f"Error processing NOTAM: {e}")
            continue
    
    return restrictions

if __name__ == "__main__":
    restrictions = get_area_restrictions()
    print(f"Found {len(restrictions)} restrictions")
    for r in restrictions:
        print(f"\n{r['type']} - {r['id']}")
        if r['shape'] == 'circle':
            print(f"Center: {r['center']}, Radius: {r['radius']}nm")
        else:
            print(f"Polygon with {len(r['coordinates'])} points")
        print(f"Valid: {r['valid_from']} to {r['valid_to']}")
        print(f"Limits: {r['lower_limit']} - {r['upper_limit']}")
