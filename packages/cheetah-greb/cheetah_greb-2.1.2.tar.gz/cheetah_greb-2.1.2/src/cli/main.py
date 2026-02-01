from __future__ import annotations

import click


@click.command()
def main():
    """Greb - AI-powered intelligent code search service.
    
    Greb is an intelligent code search service that helps developers discover code 
    through natural language queries. It provides fast and accurate code discovery 
    across your projects.
    
    KEY FEATURES:
    - Natural Language Search - Search code using plain English queries
    - Smart Ranking - AI-powered relevance scoring for accurate results
    - Multiple Integration Options - REST API and MCP server support
    - File Pattern Filtering - Search specific file types and directories
    
    INTEGRATION METHODS:
    
    1. REST API Service
       Use Greb programmatically in your applications:
       
       pip install cheetah-greb
       
       from greb import GrebClient
       client = GrebClient(
           api_key='grb_your_api_key_here',
           base_url='https://api.yourdomain.com'
       )
       results = client.search(
           query='find authentication middleware functions',
           directory='./src',
           file_patterns=['*.js', '*.py'],
       )
    
    2. MCP Server
       Integrate with AI assistants (Claude Desktop, Cline, Cursor):
       
       pip install cheetah-greb
       
       Configure in your MCP client settings:
       {
         "mcpServers": {
           "greb-mcp": {
             "disabled": false,
             "timeout": 60,
             "type": "stdio",
             "command": "greb-mcp",
             "args": [],
             "env": {
               "GREB_API_KEY": "grb_your_api_key_here",
               "GREB_API_URL": "https://api.yourdomain.com"
             }
           }
         }
       }
    
    Documentation: https://grebmcp.com/get-started/introduction
    """
    pass


if __name__ == '__main__':
    main()
