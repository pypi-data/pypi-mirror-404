import argparse
from .server import mcp

def main():
    parser = argparse.ArgumentParser(
        description="Plus version of MCP server for accessing RedNote"
    )
    parser.parse_args()
    mcp.run()

if __name__ == "__main__":
    main()