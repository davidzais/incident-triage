from typing import Any
import pytest
import os
import asyncio
from pathlib import Path
import json
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from db.tables import Base
from db.database import get_session   # the REAL dependency — the key we override
from app.main import api             # the FastAPI instance

TEST_DATABASE_URL = os.environ["TEST_DATABASE_URL"]

# NullPool = don't reuse connections. This is the trick that dodges the
# "attached to a different loop" asyncpg error between TestClient's loop
# and the fixture's asyncio.run loop — every use gets a fresh connection.
test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)

# THIS is your override — same shape as get_session, but the test DB.
async def override_get_session():
    async with TestSession() as s:
        yield s

@pytest.fixture
def test_db():
    # fresh schema before the test
    async def _create():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    asyncio.run(_create())

    # swap the app's DB dependency for the test one
    api.dependency_overrides[get_session] = override_get_session
    yield                                   # <-- test runs here
    api.dependency_overrides.clear()        # undo the swap

    async def _drop():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    asyncio.run(_drop())

@pytest.fixture
def test_data_json() -> dict[Any, Any]:
    test_data_json = {
                "version": "4",
                "status": "firing",
                "receiver": "incident-triage",
                "groupLabels": { "alertname": "MixedBatch" },
                "commonLabels": { "alertname": "MixedBatch" },
                "commonAnnotations": { "summary": "Mixed severity/service batch" },
                "externalURL": "http://alertmanager.example.com:9093",
                "alerts": [
                    { "status": "firing", "labels": { "alertname": "HighErrorRate", "service": "checkout", "severity": "critical", "namespace": "payments", "instance": "checkout-1:8080" }, "annotations": { "summary": "Error rate above 5% on checkout", "description": "checkout 5xx over threshold" }, "startsAt": "2026-07-07T17:42:10.123Z", "endsAt": "0001-01-01T00:00:00Z", "generatorURL": "http://prometheus.example.com/graph?g0.expr=checkout", "fingerprint": "1111111111111111" },
                    { "status": "firing", "labels": { "alertname": "PaymentGatewayDown", "service": "payments", "severity": "critical", "namespace": "payments", "instance": "payments-1:8080" }, "annotations": { "summary": "Payment gateway unreachable", "description": "payments provider timing out" }, "startsAt": "2026-07-07T17:40:00.000Z", "endsAt": "0001-01-01T00:00:00Z", "generatorURL": "http://prometheus.example.com/graph?g0.expr=payments", "fingerprint": "2222222222222222" },
                    { "status": "firing", "labels": { "alertname": "ElevatedLatency", "service": "checkout", "severity": "warning", "namespace": "payments", "instance": "checkout-2:8080" }, "annotations": { "summary": "p95 latency elevated on checkout", "description": "latency above SLO" }, "startsAt": "2026-07-07T17:38:00.000Z", "endsAt": "0001-01-01T00:00:00Z", "generatorURL": "http://prometheus.example.com/graph?g0.expr=latency", "fingerprint": "3333333333333333" },
                    { "status": "firing", "labels": { "alertname": "ReturnsErrors", "service": "returns", "severity": "critical", "namespace": "orders", "instance": "returns-1:8080" }, "annotations": { "summary": "Returns service failing", "description": "returns 5xx spike" }, "startsAt": "2026-07-07T17:35:00.000Z", "endsAt": "0001-01-01T00:00:00Z", "generatorURL": "http://prometheus.example.com/graph?g0.expr=returns", "fingerprint": "4444444444444444" },
                    { "status": "firing", "labels": { "alertname": "InventoryLag", "service": "inventory", "severity": "warning", "namespace": "orders", "instance": "inventory-1:8080" }, "annotations": { "summary": "Inventory sync lagging", "description": "sync delay above threshold" }, "startsAt": "2026-07-07T17:30:00.000Z", "endsAt": "0001-01-01T00:00:00Z", "generatorURL": "http://prometheus.example.com/graph?g0.expr=inventory", "fingerprint": "5555555555555555" },
                    { "status": "firing", "labels": { "alertname": "BillingInfo", "service": "billing", "severity": "info", "namespace": "finance", "instance": "billing-1:8080" }, "annotations": { "summary": "Billing nightly job started", "description": "informational" }, "startsAt": "2026-07-07T17:25:00.000Z", "endsAt": "0001-01-01T00:00:00Z", "generatorURL": "http://prometheus.example.com/graph?g0.expr=billing", "fingerprint": "6666666666666666" }
                ]
                }
    return dict(test_data_json)



           
   

test_data_file = "fixtures/alertmanager_firing.json"
test_multi_file = "fixtures/alertmanager_multi.json"

@pytest.fixture
def sample_message() -> dict[Any, Any]:
    file_path = Path(__file__).parent / test_data_file
    
    with open( file_path) as f:
        json_data = json.load( f)
           
    return dict(json_data)

@pytest.fixture
def sample_multi_message() -> dict[Any, Any]:
    file_path = Path(__file__).parent / test_multi_file
    
    with open( file_path) as f:
        json_data = json.load( f)
           
    return dict(json_data)


