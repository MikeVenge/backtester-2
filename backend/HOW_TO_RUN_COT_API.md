# How to Call FinChat API to Run a COT Prompt

This guide explains how to call the FinChat API to execute a Chain of Thought (COT) prompt and retrieve the results.

## Overview

The process involves:
1. **Creating a session** - Establish a new session for the COT execution
2. **Getting COT details** - Retrieve the COT configuration (optional, if you already know the slug)
3. **Running the COT** - Send a chat message with COT syntax
4. **Polling for completion** - Check the chat status until the COT completes
5. **Retrieving results** - Fetch the final results

## Prerequisites

- API Base URL: `https://finchat-api.adgo.io` (or configured via `FINCHAT_API_URL` environment variable)
- Authentication: **Optional** - Bearer token in `Authorization` header (not required)
- COT Slug or ID: The identifier of the COT prompt you want to run

## Step-by-Step Guide

### Step 1: Create a Session

First, create a new session to execute the COT prompt.

**Endpoint:** `POST /api/v1/sessions/`

**Request Body:**
```json
{
  "client_id": "your-client-id",  // Optional: unique client identifier
  "data_source": "alpha_vantage",  // Optional: "alpha_vantage" or "edgar"
  "group": "optional-group-name"  // Optional: session group identifier
}
```

**Response:**
```json
{
  "id": "session-uuid",
  "status": "idle",
  "title": null,
  "data_source": "alpha_vantage",
  "created_on": "2024-01-01T00:00:00Z"
}
```

**Example:**
```javascript
const headers = {
  'Content-Type': 'application/json'
};
// Optional: Add authorization header if you have a token
if (yourToken) {
  headers['Authorization'] = `Bearer ${yourToken}`;
}

const sessionResponse = await fetch(`${API_URL}/api/v1/sessions/`, {
  method: 'POST',
  headers: headers,
  body: JSON.stringify({
    client_id: 'my-client-id',
    data_source: 'alpha_vantage'
  })
});

const session = await sessionResponse.json();
const sessionId = session.id;
```

### Step 2: Get COT Details (Optional)

If you only have a COT ID and need the slug, fetch the COT details first.

**Endpoint:** `GET /api/v1/cot/{cot_id}/`

**Response:**
```json
{
  "id": "cot-uuid",
  "slug": "my-cot-slug",
  "title": "My COT Title",
  "description": "COT description",
  "parameters": [
    {
      "id": "param-id",
      "name": "ticker",
      "label": "Ticker Symbol",
      "required": true,
      "field_type": "string",
      "default": null
    }
  ],
  "pdf_download_mode": "full"
}
```

**Example:**
```javascript
const headers = {};
if (yourToken) {
  headers['Authorization'] = `Bearer ${yourToken}`;
}

const cotResponse = await fetch(`${API_URL}/api/v1/cot/${cotId}/`, {
  method: 'GET',
  headers: headers
});

const cot = await cotResponse.json();
const cotSlug = cot.slug;
```

### Step 3: Run the COT Prompt

Send a chat message with COT syntax to execute the prompt.

**Endpoint:** `POST /api/v1/chats/`

**COT Syntax:**
- Basic: `cot {slug}`
- With parameters: `cot {slug} $param1:value1 $param2:value2`
- Multiple file parameters: `cot {slug} $files:file1.pdf,file2.pdf`

**Request Body:**
```json
{
  "session": "session-uuid",
  "message": "cot my-cot-slug $ticker:AAPL $date:2024-01-01",
  "analysis_model": "gpt-4",  // Optional
  "use_web_search": false,     // Optional
  "live_cot_model": "gpt-4",   // Optional
  "translate": "en"            // Optional
}
```

**Response:**
```json
{
  "id": "chat-uuid",
  "parent": null,
  "role": "user",
  "created_on": "2024-01-01T00:00:00Z",
  "message": "cot my-cot-slug $ticker:AAPL",
  "intent": "message",
  "result_id": null,
  "respond_to": null
}
```

**Example:**
```javascript
// Construct COT message with parameters
const cotMessage = `cot ${cotSlug} $ticker:AAPL $date:2024-01-01`;

const headers = {
  'Content-Type': 'application/json'
};
if (yourToken) {
  headers['Authorization'] = `Bearer ${yourToken}`;
}

const chatResponse = await fetch(`${API_URL}/api/v1/chats/`, {
  method: 'POST',
  headers: headers,
  body: JSON.stringify({
    session: sessionId,
    message: cotMessage
  })
});

const cotChat = await chatResponse.json();
const cotChatId = cotChat.id;
```

### Step 4: Poll for Completion

Poll the chats endpoint to check when the COT execution completes. The response chat will have a `result_id` when finished.

