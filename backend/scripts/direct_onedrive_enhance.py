"""
Direct OneDrive Enhancement - No API Required

Directly loads your OneDrive documents and exports enhancement data
Auto-discovers all OneDrive accounts on the system
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.document_ingestion import document_ingestion


def discover_onedrive_accounts() -> Dict[str, str]:
    """Auto-discover all OneDrive accounts on the system"""
    accounts = {}
    user_path = Path("C:\\Users\\1R6")
    
    if not user_path.exists():
        return accounts
    
    # Look for all OneDrive directories
    for folder in user_path.iterdir():
        if folder.is_dir() and "OneDrive" in folder.name:
            # Clean up the account name for display
            if folder.name == "OneDrive":
                display_name = "Primary"
            else:
                # Remove "OneDrive - " prefix
                display_name = folder.name.replace("OneDrive - ", "")
            
            accounts[display_name] = str(folder)
    
    return accounts


async def enhance_from_onedrive_accounts():
    """Process all discovered OneDrive accounts for ML/AI enhancement"""
    
    # Auto-discover accounts instead of hardcoding
    accounts = discover_onedrive_accounts()
    
    if not accounts:
        print("❌ No OneDrive accounts found on the system")
        return
    
    # Display discovered accounts
    print(f"\n{'='*80}")
    print(f"[*] DISCOVERED {len(accounts)} ONEDRIVE ACCOUNT(S)")
    print(f"{'='*80}")
    for name, path in accounts.items():
        print(f"  • {name}: {path}")
    print()
    
    all_stats = {}
    
    for account_name, storage_path in accounts.items():
        print(f"\n{'='*80}")
        print(f"[>] Processing {account_name} Account")
        print(f"{'='*80}")
        print(f"Path: {storage_path}\n")
        
        # Connect to storage
        print("[*] Connecting to storage...")
        success = await document_ingestion.connect_to_storage(
            storage_path=storage_path,
            storage_type="onedrive"
        )
        
        if not success:
            print(f"[!] Failed to connect to {account_name}")
            continue
        
        print("[+] Connected successfully\n")
        
        # Scan documents
        print("[*] Scanning for documents (this may take a moment)...")
        count = await document_ingestion.scan_documents(
            file_extensions=[
                '.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp',
                '.xlsx', '.xls', '.csv', '.json', '.docx', '.doc'
            ],
            recursive=True
        )
        
        print(f"[+] Loaded {count} documents\n")
        
        # Get statistics
        stats = document_ingestion.get_statistics()
        all_stats[account_name] = stats
        
        print("[INFO] DOCUMENT STATISTICS:")
        print(f"   Total: {stats.get('total_documents', 0)} documents")
        print(f"   With Supplier Info: {stats.get('with_supplier_names', 0)} documents")
        print(f"   With Amounts: {stats.get('with_amounts', 0)} documents")
        print(f"   Total Value: ${stats.get('total_amount_usd', 0):,.2f}")
        print(f"   Total Size: {stats.get('total_size_mb', 0):.1f} MB\n")
        
        print("[INFO] DOCUMENTS BY TYPE:")
        for file_type, count in stats.get('by_file_type', {}).items():
            print(f"   {file_type:10} : {count:4} files")
        
        print("\n[INFO] DOCUMENTS BY CATEGORY:")
        for doc_type, count in stats.get('by_type', {}).items():
            print(f"   {doc_type:15} : {count:4} files")
    
    # Export combined data
    print(f"\n{'='*80}")
    print("[*] EXPORTING DATA FOR ML/AI ENHANCEMENT")
    print(f"{'='*80}\n")
    
    output_base = Path("C:\\Users\\1R6\\OneDrive\\Project Catalyst\\KraftdIntel\\backend\\output\\onedrive_data")
    output_base.mkdir(parents=True, exist_ok=True)
    
    # The documents are already loaded, now export them
    print("[*] Exporting training data for ML models...")
    ml_export_success = document_ingestion.export_for_ml_training(str(output_base))
    
    if ml_export_success:
        print("[+] Training data exported: training_data.jsonl")
    else:
        print("[!] Failed to export training data")
    
    print("\n[*] Exporting context examples for gpt-4o...")
    ai_export_success = document_ingestion.export_for_ai_context(str(output_base), sample_size=20)
    
    if ai_export_success:
        print("[+] AI context exported: ai_context_examples.json")
    else:
        print("[!] Failed to export AI context")
    
    # Summary
    print(f"\n{'='*80}")
    print("[SUCCESS] ONEDRIVE ENHANCEMENT COMPLETE")
    print(f"{'='*80}\n")
    
    total_docs = sum(s.get('total_documents', 0) for s in all_stats.values())
    total_value = sum(s.get('total_amount_usd', 0) for s in all_stats.values())
    total_size = sum(s.get('total_size_mb', 0) for s in all_stats.values())
    
    print(f"[INFO] COMBINED STATISTICS:")
    print(f"   Total Documents: {total_docs:,}")
    print(f"   Total Procurement Value: ${total_value:,.2f}")
    print(f"   Total Data Size: {total_size:,.1f} MB")
    
    print(f"\n[INFO] EXPORTED LOCATION:")
    print(f"   {output_base}/")
    print(f"   - training_data.jsonl (for ML model retraining)")
    print(f"   - ai_context_examples.json (for gpt-4o enhancement)")
    
    print(f"\n[INFO] NEXT STEPS:")
    print(f"""
   1. Review the exported data files
   2. Use the data to retrain ML models with your procurement patterns
   3. Enhance gpt-4o with your document examples
   4. Monitor improvement metrics

   SYSTEM NOW CUSTOMIZED WITH YOUR ORGANIZATION'S PROCUREMENT DATA!
    """)
    
    # Save a summary report
    import time
    summary = {
        "timestamp": str(time.strftime("%Y-%m-%d %H:%M:%S")),
        "accounts_processed": list(accounts.keys()),
        "total_documents": total_docs,
        "total_procurement_value_usd": total_value,
        "total_data_size_mb": total_size,
        "statistics_by_account": all_stats,
        "export_location": str(output_base),
        "files_exported": [
            "training_data.jsonl",
            "ai_context_examples.json"
        ]
    }
    
    summary_file = output_base / "enhancement_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"[+] Summary saved to: {summary_file}")


if __name__ == "__main__":
    asyncio.run(enhance_from_onedrive_accounts())
