"""
API wiring tests for the prompt analysis endpoint.

These verify the route is registered and guarded by authentication. The
analysis logic itself is covered by the service unit tests (which mock the LLM
provider), so these stay deliberately light and don't require a real model.
"""

import pytest


@pytest.mark.asyncio
async def test_analyze_route_is_registered(client):
    resp = await client.get("/api/openapi.json")
    assert resp.status_code == 200
    assert "/api/v1/prompts/analyze" in resp.json()["paths"]


@pytest.mark.asyncio
async def test_analyze_requires_authentication(client):
    resp = await client.post(
        "/api/v1/prompts/analyze",
        json={"prompt": "An inspiring short film about space exploration"},
    )
    assert resp.status_code == 401
