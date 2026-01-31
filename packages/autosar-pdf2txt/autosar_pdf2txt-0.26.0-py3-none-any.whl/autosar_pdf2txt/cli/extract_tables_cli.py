"""Command-line interface for extracting tables from PDF files."""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

import pdfplumber


def is_autosar_table(table: List[List[Optional[str]]]) -> bool:
    """Check if a table is AUTOSAR-related by verifying it contains Class and/or Package fields.

    Args:
        table: The table data as a list of rows, where each row is a list of cell values

    Returns:
        True if the table is AUTOSAR-related, False otherwise
    """
    if not table or len(table) == 0:
        return False

    # Get the first row (header) and normalize it
    header = table[0]
    if not header:
        return False

    # Normalize header values: convert to lowercase, strip whitespace, handle None
    normalized_header = []
    for cell in header:
        if cell is None:
            normalized_header.append("")
        else:
            normalized_header.append(str(cell).strip().lower())

    # Check if the header contains both "class" and "package" fields
    has_class = False
    has_package = False

    for cell in normalized_header:
        if "class" in cell:
            has_class = True
        if "package" in cell:
            has_package = True

    is_autosar = has_class and has_package

    if is_autosar:
        logging.debug(f"  AUTOSAR table detected - Header: {header}")

    return is_autosar


def extract_tables_from_pdf(pdf_path: Path, output_dir: Path) -> List[Path]:
    """Extract AUTOSAR-related tables from a PDF file.

    Only extracts tables that contain both Class and Package fields in their header.

    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save extracted table images

    Returns:
        List of paths to the extracted table images
    """
    table_image_paths = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # Extract tables from the current page
                tables = page.extract_tables()

                if tables:
                    logging.debug(f"Found {len(tables)} table(s) on page {page_num}")

                    for table_num, table in enumerate(tables, start=1):
                        # Check if this is an AUTOSAR-related table
                        if not is_autosar_table(table):
                            logging.debug(f"  Skipping table {table_num} on page {page_num} - not AUTOSAR-related")
                            continue

                        # Create an image from the page
                        img = page.to_image()

                        # Crop the image to the table area
                        # First, find the bounding box of the table
                        tables_found = page.find_tables()
                        if tables_found and table_num - 1 < len(tables_found):
                            bbox = tables_found[table_num - 1].bbox
                            # Use PIL's crop method on the underlying PIL image
                            img.original = img.original.crop(bbox)

                        # Save the image
                        img_path = output_dir / f"table_page{page_num}_table{table_num}.png"
                        img.save(img_path)

                        table_image_paths.append(img_path)
                        logging.debug(f"  Saved AUTOSAR table {table_num} from page {page_num} to {img_path}")

        return table_image_paths

    except Exception as e:
        logging.error(f"Error processing PDF {pdf_path}: {e}")
        return []


def main() -> int:
    """Main entry point for the CLI.

    Requirements:
        SWR_CLI_00002: CLI File Input Support
        SWR_CLI_00013: CLI Table Extraction

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Extract AUTOSAR-related tables (containing Class and Package fields) from PDF files and save them as images."
    )
    parser.add_argument(
        "pdf_files",
        type=str,
        nargs="+",
        help="Path(s) to PDF file(s) or director(y/ies) containing PDFs to parse",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="Output directory path for extracted table images",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output mode for detailed debug information",
    )

    args = parser.parse_args()

    # Configure logging based on verbose flag
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
    )

    # Suppress pdfminer warnings about invalid color values in PDF files
    logging.getLogger("pdfminer").setLevel(logging.ERROR)

    # Validate output directory
    output_dir = Path(args.output)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logging.error(f"Failed to create output directory {args.output}: {e}")
        return 1

    # Validate and collect input paths (files and directories)
    pdf_paths = []
    for input_path in args.pdf_files:
        path = Path(input_path)
        if not path.exists():
            logging.error(f"Path not found: {input_path}")
            return 1

        if path.is_file():
            # It's a file, add directly
            if path.suffix.lower() != ".pdf":
                logging.warning(f"Skipping non-PDF file: {input_path}")
                continue
            pdf_paths.append(path)
        elif path.is_dir():
            # It's a directory, find all PDF files
            pdf_files_in_dir = sorted(path.glob("*.pdf"))
            if not pdf_files_in_dir:
                logging.warning(f"No PDF files found in directory: {input_path}")
                continue
            pdf_paths.extend(pdf_files_in_dir)
            logging.info(f"Found {len(pdf_files_in_dir)} PDF file(s) in directory: {input_path}")
        else:
            logging.error(f"Not a file or directory: {input_path}")
            return 1

    if not pdf_paths:
        logging.error("No PDF files to process")
        return 1

    try:
        logging.info(f"Extracting tables from {len(pdf_paths)} PDF file(s)...")
        logging.info(f"Output directory: {output_dir}")

        all_table_paths = []
        for pdf_path in pdf_paths:
            logging.info(f"Processing: {pdf_path}")
            table_paths = extract_tables_from_pdf(pdf_path, output_dir)
            all_table_paths.extend(table_paths)
            logging.info(f"  Extracted {len(table_paths)} table(s) from {pdf_path.name}")

        logging.info("\nExtraction complete!")
        logging.info(f"Total tables extracted: {len(all_table_paths)}")
        logging.info(f"Images saved to: {output_dir}")

        return 0

    except Exception as e:
        logging.error(f"{e}")
        if args.verbose:
            logging.exception("Detailed error traceback:")
        return 1


if __name__ == "__main__":
    sys.exit(main())