**Endpoint:** `GET /api/v1/chats/?session_id={session_id}&page_size=500`

**Polling Logic:**
1. Fetch all chats for the session
2. Find the chat where `respond_to` matches your COT chat ID
3. Check if that chat has a `result_id` (indicates completion)
4. Check `intent` field - if it's "error", the COT failed
5. Check `metadata` for progress information while running

**Response Structure:**
```json
{
  "results": [
    {
      "id": "response-chat-uuid",
      "parent": null,
      "role": "assistant",
      "respond_to": "cot-chat-uuid",
      "result_id": "result-uuid",  // Present when complete
      "intent": "message",
      "metadata": {
        "loading": true,
        "current_step": "Analyzing data...",
        "total_progress": 100,
        "current_progress": 50
      }
    }
  ],
  "count": 1,
  "next": null,
  "previous": null
}
```

**Example Polling Function:**
```javascript
async function pollForCOTCompletion(sessionId, cotChatId, maxAttempts = 60, intervalMs = 5000) {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    // Fetch chats
    const chatsResponse = await fetch(
      `${API_URL}/api/v1/chats/?session_id=${sessionId}&page_size=500`,
      {
        headers: {
          'Authorization': `Bearer ${yourToken}`
        }
      }
    );
    
    const chatsData = await chatsResponse.json();
    const chats = chatsData.results;
    
    // Find the response chat
    const responseChat = chats.find(chat => chat.respond_to === cotChatId);
    
    if (!responseChat) {
      // No response yet, wait and retry
      await new Promise(resolve => setTimeout(resolve, intervalMs));
      continue;
    }
    
    // Check for errors
    if (responseChat.intent === 'error') {
      throw new Error('COT execution failed');
    }
    
    // Check if complete (has result_id)
    if (responseChat.result_id) {
      return {
        responseChatId: responseChat.id,
        resultId: responseChat.result_id,
        metadata: responseChat.metadata
      };
    }
    
    // Still running - check progress
    const loadingInfo = responseChat.metadata;
    if (loadingInfo) {
      const progress = (loadingInfo.current_progress / loadingInfo.total_progress) * 100;
      console.log(`Progress: ${progress.toFixed(1)}% - ${loadingInfo.current_step}`);
    }
    
    // Wait before next poll
    await new Promise(resolve => setTimeout(resolve, intervalMs));
  }
  
  throw new Error('COT execution timed out');
}

// Usage
const completion = await pollForCOTCompletion(sessionId, cotChatId);
console.log('COT completed! Result ID:', completion.resultId);
```

### Step 5: Retrieve Results

Once the COT completes, fetch the results using the `result_id`.

**Endpoint:** `GET /api/v1/results/{result_id}/`

**Response:**
```json
{
  "id": "result-uuid",
  "content": "## Analysis Results\n\n[Markdown content with analysis results]",
  "content_translated": ""
}
```

**Example:**
```javascript
const headers = {};
if (yourToken) {
  headers['Authorization'] = `Bearer ${yourToken}`;
}

const resultResponse = await fetch(
  `${API_URL}/api/v1/results/${completion.resultId}/`,
  {
    headers: headers
  }
);

const result = await resultResponse.json();
console.log('Result content:', result.content);
```

### Step 6: Handle Multiple Results (Optional)

Some COTs may produce multiple results (one per step). To get all results:

1. Fetch all chats for the session
2. Filter chats where `parent` is set and `result_id` exists
3. Fetch each result individually

**Example:**
```javascript
// Get all child chats with results
const chatsResponse = await fetch(
  `${API_URL}/api/v1/chats/?session_id=${sessionId}&page_size=500`,
  {
    headers: {
      'Authorization': `Bearer ${yourToken}`
    }
  }
);

const chatsData = await chatsResponse.json();
const childChats = chatsData.results.filter(
  chat => chat.parent && chat.result_id
);

// Fetch all results
const resultIds = childChats.map(chat => chat.result_id);
const results = await Promise.all(
  resultIds.map(resultId =>
    fetch(`${API_URL}/api/v1/results/${resultId}/`, {
      headers: {
        'Authorization': `Bearer ${yourToken}`
      }
    }).then(res => res.json())
  )
);

console.log('All results:', results);
```

## Complete Example

Here's a complete example that ties everything together:

