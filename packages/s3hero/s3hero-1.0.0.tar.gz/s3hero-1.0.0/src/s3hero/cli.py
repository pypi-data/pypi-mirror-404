"""
S3Hero CLI - Command Line Interface for S3 management.

A powerful CLI tool to manage S3 buckets across AWS, Cloudflare R2,
and other S3-compatible services.
"""

import os
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from . import __version__
from .client import S3Client, S3Error, S3Provider
from .config import (
    ConfigError,
    ConfigManager,
    Profile,
    create_profile_interactive,
    get_config_manager,
)
from .utils import (
    build_s3_uri,
    confirm_action,
    console,
    create_bucket_table,
    create_objects_table,
    create_object_tree,
    create_progress_bar,
    create_simple_progress,
    format_size,
    parse_s3_uri,
    print_error,
    print_info,
    print_stats,
    print_success,
    print_warning,
    validate_bucket_name,
    ProgressCallback,
)


# Context object to pass around
class Context:
    """CLI Context object."""
    
    def __init__(self) -> None:
        self.config: Optional[ConfigManager] = None
        self.client: Optional[S3Client] = None
        self.profile_name: Optional[str] = None
        self.verbose: bool = False

    def get_client(self) -> S3Client:
        """Get or create S3 client."""
        if self.client:
            return self.client
        
        if not self.config:
            self.config = get_config_manager()
        
        profile = self.config.get_profile(self.profile_name)
        if not profile:
            raise click.ClickException(
                "No profile configured. Run 's3hero configure' to set up a profile."
            )
        
        self.client = S3Client(profile.to_s3_config())
        return self.client


pass_context = click.make_pass_decorator(Context, ensure=True)


# =====================
# Main CLI Group
# =====================

@click.group()
@click.option(
    '-p', '--profile',
    help='Profile to use for S3 connection',
    envvar='S3HERO_PROFILE'
)
@click.option(
    '-v', '--verbose',
    is_flag=True,
    help='Enable verbose output'
)
@click.version_option(version=__version__, prog_name='s3hero')
@pass_context
def main(ctx: Context, profile: Optional[str], verbose: bool) -> None:
    """
    S3Hero - A powerful CLI to manage S3 buckets.
    
    Supports AWS S3, Cloudflare R2, and other S3-compatible services.
    
    Run 's3hero configure' to set up your first profile.
    """
    ctx.profile_name = profile
    ctx.verbose = verbose
    ctx.config = get_config_manager()


# =====================
# Configuration Commands
# =====================

@main.group()
def configure() -> None:
    """Manage S3Hero configuration and profiles."""
    pass


@configure.command('add')
@click.option('--name', '-n', help='Profile name')
@click.option(
    '--provider', '-t',
    type=click.Choice(['aws', 'cloudflare_r2', 'other']),
    help='S3 provider type'
)
@click.option('--access-key', '-a', help='Access Key ID')
@click.option('--secret-key', '-s', help='Secret Access Key')
@click.option('--region', '-r', default='us-east-1', help='AWS Region')
@click.option('--endpoint', '-e', help='Custom endpoint URL')
@click.option('--account-id', help='Cloudflare Account ID (for R2)')
@click.option('--default', 'set_default', is_flag=True, help='Set as default profile')
@pass_context
def config_add(
    ctx: Context,
    name: Optional[str],
    provider: Optional[str],
    access_key: Optional[str],
    secret_key: Optional[str],
    region: str,
    endpoint: Optional[str],
    account_id: Optional[str],
    set_default: bool
) -> None:
    """Add a new S3 profile."""
    # Interactive mode if required params not provided
    if not all([name, provider, access_key, secret_key]):
        profile = create_profile_interactive()
    else:
        provider_enum = S3Provider(provider)
        profile = Profile(
            name=name,  # type: ignore
            provider=provider_enum,
            access_key=access_key,  # type: ignore
            secret_key=secret_key,  # type: ignore
            region=region,
            endpoint_url=endpoint,
            account_id=account_id
        )
    
    config = get_config_manager()
    config.add_profile(profile, set_default=set_default)
    print_success(f"Profile '{profile.name}' added successfully!")
    
    if set_default or len(config.profiles) == 1:
        print_info(f"'{profile.name}' is now the default profile")


