#!/usr/bin/env python3
"""
Clean Up CloudBrain Server

This script removes unnecessary files from the server folder:
- Corrupted database files
- Historical backup databases (migration complete)
- Temporary files

Usage:
    python clean_server.py

WARNING: This will permanently delete files!
"""

import sys
from pathlib import Path


def print_banner():
    """Print cleanup banner."""
    print("\n" + "=" * 70)
    print("  CloudBrain Server Cleanup")
    print("=" * 70)
    print()


def get_server_dir():
    """Get server directory."""
    return Path(__file__).parent


def get_files_to_remove():
    """Get list of files to remove."""
    server_dir = get_server_dir()
    
    files_to_remove = [
        {
            'path': server_dir / "ai_db" / "cloudbrain_corrupted.db",
            'reason': 'Corrupted database file',
            'size_kb': lambda p: p.stat().st_size / 1024 if p.exists() else 0
        },
        {
            'path': server_dir / "ai_db" / "backup" / "ai_memory.db",
            'reason': 'Historical backup (migration complete)',
            'size_kb': lambda p: p.stat().st_size / 1024 if p.exists() else 0
        },
        {
            'path': server_dir / "ai_db" / "backup" / "cloudbrainprivate.db",
            'reason': 'Historical backup (empty)',
            'size_kb': lambda p: p.stat().st_size / 1024 if p.exists() else 0
        },
    ]
    
    return files_to_remove


def print_files_to_remove(files):
    """Print files that will be removed."""
    print("📋 Files to remove:")
    print()
    
    total_size = 0
    for file_info in files:
        path = file_info['path']
        reason = file_info['reason']
        size_kb = file_info['size_kb'](path)
        
        if path.exists():
            print(f"  📄 {path.relative_to(get_server_dir())}")
            print(f"     Reason: {reason}")
            print(f"     Size: {size_kb:.2f} KB")
            print()
            total_size += size_kb
        else:
            print(f"  ⚠️  {path.relative_to(get_server_dir())} (not found)")
            print()
    
    print(f"📊 Total size to remove: {total_size:.2f} KB")
    print()


def confirm_removal():
    """Ask user to confirm removal."""
    print("⚠️  WARNING: This will permanently delete these files!")
    print()
    response = input("Do you want to proceed? (yes/no): ")
    
    return response.lower() in ['yes', 'y']


def remove_files(files):
    """Remove files."""
    print("🗑️  Removing files...")
    print()
    
    removed_count = 0
    total_size = 0
    
    for file_info in files:
        path = file_info['path']
        
        if path.exists():
            size_kb = path.stat().st_size / 1024
            path.unlink()
            print(f"  ✅ Removed: {path.relative_to(get_server_dir())} ({size_kb:.2f} KB)")
            removed_count += 1
            total_size += size_kb
        else:
            print(f"  ⚠️  Skipped: {path.relative_to(get_server_dir())} (not found)")
    
    print()
    print(f"✅ Removed {removed_count} file(s)")
    print(f"📊 Total freed space: {total_size:.2f} KB")
    print()
    
    return removed_count > 0


def print_summary():
    """Print cleanup summary."""
    print("=" * 70)
    print("  Cleanup Summary")
    print("=" * 70)
    print()
    print("✅ Server cleanup complete!")
    print()
    print("📁 Remaining files:")
    print("  - cloudbrain.db (main database)")
    print("  - backup/README.md (historical reference)")
    print()
    print("🚀 Next steps:")
    print("  1. Initialize database: python init_database.py")
    print("  2. Start server: python start_server.py")
    print("  3. Test server: python ../test_server.py")
    print()


def main():
    """Main entry point."""
    print_banner()
    
    files_to_remove = get_files_to_remove()
    
    if not files_to_remove:
        print("✅ No files to remove!")
        return 0
    
    print_files_to_remove(files_to_remove)
    
    if not confirm_removal():
        print("❌ Cleanup cancelled")
        return 1
    
    if not remove_files(files_to_remove):
        print("❌ No files were removed")
        return 1
    
    print_summary()
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Cleanup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Cleanup error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
