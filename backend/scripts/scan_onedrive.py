"""
Dual OneDrive Account Scanner & Connection Helper

Connects to both OneDrive accounts and scans for procurement documents
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any

async def scan_onedrive_accounts() -> Dict[str, Any]:
    """Scan both linked OneDrive accounts for procurement documents"""
    
    accounts = {
        "Primary": "C:\\Users\\1R6\\OneDrive",
        "Advanced Creativity Company": "C:\\Users\\1R6\\OneDrive - Advanced Creativity Company"
    }
    
    results = {}
    
    for account_name, account_path in accounts.items():
        path = Path(account_path)
        
        if not path.exists():
            results[account_name] = {
                "status": "not_found",
                "path": account_path
            }
            continue
        
        # Scan for document files
        doc_extensions = {'.pdf', '.xlsx', '.xls', '.csv', '.docx', '.doc', '.jpg', '.jpeg', '.png', '.json'}
        
        documents = []
        for ext in doc_extensions:
            documents.extend(path.glob(f'**/*{ext}'))
        
        # Categorize by type
        document_stats = {
            'total': len(documents),
            'by_type': {},
            'by_folder': {}
        }
        
        for doc in documents:
            ext = doc.suffix.lower()
            if ext not in document_stats['by_type']:
                document_stats['by_type'][ext] = 0
            document_stats['by_type'][ext] += 1
            
            # Track by parent folder
            folder = doc.parent.name
            if folder not in document_stats['by_folder']:
                document_stats['by_folder'][folder] = 0
            document_stats['by_folder'][folder] += 1
        
        results[account_name] = {
            "status": "connected",
            "path": account_path,
            "statistics": document_stats,
            "sample_documents": [str(d.relative_to(path)) for d in list(documents)[:5]]
        }
    
    return results


async def main():
    print("\n🔍 SCANNING YOUR ONEDRIVE ACCOUNTS...\n")
    results = await scan_onedrive_accounts()
    
    for account_name, data in results.items():
        print(f"{'='*80}")
        print(f"📁 {account_name}")
        print(f"{'='*80}")
        print(f"Path: {data['path']}")
        
        if data['status'] == 'not_found':
            print("❌ Account not found or inaccessible\n")
            continue
        
        if data['status'] == 'connected':
            stats = data.get('statistics', {})
            print(f"✓ Connected - {stats.get('total', 0)} documents found\n")
            
            print("📊 DOCUMENTS BY TYPE:")
            for ext, count in stats.get('by_type', {}).items():
                print(f"  {ext:10} : {count:4} files")
            
            print("\n📂 TOP FOLDERS WITH DOCUMENTS:")
            folders = sorted(stats.get('by_folder', {}).items(), key=lambda x: x[1], reverse=True)[:5]
            for folder, count in folders:
                print(f"  {folder:30} : {count:4} files")
            
            if data.get('sample_documents'):
                print("\n📄 SAMPLE DOCUMENTS:")
                for doc in data['sample_documents'][:3]:
                    print(f"  • {doc}")
            
            print()


if __name__ == "__main__":
    asyncio.run(main())
