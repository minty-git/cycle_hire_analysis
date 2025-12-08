import zipfile
import os
from pathlib import Path

def extract_zip_files_and_consolidate_csvs(target_directory):
    """
    Recursively finds and extracts all ZIP files within the target directory 
    and its subdirectories. Then, it moves all found CSV files to the top level 
    of the target directory.
    
    Args:
        target_directory (str): The path to the main directory.
    """
    base_path = Path(target_directory).resolve()
    
    if not base_path.is_dir():
        print(f"ERROR: Directory not found at {base_path}")
        return

    print(f"--- Starting Recursive ZIP Extraction in: {base_path} ---")
    
    zip_files_found = 0
    csv_files_moved = 0
    
    # 1. Recursive ZIP Extraction
    # os.walk traverses the directory tree starting at base_path
    for root, dirs, files in os.walk(base_path, topdown=False):
        current_dir = Path(root)
        
        for file_name in files:
            if file_name.lower().endswith('.zip'):
                zip_path = current_dir / file_name
                zip_files_found += 1
                
                # Determine the name of the new extraction directory
                # We extract in place (current_dir) but create a subfolder based on the ZIP name
                extract_folder_name = zip_path.stem 
                extract_path = current_dir / extract_folder_name
                
                print(f"\nProcessing ZIP: {zip_path.relative_to(base_path)}")
                
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        extract_path.mkdir(parents=True, exist_ok=True)
                        zip_ref.extractall(extract_path)
                        print(f"  ✅ Extracted to: {extract_path.relative_to(base_path)}")
                        
                    # Optional: Delete the ZIP file after successful extraction
                    # os.remove(zip_path) 
                    # print(f"  🗑️ Deleted original ZIP file.")
                        
                except zipfile.BadZipFile:
                    print(f"  ❌ ERROR: {file_name} is not a valid ZIP file or is corrupted.")
                except Exception as e:
                    print(f"  ❌ An unexpected error occurred while processing {file_name}: {e}")

    print("\n--- Starting CSV Consolidation ---")
    
    # 2. CSV Consolidation
    # We walk the directory again (including newly extracted folders) to find CSVs
    # Note: topdown=False is important here to ensure we move files before checking their parent directory
    
    # We must walk the directory again, but we should exclude the base_path from the move
    for root, dirs, files in os.walk(base_path):
        if Path(root) == base_path:
            # Skip the top-level directory when looking for files to move
            continue
            
        for file_name in files:
            if file_name.lower().endswith('.csv'):
                source_path = Path(root) / file_name
                
                # Create a unique target name to prevent overwriting files with the same name
                # e.g., 'data.csv' becomes 'subfolder_data.csv'
                relative_path_parts = source_path.relative_to(base_path).parts
                new_filename = "_".join(relative_path_parts)
                
                # Remove the original extension from the joined name before adding CSV back
                if new_filename.lower().endswith('.csv'):
                     new_filename = new_filename[:-4]
                     
                target_path = base_path / (new_filename + ".csv")
                
                # If the target file already exists (unlikely with our unique naming), 
                # we could add a counter, but for this script, we rely on the unique path-based name.
                
                try:
                    os.rename(source_path, target_path)
                    # print(f"  Moved: {source_path.relative_to(base_path)} -> {target_path.name}")
                    csv_files_moved += 1
                except Exception as e:
                    print(f"  ❌ Failed to move {file_name}: {e}")


    print(f"\n--- Final Summary ---")
    print(f"Found and processed {zip_files_found} ZIP file(s).")
    print(f"Successfully moved {csv_files_moved} CSV file(s) to the top level: {base_path}")
    print("\n✅ Extraction and Consolidation complete.")


# --- Execution Block ---

if __name__ == "__main__":
    # 📌 IMPORTANT: Replace this with the path to the directory containing your data
    DOWNLOAD_DIRECTORY = "./citibike_trip_data" 

    extract_zip_files_and_consolidate_csvs(DOWNLOAD_DIRECTORY)
