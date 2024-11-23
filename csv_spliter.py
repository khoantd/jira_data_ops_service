import os
import csv
import logging
from typing import List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

def split_csv_file(input_file: str, max_size_mb: float = 100.0, output_dir: str = None) -> List[str]:
    """
    Split a large CSV file into multiple smaller files based on size limit.
    
    Args:
        input_file: Path to the input CSV file
        max_size_mb: Maximum size in megabytes for each output file (default 100MB)
        output_dir: Directory to save output files (default is same as input file)
    
    Returns:
        List of paths to the generated output files
    """
    try:
        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        # Set output directory
        output_path = Path(output_dir) if output_dir else input_path.parent
        output_path.mkdir(parents=True, exist_ok=True)

        # Calculate max bytes per file
        max_bytes = max_size_mb * 1024 * 1024
        output_files = []
        current_size = 0
        file_counter = 1

        with open(input_file, 'r', encoding='utf-8') as csvfile:
            # Read header
            reader = csv.reader(csvfile)
            header = next(reader)
            header_str = ','.join(header) + '\n'
            
            # Initialize first output file
            current_output = output_path / f"{input_path.stem}_part{file_counter}{input_path.suffix}"
            current_file = open(current_output, 'w', encoding='utf-8')
            current_file.write(header_str)
            current_size = len(header_str.encode('utf-8'))
            output_files.append(str(current_output))

            # Process rows
            for row in reader:
                row_str = ','.join(row) + '\n'
                row_size = len(row_str.encode('utf-8'))

                # Check if adding this row would exceed size limit
                if current_size + row_size > max_bytes:
                    current_file.close()
                    file_counter += 1
                    
                    # Create new output file
                    current_output = output_path / f"{input_path.stem}_part{file_counter}{input_path.suffix}"
                    current_file = open(current_output, 'w', encoding='utf-8')
                    current_file.write(header_str)
                    current_size = len(header_str.encode('utf-8'))
                    output_files.append(str(current_output))

                # Write row to current file
                current_file.write(row_str)
                current_size += row_size

            current_file.close()

        logger.info(f"Split CSV file into {len(output_files)} parts")
        return output_files

    except Exception as e:
        logger.error(f"Error splitting CSV file: {str(e)}")
        raise
