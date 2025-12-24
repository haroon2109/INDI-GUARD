import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import uuid

def generate_cap_xml(sender_id, headline, description, severity, location, disaster_type, instructions):
    """
    Generates a CAP 1.2 compatible XML alert.
    """
    
    # 1. Root: alert
    alert = ET.Element('alert', xmlns='urn:oasis:names:tc:emergency:cap:1.2')
    
    # --- Header ---
    ET.SubElement(alert, 'identifier').text = str(uuid.uuid4())
    ET.SubElement(alert, 'sender').text = sender_id
    ET.SubElement(alert, 'sent').text = datetime.now(timezone.utc).isoformat()
    ET.SubElement(alert, 'status').text = 'Actual'
    ET.SubElement(alert, 'msgType').text = 'Alert'
    ET.SubElement(alert, 'scope').text = 'Public'
    
    # --- Info Block ---
    info = ET.SubElement(alert, 'info')
    
    # Categorization
    category_map = {
        'Weather': 'Met', 'Flood': 'Met', 'Cyclone': 'Met',
        'Earthquake': 'Geo', 'Tsunami': 'Geo', 'Drought': 'Met'
    }
    ET.SubElement(info, 'category').text = category_map.get(disaster_type, 'Safety')
    ET.SubElement(info, 'event').text = f"{disaster_type} Warning"
    ET.SubElement(info, 'urgency').text = 'Immediate' if severity == 'Extreme' else 'Expected'
    ET.SubElement(info, 'severity').text = severity # Severe, Moderate, etc.
    ET.SubElement(info, 'certainty').text = 'Likely'
    
    # Text Content
    ET.SubElement(info, 'headline').text = headline
    ET.SubElement(info, 'description').text = description
    ET.SubElement(info, 'instruction').text = instructions
    
    # Area
    area = ET.SubElement(info, 'area')
    ET.SubElement(area, 'areaDesc').text = location
    
    # Pretty print hack
    from xml.dom import minidom
    xmlstr = minidom.parseString(ET.tostring(alert)).toprettyxml(indent="   ")
    
    return xmlstr

def parse_cap_sample(xml_content):
    """Validates if a file is CAP 1.2 compliant (basic check)."""
    try:
        root = ET.fromstring(xml_content)
        # Check namespace or root
        if 'urn:oasis:names:tc:emergency:cap:1.2' in root.tag or root.tag == 'alert':
            return True, root.find(".//headline").text
    except Exception as e:
        return False, str(e)
    return False, "Unknown structure"
