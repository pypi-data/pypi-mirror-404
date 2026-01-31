"""
ISAF Command Line Interface

Provides CLI commands for inspecting, verifying, and exporting lineage data.
"""

import json
import sys
from pathlib import Path
from typing import Optional

try:
    import click
except ImportError:
    click = None


def _check_click():
    if click is None:
        print("Error: click package required for CLI. Install with: pip install click")
        sys.exit(1)


if click:
    @click.group()
    @click.version_option(version='0.1.0', prog_name='isaf')
    def cli():
        """ISAF Logger - Instruction Stack Audit Framework CLI"""
        pass

    @cli.command()
    @click.argument('lineage_file', type=click.Path(exists=True))
    def inspect(lineage_file: str):
        """Display formatted report of a lineage file."""
        with open(lineage_file, 'r') as f:
            data = json.load(f)
        
        click.echo("\n" + "=" * 60)
        click.echo("ISAF LINEAGE REPORT")
        click.echo("=" * 60)
        
        click.echo(f"\nAudit ID: {data.get('audit_id', 'N/A')}")
        click.echo(f"Session ID: {data.get('session_id', 'N/A')}")
        click.echo(f"Generated: {data.get('generated_at', 'N/A')}")
        click.echo(f"ISAF Version: {data.get('isaf_version', 'N/A')}")
        
        stack = data.get('instruction_stack', [])
        click.echo(f"\nLayers Logged: {len(stack)}")
        
        for layer in stack:
            click.echo(f"\n  Layer {layer.get('layer')}: {layer.get('layer_name')}")
            click.echo(f"    Owner: {layer.get('owner')}")
            click.echo(f"    Logged: {layer.get('logged_at')}")
        
        if 'hash_chain' in data:
            chain = data['hash_chain']
            click.echo(f"\nHash Chain: ✓ Present")
            click.echo(f"  Algorithm: {chain.get('algorithm')}")
            click.echo(f"  Root Hash: {chain.get('root_hash', '')[:32]}...")
        else:
            click.echo(f"\nHash Chain: ✗ Not present")
        
        if 'compliance' in data:
            click.echo("\nCompliance Mappings:")
            for framework, mapping in data['compliance'].items():
                coverage = mapping.get('coverage_percentage', 0)
                click.echo(f"  {mapping.get('framework_name')}: {coverage}% coverage")
        
        click.echo("\n" + "=" * 60 + "\n")

    @cli.command()
    @click.argument('lineage_file', type=click.Path(exists=True))
    def verify(lineage_file: str):
        """Verify cryptographic integrity of a lineage file."""
        import isaf
        
        try:
            result = isaf.verify_lineage(lineage_file)
            
            if result:
                click.echo(click.style("✓ VERIFICATION PASSED", fg='green', bold=True))
                click.echo("Hash chain integrity verified successfully.")
            else:
                click.echo(click.style("✗ VERIFICATION FAILED", fg='red', bold=True))
                click.echo("Hash chain integrity check failed. Data may have been modified.")
                sys.exit(1)
        except Exception as e:
            click.echo(click.style(f"✗ ERROR: {str(e)}", fg='red'))
            sys.exit(1)

    @cli.command('export-from-db')
    @click.argument('db_path', type=click.Path(exists=True))
    @click.option('--output', '-o', default='lineage_export.json', help='Output file path')
    @click.option('--session', '-s', default=None, help='Specific session ID to export')
    @click.option('--compliance', '-c', multiple=True, help='Compliance frameworks to map')
    def export_from_db(db_path: str, output: str, session: Optional[str], compliance: tuple):
        """Export lineage from SQLite database to JSON."""
        from isaf.storage.sqlite_backend import SQLiteBackend
        from isaf.export.exporter import ISAFExporter
        
        backend = SQLiteBackend(db_path)
        
        if session:
            lineage = backend.retrieve(session)
        else:
            lineage = backend.get_latest_session()
        
        if not lineage:
            click.echo(click.style("No lineage data found in database.", fg='yellow'))
            sys.exit(1)
        
        exporter = ISAFExporter()
        output_path = exporter.export(
            lineage,
            output,
            include_hash_chain=True,
            compliance_mappings=list(compliance) if compliance else None
        )
        
        click.echo(click.style(f"✓ Exported to: {output_path}", fg='green'))

    @cli.command('list-sessions')
    @click.argument('db_path', type=click.Path(exists=True))
    @click.option('--limit', '-n', default=10, help='Number of sessions to list')
    def list_sessions(db_path: str, limit: int):
        """List sessions in a database."""
        from isaf.storage.sqlite_backend import SQLiteBackend
        
        backend = SQLiteBackend(db_path)
        sessions = backend.list_sessions(limit=limit)
        
        if not sessions:
            click.echo("No sessions found.")
            return
        
        click.echo(f"\nRecent Sessions ({len(sessions)}):\n")
        for s in sessions:
            click.echo(f"  {s['session_id'][:8]}...  {s['created_at']}")


def main():
    _check_click()
    cli()


if __name__ == '__main__':
    main()
