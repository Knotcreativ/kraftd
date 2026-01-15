# Kraftd AI Agent Setup

## Prerequisites

1. **Microsoft Foundry Project** (formerly Azure AI Foundry)
   - Create a project: https://portal.azure.com
   - Deploy a model (GPT-4 recommended)
   - Note your project endpoint and model deployment name

2. **Azure Authentication**
   - Ensure you're logged in: `az login`
   - Have appropriate permissions in your Foundry project

## Installation

### 1. Install Agent Framework

The `--pre` flag is **required** as Agent Framework is in preview.

```bash
cd backend
pip install agent-framework-azure-ai --pre
pip install azure-ai-projects
pip install httpx
```

### 2. Update requirements.txt

```txt
# Add to backend/requirements.txt:
agent-framework-azure-ai
azure-ai-projects
httpx
```

### 3. Set Environment Variables

**Option A: PowerShell (Development)**
```powershell
$env:FOUNDRY_PROJECT_ENDPOINT = "https://<your-project>.cognitiveservices.azure.com/"
$env:FOUNDRY_MODEL_DEPLOYMENT = "gpt-4"  # or your deployed model name
```

**Option B: .env File (Development)**
```bash
FOUNDRY_PROJECT_ENDPOINT=https://<your-project>.cognitiveservices.azure.com/
FOUNDRY_MODEL_DEPLOYMENT=gpt-4
```

**Option C: Production (Azure Key Vault)**
```bash
# Store in Azure Key Vault and retrieve via managed identity
az keyvault secret set --vault-name <vault-name> --name FOUNDRY-PROJECT-ENDPOINT --value <endpoint>
az keyvault secret set --vault-name <vault-name> --name FOUNDRY-MODEL-DEPLOYMENT --value gpt-4
```

## Running the Agent

### Interactive Mode

```bash
cd backend
python agent/kraft_agent.py
```

This starts an interactive chat where you can:
- Upload and process documents
- Compare quotations
- Detect risks
- Create purchase orders
- Ask questions about procurement

Example conversation:
```
You: Upload and extract intelligence from this RFQ
Agent: I'll help you process that RFQ. Please provide the file path...

You: Compare these 3 quotations
Agent: I'll analyze all 3 quotations and recommend the best option...
```

### As a Service (Integration with FastAPI)

Create `agent_endpoint.py`:

```python
from fastapi import FastAPI, WebSocket
from agent import KraftdAIAgent
import asyncio

app = FastAPI()
agent = KraftdAIAgent()

@app.on_event("startup")
async def startup():
    await agent.initialize()

@app.websocket("/ws/agent")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    thread = agent.agent.get_new_thread()
    
    while True:
        data = await websocket.receive_text()
        response = await agent.run(data, thread=thread)
        await websocket.send_text(response)
```

## Configuration

### Finding Your Foundry Endpoint

1. Go to [Azure Portal](https://portal.azure.com)
2. Find your Foundry project resource
3. Look for "Endpoint" in the resource overview
4. Should look like: `https://your-project.cognitiveservices.azure.com/`

### Finding Your Model Deployment

1. In the same Foundry resource
2. Go to "Model deployments" or "Deployments"
3. Note your model name (e.g., "gpt-4", "gpt-4-turbo", "gpt-35-turbo")

## Troubleshooting

### Error: "FOUNDRY_PROJECT_ENDPOINT not set"
```bash
# Check if environment variable is set
echo $env:FOUNDRY_PROJECT_ENDPOINT  # PowerShell
echo $FOUNDRY_PROJECT_ENDPOINT      # Bash

# If empty, set it again
$env:FOUNDRY_PROJECT_ENDPOINT = "https://your-project.cognitiveservices.azure.com/"
```

### Error: "Unauthorized" or "403"
- Check your Azure credentials: `az account show`
- Ensure you have access to the Foundry project
- Verify your environment variables are correct

### Agent not responding
- Check backend API is running: `curl http://127.0.0.1:8000/`
- Verify network connectivity to Foundry endpoint
- Check logs for detailed error messages

## API Reference

### KraftdAIAgent Methods

```python
agent = KraftdAIAgent()

# Initialize the agent
await agent.initialize()

# Run with user input
response = await agent.run("Process this RFQ")

# Run with conversation thread (maintains context)
thread = agent.agent.get_new_thread()
response = await agent.run("Upload this document", thread=thread)
response = await agent.run("Now compare quotations", thread=thread)

# Close and cleanup
await agent.close()
```

### Available Tools

The agent has access to these tools:

1. **upload_document** - Upload a document for processing
2. **extract_intelligence** - Extract structured data from a document
3. **validate_document** - Check document completeness and accuracy
4. **compare_quotations** - Compare multiple quotations
5. **get_document** - Retrieve document details
6. **create_po** - Create a purchase order
7. **analyze_supplier** - Analyze supplier information
8. **detect_risks** - Identify risks and anomalies
9. **generate_report** - Create analysis reports

## Cost Considerations

- **API Calls**: Charged per request to Foundry/OpenAI
- **Tokens**: GPT-4 is more expensive than GPT-3.5
- **Optimization**: Use caching where possible

## Next Steps

1. ✅ Install Agent Framework
2. ✅ Set environment variables
3. ✅ Run interactive agent
4. ⏳ Build frontend for agent interaction
5. ⏳ Deploy to Azure
6. ⏳ Monitor and optimize

## References

- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [Azure OpenAI](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Foundry Docs](https://learn.microsoft.com/en-us/azure/ai-studio/)