```javascript
async function runCOTPrompt(cotSlug, parameters = {}, token = null) {
  const API_URL = process.env.FINCHAT_API_URL || 'https://finchat-api.adgo.io';
  // Token is optional - FinChat API doesn't require authentication
  
  try {
    // Step 1: Create session
    const headers = {
      'Content-Type': 'application/json'
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    const sessionResponse = await fetch(`${API_URL}/api/v1/sessions/`, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify({
        client_id: `client-${Date.now()}`,
        data_source: 'alpha_vantage'
      })
    });
    const session = await sessionResponse.json();
    const sessionId = session.id;
    console.log('Session created:', sessionId);
    
    // Step 2: Construct COT message
    let cotMessage = `cot ${cotSlug}`;
    if (Object.keys(parameters).length > 0) {
      const paramString = Object.entries(parameters)
        .map(([key, value]) => `$${key}:${value}`)
        .join(' ');
      cotMessage += ` ${paramString}`;
    }
    
    // Step 3: Run COT
    const chatHeaders = {
      'Content-Type': 'application/json'
    };
    if (token) {
      chatHeaders['Authorization'] = `Bearer ${token}`;
    }
    
    const chatResponse = await fetch(`${API_URL}/api/v1/chats/`, {
      method: 'POST',
      headers: chatHeaders,
      body: JSON.stringify({
        session: sessionId,
        message: cotMessage
      })
    });
    const cotChat = await chatResponse.json();
    const cotChatId = cotChat.id;
    console.log('COT started:', cotChatId);
    
    // Step 4: Poll for completion
    console.log('Polling for completion...');
    const completion = await pollForCOTCompletion(sessionId, cotChatId);
    console.log('COT completed!');
    
    // Step 5: Get results
    const resultHeaders = {};
    if (token) {
      resultHeaders['Authorization'] = `Bearer ${token}`;
    }
    
    const resultResponse = await fetch(
      `${API_URL}/api/v1/results/${completion.resultId}/`,
      {
        headers: resultHeaders
      }
    );
    const result = await resultResponse.json();
    
    return {
      sessionId,
      resultId: completion.resultId,
      content: result.content,
      contentTranslated: result.content_translated
    };
    
  } catch (error) {
    console.error('Error running COT:', error);
    throw error;
  }
}

// Helper function for polling
async function pollForCOTCompletion(sessionId, cotChatId, maxAttempts = 60, intervalMs = 5000, token = null) {
  const API_URL = process.env.FINCHAT_API_URL || 'https://finchat-api.adgo.io';
  
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    const chatsResponse = await fetch(
      `${API_URL}/api/v1/chats/?session_id=${sessionId}&page_size=500`,
      {
        headers: headers
      }
    );
    
    const chatsData = await chatsResponse.json();
    const responseChat = chatsData.results.find(chat => chat.respond_to === cotChatId);
    
    if (!responseChat) {
      await new Promise(resolve => setTimeout(resolve, intervalMs));
      continue;
    }
    
    if (responseChat.intent === 'error') {
      throw new Error('COT execution failed');
    }
    
    if (responseChat.result_id) {
      return {
        responseChatId: responseChat.id,
        resultId: responseChat.result_id,
        metadata: responseChat.metadata
      };
    }
    
    const loadingInfo = responseChat.metadata;
    if (loadingInfo) {
      const progress = (loadingInfo.current_progress / loadingInfo.total_progress) * 100;
      console.log(`Progress: ${progress.toFixed(1)}% - ${loadingInfo.current_step}`);
    }
    
    await new Promise(resolve => setTimeout(resolve, intervalMs));
  }
  
  throw new Error('COT execution timed out');
}

// Usage (no token required)
runCOTPrompt('conditional-stock-purchase', {
  ticker: 'AAPL',
  date: '2024-01-01'
}).then(result => {
  console.log('Final result:', result.content);
}).catch(error => {
  console.error('Failed:', error);
});

// Usage with optional token
runCOTPrompt('conditional-stock-purchase', {
  ticker: 'AAPL',
  date: '2024-01-01'
}, 'your-optional-token').then(result => {
  console.log('Final result:', result.content);
}).catch(error => {
  console.error('Failed:', error);
});
```

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/sessions/` | POST | Create a new session |
| `/api/v1/sessions/{id}/` | GET | Get session details |
| `/api/v1/cot/{id}/` | GET | Get COT configuration |
| `/api/v1/chats/` | POST | Send chat message (run COT) |
| `/api/v1/chats/` | GET | Get chats (poll for completion) |
| `/api/v1/results/{id}/` | GET | Get result content |

## Error Handling

- **403 Forbidden**: If using authentication, check your API token (authentication is optional)
- **404 Not Found**: Verify COT slug/ID exists
- **Timeout**: Increase `maxAttempts` or `intervalMs` in polling function
- **Error Intent**: Check `chat.intent === 'error'` for execution failures

## Notes

- Polling interval: Recommended 5-30 seconds depending on COT complexity
- Timeout: Most COTs complete within 5-10 minutes, but complex ones may take longer
- Progress tracking: Use `metadata.current_progress` and `metadata.total_progress` for progress updates
- Multiple results: Some COTs produce step-by-step results; check `parent` field in chats to identify child results

