"""
Command-line interface for Digilog.
"""

import argparse
import getpass
import os
import sys
from typing import Optional
from .exceptions import DigilogError


def login(api_key: Optional[str] = None, foom_api_key: Optional[str] = None, foom_server_url: Optional[str] = None) -> None:
    """Interactive login to get authentication token.
    
    Args:
        api_key: Optional Digilog API key for headless/non-interactive mode
        foom_api_key: Optional foom2 API key for foom2 integration
        foom_server_url: Optional foom2 server URL
    """
    print("Digilog Login")
    print("=" * 50)
    
    # Get token from argument or prompt user
    if api_key:
        token = api_key
    else:
        token = getpass.getpass("Enter your Digilog API key: ")
    
    if not token.strip():
        print("Error: Token cannot be empty")
        sys.exit(1)
    
    # Save token to environment
    os.environ['DIGILOG_API_KEY'] = token
    print("✓ Digilog API key saved to environment variable DIGILOG_API_KEY")
    
    # Configure foom2 if provided
    if foom_api_key or foom_server_url:
        if foom_api_key:
            os.environ['FOOM_API_KEY'] = foom_api_key
            print("✓ Foom2 API key saved to environment variable FOOM_API_KEY")
        if foom_server_url:
            os.environ['FOOM_SERVER_URL'] = foom_server_url
            print(f"✓ Foom2 server URL saved to environment variable FOOM_SERVER_URL: {foom_server_url}")
    
    print("\n  You can also set these in your shell profile for persistence.")


def configure_foom(server_url: Optional[str] = None, api_key: Optional[str] = None) -> None:
    """Configure foom2 integration settings.
    
    Args:
        server_url: Foom2 server URL (e.g., http://localhost:3001)
        api_key: Foom2 API key
    """
    print("Foom2 Configuration")
    print("=" * 50)
    
    if not server_url and not api_key:
        # Interactive mode
        server_url = input("Enter foom2 server URL (default: http://localhost:3001): ").strip()
        if not server_url:
            server_url = "http://localhost:3001"
        api_key = getpass.getpass("Enter your foom2 API key: ")
    
    if server_url:
        os.environ['FOOM_SERVER_URL'] = server_url
        print(f"✓ Foom2 server URL saved: {server_url}")
    
    if api_key:
        os.environ['FOOM_API_KEY'] = api_key
        print("✓ Foom2 API key saved")
    
    print("\n  Note: Foom2 integration is optional. Digilog works standalone without it.")
    print("  Set FOOM_SERVER_URL and FOOM_API_KEY in your shell profile for persistence.")


def version() -> None:
    """Show Digilog version and configuration."""
    from . import __version__, get_effective_api_url
    
    print(f"Digilog v{__version__}")
    print()
    
    # Configuration
    print("Configuration:")
    print("-" * 40)
    
    # Digilog API key
    token = os.environ.get('DIGILOG_API_KEY')
    if token:
        # Show first 4 and last 4 characters
        if len(token) > 8:
            obfuscated = f"{token[:4]}...{token[-4:]}"
        else:
            obfuscated = "***"
        print(f"  DIGILOG_API_KEY: {obfuscated}")
    else:
        print(f"  DIGILOG_API_KEY: (not set)")
    
    # Digilog API URL
    api_url = get_effective_api_url()
    print(f"  DIGILOG_API_URL: {api_url}")
    
    # Foom2 configuration (optional)
    foom_server_url = os.environ.get('FOOM_SERVER_URL')
    foom_api_key = os.environ.get('FOOM_API_KEY')
    
    if foom_server_url:
        print(f"  FOOM_SERVER_URL: {foom_server_url}")
    else:
        print(f"  FOOM_SERVER_URL: (not set)")
    
    if foom_api_key:
        # Show first 4 and last 4 characters
        if len(foom_api_key) > 8:
            obfuscated = f"{foom_api_key[:4]}...{foom_api_key[-4:]}"
        else:
            obfuscated = "***"
        print(f"  FOOM_API_KEY: {obfuscated}")
    else:
        print(f"  FOOM_API_KEY: (not set)")


def status() -> None:
    """Show current Digilog status."""
    print("Digilog Status")
    print("=" * 50)
    
    # Check token
    token = os.environ.get('DIGILOG_API_KEY')
    if token:
        print(f"✓ Digilog API key: {'*' * (len(token) - 4) + token[-4:]}")
    else:
        print("✗ No Digilog API key found")
        print("  Set DIGILOG_API_KEY environment variable or run 'digilog login'")
    
    # Check API base URL
    from . import get_effective_api_url
    api_url = get_effective_api_url()
    print(f"Digilog API URL: {api_url}")
    
    # Test connection if token is available
    if token:
        try:
            from .api import APIClient
            client = APIClient(api_url, token)
            projects = client.get_projects()
            print(f"✓ Connected successfully - {len(projects)} projects found")
        except Exception as e:
            print(f"✗ Connection failed: {e}")
    
    # Check foom2 configuration (optional)
    print("\nFoom2 Integration (Optional)")
    print("-" * 50)
    foom_server_url = os.environ.get('FOOM_SERVER_URL')
    foom_api_key = os.environ.get('FOOM_API_KEY')
    
    if foom_server_url or foom_api_key:
        if foom_server_url:
            print(f"✓ Foom2 server URL: {foom_server_url}")
        else:
            print("✗ Foom2 server URL not configured")
        
        if foom_api_key:
            print(f"✓ Foom2 API key: {'*' * (len(foom_api_key) - 4) + foom_api_key[-4:]}")
        else:
            print("✗ Foom2 API key not configured")
    else:
        print("✗ Foom2 not configured (this is optional)")
        print("  Run 'digilog configure-foom' to set up foom2 integration")


