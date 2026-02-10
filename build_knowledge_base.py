#!/usr/bin/env python3
"""
ChronoForge RAG - Knowledge Base Builder

Build and populate the knowledge base from data files.

Usage:
    python build_knowledge_base.py <output_path> <data_file1> [data_file2] ...

Example:
    python build_knowledge_base.py ./kb sales_2023.csv sales_2024.csv
"""

import sys
import os
import argparse

from chronoforge_rag import EmbeddingConfig, VectorStoreConfig
from knowledge_base import create_knowledge_base


def main():
    parser = argparse.ArgumentParser(
        description="Build ChronoForge RAG Knowledge Base",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s ./kb sales_data.csv
    %(prog)s ./kb data1.csv data2.json --embedding-model all-MiniLM-L6-v2
    %(prog)s ./kb data.csv --use-api --api-provider openai
        """
    )
    
    parser.add_argument("output_path", help="Output directory for knowledge base")
    parser.add_argument("data_files", nargs="+", help="Input data files (.csv or .json)")
    
    parser.add_argument("--embedding-model", default="all-MiniLM-L6-v2",
                       help="Embedding model name (default: all-MiniLM-L6-v2)")
    parser.add_argument("--use-api", action="store_true",
                       help="Use API for embeddings instead of local model")
    parser.add_argument("--api-provider", default="openai", choices=["openai", "gemini"],
                       help="API provider for embeddings (default: openai)")
    parser.add_argument("--dimension", type=int, default=384,
                       help="Embedding dimension (default: 384)")
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("ChronoForge RAG - Knowledge Base Builder")
    print("=" * 50)
    print()
    
    # Configure embedding
    embed_config = EmbeddingConfig(
        model_name=args.embedding_model,
        dimension=args.dimension,
        use_api=args.use_api,
        api_provider=args.api_provider
    )
    
    # Configure vector store
    vs_config = VectorStoreConfig(
        dimension=args.dimension,
        persist_directory=os.path.join(args.output_path, "vectors"),
        collection_name="sales_scenarios"
    )
    
    try:
        # Create knowledge base
        print(f"Embedding Model: {embed_config.model_name}")
        print(f"Use API: {embed_config.use_api}")
        if embed_config.use_api:
            print(f"API Provider: {embed_config.api_provider}")
        print()
        
        kb = create_knowledge_base(embed_config, vs_config)
        print("✓ Knowledge base initialized\n")
        
        # Process each input file
        total_imported = 0
        
        for file_path in args.data_files:
            if not os.path.exists(file_path):
                print(f"⚠ Warning: File not found: {file_path}")
                continue
            
            print(f"Processing: {file_path}")
            
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == ".csv":
                count = kb.import_from_csv(file_path)
            elif ext == ".json":
                count = kb.import_from_json(file_path)
            else:
                print(f"  ⚠ Unsupported format: {ext}")
                continue
            
            print(f"  ✓ Imported {count} scenarios")
            total_imported += count
        
        if total_imported == 0:
            print("\n No scenarios imported. Aborting.")
            return 1
        
        # Print statistics
        stats = kb.get_statistics()
        print()
        print("-" * 40)
        print("Knowledge Base Statistics")
        print("-" * 40)
        print(f"Total Scenarios:   {stats.total_scenarios}")
        print(f"Unique Regions:    {stats.unique_regions}")
        print(f"Unique Categories: {stats.unique_categories}")
        print(f"Sales Range:       ${stats.min_sales_value:,.2f} - ${stats.max_sales_value:,.2f}")
        print(f"Average Sales:     ${stats.avg_sales_value:,.2f}")
        print(f"Date Range:        {stats.earliest_date} to {stats.latest_date}")
        print()
        
        # Save
        print(f"Saving to: {args.output_path}")
        kb.save(args.output_path)
        print("✓ Knowledge base saved successfully!")
        
        return 0
        
    except Exception as e:
        print(f"\n Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
