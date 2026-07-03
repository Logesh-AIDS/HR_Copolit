import pytest
import time
import uuid

import sys
import os
sys.path.insert(0, os.path.abspath("services/candidate-service"))

from app.adapter.db import orm
from services.common.storage import get_storage_provider
from services.common.messaging import get_event_publisher, KafkaEventConsumer
from services.common.search import get_search_client
from services.common.config import settings

def test_minio_storage():
    """Test object storage connectivity and basic ops."""
    storage = get_storage_provider()
    
    test_key = f"test_resume_{uuid.uuid4().hex[:8]}.txt"
    test_data = b"Hello, this is a test resume."
    
    # Upload
    assert storage.upload_file(test_key, test_data, mime_type="text/plain")
    
    # Download
    downloaded = storage.download_file(test_key)
    assert downloaded == test_data
    
    # Presigned URL
    url = storage.get_presigned_url(test_key)
    assert url is not None
    assert "http" in url
    
    # Delete
    assert storage.delete_file(test_key)

def test_elasticsearch_client():
    """Test full-text search engine connectivity."""
    es = get_search_client()
    index_name = "test_candidates"
    doc_id = str(uuid.uuid4())
    
    document = {
        "name": "Jane Doe",
        "skills": ["Python", "Kubernetes", "Kafka"],
        "experience_years": 5
    }
    
    # Index document
    assert es.index_document(index_name, doc_id, document)
    
    # ES is near real-time, sleep briefly
    time.sleep(1)
    
    # Search document
    query = {
        "query": {
            "match": {
                "skills": "Kafka"
            }
        }
    }
    results = es.search(index_name, query)
    assert len(results) > 0
    assert any(r["name"] == "Jane Doe" for r in results)
    
    # Delete document
    assert es.delete_document(index_name, doc_id)

def test_kafka_messaging():
    """Test event streaming connectivity."""
    publisher = get_event_publisher()
    test_topic = "test_candidate_events"
    
    # Consumer setup
    consumer = KafkaEventConsumer(group_id="test_group", topics=[test_topic])
    
    event_payload = {
        "event_id": str(uuid.uuid4()),
        "type": "CANDIDATE_CREATED",
        "data": {"name": "John Smith"}
    }
    
    # Publish event
    publisher.publish(topic=test_topic, key=event_payload["event_id"], payload=event_payload)
    publisher.flush()
    
    # Consume event
    received_event = None
    
    def on_message(payload):
        nonlocal received_event
        received_event = payload
        
    # Poll a few times
    for _ in range(5):
        consumer.consume(on_message, timeout=1.0)
        if received_event:
            break
            
    consumer.close()
    
    assert received_event is not None
    assert received_event["event_id"] == event_payload["event_id"]
    assert received_event["data"]["name"] == "John Smith"
