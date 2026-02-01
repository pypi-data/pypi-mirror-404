import os
from pathlib import Path
from docling.document_converter import DocumentConverter
import logging 
logger = logging.getLogger(__name__)

def convert_pdfs_to_md(input_folder: str = "src/data/data_source", output_folder: str = "src/data/markdown_data_sources"):
    """
    Uses Docling to convert PDF files ONLY if corresponding MD files don't exist.
    SKIPS ENTIRE PROCESS if all PDFs already have MD counterparts.
    """
    logger.info("inside the convert pdfs to markdown ")
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    
    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get all PDF files from input folder
    pdf_files = list(input_path.glob("*.pdf"))
    
    if not pdf_files:
        print("ℹ️ No PDF files found in input folder. Nothing to do.")
        return
    
    # Get existing MD files (stems only)
    existing_md_stems = {f.stem for f in output_path.glob("*.md")}
    pdf_stems = {f.stem for f in pdf_files}
    
    # CRITICAL CHECK: Skip ENTIRE process if all PDFs have MD files
    missing_md_files = pdf_stems - existing_md_stems
    if not missing_md_files:
        print(f"✅ All {len(pdf_stems)} PDFs already have corresponding MD files.")
        print("✨ No conversion needed - completely skipping!")
        return
    
    # Only proceed if some files are missing
    print(f"🚀 Found {len(pdf_files)} PDFs, {len(missing_md_files)} need conversion...")
    
    # Initialize Docling only when needed
    converter = DocumentConverter()
    
    conversion_count = 0
    for pdf_file in pdf_files:
        output_file = output_path / f"{pdf_file.stem}.md"
        
        # Skip if MD file already exists (individual file check)
        if output_file.exists():
            print(f"⏭️ Skipping (exists): {pdf_file.name}")
            continue
        
        try:
            print(f"🔄 Converting: {pdf_file.name}...")
            
            # Convert PDF to Docling document
            result = converter.convert(pdf_file)
            
            # Export to Markdown
            md_output = result.document.export_to_markdown()
            
            # Save MD file
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(md_output)
                
            print(f"✅ Converted: {output_file.name}")
            conversion_count += 1
            
        except Exception as e:
            print(f"❌ Error converting {pdf_file.name}: {e}")
    
    print(f"\n✨ Completed! Converted {conversion_count} new files.")
    # print(f"📁 Total MD files now: {len(output_path.glob('*.md'))}")
    return {"sucess":True}




