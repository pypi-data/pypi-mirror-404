# Shared Types

```python
from brainbase_labs.types import (
    Flow,
    Integration,
    Log,
    Resource,
    VoiceDeployment,
    VoiceV1Deployment,
    Worker,
)
```

# Team

Types:

```python
from brainbase_labs.types import TeamRetrieveResponse, TeamRetrieveSubaccountCredentialsResponse
```

Methods:

- <code title="get /api/team">client.team.<a href="./src/brainbase_labs/resources/team/team.py">retrieve</a>(\*\*<a href="src/brainbase_labs/types/team_retrieve_params.py">params</a>) -> <a href="./src/brainbase_labs/types/team_retrieve_response.py">TeamRetrieveResponse</a></code>
- <code title="get /api/team/subaccount-credentials">client.team.<a href="./src/brainbase_labs/resources/team/team.py">retrieve_subaccount_credentials</a>() -> <a href="./src/brainbase_labs/types/team_retrieve_subaccount_credentials_response.py">TeamRetrieveSubaccountCredentialsResponse</a></code>

## Assets

Types:

```python
from brainbase_labs.types.team import (
    AssetListPhoneNumbersResponse,
    AssetRegisterPhoneNumberResponse,
)
```

Methods:

- <code title="delete /api/team/assets/phone_numbers/{phoneNumberId}/delete">client.team.assets.<a href="./src/brainbase_labs/resources/team/assets.py">delete_phone_number</a>(phone_number_id) -> None</code>
- <code title="get /api/team/assets/available_phone_numbers">client.team.assets.<a href="./src/brainbase_labs/resources/team/assets.py">list_available_phone_numbers</a>(\*\*<a href="src/brainbase_labs/types/team/asset_list_available_phone_numbers_params.py">params</a>) -> None</code>
- <code title="get /api/team/assets/phone_numbers">client.team.assets.<a href="./src/brainbase_labs/resources/team/assets.py">list_phone_numbers</a>(\*\*<a href="src/brainbase_labs/types/team/asset_list_phone_numbers_params.py">params</a>) -> <a href="./src/brainbase_labs/types/team/asset_list_phone_numbers_response.py">AssetListPhoneNumbersResponse</a></code>
- <code title="post /api/team/assets/purchase_phone_numbers">client.team.assets.<a href="./src/brainbase_labs/resources/team/assets.py">purchase_phone_numbers</a>(\*\*<a href="src/brainbase_labs/types/team/asset_purchase_phone_numbers_params.py">params</a>) -> None</code>
- <code title="post /api/team/assets/purchase_whatsapp_sender">client.team.assets.<a href="./src/brainbase_labs/resources/team/assets.py">purchase_whatsapp_sender</a>(\*\*<a href="src/brainbase_labs/types/team/asset_purchase_whatsapp_sender_params.py">params</a>) -> None</code>
- <code title="post /api/team/assets/register_phone_number">client.team.assets.<a href="./src/brainbase_labs/resources/team/assets.py">register_phone_number</a>(\*\*<a href="src/brainbase_labs/types/team/asset_register_phone_number_params.py">params</a>) -> <a href="./src/brainbase_labs/types/team/asset_register_phone_number_response.py">AssetRegisterPhoneNumberResponse</a></code>
- <code title="get /api/team/assets/whatsapp_sender_status/{senderSid}">client.team.assets.<a href="./src/brainbase_labs/resources/team/assets.py">retrieve_whatsapp_sender_status</a>(sender_sid) -> None</code>

## Integrations

Types:

```python
from brainbase_labs.types.team import IntegrationListResponse
```

Methods:

- <code title="get /api/team/integrations/{integrationId}">client.team.integrations.<a href="./src/brainbase_labs/resources/team/integrations/integrations.py">retrieve</a>(integration_id) -> <a href="./src/brainbase_labs/types/shared/integration.py">Integration</a></code>
- <code title="patch /api/team/integrations/{integrationId}">client.team.integrations.<a href="./src/brainbase_labs/resources/team/integrations/integrations.py">update</a>(integration_id, \*\*<a href="src/brainbase_labs/types/team/integration_update_params.py">params</a>) -> <a href="./src/brainbase_labs/types/shared/integration.py">Integration</a></code>
- <code title="get /api/team/integrations">client.team.integrations.<a href="./src/brainbase_labs/resources/team/integrations/integrations.py">list</a>() -> <a href="./src/brainbase_labs/types/team/integration_list_response.py">IntegrationListResponse</a></code>

### Twilio

Methods:

- <code title="post /api/team/integrations/twilio/create">client.team.integrations.twilio.<a href="./src/brainbase_labs/resources/team/integrations/twilio.py">create</a>(\*\*<a href="src/brainbase_labs/types/team/integrations/twilio_create_params.py">params</a>) -> <a href="./src/brainbase_labs/types/shared/integration.py">Integration</a></code>
- <code title="delete /api/team/integrations/twilio/{integrationId}/delete">client.team.integrations.twilio.<a href="./src/brainbase_labs/resources/team/integrations/twilio.py">delete</a>(integration_id) -> None</code>

## DefaultChecks

Methods:

- <code title="get /api/team/default-checks">client.team.default_checks.<a href="./src/brainbase_labs/resources/team/default_checks.py">retrieve</a>() -> None</code>
- <code title="put /api/team/default-checks">client.team.default_checks.<a href="./src/brainbase_labs/resources/team/default_checks.py">update</a>(\*\*<a href="src/brainbase_labs/types/team/default_check_update_params.py">params</a>) -> None</code>
- <code title="post /api/team/default-checks">client.team.default_checks.<a href="./src/brainbase_labs/resources/team/default_checks.py">initialize</a>() -> None</code>

## CustomVoices

Methods:

- <code title="post /api/team/customVoices">client.team.custom_voices.<a href="./src/brainbase_labs/resources/team/custom_voices.py">create</a>(\*\*<a href="src/brainbase_labs/types/team/custom_voice_create_params.py">params</a>) -> None</code>
- <code title="get /api/team/customVoices">client.team.custom_voices.<a href="./src/brainbase_labs/resources/team/custom_voices.py">list</a>() -> None</code>
- <code title="delete /api/team/customVoices/{id}">client.team.custom_voices.<a href="./src/brainbase_labs/resources/team/custom_voices.py">delete</a>(id) -> None</code>

# Workers

Types:

```python
from brainbase_labs.types import (
    WorkerListResponse,
    WorkerCheckCallableResponse,
    WorkerRetrieveSessionResponse,
)
```

Methods:

- <code title="post /api/workers">client.workers.<a href="./src/brainbase_labs/resources/workers/workers.py">create</a>(\*\*<a href="src/brainbase_labs/types/worker_create_params.py">params</a>) -> <a href="./src/brainbase_labs/types/shared/worker.py">Worker</a></code>
- <code title="get /api/workers/{id}">client.workers.<a href="./src/brainbase_labs/resources/workers/workers.py">retrieve</a>(id) -> <a href="./src/brainbase_labs/types/shared/worker.py">Worker</a></code>
- <code title="patch /api/workers/{id}">client.workers.<a href="./src/brainbase_labs/resources/workers/workers.py">update</a>(id, \*\*<a href="src/brainbase_labs/types/worker_update_params.py">params</a>) -> <a href="./src/brainbase_labs/types/shared/worker.py">Worker</a></code>
- <code title="get /api/workers">client.workers.<a href="./src/brainbase_labs/resources/workers/workers.py">list</a>() -> <a href="./src/brainbase_labs/types/worker_list_response.py">WorkerListResponse</a></code>
- <code title="delete /api/workers/{id}">client.workers.<a href="./src/brainbase_labs/resources/workers/workers.py">delete</a>(id) -> None</code>
- <code title="post /api/workers/check-callable">client.workers.<a href="./src/brainbase_labs/resources/workers/workers.py">check_callable</a>(\*\*<a href="src/brainbase_labs/types/worker_check_callable_params.py">params</a>) -> <a href="./src/brainbase_labs/types/worker_check_callable_response.py">WorkerCheckCallableResponse</a></code>
- <code title="get /api/workers/{workerId}/sessions/{sessionId}">client.workers.<a href="./src/brainbase_labs/resources/workers/workers.py">retrieve_session</a>(session_id, \*, worker_id) -> <a href="./src/brainbase_labs/types/worker_retrieve_session_response.py">WorkerRetrieveSessionResponse</a></code>

## Deployments

### Voice

Types:

```python
from brainbase_labs.types.workers.deployments import (
    VoiceListResponse,
    VoiceMakeBatchCallsResponse,
    VoiceStopBatchCallsResponse,
    VoiceStopCampaignResponse,
)
```

Methods:

- <code title="post /api/workers/{workerId}/deployments/voice">client.workers.deployments.voice.<a href="./src/brainbase_labs/resources/workers/deployments/voice/voice.py">create</a>(worker_id, \*\*<a href="src/brainbase_labs/types/workers/deployments/voice_create_params.py">params</a>) -> <a href="./src/brainbase_labs/types/shared/voice_deployment.py">VoiceDeployment</a></code>
- <code title="get /api/workers/{workerId}/deployments/voice/{deploymentId}">client.workers.deployments.voice.<a href="./src/brainbase_labs/resources/workers/deployments/voice/voice.py">retrieve</a>(deployment_id, \*, worker_id) -> <a href="./src/brainbase_labs/types/shared/voice_deployment.py">VoiceDeployment</a></code>
- <code title="patch /api/workers/{workerId}/deployments/voice/{deploymentId}">client.workers.deployments.voice.<a href="./src/brainbase_labs/resources/workers/deployments/voice/voice.py">update</a>(deployment_id, \*, worker_id, \*\*<a href="src/brainbase_labs/types/workers/deployments/voice_update_params.py">params</a>) -> <a href="./src/brainbase_labs/types/shared/voice_deployment.py">VoiceDeployment</a></code>
- <code title="get /api/workers/{workerId}/deployments/voice">client.workers.deployments.voice.<a href="./src/brainbase_labs/resources/workers/deployments/voice/voice.py">list</a>(worker_id) -> <a href="./src/brainbase_labs/types/workers/deployments/voice_list_response.py">VoiceListResponse</a></code>
- <code title="delete /api/workers/{workerId}/deployments/voice/{deploymentId}">client.workers.deployments.voice.<a href="./src/brainbase_labs/resources/workers/deployments/voice/voice.py">delete</a>(deployment_id, \*, worker_id) -> None</code>
- <code title="post /api/workers/{workerId}/deployments/voice/{deploymentId}/make-batch-calls">client.workers.deployments.voice.<a href="./src/brainbase_labs/resources/workers/deployments/voice/voice.py">make_batch_calls</a>(deployment_id, \*, worker_id, \*\*<a href="src/brainbase_labs/types/workers/deployments/voice_make_batch_calls_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/deployments/voice_make_batch_calls_response.py">VoiceMakeBatchCallsResponse</a></code>
- <code title="post /api/workers/{workerId}/deployments/voice/{deploymentId}/stop-batch-calls">client.workers.deployments.voice.<a href="./src/brainbase_labs/resources/workers/deployments/voice/voice.py">stop_batch_calls</a>(deployment_id, \*, worker_id) -> <a href="./src/brainbase_labs/types/workers/deployments/voice_stop_batch_calls_response.py">VoiceStopBatchCallsResponse</a></code>
- <code title="post /api/workers/{workerId}/deployments/voice/{deploymentId}/stop-campaign">client.workers.deployments.voice.<a href="./src/brainbase_labs/resources/workers/deployments/voice/voice.py">stop_campaign</a>(deployment_id, \*, worker_id, \*\*<a href="src/brainbase_labs/types/workers/deployments/voice_stop_campaign_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/deployments/voice_stop_campaign_response.py">VoiceStopCampaignResponse</a></code>

#### CustomWebhooks

Methods:

- <code title="post /api/workers/{workerId}/deployments/{deploymentId}/voice/customWebhooks">client.workers.deployments.voice.custom_webhooks.<a href="./src/brainbase_labs/resources/workers/deployments/voice/custom_webhooks.py">create</a>(deployment_id, \*, worker_id, \*\*<a href="src/brainbase_labs/types/workers/deployments/voice/custom_webhook_create_params.py">params</a>) -> None</code>
- <code title="get /api/workers/{workerId}/deployments/{deploymentId}/voice/customWebhooks/{webhookId}">client.workers.deployments.voice.custom_webhooks.<a href="./src/brainbase_labs/resources/workers/deployments/voice/custom_webhooks.py">retrieve</a>(webhook_id, \*, worker_id, deployment_id) -> None</code>
- <code title="patch /api/workers/{workerId}/deployments/{deploymentId}/voice/customWebhooks/{webhookId}">client.workers.deployments.voice.custom_webhooks.<a href="./src/brainbase_labs/resources/workers/deployments/voice/custom_webhooks.py">update</a>(webhook_id, \*, worker_id, deployment_id, \*\*<a href="src/brainbase_labs/types/workers/deployments/voice/custom_webhook_update_params.py">params</a>) -> None</code>
- <code title="get /api/workers/{workerId}/deployments/{deploymentId}/voice/customWebhooks">client.workers.deployments.voice.custom_webhooks.<a href="./src/brainbase_labs/resources/workers/deployments/voice/custom_webhooks.py">list</a>(deployment_id, \*, worker_id) -> None</code>
- <code title="delete /api/workers/{workerId}/deployments/{deploymentId}/voice/customWebhooks/{webhookId}">client.workers.deployments.voice.custom_webhooks.<a href="./src/brainbase_labs/resources/workers/deployments/voice/custom_webhooks.py">delete</a>(webhook_id, \*, worker_id, deployment_id) -> None</code>

#### OutboundCampaigns

Types:

```python
from brainbase_labs.types.workers.deployments.voice import (
    OutboundCampaignCreateResponse,
    OutboundCampaignRetrieveResponse,
    OutboundCampaignUpdateResponse,
    OutboundCampaignListResponse,
)
```

Methods:

- <code title="post /api/workers/{workerId}/deployments/voice/{deploymentId}/outbound-campaigns">client.workers.deployments.voice.outbound_campaigns.<a href="./src/brainbase_labs/resources/workers/deployments/voice/outbound_campaigns.py">create</a>(deployment_id, \*, worker_id, \*\*<a href="src/brainbase_labs/types/workers/deployments/voice/outbound_campaign_create_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/deployments/voice/outbound_campaign_create_response.py">OutboundCampaignCreateResponse</a></code>
- <code title="get /api/workers/{workerId}/deployments/voice/{deploymentId}/outbound-campaigns/{campaignId}">client.workers.deployments.voice.outbound_campaigns.<a href="./src/brainbase_labs/resources/workers/deployments/voice/outbound_campaigns.py">retrieve</a>(campaign_id, \*, worker_id, deployment_id) -> <a href="./src/brainbase_labs/types/workers/deployments/voice/outbound_campaign_retrieve_response.py">OutboundCampaignRetrieveResponse</a></code>
- <code title="patch /api/workers/{workerId}/deployments/voice/{deploymentId}/outbound-campaigns/{campaignId}">client.workers.deployments.voice.outbound_campaigns.<a href="./src/brainbase_labs/resources/workers/deployments/voice/outbound_campaigns.py">update</a>(campaign_id, \*, worker_id, deployment_id, \*\*<a href="src/brainbase_labs/types/workers/deployments/voice/outbound_campaign_update_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/deployments/voice/outbound_campaign_update_response.py">OutboundCampaignUpdateResponse</a></code>
- <code title="get /api/workers/{workerId}/deployments/voice/{deploymentId}/outbound-campaigns">client.workers.deployments.voice.outbound_campaigns.<a href="./src/brainbase_labs/resources/workers/deployments/voice/outbound_campaigns.py">list</a>(deployment_id, \*, worker_id) -> <a href="./src/brainbase_labs/types/workers/deployments/voice/outbound_campaign_list_response.py">OutboundCampaignListResponse</a></code>
- <code title="delete /api/workers/{workerId}/deployments/voice/{deploymentId}/outbound-campaigns/{campaignId}">client.workers.deployments.voice.outbound_campaigns.<a href="./src/brainbase_labs/resources/workers/deployments/voice/outbound_campaigns.py">delete</a>(campaign_id, \*, worker_id, deployment_id) -> None</code>

### Voicev1

Types:

```python
from brainbase_labs.types.workers.deployments import Voicev1ListResponse
```

Methods:

- <code title="post /api/workers/{workerId}/deployments/voicev1">client.workers.deployments.voicev1.<a href="./src/brainbase_labs/resources/workers/deployments/voicev1/voicev1.py">create</a>(worker_id, \*\*<a href="src/brainbase_labs/types/workers/deployments/voicev1_create_params.py">params</a>) -> <a href="./src/brainbase_labs/types/shared/voice_v1_deployment.py">VoiceV1Deployment</a></code>
- <code title="get /api/workers/{workerId}/deployments/voicev1/{deploymentId}">client.workers.deployments.voicev1.<a href="./src/brainbase_labs/resources/workers/deployments/voicev1/voicev1.py">retrieve</a>(deployment_id, \*, worker_id) -> <a href="./src/brainbase_labs/types/shared/voice_v1_deployment.py">VoiceV1Deployment</a></code>
- <code title="put /api/workers/{workerId}/deployments/voicev1/{deploymentId}">client.workers.deployments.voicev1.<a href="./src/brainbase_labs/resources/workers/deployments/voicev1/voicev1.py">update</a>(deployment_id, \*, worker_id, \*\*<a href="src/brainbase_labs/types/workers/deployments/voicev1_update_params.py">params</a>) -> <a href="./src/brainbase_labs/types/shared/voice_v1_deployment.py">VoiceV1Deployment</a></code>
- <code title="get /api/workers/{workerId}/deployments/voicev1">client.workers.deployments.voicev1.<a href="./src/brainbase_labs/resources/workers/deployments/voicev1/voicev1.py">list</a>(worker_id) -> <a href="./src/brainbase_labs/types/workers/deployments/voicev1_list_response.py">Voicev1ListResponse</a></code>
- <code title="delete /api/workers/{workerId}/deployments/voicev1/{deploymentId}">client.workers.deployments.voicev1.<a href="./src/brainbase_labs/resources/workers/deployments/voicev1/voicev1.py">delete</a>(deployment_id, \*, worker_id) -> None</code>
- <code title="post /api/workers/{workerId}/deployments/voicev1/{deploymentId}/make-batch-calls">client.workers.deployments.voicev1.<a href="./src/brainbase_labs/resources/workers/deployments/voicev1/voicev1.py">make_batch_calls</a>(deployment_id, \*, worker_id, \*\*<a href="src/brainbase_labs/types/workers/deployments/voicev1_make_batch_calls_params.py">params</a>) -> None</code>

#### Campaigns

Types:

```python
from brainbase_labs.types.workers.deployments.voicev1 import CampaignCreateResponse
```

Methods:

- <code title="post /api/workers/{workerId}/deployments/voicev1/{deploymentId}/campaigns">client.workers.deployments.voicev1.campaigns.<a href="./src/brainbase_labs/resources/workers/deployments/voicev1/campaigns/campaigns.py">create</a>(deployment_id, \*, worker_id, \*\*<a href="src/brainbase_labs/types/workers/deployments/voicev1/campaign_create_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/deployments/voicev1/campaign_create_response.py">CampaignCreateResponse</a></code>
- <code title="get /api/workers/{workerId}/deployments/voicev1/{deploymentId}/campaigns/{campaignId}">client.workers.deployments.voicev1.campaigns.<a href="./src/brainbase_labs/resources/workers/deployments/voicev1/campaigns/campaigns.py">retrieve</a>(campaign_id, \*, worker_id, deployment_id) -> None</code>
- <code title="post /api/workers/{workerId}/deployments/voicev1/{deploymentId}/campaigns/{campaignId}/run">client.workers.deployments.voicev1.campaigns.<a href="./src/brainbase_labs/resources/workers/deployments/voicev1/campaigns/campaigns.py">run</a>(campaign_id, \*, worker_id, deployment_id, \*\*<a href="src/brainbase_labs/types/workers/deployments/voicev1/campaign_run_params.py">params</a>) -> None</code>

##### Data

Methods:

- <code title="get /api/workers/{workerId}/deployments/voicev1/{deploymentId}/campaigns/{campaignId}/data/{dataId}">client.workers.deployments.voicev1.campaigns.data.<a href="./src/brainbase_labs/resources/workers/deployments/voicev1/campaigns/data.py">retrieve</a>(data_id, \*, worker_id, deployment_id, campaign_id) -> None</code>
- <code title="put /api/workers/{workerId}/deployments/voicev1/{deploymentId}/campaigns/{campaignId}/data/{dataId}">client.workers.deployments.voicev1.campaigns.data.<a href="./src/brainbase_labs/resources/workers/deployments/voicev1/campaigns/data.py">update</a>(data_id, \*, worker_id, deployment_id, campaign_id, \*\*<a href="src/brainbase_labs/types/workers/deployments/voicev1/campaigns/data_update_params.py">params</a>) -> None</code>

### Chat

Types:

```python
from brainbase_labs.types.workers.deployments import (
    ChatCreateResponse,
    ChatRetrieveResponse,
    ChatUpdateResponse,
    ChatListResponse,
    ChatRetrieveAgentResponse,
)
```

Methods:

- <code title="post /api/workers/{workerId}/deployments/chat">client.workers.deployments.chat.<a href="./src/brainbase_labs/resources/workers/deployments/chat/chat.py">create</a>(worker_id, \*\*<a href="src/brainbase_labs/types/workers/deployments/chat_create_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/deployments/chat_create_response.py">ChatCreateResponse</a></code>
- <code title="get /api/workers/{workerId}/deployments/chat/{deploymentId}">client.workers.deployments.chat.<a href="./src/brainbase_labs/resources/workers/deployments/chat/chat.py">retrieve</a>(deployment_id, \*, worker_id) -> <a href="./src/brainbase_labs/types/workers/deployments/chat_retrieve_response.py">ChatRetrieveResponse</a></code>
- <code title="patch /api/workers/{workerId}/deployments/chat/{deploymentId}">client.workers.deployments.chat.<a href="./src/brainbase_labs/resources/workers/deployments/chat/chat.py">update</a>(deployment_id, \*, worker_id, \*\*<a href="src/brainbase_labs/types/workers/deployments/chat_update_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/deployments/chat_update_response.py">ChatUpdateResponse</a></code>
- <code title="get /api/workers/{workerId}/deployments/chat">client.workers.deployments.chat.<a href="./src/brainbase_labs/resources/workers/deployments/chat/chat.py">list</a>(worker_id) -> <a href="./src/brainbase_labs/types/workers/deployments/chat_list_response.py">ChatListResponse</a></code>
- <code title="delete /api/workers/{workerId}/deployments/chat/{deploymentId}">client.workers.deployments.chat.<a href="./src/brainbase_labs/resources/workers/deployments/chat/chat.py">delete</a>(deployment_id, \*, worker_id) -> None</code>
- <code title="get /api/workers/{workerId}/deployments/chat/agent/{chatAgentId}">client.workers.deployments.chat.<a href="./src/brainbase_labs/resources/workers/deployments/chat/chat.py">retrieve_agent</a>(chat_agent_id, \*, worker_id) -> <a href="./src/brainbase_labs/types/workers/deployments/chat_retrieve_agent_response.py">ChatRetrieveAgentResponse</a></code>

#### Embed

Types:

```python
from brainbase_labs.types.workers.deployments.chat import (
    EmbedCreateResponse,
    EmbedRetrieveResponse,
    EmbedUpdateResponse,
    EmbedListResponse,
    EmbedRetrieveByEmbedResponse,
)
```

Methods:

- <code title="post /api/workers/{workerId}/deployments/chat-embed">client.workers.deployments.chat.embed.<a href="./src/brainbase_labs/resources/workers/deployments/chat/embed.py">create</a>(worker_id, \*\*<a href="src/brainbase_labs/types/workers/deployments/chat/embed_create_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/deployments/chat/embed_create_response.py">EmbedCreateResponse</a></code>
- <code title="get /api/workers/{workerId}/deployments/chat-embed/{deploymentId}">client.workers.deployments.chat.embed.<a href="./src/brainbase_labs/resources/workers/deployments/chat/embed.py">retrieve</a>(deployment_id, \*, worker_id) -> <a href="./src/brainbase_labs/types/workers/deployments/chat/embed_retrieve_response.py">EmbedRetrieveResponse</a></code>
- <code title="patch /api/workers/{workerId}/deployments/chat-embed/{deploymentId}">client.workers.deployments.chat.embed.<a href="./src/brainbase_labs/resources/workers/deployments/chat/embed.py">update</a>(deployment_id, \*, worker_id, \*\*<a href="src/brainbase_labs/types/workers/deployments/chat/embed_update_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/deployments/chat/embed_update_response.py">EmbedUpdateResponse</a></code>
- <code title="get /api/workers/{workerId}/deployments/chat-embed">client.workers.deployments.chat.embed.<a href="./src/brainbase_labs/resources/workers/deployments/chat/embed.py">list</a>(worker_id) -> <a href="./src/brainbase_labs/types/workers/deployments/chat/embed_list_response.py">EmbedListResponse</a></code>
- <code title="delete /api/workers/{workerId}/deployments/chat-embed/{deploymentId}">client.workers.deployments.chat.embed.<a href="./src/brainbase_labs/resources/workers/deployments/chat/embed.py">delete</a>(deployment_id, \*, worker_id) -> None</code>
- <code title="get /api/workers/deployments/chat-embed/by-embed/{embedId}">client.workers.deployments.chat.embed.<a href="./src/brainbase_labs/resources/workers/deployments/chat/embed.py">retrieve_by_embed</a>(embed_id) -> <a href="./src/brainbase_labs/types/workers/deployments/chat/embed_retrieve_by_embed_response.py">EmbedRetrieveByEmbedResponse</a></code>

### DefaultChecks

Methods:

- <code title="get /api/workers/{workerId}/deployments/{deploymentId}/default-checks">client.workers.deployments.default_checks.<a href="./src/brainbase_labs/resources/workers/deployments/default_checks.py">retrieve</a>(deployment_id, \*, worker_id) -> None</code>
- <code title="put /api/workers/{workerId}/deployments/{deploymentId}/default-checks">client.workers.deployments.default_checks.<a href="./src/brainbase_labs/resources/workers/deployments/default_checks.py">update</a>(deployment_id, \*, worker_id, \*\*<a href="src/brainbase_labs/types/workers/deployments/default_check_update_params.py">params</a>) -> None</code>
- <code title="delete /api/workers/{workerId}/deployments/{deploymentId}/default-checks">client.workers.deployments.default_checks.<a href="./src/brainbase_labs/resources/workers/deployments/default_checks.py">delete</a>(deployment_id, \*, worker_id) -> None</code>

## Flows

Types:

```python
from brainbase_labs.types.workers import FlowListResponse
```

Methods:

- <code title="post /api/workers/{workerId}/flows">client.workers.flows.<a href="./src/brainbase_labs/resources/workers/flows.py">create</a>(worker_id, \*\*<a href="src/brainbase_labs/types/workers/flow_create_params.py">params</a>) -> <a href="./src/brainbase_labs/types/shared/flow.py">Flow</a></code>
- <code title="get /api/workers/{workerId}/flows/{flowId}">client.workers.flows.<a href="./src/brainbase_labs/resources/workers/flows.py">retrieve</a>(flow_id, \*, worker_id) -> <a href="./src/brainbase_labs/types/shared/flow.py">Flow</a></code>
- <code title="patch /api/workers/{workerId}/flows/{flowId}">client.workers.flows.<a href="./src/brainbase_labs/resources/workers/flows.py">update</a>(flow_id, \*, worker_id, \*\*<a href="src/brainbase_labs/types/workers/flow_update_params.py">params</a>) -> <a href="./src/brainbase_labs/types/shared/flow.py">Flow</a></code>
- <code title="get /api/workers/{workerId}/flows">client.workers.flows.<a href="./src/brainbase_labs/resources/workers/flows.py">list</a>(worker_id) -> <a href="./src/brainbase_labs/types/workers/flow_list_response.py">FlowListResponse</a></code>
- <code title="delete /api/workers/{workerId}/flows/{flowId}">client.workers.flows.<a href="./src/brainbase_labs/resources/workers/flows.py">delete</a>(flow_id, \*, worker_id) -> None</code>

## Resources

Types:

```python
from brainbase_labs.types.workers import ResourceQueryResponse
```

Methods:

- <code title="get /api/workers/{workerId}/resources/{resourceId}">client.workers.resources.<a href="./src/brainbase_labs/resources/workers/resources/resources.py">retrieve</a>(resource_id, \*, worker_id) -> <a href="./src/brainbase_labs/types/shared/resource.py">Resource</a></code>
- <code title="delete /api/workers/{workerId}/resources/{resourceId}">client.workers.resources.<a href="./src/brainbase_labs/resources/workers/resources/resources.py">delete</a>(resource_id, \*, worker_id) -> None</code>
- <code title="post /api/workers/{workerId}/resources/{resourceId}/move">client.workers.resources.<a href="./src/brainbase_labs/resources/workers/resources/resources.py">move</a>(resource_id, \*, worker_id, \*\*<a href="src/brainbase_labs/types/workers/resource_move_params.py">params</a>) -> <a href="./src/brainbase_labs/types/shared/resource.py">Resource</a></code>
- <code title="post /api/workers/{workerId}/resources/query">client.workers.resources.<a href="./src/brainbase_labs/resources/workers/resources/resources.py">query</a>(worker_id, \*\*<a href="src/brainbase_labs/types/workers/resource_query_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/resource_query_response.py">ResourceQueryResponse</a></code>

### Link

Types:

```python
from brainbase_labs.types.workers.resources import LinkListResponse
```

Methods:

- <code title="post /api/workers/{workerId}/resources/link">client.workers.resources.link.<a href="./src/brainbase_labs/resources/workers/resources/link.py">create</a>(worker_id, \*\*<a href="src/brainbase_labs/types/workers/resources/link_create_params.py">params</a>) -> <a href="./src/brainbase_labs/types/shared/resource.py">Resource</a></code>
- <code title="get /api/workers/{workerId}/resources/link">client.workers.resources.link.<a href="./src/brainbase_labs/resources/workers/resources/link.py">list</a>(worker_id) -> <a href="./src/brainbase_labs/types/workers/resources/link_list_response.py">LinkListResponse</a></code>

### File

Types:

```python
from brainbase_labs.types.workers.resources import FileListResponse
```

Methods:

- <code title="post /api/workers/{workerId}/resources/file">client.workers.resources.file.<a href="./src/brainbase_labs/resources/workers/resources/file.py">create</a>(worker_id, \*\*<a href="src/brainbase_labs/types/workers/resources/file_create_params.py">params</a>) -> <a href="./src/brainbase_labs/types/shared/resource.py">Resource</a></code>
- <code title="get /api/workers/{workerId}/resources/file">client.workers.resources.file.<a href="./src/brainbase_labs/resources/workers/resources/file.py">list</a>(worker_id) -> <a href="./src/brainbase_labs/types/workers/resources/file_list_response.py">FileListResponse</a></code>

## Tests

Types:

```python
from brainbase_labs.types.workers import TestCreateResponse
```

Methods:

- <code title="post /api/workers/{workerId}/tests">client.workers.tests.<a href="./src/brainbase_labs/resources/workers/tests.py">create</a>(worker_id, \*\*<a href="src/brainbase_labs/types/workers/test_create_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/test_create_response.py">TestCreateResponse</a></code>
- <code title="put /api/workers/{workerId}/tests/{testId}">client.workers.tests.<a href="./src/brainbase_labs/resources/workers/tests.py">update</a>(test_id, \*, worker_id, \*\*<a href="src/brainbase_labs/types/workers/test_update_params.py">params</a>) -> None</code>
- <code title="delete /api/workers/{workerId}/tests/{testId}">client.workers.tests.<a href="./src/brainbase_labs/resources/workers/tests.py">delete</a>(test_id, \*, worker_id) -> None</code>
- <code title="get /api/workers/{workerId}/tests/{testId}/runs">client.workers.tests.<a href="./src/brainbase_labs/resources/workers/tests.py">list_runs</a>(test_id, \*, worker_id) -> None</code>
- <code title="post /api/workers/{workerId}/tests/{testId}/run">client.workers.tests.<a href="./src/brainbase_labs/resources/workers/tests.py">run</a>(test_id, \*, worker_id) -> None</code>

## DeploymentLogs

### Voice

Types:

```python
from brainbase_labs.types.workers.deployment_logs import VoiceListResponse
```

Methods:

- <code title="get /api/workers/{workerId}/deploymentLogs/voice/{logId}">client.workers.deployment_logs.voice.<a href="./src/brainbase_labs/resources/workers/deployment_logs/voice.py">retrieve</a>(log_id, \*, worker_id) -> <a href="./src/brainbase_labs/types/shared/log.py">Log</a></code>
- <code title="get /api/workers/{workerId}/deploymentLogs/voice">client.workers.deployment_logs.voice.<a href="./src/brainbase_labs/resources/workers/deployment_logs/voice.py">list</a>(worker_id, \*\*<a href="src/brainbase_labs/types/workers/deployment_logs/voice_list_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/deployment_logs/voice_list_response.py">VoiceListResponse</a></code>

### Chat

Types:

```python
from brainbase_labs.types.workers.deployment_logs import ChatRetrieveResponse, ChatListResponse
```

Methods:

- <code title="get /api/workers/{workerId}/deploymentLogs/chat/{logId}">client.workers.deployment_logs.chat.<a href="./src/brainbase_labs/resources/workers/deployment_logs/chat/chat.py">retrieve</a>(log_id, \*, worker_id) -> <a href="./src/brainbase_labs/types/workers/deployment_logs/chat_retrieve_response.py">ChatRetrieveResponse</a></code>
- <code title="get /api/workers/{workerId}/deploymentLogs/chat">client.workers.deployment_logs.chat.<a href="./src/brainbase_labs/resources/workers/deployment_logs/chat/chat.py">list</a>(worker_id, \*\*<a href="src/brainbase_labs/types/workers/deployment_logs/chat_list_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/deployment_logs/chat_list_response.py">ChatListResponse</a></code>

#### Embed

Types:

```python
from brainbase_labs.types.workers.deployment_logs.chat import (
    EmbedRetrieveResponse,
    EmbedListResponse,
)
```

Methods:

- <code title="get /api/workers/{workerId}/deploymentLogs/chat-embed/{logId}">client.workers.deployment_logs.chat.embed.<a href="./src/brainbase_labs/resources/workers/deployment_logs/chat/embed.py">retrieve</a>(log_id, \*, worker_id) -> <a href="./src/brainbase_labs/types/workers/deployment_logs/chat/embed_retrieve_response.py">EmbedRetrieveResponse</a></code>
- <code title="get /api/workers/{workerId}/deploymentLogs/chat-embed">client.workers.deployment_logs.chat.embed.<a href="./src/brainbase_labs/resources/workers/deployment_logs/chat/embed.py">list</a>(worker_id, \*\*<a href="src/brainbase_labs/types/workers/deployment_logs/chat/embed_list_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/deployment_logs/chat/embed_list_response.py">EmbedListResponse</a></code>

### Whatsapp

Methods:

- <code title="get /api/workers/{workerId}/deploymentLogs/whatsapp/{logId}">client.workers.deployment_logs.whatsapp.<a href="./src/brainbase_labs/resources/workers/deployment_logs/whatsapp.py">retrieve</a>(log_id, \*, worker_id) -> None</code>
- <code title="get /api/workers/{workerId}/deploymentLogs/whatsapp">client.workers.deployment_logs.whatsapp.<a href="./src/brainbase_labs/resources/workers/deployment_logs/whatsapp.py">list</a>(worker_id, \*\*<a href="src/brainbase_labs/types/workers/deployment_logs/whatsapp_list_params.py">params</a>) -> None</code>

### SMS

Methods:

- <code title="get /api/workers/{workerId}/deploymentLogs/sms/{logId}">client.workers.deployment_logs.sms.<a href="./src/brainbase_labs/resources/workers/deployment_logs/sms.py">retrieve</a>(log_id, \*, worker_id) -> None</code>
- <code title="get /api/workers/{workerId}/deploymentLogs/sms">client.workers.deployment_logs.sms.<a href="./src/brainbase_labs/resources/workers/deployment_logs/sms.py">list</a>(worker_id, \*\*<a href="src/brainbase_labs/types/workers/deployment_logs/sms_list_params.py">params</a>) -> None</code>

## Folders

Types:

```python
from brainbase_labs.types.workers import (
    FolderCreateResponse,
    FolderRetrieveResponse,
    FolderUpdateResponse,
    FolderListResponse,
    FolderListResourcesResponse,
)
```

Methods:

- <code title="post /api/workers/{workerId}/folders">client.workers.folders.<a href="./src/brainbase_labs/resources/workers/folders.py">create</a>(worker_id, \*\*<a href="src/brainbase_labs/types/workers/folder_create_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/folder_create_response.py">FolderCreateResponse</a></code>
- <code title="get /api/workers/{workerId}/folders/{folderId}">client.workers.folders.<a href="./src/brainbase_labs/resources/workers/folders.py">retrieve</a>(folder_id, \*, worker_id) -> <a href="./src/brainbase_labs/types/workers/folder_retrieve_response.py">FolderRetrieveResponse</a></code>
- <code title="put /api/workers/{workerId}/folders/{folderId}">client.workers.folders.<a href="./src/brainbase_labs/resources/workers/folders.py">update</a>(folder_id, \*, worker_id, \*\*<a href="src/brainbase_labs/types/workers/folder_update_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/folder_update_response.py">FolderUpdateResponse</a></code>
- <code title="get /api/workers/{workerId}/folders">client.workers.folders.<a href="./src/brainbase_labs/resources/workers/folders.py">list</a>(worker_id) -> <a href="./src/brainbase_labs/types/workers/folder_list_response.py">FolderListResponse</a></code>
- <code title="delete /api/workers/{workerId}/folders/{folderId}">client.workers.folders.<a href="./src/brainbase_labs/resources/workers/folders.py">delete</a>(folder_id, \*, worker_id) -> None</code>
- <code title="get /api/workers/{workerId}/folders/{folderId}/resources">client.workers.folders.<a href="./src/brainbase_labs/resources/workers/folders.py">list_resources</a>(folder_id, \*, worker_id) -> <a href="./src/brainbase_labs/types/workers/folder_list_resources_response.py">FolderListResourcesResponse</a></code>

## BusinessHours

Types:

```python
from brainbase_labs.types.workers import (
    BusinessHourCreateResponse,
    BusinessHourRetrieveResponse,
    BusinessHourUpdateResponse,
    BusinessHourListResponse,
)
```

Methods:

- <code title="post /api/workers/business-hours">client.workers.business_hours.<a href="./src/brainbase_labs/resources/workers/business_hours.py">create</a>(\*\*<a href="src/brainbase_labs/types/workers/business_hour_create_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/business_hour_create_response.py">BusinessHourCreateResponse</a></code>
- <code title="get /api/workers/business-hours/{id}">client.workers.business_hours.<a href="./src/brainbase_labs/resources/workers/business_hours.py">retrieve</a>(id, \*\*<a href="src/brainbase_labs/types/workers/business_hour_retrieve_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/business_hour_retrieve_response.py">BusinessHourRetrieveResponse</a></code>
- <code title="put /api/workers/business-hours/{id}">client.workers.business_hours.<a href="./src/brainbase_labs/resources/workers/business_hours.py">update</a>(id, \*\*<a href="src/brainbase_labs/types/workers/business_hour_update_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/business_hour_update_response.py">BusinessHourUpdateResponse</a></code>
- <code title="get /api/workers/business-hours">client.workers.business_hours.<a href="./src/brainbase_labs/resources/workers/business_hours.py">list</a>(\*\*<a href="src/brainbase_labs/types/workers/business_hour_list_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/business_hour_list_response.py">BusinessHourListResponse</a></code>
- <code title="delete /api/workers/business-hours/{id}">client.workers.business_hours.<a href="./src/brainbase_labs/resources/workers/business_hours.py">delete</a>(id) -> None</code>

## TeamPhoneHours

Types:

```python
from brainbase_labs.types.workers import (
    TeamPhoneHourCreateResponse,
    TeamPhoneHourRetrieveResponse,
    TeamPhoneHourUpdateResponse,
    TeamPhoneHourListResponse,
)
```

Methods:

- <code title="post /api/workers/team-phone-hours">client.workers.team_phone_hours.<a href="./src/brainbase_labs/resources/workers/team_phone_hours.py">create</a>(\*\*<a href="src/brainbase_labs/types/workers/team_phone_hour_create_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/team_phone_hour_create_response.py">TeamPhoneHourCreateResponse</a></code>
- <code title="get /api/workers/team-phone-hours/{id}">client.workers.team_phone_hours.<a href="./src/brainbase_labs/resources/workers/team_phone_hours.py">retrieve</a>(id, \*\*<a href="src/brainbase_labs/types/workers/team_phone_hour_retrieve_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/team_phone_hour_retrieve_response.py">TeamPhoneHourRetrieveResponse</a></code>
- <code title="put /api/workers/team-phone-hours/{id}">client.workers.team_phone_hours.<a href="./src/brainbase_labs/resources/workers/team_phone_hours.py">update</a>(id, \*\*<a href="src/brainbase_labs/types/workers/team_phone_hour_update_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/team_phone_hour_update_response.py">TeamPhoneHourUpdateResponse</a></code>
- <code title="get /api/workers/team-phone-hours">client.workers.team_phone_hours.<a href="./src/brainbase_labs/resources/workers/team_phone_hours.py">list</a>(\*\*<a href="src/brainbase_labs/types/workers/team_phone_hour_list_params.py">params</a>) -> <a href="./src/brainbase_labs/types/workers/team_phone_hour_list_response.py">TeamPhoneHourListResponse</a></code>
- <code title="delete /api/workers/team-phone-hours/{id}">client.workers.team_phone_hours.<a href="./src/brainbase_labs/resources/workers/team_phone_hours.py">delete</a>(id) -> None</code>

## LlmLogs

Methods:

- <code title="get /api/workers/{workerId}/llm-logs/{logId}">client.workers.llm_logs.<a href="./src/brainbase_labs/resources/workers/llm_logs/llm_logs.py">retrieve</a>(log_id, \*, worker_id) -> None</code>
- <code title="get /api/workers/{workerId}/llm-logs">client.workers.llm_logs.<a href="./src/brainbase_labs/resources/workers/llm_logs/llm_logs.py">list</a>(worker_id, \*\*<a href="src/brainbase_labs/types/workers/llm_log_list_params.py">params</a>) -> None</code>
- <code title="delete /api/workers/{workerId}/llm-logs/{logId}">client.workers.llm_logs.<a href="./src/brainbase_labs/resources/workers/llm_logs/llm_logs.py">delete</a>(log_id, \*, worker_id) -> None</code>
- <code title="get /api/workers/{workerId}/llm-logs/by-session/{sessionId}">client.workers.llm_logs.<a href="./src/brainbase_labs/resources/workers/llm_logs/llm_logs.py">get_by_session</a>(session_id, \*, worker_id) -> None</code>

### ByCall

Methods:

- <code title="get /api/workers/{workerId}/llm-logs/by-call/{callId}">client.workers.llm_logs.by_call.<a href="./src/brainbase_labs/resources/workers/llm_logs/by_call.py">list</a>(call_id, \*, worker_id) -> None</code>
- <code title="delete /api/workers/{workerId}/llm-logs/by-call/{callId}">client.workers.llm_logs.by_call.<a href="./src/brainbase_labs/resources/workers/llm_logs/by_call.py">delete</a>(call_id, \*, worker_id) -> None</code>

## RuntimeErrors

Methods:

- <code title="get /api/workers/{workerId}/runtime-errors/{errorId}">client.workers.runtime_errors.<a href="./src/brainbase_labs/resources/workers/runtime_errors.py">retrieve</a>(error_id, \*, worker_id) -> None</code>
- <code title="get /api/workers/{workerId}/runtime-errors">client.workers.runtime_errors.<a href="./src/brainbase_labs/resources/workers/runtime_errors.py">list</a>(worker_id, \*\*<a href="src/brainbase_labs/types/workers/runtime_error_list_params.py">params</a>) -> None</code>
- <code title="post /api/workers/{workerId}/runtime-errors">client.workers.runtime_errors.<a href="./src/brainbase_labs/resources/workers/runtime_errors.py">record</a>(worker_id, \*\*<a href="src/brainbase_labs/types/workers/runtime_error_record_params.py">params</a>) -> None</code>

# VoiceAnalysis

Types:

```python
from brainbase_labs.types import VoiceAnalysisAnalyzeResponse
```

Methods:

- <code title="post /api/voice-analysis">client.voice_analysis.<a href="./src/brainbase_labs/resources/voice_analysis.py">analyze</a>(\*\*<a href="src/brainbase_labs/types/voice_analysis_analyze_params.py">params</a>) -> <a href="./src/brainbase_labs/types/voice_analysis_analyze_response.py">VoiceAnalysisAnalyzeResponse</a></code>

# PortkeyLogs

Methods:

- <code title="post /portkey-logs">client.portkey_logs.<a href="./src/brainbase_labs/resources/portkey_logs.py">create</a>(\*\*<a href="src/brainbase_labs/types/portkey_log_create_params.py">params</a>) -> None</code>
