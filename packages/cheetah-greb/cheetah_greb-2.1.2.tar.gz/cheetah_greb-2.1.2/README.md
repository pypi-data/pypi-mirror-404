# Greb Installation

Getting started with Greb code search is simple and takes just a few minutes.

## Integration Methods

Integrate Greb into your workflow using our REST API service or MCP server for AI assistants. Both provide access to intelligent code search capabilities.

Select your preferred integration method below.

## Steps

### REST API Method

Follow these steps to integrate Greb using our REST API:

#### 1. Get your API key

Sign up for a Greb account and get your API key from the dashboard. Each API key provides access to our intelligent code search capabilities.

#### 2. Install the Python client

Install the Greb Python package to use the REST API service.

```bash
pip install cheetah-greb
{
  "results": [
    {
      "path": "src/middleware/auth.js",
      "line_start": 15,
      "line_end": 25,
      "score": 0.950,
      "reason": "Core authentication middleware implementation with JWT verification",
      "span": {
        "start_line": 15,
        "end_line": 25,
        "text": "function authenticateToken(req, res, next) {\n  const authHeader = req.headers['authorization']\n  const token = authHeader && authHeader.split(' ')[1]\n  \n  if (!token) {\n    return res.status(401).json({ error: 'Access token required' })\n  }\n  \n  jwt.verify(token, process.env.JWT_SECRET, (err, user) => {\n    if (err) return res.status(403).json({ error: 'Invalid token' })\n    req.user = user\n    next()\n  })\n}"
      }
    }
  ],
  "query": "authentication middleware functions",
  "total_results": 1
}
```

Each result includes:
- `path`: File path relative to search directory
- `line_start`/`line_end`: Line numbers where the match was found
- `score`: Relevance score (0-1, higher is more relevant)
- `reason`: AI explanation of why this code matches the query
- `span`: Actual code context with surrounding lines

#### 5. API endpoints available

The REST API provides these endpoints:

```bash
# Rerank search candidates (agent provides keywords)
POST /v1/rerank

# Health check
GET /health

# List models
GET /v1/models
```

Note: The agent (Claude, GPT, etc.) must extract keywords from the query and provide them to the search pipeline. Local grep/glob/read operations run on the client side, then candidates are sent to the server for AI-powered reranking.

### MCP Server Method

Follow these steps to integrate Greb using our MCP server:

#### 1. Install the Greb package

The MCP server is included in the Greb Python package.

```bash
pip install cheetah-greb
```

#### 2. Configure your MCP client

Add the Greb MCP server to your AI assistant configuration (Claude Desktop, Cline, Cursor, etc.).

```json
{
  "mcpServers": {
    "greb-mcp": {
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "greb-mcp",
      "args": [],
      "env": {
        "GREB_API_KEY": "grb_your_api_key_here"
      }
    }
  }
}
```

#### 3. Start using natural language search

Talk to your AI assistant (Cline, Claude Desktop, etc.) and it will automatically make calls to the MCP server to search your code:

```bash
# Example queries your AI assistant can use:
User: "Search for authentication middleware in the backend directory"
Agent: "[Calls MCP server code_search tool]

User: "Find all API endpoints with file patterns *.js, *.ts"
Agent: [Calls MCP server code_search tool]

User: "Look for database connection setup in ./src"
Agent: [Calls MCP server code_search tool]

User: "Find database configuration files"
Agent: [Calls MCP server code_search tool]
```

#### 4. MCP tools available

The MCP server provides this tool for your AI assistant:

```bash
# code_search(query, keywords, directory, file_patterns)
#   Search code using natural language queries
#   - query: Natural language description
#   - keywords: Extracted keywords from AI agent
#     {
#       "primary_terms": ["term1", "term2"],
#       "file_patterns": ["*.py", "*.js"],
#       "intent": "search intent"
#     }
#   - directory: Full absolute path to search directory
#   - file_patterns: Optional file patterns to filter
#   Returns formatted results with code snippets
```

**Important:** The calling AI agent (Claude, GPT, etc.) must extract keywords from the user's query and provide them in the keywords parameter. The MCP server uses these keywords to run local grep/glob searches, then sends candidates to the API server for AI-powered reranking.

## That's it!

You now have access to intelligent code search through your chosen integration method. Start searching your codebase using natural language queries!