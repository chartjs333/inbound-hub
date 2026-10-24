"""Consumer HTTP contract tests; no server checkout, imports or shared state."""
import asyncio
import json

import httpx
import pytest
from inbound_hub.integrations.nginx_qa import DeliveryError, NginxQaClient, NginxQaProposalTarget


def test_pending_http_contract():
    calls = []
    payload = {
        'schema_version': 1, 'proposal_id': 'proposal-1', 'idempotency_key': 'proposal-1',
        'source': {'source_type': 'email', 'message_id': 'mail-1'},
        'summary': 'Review booking',
        'candidate': {'kind': 'legacy_json', 'payload': {'sprint_type': 'legacy_v1', 'actors': []}},
    }

    def server(request):
        calls.append(request)
        assert request.headers['Authorization'] == 'Bearer synthetic-token'
        assert request.headers['X-Correlation-ID'] == 'proposal-1'
        if request.method == 'POST':
            assert request.url.path == '/api/v1/projects/9008/pending-sprints'
            assert json.loads(request.content) == payload
            return httpx.Response(200, json={'proposal': {'pending_sprint_id': 'pending-1'},
                                            'deduplicated': len(calls) > 1})
        assert request.method == 'GET'
        assert request.url.path == '/api/v1/projects/9008/pending-sprints/pending-1/status'
        return httpx.Response(200, json={'status': {'activation_state': 'not_started'}})

    async def run():
        client = NginxQaClient(NginxQaProposalTarget('https://nginx.example.invalid', '9008'),
                              'synthetic-token', httpx.AsyncClient(transport=httpx.MockTransport(server)))
        first = await client.create(payload)
        assert (await client.create(payload))['deduplicated'] is True
        assert (await client.status(first['proposal']['pending_sprint_id'], 'proposal-1'))['status']['activation_state'] == 'not_started'
        await client.close()
    asyncio.run(run())
    assert len(calls) == 3


@pytest.mark.parametrize('status,retryable', [(401, False), (403, False), (302, False), (429, True), (503, True)])
def test_pending_http_errors_and_no_redirect(status, retryable):
    calls = []

    def server(request):
        calls.append(request)
        return httpx.Response(status, headers={'Location': 'https://other.invalid'})

    async def run():
        client = NginxQaClient(NginxQaProposalTarget('https://nginx.example.invalid', '9008'),
                              'synthetic-token', httpx.AsyncClient(transport=httpx.MockTransport(server)))
        with pytest.raises(DeliveryError) as error:
            await client.create({'proposal_id': 'test'})
        assert error.value.status == status and error.value.retryable is retryable
        await client.close()
    asyncio.run(run())
    assert len(calls) == 1
