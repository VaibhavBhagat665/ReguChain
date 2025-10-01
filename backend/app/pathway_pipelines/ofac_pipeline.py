"""
Pathway OFAC Sanctions Pipeline
Continuous ingestion of OFAC SDN and Consolidated lists
"""
import pathway as pw
import requests
import csv
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any
import logging
from ..config import OFAC_SDN_URL, OFAC_CONSOLIDATED_URL

logger = logging.getLogger(__name__)

class OFACPathwayPipeline:
    """Pathway-powered OFAC sanctions ingestion"""
    
    def __init__(self):
        self.sdn_url = OFAC_SDN_URL
        self.consolidated_url = OFAC_CONSOLIDATED_URL
        
    def create_sdn_pipeline(self):
        """Create Pathway pipeline for OFAC SDN CSV"""
        
        @pw.udf
        def fetch_sdn_data() -> pw.Table:
            """Fetch and parse OFAC SDN CSV data"""
            try:
                logger.info("🔍 Fetching OFAC SDN data...")
                response = requests.get(self.sdn_url, timeout=30)
                response.raise_for_status()
                
                # Parse CSV
                csv_reader = csv.DictReader(response.text.splitlines())
                documents = []
                
                for row in csv_reader:
                    doc = {
                        'id': f"ofac_sdn_{row.get('ent_num', '')}",
                        'source': 'OFAC_SDN',
                        'text': f"OFAC SDN Entry: {row.get('name', '')} - {row.get('title', '')}",
                        'timestamp': datetime.now().isoformat(),
                        'link': self.sdn_url,
                        'type': 'sanction',
                        'metadata': {
                            'entity_number': row.get('ent_num', ''),
                            'name': row.get('name', ''),
                            'title': row.get('title', ''),
                            'address': row.get('address', ''),
                            'city': row.get('city', ''),
                            'country': row.get('country', ''),
                            'list_type': row.get('list', ''),
                            'program': row.get('program', ''),
                            'risk_level': 'high'
                        }
                    }
                    documents.append(doc)
                
                logger.info(f"✅ Fetched {len(documents)} OFAC SDN entries")
                return pw.Table.from_pandas(pw.pandas.DataFrame(documents))
                
            except Exception as e:
                logger.error(f"❌ Error fetching OFAC SDN: {e}")
                return pw.Table.empty()
        
        # Create periodic input that triggers every 1 hour
        trigger = pw.io.http.rest_connector(
            host="localhost",
            port=8080,
            route="/trigger/ofac_sdn",
            schema=pw.Schema.from_types(trigger=str),
            autocommit_duration_ms=3600000  # 1 hour
        )
        
        # Transform trigger into SDN data
        sdn_data = trigger.select(
            data=fetch_sdn_data()
        ).flatten(pw.this.data)
        
        return sdn_data
    
    def create_consolidated_pipeline(self):
        """Create Pathway pipeline for OFAC Consolidated XML"""
        
        @pw.udf
        def fetch_consolidated_data() -> pw.Table:
            """Fetch and parse OFAC Consolidated XML data"""
            try:
                logger.info("🔍 Fetching OFAC Consolidated data...")
                response = requests.get(self.consolidated_url, timeout=30)
                response.raise_for_status()
                
                # Parse XML
                root = ET.fromstring(response.text)
                documents = []
                
                for entity in root.findall('.//sdnEntry'):
                    uid = entity.get('uid', '')
                    first_name = entity.findtext('.//firstName', '')
                    last_name = entity.findtext('.//lastName', '')
                    name = f"{first_name} {last_name}".strip()
                    
                    # Get addresses
                    addresses = []
                    for address in entity.findall('.//address'):
                        addr_text = address.findtext('.//address1', '')
                        city = address.findtext('.//city', '')
                        country = address.findtext('.//country', '')
                        addresses.append(f"{addr_text}, {city}, {country}")
                    
                    doc = {
                        'id': f"ofac_consolidated_{uid}",
                        'source': 'OFAC_CONSOLIDATED',
                        'text': f"OFAC Consolidated Entry: {name} - Addresses: {'; '.join(addresses)}",
                        'timestamp': datetime.now().isoformat(),
                        'link': self.consolidated_url,
                        'type': 'sanction',
                        'metadata': {
                            'uid': uid,
                            'name': name,
                            'first_name': first_name,
                            'last_name': last_name,
                            'addresses': addresses,
                            'risk_level': 'high'
                        }
                    }
                    documents.append(doc)
                
                logger.info(f"✅ Fetched {len(documents)} OFAC Consolidated entries")
                return pw.Table.from_pandas(pw.pandas.DataFrame(documents))
                
            except Exception as e:
                logger.error(f"❌ Error fetching OFAC Consolidated: {e}")
                return pw.Table.empty()
        
        # Create periodic trigger
        trigger = pw.io.http.rest_connector(
            host="localhost",
            port=8080,
            route="/trigger/ofac_consolidated",
            schema=pw.Schema.from_types(trigger=str),
            autocommit_duration_ms=3600000  # 1 hour
        )
        
        # Transform trigger into consolidated data
        consolidated_data = trigger.select(
            data=fetch_consolidated_data()
        ).flatten(pw.this.data)
        
        return consolidated_data
    
    def create_unified_pipeline(self):
        """Create unified OFAC pipeline combining SDN and Consolidated"""
        sdn_pipeline = self.create_sdn_pipeline()
        consolidated_pipeline = self.create_consolidated_pipeline()
        
        # Combine both pipelines
        unified_ofac = sdn_pipeline + consolidated_pipeline
        
        # Add processing timestamp
        unified_ofac = unified_ofac.select(
            *pw.this,
            processed_at=datetime.now().isoformat()
        )
        
        return unified_ofac

# Global instance
ofac_pathway_pipeline = OFACPathwayPipeline()
