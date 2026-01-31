"""Command-line interface for extracting AUTOSAR models from PDF files."""

import argparse
import logging
import sys
from pathlib import Path

from autosar_pdf2txt import PdfParser, MarkdownWriter
from autosar_pdf2txt.models import AutosarClass, AutosarEnumeration, AutosarPrimitive


def main() -> int:
    """Main entry point for the CLI.

    Requirements:
        SWR_CLI_00001: CLI Entry Point
        SWR_CLI_00010: CLI Class File Output
        SWR_CLI_00011: CLI Class Files Flag
        SWR_CLI_00012: CLI Class Hierarchy Flag
        SWR_CLI_00014: CLI Logger File Specification

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Extract AUTOSAR package and class hierarchies from PDF files."
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
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--include-class-details",
        action="store_true",
        help="Create separate markdown files for each class (requires -o/--output)",
    )
    parser.add_argument(
        "--include-class-hierarchy",
        action="store_true",
        help="Generate class inheritance hierarchy and write to a separate file (requires -o/--output)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output mode for detailed debug information",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        help="Write log messages to the specified file (in addition to stderr)",
    )

    args = parser.parse_args()

    # Configure logging based on verbose flag
    # SWR_CLI_00005: CLI Verbose Mode
    # SWR_CLI_00008: CLI Logging
    # SWR_CLI_00014: CLI Logger File Specification
    log_level = logging.DEBUG if args.verbose else logging.INFO
    log_format = "%(levelname)s: %(message)s"
    log_file_format = "%(asctime)s.%(msecs)03d: %(levelname)s: %(message)s"
    log_date_format = "%Y-%m-%d %H:%M:%S"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all levels

    # Console handler (stderr)
    # In verbose mode: show DEBUG and above
    # In normal mode: show INFO and above (WARNING goes to file only)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level if args.verbose else logging.INFO)
    # Filter out WARNING level messages from console (they go to file instead)
    if not args.verbose:
        console_handler.addFilter(lambda record: record.levelno != logging.WARNING)
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)

    # WARNING file handler - always log WARNING messages to a file
    # In normal mode, this keeps console output clean while preserving warnings for debugging
    # In verbose mode, warnings are shown on console AND logged to file
    if not args.verbose:
        warning_log_file = Path("autosar_pdf_warnings.log")
        try:
            warning_handler = logging.FileHandler(warning_log_file, mode='w', encoding='utf-8')
            warning_handler.setLevel(logging.WARNING)
            warning_handler.setFormatter(logging.Formatter(log_file_format, datefmt=log_date_format))
            root_logger.addHandler(warning_handler)
        except Exception as e:
            # If we can't create the warning log, just log to console
            logging.error(f"Failed to create warning log file '{warning_log_file}': {e}")

    # File handler (if --log-file is specified)
    # SWR_CLI_00014: CLI Logger File Specification
    if args.log_file:
        try:
            log_file_path = Path(args.log_file)
            # Create parent directories if they don't exist
            log_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Create file handler with timestamps
            file_handler = logging.FileHandler(log_file_path, mode='w', encoding='utf-8')
            file_handler.setLevel(log_level)
            file_handler.setFormatter(logging.Formatter(log_file_format, datefmt=log_date_format))
            root_logger.addHandler(file_handler)
        except Exception as e:
            logging.error(f"Failed to create log file '{args.log_file}': {e}")
            # Continue with console-only logging

    # Suppress pdfminer warnings about invalid color values in PDF files
    # These warnings don't affect text extraction functionality
    logging.getLogger("pdfminer").setLevel(logging.ERROR)

    # Validate and collect input paths (files and directories)
    # SWR_CLI_00006: CLI Input Validation
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
            # SWR_CLI_00003: CLI Directory Input Support
            pdf_files_in_dir = sorted(path.glob("*.pdf"))
            if not pdf_files_in_dir:
                logging.warning(f"No PDF files found in directory: {input_path}")
                continue
            pdf_paths.extend(pdf_files_in_dir)
            logging.info(f"📂 Found {len(pdf_files_in_dir)} PDF file(s) in directory: {input_path}")
        else:
            logging.error(f"Not a file or directory: {input_path}")
            return 1

    if not pdf_paths:
        logging.error("No PDF files to process")
        return 1

    try:
        # Parse all PDFs using parse_pdfs() to ensure parent/child relationships
        # are resolved after all models are loaded (not per-PDF)
        pdf_parser = PdfParser()

        # SWR_CLI_00007: CLI Progress Feedback
        logging.info(f"🔄 Parsing {len(pdf_paths)} PDF file(s)...")

        pdf_path_strings = [str(pdf_path) for pdf_path in pdf_paths]

        # Parse all PDFs at once - parent/children resolution happens on complete model
        doc = pdf_parser.parse_pdfs(pdf_path_strings)

        # Calculate statistics
        total_classes = 0
        total_enums = 0
        total_primitives = 0
        total_types = 0
        for pkg in doc.packages:
            for typ in pkg.types:
                if isinstance(typ, AutosarClass):
                    total_classes += 1
                elif isinstance(typ, AutosarEnumeration):
                    total_enums += 1
                elif isinstance(typ, AutosarPrimitive):
                    total_primitives += 1
                total_types += 1

        logging.info(f"📦 Total: {len(doc.packages)} top-level packages")
        logging.info(f"🏛️  Total: {len(doc.root_classes)} root classes")
        logging.info(f"📊 Extracted: {total_classes} classes, {total_enums} enumerations, {total_primitives} primitives ({total_types} total types)")

        if args.verbose:
            for pkg in doc.packages:
                logging.debug(f"  - {pkg.name}")

        # Write to markdown
        writer = MarkdownWriter()
        markdown = writer.write_packages(doc.packages)

        # SWR_CLI_00012: CLI Class Hierarchy Flag
        # Generate class hierarchy if requested
        class_hierarchy = None
        if args.include_class_hierarchy:
            logging.info("📊 Generating class hierarchy...")
            # Collect all classes from packages for building hierarchy
            all_classes = []
            for pkg in doc.packages:
                classes_from_pkg = writer._collect_classes_from_package(pkg)
                all_classes.extend(classes_from_pkg)

            logging.info(f"📊 Collected {len(all_classes)} classes from {len(doc.packages)} packages")
            logging.debug(f"📊 Root classes for hierarchy: {len(doc.root_classes)}")

            class_hierarchy = writer.write_class_hierarchy(doc.root_classes, all_classes)
            if class_hierarchy:
                logging.info(f"✅ Generated class hierarchy for {len(doc.root_classes)} root classes")

        # SWR_CLI_00004: CLI Output File Option
        if args.output:
            output_path = Path(args.output)
            # Create parent directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown, encoding="utf-8")
            logging.info(f"✍️  Output written to: {args.output}")

            # SWR_CLI_00012: CLI Class Hierarchy Flag
            # Write class hierarchy to separate file if flag is enabled
            if class_hierarchy:
                # Generate hierarchy file name: <package_name>_hierarchy
                # Replace hyphens with underscores in the package name
                hierarchy_path = output_path.with_stem(f"{output_path.stem.replace('-', '_')}_hierarchy")
                hierarchy_path.write_text(class_hierarchy, encoding="utf-8")
                logging.info(f"📊 Class hierarchy written to: {hierarchy_path}")

            # SWR_CLI_00010: CLI Class File Output
            # SWR_CLI_00011: CLI Class Files Flag
            # Write each class to separate files if flag is enabled
            if args.include_class_details:
                writer.write_packages_to_files(doc.packages, output_path=output_path)
                logging.info(f"📁 Class files written to directory: {output_path.parent}")
        else:
            print(markdown, end="")

        # SWR_CLI_00009: CLI Error Handling
        logging.info("✅ All PDF files processed successfully!")

        return 0

    except Exception as e:
        # SWR_CLI_00009: CLI Error Handling
        logging.error(f"{e}")
        if args.verbose:
            logging.exception("Detailed error traceback:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