@configure.command('list')
@pass_context
def config_list(ctx: Context) -> None:
    """List all configured profiles."""
    config = get_config_manager()
    profiles = config.list_profiles()
    
    if not profiles:
        print_warning("No profiles configured. Run 's3hero configure add' to add one.")
        return
    
    from rich.table import Table
    
    table = Table(title="S3Hero Profiles", show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Provider", style="green")
    table.add_column("Region", style="yellow")
    table.add_column("Default", style="blue")
    
    for profile in profiles:
        is_default = "✓" if profile.name == config.default_profile else ""
        table.add_row(
            profile.name,
            profile.provider.value,
            profile.region,
            is_default
        )
    
    console.print(table)


@configure.command('remove')
@click.argument('name')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation')
@pass_context
def config_remove(ctx: Context, name: str, force: bool) -> None:
    """Remove a profile."""
    config = get_config_manager()
    
    if not config.profile_exists(name):
        raise click.ClickException(f"Profile '{name}' not found")
    
    if not force:
        if not confirm_action(f"Remove profile '{name}'?"):
            print_info("Cancelled")
            return
    
    config.remove_profile(name)
    print_success(f"Profile '{name}' removed")


@configure.command('default')
@click.argument('name')
@pass_context
def config_default(ctx: Context, name: str) -> None:
    """Set the default profile."""
    config = get_config_manager()
    
    if not config.set_default(name):
        raise click.ClickException(f"Profile '{name}' not found")
    
    print_success(f"Default profile set to '{name}'")


@configure.command('show')
@click.argument('name', required=False)
@pass_context
def config_show(ctx: Context, name: Optional[str]) -> None:
    """Show profile details (hides secrets)."""
    config = get_config_manager()
    profile = config.get_profile(name)
    
    if not profile:
        raise click.ClickException(
            f"Profile '{name}' not found" if name else "No default profile configured"
        )
    
    from rich.panel import Panel
    
    content = f"""[bold]Name:[/bold] {profile.name}
[bold]Provider:[/bold] {profile.provider.value}
[bold]Region:[/bold] {profile.region}
[bold]Access Key:[/bold] {profile.access_key[:4]}...{profile.access_key[-4:]}
[bold]Secret Key:[/bold] ********
[bold]Endpoint:[/bold] {profile.endpoint_url or 'Default'}
[bold]Account ID:[/bold] {profile.account_id or 'N/A'}
[bold]Default Bucket:[/bold] {profile.default_bucket or 'None'}"""
    
    console.print(Panel(content, title=f"Profile: {profile.name}", border_style="cyan"))


# =====================
# Bucket Commands
# =====================

@main.group()
def bucket() -> None:
    """Manage S3 buckets."""
    pass


@bucket.command('list')
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@pass_context
def bucket_list(ctx: Context, as_json: bool) -> None:
    """List all buckets."""
    client = ctx.get_client()
    
    try:
        buckets = client.list_buckets()
        
        if as_json:
            import json
            data = [{'name': b.name, 'created': str(b.creation_date)} for b in buckets]
            console.print_json(json.dumps(data))
        else:
            if not buckets:
                print_info("No buckets found")
                return
            
            table = create_bucket_table(buckets)
            console.print(table)
            print_info(f"Total: {len(buckets)} buckets")
    except S3Error as e:
        raise click.ClickException(str(e))


@bucket.command('create')
@click.argument('name')
@click.option('--region', '-r', help='Bucket region')
@pass_context
def bucket_create(ctx: Context, name: str, region: Optional[str]) -> None:
    """Create a new bucket."""
    # Validate bucket name
    is_valid, error = validate_bucket_name(name)
    if not is_valid:
        raise click.ClickException(f"Invalid bucket name: {error}")
    
    client = ctx.get_client()
    
    try:
        client.create_bucket(name, region)
        print_success(f"Bucket '{name}' created successfully!")
    except S3Error as e:
        raise click.ClickException(str(e))


@bucket.command('delete')
@click.argument('name')
@click.option('--force', '-f', is_flag=True, help='Empty bucket before deleting')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@pass_context
def bucket_delete(ctx: Context, name: str, force: bool, yes: bool) -> None:
    """Delete a bucket."""
    client = ctx.get_client()
    
    if not client.bucket_exists(name):
        raise click.ClickException(f"Bucket '{name}' not found")
    
    if force:
        msg = f"This will [bold red]DELETE ALL OBJECTS[/bold red] in '{name}' and the bucket. Continue?"
    else:
        msg = f"Delete bucket '{name}'?"
    
    if not yes:
        if not confirm_action(msg):
            print_info("Cancelled")
            return
    
    try:
        if force:
            with create_simple_progress() as progress:
                task = progress.add_task(f"Emptying {name}...", total=None)
                
                def callback(count: int) -> None:
                    progress.update(task, advance=count)
                
                deleted = client.empty_bucket(name, callback=callback)
                progress.update(task, completed=deleted, total=deleted)
            
            print_info(f"Deleted {deleted} objects")
        
        client.delete_bucket(name)
        print_success(f"Bucket '{name}' deleted")
    except S3Error as e:
        raise click.ClickException(str(e))


@bucket.command('empty')
@click.argument('name')
@click.option('--prefix', '-p', default='', help='Only delete objects with this prefix')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@pass_context
def bucket_empty(ctx: Context, name: str, prefix: str, yes: bool) -> None:
    """Empty a bucket (delete all objects)."""
    client = ctx.get_client()
    
    if not client.bucket_exists(name):
        raise click.ClickException(f"Bucket '{name}' not found")
    
    if prefix:
        msg = f"Delete all objects with prefix '{prefix}' in bucket '{name}'?"
    else:
        msg = f"[bold red]DELETE ALL OBJECTS[/bold red] in bucket '{name}'?"
    
    if not yes:
        if not confirm_action(msg):
            print_info("Cancelled")
            return
    
    try:
        with create_simple_progress() as progress:
            task = progress.add_task(f"Deleting objects...", total=None)
            
            def callback(count: int) -> None:
                progress.update(task, advance=count)
            
            deleted = client.empty_bucket(name, prefix=prefix, callback=callback)
            progress.update(task, completed=deleted, total=deleted)
        
        print_success(f"Deleted {deleted} objects from '{name}'")
    except S3Error as e:
        raise click.ClickException(str(e))


@bucket.command('size')
@click.argument('name')
@pass_context
def bucket_size(ctx: Context, name: str) -> None:
    """Get bucket size and object count."""
    client = ctx.get_client()
    
    if not client.bucket_exists(name):
        raise click.ClickException(f"Bucket '{name}' not found")
    
    try:
        with create_simple_progress() as progress:
            progress.add_task("Calculating bucket size...", total=None)
            total_size, object_count = client.get_bucket_size(name)
        
        print_stats({
            "Bucket": name,
            "Total Size": format_size(total_size),
            "Object Count": f"{object_count:,}"
        }, title="Bucket Statistics")
    except S3Error as e:
        raise click.ClickException(str(e))


@bucket.command('exists')
@click.argument('name')
@pass_context
def bucket_exists(ctx: Context, name: str) -> None:
    """Check if a bucket exists."""
    client = ctx.get_client()
    
    if client.bucket_exists(name):
        print_success(f"Bucket '{name}' exists")
    else:
        print_warning(f"Bucket '{name}' does not exist")
        sys.exit(1)


# =====================
# Object Commands
# =====================

@main.command('ls')
@click.argument('path', required=False)
@click.option('--recursive', '-r', is_flag=True, help='List recursively')
@click.option('--tree', '-t', is_flag=True, help='Show as tree view')
@click.option('--limit', '-n', type=int, help='Maximum number of objects to list')
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@pass_context
def list_objects(
    ctx: Context,
    path: Optional[str],
    recursive: bool,
    tree: bool,
    limit: Optional[int],
    as_json: bool
) -> None:
    """
    List objects in a bucket.
    
    PATH can be a bucket name or s3://bucket/prefix
    """
    client = ctx.get_client()
    
    # Parse path
    if not path:
        # Try to use default bucket from profile
        if ctx.config and ctx.profile_name:
            profile = ctx.config.get_profile(ctx.profile_name)
            if profile and profile.default_bucket:
                path = profile.default_bucket
        
        if not path:
            raise click.ClickException("Please specify a bucket or path")
    
    bucket, prefix = parse_s3_uri(path)
    
    try:
        objects = client.list_objects(bucket, prefix, max_keys=limit or 1000)
        
        if as_json:
            import json
            data = [
                {
                    'key': obj.key,
                    'size': obj.size,
                    'last_modified': str(obj.last_modified)
                }
                for obj in objects
            ]
            console.print_json(json.dumps(data))
        elif tree:
            tree_view = create_object_tree(objects, bucket)
            console.print(tree_view)
        else:
            if not objects:
                print_info(f"No objects found in {build_s3_uri(bucket, prefix)}")
                return
            
            table = create_objects_table(objects)
            console.print(table)
            
            total_size = sum(obj.size for obj in objects)
            print_info(f"Total: {len(objects)} objects, {format_size(total_size)}")
    except S3Error as e:
        raise click.ClickException(str(e))


@main.command('cp')
@click.argument('source')
@click.argument('destination')
@click.option('--recursive', '-r', is_flag=True, help='Copy recursively')
@pass_context
def copy_file(ctx: Context, source: str, destination: str, recursive: bool) -> None:
    """
    Copy files to/from S3.
    
    Examples:
    
        s3hero cp file.txt s3://bucket/file.txt
        
        s3hero cp s3://bucket/file.txt ./local/
        
        s3hero cp -r ./folder/ s3://bucket/folder/
        
        s3hero cp s3://bucket/key s3://other-bucket/key
    """
    client = ctx.get_client()
    
    is_s3_source = source.startswith('s3://') or '/' in source and not os.path.exists(source.split('/')[0])
    is_s3_dest = destination.startswith('s3://')
    
    try:
        if is_s3_source and is_s3_dest:
            # S3 to S3 copy
            src_bucket, src_key = parse_s3_uri(source)
            dst_bucket, dst_key = parse_s3_uri(destination)
            
            if not dst_key:
                dst_key = src_key.split('/')[-1]
            
            client.copy_object(src_bucket, src_key, dst_bucket, dst_key)
            print_success(f"Copied to {build_s3_uri(dst_bucket, dst_key)}")
        
        elif is_s3_source:
            # Download from S3
            src_bucket, src_key = parse_s3_uri(source)
            
            # Handle destination
            if os.path.isdir(destination):
                local_path = os.path.join(destination, os.path.basename(src_key))
            else:
                local_path = destination
            
            # Get file size for progress
            obj_info = client.get_object_info(src_bucket, src_key)
            
            with create_progress_bar() as progress:
                task = progress.add_task(f"Downloading {os.path.basename(src_key)}", total=obj_info.size)
                callback = ProgressCallback(progress, task, obj_info.size)
                client.download_file(src_bucket, src_key, local_path, callback)
            
            print_success(f"Downloaded to {local_path}")
        
        elif is_s3_dest:
            # Upload to S3
            dst_bucket, dst_key = parse_s3_uri(destination)
            
            if recursive and os.path.isdir(source):
                # Upload directory
                from .utils import walk_directory
                
                files = list(walk_directory(source))
                
                with create_simple_progress() as progress:
                    task = progress.add_task("Uploading files...", total=len(files))
                    
                    for relative_path, size in files:
                        local_path = os.path.join(source, relative_path)
                        s3_key = os.path.join(dst_key, relative_path).replace('\\', '/')
                        
                        if s3_key.startswith('/'):
                            s3_key = s3_key[1:]
                        
                        client.upload_file(dst_bucket, local_path, s3_key)
                        progress.advance(task)
                
                print_success(f"Uploaded {len(files)} files to {build_s3_uri(dst_bucket, dst_key)}")
            else:
                # Upload single file
                if not os.path.exists(source):
                    raise click.ClickException(f"File not found: {source}")
                
                if not dst_key:
                    dst_key = os.path.basename(source)
                
                file_size = os.path.getsize(source)
                
                with create_progress_bar() as progress:
                    task = progress.add_task(f"Uploading {os.path.basename(source)}", total=file_size)
                    callback = ProgressCallback(progress, task, file_size)
                    client.upload_file(dst_bucket, source, dst_key, callback)
                
                print_success(f"Uploaded to {build_s3_uri(dst_bucket, dst_key)}")
        else:
            raise click.ClickException("Either source or destination must be an S3 path")
    
    except S3Error as e:
        raise click.ClickException(str(e))


@main.command('mv')
@click.argument('source')
@click.argument('destination')
@pass_context
def move_file(ctx: Context, source: str, destination: str) -> None:
    """
    Move/rename objects in S3.
    
    Examples:
    
        s3hero mv s3://bucket/old.txt s3://bucket/new.txt
        
        s3hero mv s3://bucket/file.txt s3://other-bucket/file.txt
    """
    client = ctx.get_client()
    
    src_bucket, src_key = parse_s3_uri(source)
    dst_bucket, dst_key = parse_s3_uri(destination)
    
    if not src_key:
        raise click.ClickException("Source must include an object key")
    
    if not dst_key:
        dst_key = src_key.split('/')[-1]
    
    try:
        client.move_object(src_bucket, src_key, dst_bucket, dst_key)
        print_success(f"Moved to {build_s3_uri(dst_bucket, dst_key)}")
    except S3Error as e:
        raise click.ClickException(str(e))


@main.command('rm')
@click.argument('path')
@click.option('--recursive', '-r', is_flag=True, help='Delete recursively')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@pass_context
def remove_object(ctx: Context, path: str, recursive: bool, yes: bool) -> None:
    """
    Delete objects from S3.
    
    Examples:
    
        s3hero rm s3://bucket/file.txt
        
        s3hero rm -r s3://bucket/folder/
    """
    client = ctx.get_client()
    bucket, key = parse_s3_uri(path)
    
    if not key and not recursive:
        raise click.ClickException("Specify an object key or use --recursive to delete all")
    
    try:
        if recursive:
            # Get objects to delete
            objects = list(client.list_objects_iter(bucket, key))
            
            if not objects:
                print_info("No objects found to delete")
                return
            
            if not yes:
                if not confirm_action(f"Delete {len(objects)} objects?"):
                    print_info("Cancelled")
                    return
            
            keys = [obj.key for obj in objects]
            
            with create_simple_progress() as progress:
                task = progress.add_task("Deleting objects...", total=len(keys))
                
                def callback(count: int) -> None:
                    progress.advance(task, count)
                
                deleted = client.delete_objects(bucket, keys, callback)
            
            print_success(f"Deleted {deleted} objects")
        else:
            if not client.object_exists(bucket, key):
                raise click.ClickException(f"Object not found: {path}")
            
            if not yes:
                if not confirm_action(f"Delete {path}?"):
                    print_info("Cancelled")
                    return
            
            client.delete_object(bucket, key)
            print_success(f"Deleted {path}")
    except S3Error as e:
        raise click.ClickException(str(e))


@main.command('sync')
@click.argument('source')
@click.argument('destination')
@click.option('--delete', is_flag=True, help='Delete files that exist in destination but not in source')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@pass_context
def sync_files(ctx: Context, source: str, destination: str, delete: bool, dry_run: bool) -> None:
    """
    Sync files between local and S3.
    
    Examples:
    
        s3hero sync ./local/ s3://bucket/prefix/
        
        s3hero sync s3://bucket/prefix/ ./local/
        
        s3hero sync --delete ./local/ s3://bucket/
    """
    client = ctx.get_client()
    
    is_s3_source = source.startswith('s3://')
    is_s3_dest = destination.startswith('s3://')
    
    if is_s3_source and is_s3_dest:
        raise click.ClickException("Cannot sync between two S3 locations")
    
    if not is_s3_source and not is_s3_dest:
        raise click.ClickException("Either source or destination must be an S3 path")
    
    try:
        if is_s3_dest:
            # Upload sync
            dst_bucket, dst_prefix = parse_s3_uri(destination)
            
            if dry_run:
                print_info(f"Would sync {source} to {destination}")
                return
            
            with create_simple_progress() as progress:
                task = progress.add_task("Syncing to S3...", total=None)
                
                def callback(key: str, size: int) -> None:
                    progress.update(task, description=f"Uploading {os.path.basename(key)}")
                
                uploaded, skipped, deleted_count = client.sync_to_s3(
                    source, dst_bucket, dst_prefix, delete=delete, callback=callback
                )
            
            print_stats({
                "Uploaded": uploaded,
                "Skipped": skipped,
                "Deleted": deleted_count
            }, title="Sync Complete")
        else:
            # Download sync
            src_bucket, src_prefix = parse_s3_uri(source)
            
            if dry_run:
                print_info(f"Would sync {source} to {destination}")
                return
            
            # Create destination directory
            os.makedirs(destination, exist_ok=True)
            
            with create_simple_progress() as progress:
                task = progress.add_task("Syncing from S3...", total=None)
                
                def callback(key: str, size: int) -> None:
                    progress.update(task, description=f"Downloading {os.path.basename(key)}")
                
                downloaded, skipped, deleted_count = client.sync_from_s3(
                    src_bucket, destination, src_prefix, delete=delete, callback=callback
                )
            
            print_stats({
                "Downloaded": downloaded,
                "Skipped": skipped,
                "Deleted": deleted_count
            }, title="Sync Complete")
    except S3Error as e:
        raise click.ClickException(str(e))


@main.command('presign')
@click.argument('path')
@click.option('--expires', '-e', type=int, default=3600, help='URL expiration time in seconds')
@pass_context
def presign_url(ctx: Context, path: str, expires: int) -> None:
    """
    Generate a presigned URL for an object.
    
    Example:
    
        s3hero presign s3://bucket/file.txt --expires 7200
    """
    client = ctx.get_client()
    bucket, key = parse_s3_uri(path)
    
    if not key:
        raise click.ClickException("Please specify an object key")
    
    try:
        url = client.generate_presigned_url(bucket, key, expires)
        console.print(f"\n[bold cyan]Presigned URL:[/bold cyan]\n{url}")
        print_info(f"Valid for {expires} seconds")
    except S3Error as e:
        raise click.ClickException(str(e))


@main.command('cat')
@click.argument('path')
@pass_context
def cat_object(ctx: Context, path: str) -> None:
    """
    Display object contents.
    
    Example:
    
        s3hero cat s3://bucket/file.txt
    """
    import tempfile
    
    client = ctx.get_client()
    bucket, key = parse_s3_uri(path)
    
    if not key:
        raise click.ClickException("Please specify an object key")
    
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            client.download_file(bucket, key, tmp.name)
            tmp.close()
            
            with open(tmp.name, 'r') as f:
                content = f.read()
            
            os.unlink(tmp.name)
            console.print(content)
    except S3Error as e:
        raise click.ClickException(str(e))
    except UnicodeDecodeError:
        raise click.ClickException("Cannot display binary file content")


@main.command('info')
@click.argument('path')
@pass_context
def object_info(ctx: Context, path: str) -> None:
    """
    Display object metadata.
    
    Example:
    
        s3hero info s3://bucket/file.txt
    """
    from rich.panel import Panel
    
    client = ctx.get_client()
    bucket, key = parse_s3_uri(path)
    
    if not key:
        raise click.ClickException("Please specify an object key")
    
    try:
        obj = client.get_object_info(bucket, key)
        
        content = f"""[bold]Key:[/bold] {obj.key}
[bold]Size:[/bold] {format_size(obj.size)} ({obj.size:,} bytes)
[bold]Last Modified:[/bold] {obj.last_modified}
[bold]ETag:[/bold] {obj.etag}
[bold]Storage Class:[/bold] {obj.storage_class or 'STANDARD'}"""
        
        console.print(Panel(content, title="Object Info", border_style="cyan"))
    except S3Error as e:
        raise click.ClickException(str(e))


if __name__ == '__main__':
    main()
