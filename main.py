from widget_setup_server import mcp

def main():
    """
    Start the widget setup MCP server.
    """
    print("Starting widget-setup MCP server...")
    mcp.run()

if __name__ == "__main__":
    main()