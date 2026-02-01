"""Duplicate command - Detect duplicate content in WordPress"""

import click
from rich.console import Console
from rich.table import Table

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.logger import get_logger
from praisonaiwp.utils.ai_formatter import AIFormatter
from praisonaiwp.ai import AI_AVAILABLE

console = Console()
logger = get_logger(__name__)


@click.group()
def duplicate():
    """Detect duplicate content in WordPress"""
    pass


@duplicate.command()
@click.argument('content')
@click.option('--threshold', type=float, default=0.7, 
              help='Similarity threshold (0-1, default: 0.7)')
@click.option('--duplicate-threshold', type=float, default=0.95,
              help='Threshold to flag as definite duplicate (0-1, default: 0.95)')
@click.option('--type', 'post_type', default='post', help='Post type to search')
@click.option('--category', default=None, help='Category filter (default: all)')
@click.option('--count', type=int, default=5, help='Number of similar posts to show')
@click.option('--file', 'content_file', type=click.Path(exists=True),
              help='Read content from file instead of argument')
@click.option('--title-only', is_flag=True, help='Only check against titles')
@click.option('--server', default=None, help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def check(content, threshold, duplicate_threshold, post_type, category, 
          count, content_file, title_only, server, json_output, verbose):
    """
    Check if content is duplicate before publishing.
    
    Examples:
    
        # Check by title
        praisonaiwp duplicate check "PraisonAI Streaming Guide"
        
        # Check content from file
        praisonaiwp duplicate check "" --file article.md
        
        # Stricter threshold
        praisonaiwp duplicate check "My Article" --threshold 0.9
        
        # JSON output for scripting
        praisonaiwp duplicate check "Test" --json
    """
    # Check AI availability
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="duplicate check",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Read from file if provided
    if content_file:
        with open(content_file, 'r') as f:
            content = f.read()
    
    if not content.strip():
        error_msg = AIFormatter.error_response(
            "No content provided. Use an argument or --file option.",
            command="duplicate check",
            error_code="NO_CONTENT"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    try:
        # Load configuration
        config = Config()
        server_config = config.get_server(server)
        
        if verbose:
            console.print(f"[yellow]Checking for duplicates...[/yellow]")
            console.print(f"Content: {content[:50]}...")
            console.print(f"Threshold: {threshold}")
        
        with SSHManager(
            server_config['hostname'],
            server_config['username'],
            server_config['key_file'],
            server_config.get('port', 22)
        ) as ssh:
            wp = WPClient(
                ssh,
                server_config['wp_path'],
                server_config.get('php_bin', 'php'),
                server_config.get('wp_cli', '/usr/local/bin/wp'),
                verify_installation=False
            )
            
            # Import and create detector
            from praisonaiwp.ai.duplicate_detector import DuplicateDetector
            
            detector = DuplicateDetector(
                wp_client=wp,
                threshold=threshold,
                duplicate_threshold=duplicate_threshold,
                verbose=1 if verbose else 0
            )
            
            # Index posts
            if verbose:
                console.print("[cyan]Indexing posts...[/cyan]")
            
            indexed = detector.index_posts(
                post_type=post_type,
                category=category
            )
            
            if verbose:
                console.print(f"[green]Indexed {indexed} posts[/green]")
            
            # Check for duplicates
            # Split title from content if title-only mode
            title = None
            check_content = content
            if title_only:
                title = content
                check_content = ""
            elif '\n' in content:
                lines = content.split('\n', 1)
                title = lines[0]
                check_content = lines[1] if len(lines) > 1 else ""
            
            result = detector.check_duplicate(
                content=check_content,
                title=title or content,
                top_k=count
            )
            
            # Format output
            if json_output:
                import json
                click.echo(json.dumps(result.to_dict(), indent=2))
            else:
                _format_check_result(result, verbose)
                
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="duplicate check",
            error_code="DUPLICATE_CHECK_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        logger.error(f"Duplicate check failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()


def _format_check_result(result, verbose: bool = False):
    """Format and display duplicate check result."""
    console.print()
    console.print("[bold]🔍 Duplicate Check Results[/bold]")
    console.print("=" * 50)
    console.print(f"Query: {result.query}")
    console.print(f"Threshold: {result.threshold}")
    console.print(f"Posts checked: {result.total_posts_checked}")
    console.print()
    
    if not result.matches:
        console.print("[green]✅ No duplicates or similar content found![/green]")
        console.print("This content appears to be unique.")
        return
    
    if result.has_duplicates:
        console.print("[red]⚠️  POTENTIAL DUPLICATES FOUND:[/red]")
    else:
        console.print("[yellow]📋 Similar content found:[/yellow]")
    
    console.print()
    
    for i, match in enumerate(result.matches, 1):
        if match.status == "duplicate":
            status_color = "red"
            status_icon = "🔴"
        elif match.status == "similar":
            status_color = "yellow"
            status_icon = "🟡"
        else:
            status_color = "green"
            status_icon = "🟢"
        
        console.print(f"{i}. [bold]{match.title}[/bold] (ID: {match.post_id})")
        console.print(f"   Similarity: [{status_color}]{match.similarity_score:.2f}[/{status_color}] | Status: {status_icon} {match.status.upper()}")
        if match.url and verbose:
            console.print(f"   URL: {match.url}")
        console.print()
    
    # Recommendation
    if result.has_duplicates:
        top_match = result.matches[0]
        console.print("[bold]Recommendation:[/bold]")
        console.print(f"  Consider updating existing post [cyan]{top_match.post_id}[/cyan] instead of creating a new one.")


@duplicate.command()
@click.argument('post_id', type=int)
@click.option('--count', type=int, default=5, help='Number of related posts to find')
@click.option('--threshold', type=float, default=0.3, help='Minimum similarity (0-1)')
@click.option('--server', default=None, help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def related(post_id, count, threshold, server, json_output, verbose):
    """
    Find posts related to an existing post.
    
    Examples:
    
        # Find related posts
        praisonaiwp duplicate related 49287
        
        # More results with lower threshold
        praisonaiwp duplicate related 49287 --count 10 --threshold 0.2
    """
    # Check AI availability
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"duplicate related {post_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    try:
        # Load configuration
        config = Config()
        server_config = config.get_server(server)
        
        with SSHManager(
            server_config['hostname'],
            server_config['username'],
            server_config['key_file'],
            server_config.get('port', 22)
        ) as ssh:
            wp = WPClient(
                ssh,
                server_config['wp_path'],
                server_config.get('php_bin', 'php'),
                server_config.get('wp_cli', '/usr/local/bin/wp'),
                verify_installation=False
            )
            
            # Get the target post
            post = wp.get_post(post_id)
            if not post:
                error_msg = AIFormatter.error_response(
                    f"Post {post_id} not found",
                    command=f"duplicate related {post_id}",
                    error_code="NOT_FOUND"
                )
                click.echo(AIFormatter.format_output(error_msg, json_output))
                return
            
            # Create detector and find related
            from praisonaiwp.ai.duplicate_detector import DuplicateDetector
            
            detector = DuplicateDetector(
                wp_client=wp,
                threshold=threshold,
                verbose=1 if verbose else 0
            )
            
            detector.index_posts()
            
            result = detector.find_related_posts(
                post=post,
                count=count,
                similarity_threshold=threshold
            )
            
            if json_output:
                import json
                click.echo(json.dumps(result, indent=2))
            else:
                _format_related_result(post, result, verbose)
                
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"duplicate related {post_id}",
            error_code="RELATED_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        logger.error(f"Find related failed: {e}")


@duplicate.command('check-batch')
@click.argument('items', nargs=-1, required=True)
@click.option('--threshold', type=float, default=0.7, 
              help='Similarity threshold (0-1, default: 0.7)')
@click.option('--duplicate-threshold', type=float, default=0.8,
              help='Threshold to flag as definite duplicate (0-1, default: 0.8)')
@click.option('--type', 'post_type', default='post', help='Post type to search')
@click.option('--count', type=int, default=5, help='Number of similar posts to show')
@click.option('--any-match', is_flag=True, default=True, 
              help='Flag as duplicate if ANY item matches (default: True)')
@click.option('--all-match', is_flag=True, 
              help='Flag as duplicate only if ALL items match')
@click.option('--server', default=None, help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def check_batch(items, threshold, duplicate_threshold, post_type, count, 
                any_match, all_match, server, json_output, verbose):
    """
    Check multiple items (sentences, paragraphs) for duplicates.
    
    More robust than single-string checking - checks each item independently.
    
    Examples:
    
        # Check multiple sentences
        praisonaiwp duplicate check-batch "OpenAI launches GPT-5" "AI breakthrough 2026"
        
        # Check from JSON list
        echo '["sentence1", "sentence2"]' | praisonaiwp duplicate check-batch --json
        
        # Require ALL items to match
        praisonaiwp duplicate check-batch "title" "content" --all-match
    """
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="duplicate check-batch",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    if not items:
        error_msg = AIFormatter.error_response(
            "No items provided. Pass multiple strings as arguments.",
            command="duplicate check-batch",
            error_code="NO_ITEMS"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Convert to list
    items_list = list(items)
    
    try:
        config = Config()
        server_config = config.get_server(server)
        
        if verbose:
            console.print(f"[yellow]Checking {len(items_list)} items for duplicates...[/yellow]")
            for i, item in enumerate(items_list, 1):
                console.print(f"  {i}. {item[:50]}...")
        
        with SSHManager(
            server_config['hostname'],
            server_config['username'],
            server_config['key_file'],
            server_config.get('port', 22)
        ) as ssh:
            wp = WPClient(
                ssh,
                server_config['wp_path'],
                server_config.get('php_bin', 'php'),
                server_config.get('wp_cli', '/usr/local/bin/wp'),
                verify_installation=False
            )
            
            from praisonaiwp.ai.duplicate_detector import DuplicateDetector
            
            detector = DuplicateDetector(
                wp_client=wp,
                threshold=threshold,
                duplicate_threshold=duplicate_threshold,
                verbose=1 if verbose else 0
            )
            
            if verbose:
                console.print("[cyan]Indexing posts...[/cyan]")
            
            indexed = detector.index_posts(post_type=post_type)
            
            if verbose:
                console.print(f"[green]Indexed {indexed} posts[/green]")
            
            # Use all_match flag to invert any_match
            use_any_match = not all_match
            
            result = detector.check_duplicates_batch(
                items=items_list,
                top_k=count,
                any_match=use_any_match
            )
            
            if json_output:
                import json
                click.echo(json.dumps(result.to_dict(), indent=2))
            else:
                _format_batch_result(result, items_list, verbose)
                
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="duplicate check-batch",
            error_code="BATCH_CHECK_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        logger.error(f"Batch duplicate check failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()


def _format_batch_result(result, items, verbose: bool = False):
    """Format and display batch duplicate check result."""
    console.print()
    console.print("[bold]🔍 Batch Duplicate Check Results[/bold]")
    console.print("=" * 50)
    console.print(f"Items checked: {len(items)}")
    console.print(f"Threshold: {result.threshold}")
    console.print(f"Posts checked: {result.total_posts_checked}")
    console.print()
    
    if not result.matches:
        console.print("[green]✅ No duplicates found for any item![/green]")
        console.print("All content appears to be unique.")
        return
    
    if result.has_duplicates:
        console.print("[red]⚠️  DUPLICATES FOUND:[/red]")
    else:
        console.print("[yellow]📋 Similar content found:[/yellow]")
    
    console.print()
    
    for i, match in enumerate(result.matches, 1):
        if match.status == "duplicate":
            status_color = "red"
            status_icon = "🔴"
        else:
            status_color = "yellow"
            status_icon = "🟡"
        
        console.print(f"{i}. [bold]{match.title}[/bold] (ID: {match.post_id})")
        console.print(f"   Similarity: [{status_color}]{match.similarity_score:.2f}[/{status_color}] | Status: {status_icon} {match.status.upper()}")
        if match.url and verbose:
            console.print(f"   URL: {match.url}")
        console.print()
    
    if result.has_duplicates:
        console.print("[bold]Recommendation:[/bold]")
        console.print("  One or more items match existing content. Consider updating instead of creating new.")


def _format_related_result(post, result, verbose: bool = False):
    """Format and display related posts result."""
    console.print()
    console.print("[bold]🔗 Related Posts[/bold]")
    console.print("=" * 50)
    console.print(f"Source post: {post.get('post_title', post.get('title', 'Unknown'))}")
    console.print(f"Source ID: {post.get('ID')}")
    console.print()
    
    posts = result.get("posts", [])
    if not posts:
        console.print("[yellow]No related posts found with the given threshold.[/yellow]")
        return
    
    console.print(f"Found {len(posts)} related posts:")
    console.print()
    
    for i, p in enumerate(posts, 1):
        score = p.get("similarity_score", 0)
        if p.get("is_duplicate"):
            status = "[red]DUPLICATE[/red]"
        elif score >= 0.7:
            status = "[yellow]VERY SIMILAR[/yellow]"
        else:
            status = "[green]RELATED[/green]"
        
        console.print(f"{i}. [bold]{p.get('title', 'Untitled')}[/bold]")
        console.print(f"   ID: {p.get('id')} | Similarity: {score:.2f} | {status}")
        if verbose and p.get("url"):
            console.print(f"   URL: {p['url']}")
        console.print()