def init_project(project: str, description: Optional[str] = None) -> None:
    """Initialize a new project."""
    
    try:
        from .api import APIClient, get_effective_api_url
        
        token = os.environ.get('DIGILOG_API_KEY')
        if not token:
            print("Error: No authentication token found")
            print("Set DIGILOG_API_KEY environment variable or run 'digilog login'")
            sys.exit(1)
        
        client = APIClient(get_effective_api_url(), token)
        created_project = client.create_project(project, description)
        
        print(f"✓ Project '{created_project['name']}' created successfully")
        print(f"  ID: {created_project['id']}")
        if created_project.get('description'):
            print(f"  Description: {created_project['description']}")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def list_projects() -> None:
    """List all projects."""
    try:
        from .api import APIClient, get_effective_api_url
        
        token = os.environ.get('DIGILOG_API_KEY')
        if not token:
            print("Error: No authentication token found")
            print("Set DIGILOG_API_KEY environment variable or run 'digilog login'")
            sys.exit(1)
        
        client = APIClient(get_effective_api_url(), token)
        projects = client.get_projects()
        
        if not projects:
            print("No projects found")
            return
        
        print("Your Projects")
        print("=" * 50)
        for project in projects:
            print(f"• Name: {project['name']}")
            print(f"  ID: {project['id']}")
            if project.get('description'):
                print(f"  Description: {project['description']}\n")
            print(f"  Runs: {project['_count']['runs']}")
            print(f"  Created: {project['createdAt']}")
            print()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def list_runs(project_id: str, limit: int = 50, offset: int = 0) -> None:
    """List runs for a project."""
    
    try:
        from .api import APIClient, get_effective_api_url
        
        token = os.environ.get('DIGILOG_API_KEY')
        if not token:
            print("Error: No authentication token found")
            print("Set DIGILOG_API_KEY environment variable or run 'digilog login'")
            sys.exit(1)
        
        client = APIClient(get_effective_api_url(), token)
        runs = client.get_runs(project_id, limit, offset)
        
        if not runs:
            print(f"No runs found for project {project_id}")
            return
        
        print(f"Runs for Project {project_id}")
        print("=" * 50)
        for run in runs:
            print(f"• Name: {run.get('name', 'Unnamed')}")
            print(f"  ID: {run['id']}")
            if run.get('description'):
                print(f"  Description: {run['description']}")
            print(f"  Status: {run.get('status', 'UNKNOWN')}")
            print(f"  Created: {run.get('createdAt', 'Unknown')}")
            if run.get('finishedAt'):
                print(f"  Finished: {run['finishedAt']}")
            print()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Digilog - Experiment tracking with wandb-like interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  digilog --version                # Show version and configuration
  digilog login                    # Interactive login to get authentication token
  digilog login --key <api-key>    # Non-interactive login (headless mode)
  digilog status                   # Show current status
  digilog init my-project          # Initialize a new project
  digilog projects                 # List all projects
  digilog runs <project-id>        # List runs for a project
        """
    )
    
    # Add version flag
    parser.add_argument('--version', '-v', action='store_true', help='Show version and configuration')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Login command
    login_parser = subparsers.add_parser('login', help='Login to get authentication token')
    login_parser.add_argument('--key', '-k', help='Digilog API key for headless/non-interactive mode')
    login_parser.add_argument('--foom-api-key', help='Foom2 API key (optional, for foom2 integration)')
    login_parser.add_argument('--foom-server-url', help='Foom2 server URL (optional, for foom2 integration)')
    
    # Configure foom2 command
    foom_parser = subparsers.add_parser('configure-foom', help='Configure foom2 integration (optional)')
    foom_parser.add_argument('--server-url', help='Foom2 server URL')
    foom_parser.add_argument('--api-key', help='Foom2 API key')
    
    # Status command
    subparsers.add_parser('status', help='Show current status')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize a new project')
    init_parser.add_argument('project', help='Project name')
    init_parser.add_argument('--description', '-d', help='Project description')
    
    # Projects command
    subparsers.add_parser('projects', help='List all projects')
    
    # Runs command
    runs_parser = subparsers.add_parser('runs', help='List runs for a project')
    runs_parser.add_argument('project_id', help='Project ID')
    runs_parser.add_argument('--limit', '-l', type=int, default=50, help='Maximum number of runs to return (default: 50)')
    runs_parser.add_argument('--offset', '-o', type=int, default=0, help='Number of runs to skip (default: 0)')
    
    args = parser.parse_args()
    
    try:
        if args.version:
            version()
            return
        
        if args.command == 'login':
            login(api_key=args.key, foom_api_key=getattr(args, 'foom_api_key', None), foom_server_url=getattr(args, 'foom_server_url', None))
        elif args.command == 'configure-foom':
            configure_foom(server_url=getattr(args, 'server_url', None), api_key=getattr(args, 'api_key', None))
        elif args.command == 'status':
            status()
        elif args.command == 'init':
            init_project(args.project, args.description)
        elif args.command == 'projects':
            list_projects()
        elif args.command == 'runs':
            list_runs(args.project_id, args.limit, args.offset)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except DigilogError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 