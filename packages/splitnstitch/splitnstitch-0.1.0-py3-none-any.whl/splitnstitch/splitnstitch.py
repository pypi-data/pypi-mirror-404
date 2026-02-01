import os
import json
from itertools import islice

import pandas as pd
import questionary as q
from halo import Halo

spinner = Halo(text='Processing...', spinner='dots')
sample_size = 20 # Number of sample values to show during inspection

splash_screen = r"""
   ____     ___ __          _  __        ______  _ __      __ 
  / __/__  / (_) /_  ____  / |/ / ____  / __/ /_(_) /_____/ / 
 _\ \/ _ \/ / / __/ /___/ /    / /___/ _\ \/ __/ / __/ __/ _ \
/___/ .__/_/_/\__/       /_/|_/       /___/\__/_/\__/\__/_//_/
   /_/
``````````````````````````````````````````````````````````````
"""


def clear_console() -> None:
    """Clear console in a cross-platform way."""
    try:
        os.system("cls" if os.name == "nt" else "clear")
    except Exception:
        # As a last resort, print many newlines
        print("\n" * 80)


def choose_file(prompt, supported_formats=('.csv', '.xlsx')):
    try:
        files_in_dir = [f for f in os.listdir('.') if f.endswith(supported_formats)]
        assert files_in_dir, "🔎 No supported files found in current directory."
        file_path = q.select(prompt, choices=files_in_dir).ask()
        return file_path
    except AssertionError as e:
        print(e)
        return None


def read_file(file_path):
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path, dtype=str)
    elif file_path.endswith('.xlsx'):
        return pd.read_excel(file_path, dtype=str)
    elif file_path.endswith('.json'):
        return pd.read_json(file_path)
    else:
        raise ValueError("Unsupported file format.")


def join_detail(df):
    detail_file = choose_file("Select detail file to join:")
    if not detail_file:
        print("No detail file selected. Skipping detail join.")
        return df
    for attempt in range(3, 0, -1):
        try:
            q.press_any_key_to_continue(f"Make sure {detail_file} if refreshed and file is closed.\nPress any key to continue...").ask()
            detail_df = read_file(detail_file)
            break
        except PermissionError:
            print(f"⚠️  File is in use or locked. {attempt - 1} attempt(s) remain...")
            if attempt == 1:
                print("❌ Unable to access package detail file. Skipping detail join.")
                return df
        except KeyboardInterrupt:
            print("Operation cancelled by user.")
            return df
        except Exception as e:
            print(f"❌ Error reading package detail file: {e}")
            return df

    all_columns = detail_df.columns.tolist()
    detail_key_column = q.select("Select the key column (from detail) to join on:", choices=all_columns).ask()
    try:
        all_columns.remove(detail_key_column)
    except ValueError:
        print(f"Warning: Key column '{detail_key_column}' not found in detail file.")
        print("Proceeding without joining details.")
        return df
    columns_to_add = q.checkbox(
        "Select detail columns to add:",
        choices=all_columns
    ).ask()
    if not columns_to_add:
        print("No detail columns selected.")
        return df
    source_key_column = q.select("Select the key column (from source) to join on:", choices=df.columns.tolist()).ask()
    spinner.start("Joining detail data...")
    try:
        pkg_subset = detail_df[[detail_key_column] + columns_to_add]

        # Change source key to match detail key
        df.rename(columns={source_key_column: detail_key_column}, inplace=True)

        merged_df = df.merge(
            right=pkg_subset,
            on=detail_key_column,
            how='left'
        )
        spinner.succeed("Detail data joined.")
        return merged_df
    except Exception as e:
        spinner.fail("Failed to join detail data.")
        print(f"Error: {e}")
        return df
    


def export_safe():
    # Get safe columns file
    safe_columns_file = choose_file("Select the SAFE COLUMNS file to use:", supported_formats=('.json',))
    if not safe_columns_file:
        user = q.confirm("Would you like to create a safe columns file now?", default=True).ask()
        if user:
            create_safe_columns_file()
        print("Please restart the export process.")
        return
        
    # Load safe column list
    with open(safe_columns_file, "r") as f:
        safe_cols = set(json.load(f))

    in_file = choose_file("Select the INTERNAL (Source) file to export a safe version from:")
    if not in_file:
        print("No file selected.")
        return
    
    # Optionally join package details
    join_details = q.confirm("Would you like to join detail data?", default=False).ask()
    
    spinner.start()
    try:
        df = read_file(in_file)

        # Select only safe columns that actually exist
        export_cols = [c for c in df.columns if c in safe_cols]
        df_safe = df[export_cols]

        if join_details:
            spinner.succeed("Export data prepared, joining details...")
            df_safe = join_detail(df_safe)
        else:
            spinner.succeed("Export data prepared.")
        
        out_file = q.text("Enter output filename:", default=f"{in_file.split('.')[0]}_Clean").ask()
        if not out_file:
            return
        spinner.start("Finalizing export...")
        if not out_file.endswith('.csv'):
            out_file += '.csv'
        df_safe.to_csv(out_file, index=False)

        spinner.succeed("Export complete.")
        print(f"Safe export created: {out_file}")
    except Exception as e:
        spinner.fail("Export failed.")
        print(f"Error: {e}")


def import_merge():
    internal = choose_file("Select ORIGINAL internal (Source) file:")
    if not internal:
        return
    external = choose_file("Select 3rd party RETURNED (Cleaned) file:")
    if not external:
        return
    
    spinner.start("Loading files...")
    try:
        df_int = read_file(internal)
        df_ext = read_file(external)
        spinner.succeed("Files loaded.")
    except Exception as e:
        spinner.fail("Failed to load files.")
        print(e)
        return
    
    source_key_column = q.select("Select the ORIGINAL KEY column to merge on:", choices=df_int.columns.tolist()).ask()
    if not source_key_column:
        return

    spinner.start()
    try:

        if source_key_column not in df_int.columns:
            spinner.fail(f"ID column '{source_key_column}' not found in internal file.")
            return
        if source_key_column not in df_ext.columns:
            spinner.fail(f"ID column '{source_key_column}' not found in external file.")
            return

        # Only add NEW columns from external
        new_cols = [c for c in df_ext.columns if c not in df_int.columns]

        df_merge = df_int.merge(
            right=df_ext[[source_key_column] + new_cols],
            on=source_key_column,
            how="left"
        )

        # Ask if details should be added
        spinner.succeed("Merging complete")
        if q.confirm("Would you like to join detail file? (Select 'N' if it was already added)", default=False).ask():
            df_merge = join_detail(df_merge)

        out_file = q.text("Enter output filename:", default=f"{internal.split('.')[0]}_Merged").ask()
        if not out_file:
            return
        spinner.start("Creating file...")
        if not out_file.endswith('.csv'):
            out_file += '.csv'
        df_merge.to_csv(out_file, index=False)

        spinner.succeed("Import and merge complete.")
        print(f"Merged file created: {out_file}")
    except Exception as e:
        spinner.fail("Import failed.")


def inspect_column_safety(column: pd.Series) -> bool:
    while True:
        # Print header
        print(f"Inspecting column: {column.name}")
        print(f"{'-'*40}")
        # Show sample values
        sample_values = column.sample(min(sample_size, len(column))).tolist()
        for val in sample_values:
            print(f" {val}")
        print() # Extra newline for spacing
        user = q.select(
            "Is this column SAFE to include in the export?",
            choices=[
                "Yes, safe to include.",
                "No, contains sensitive data.",
                "Show sample values again."
            ]).ask()
        if user.startswith("Yes"):
            return True
        elif user.startswith("No"):
            return False


def create_safe_columns_file():
    def preview_last_choices(choices: dict, N: int=0) -> None:
        # N=0 means show all
        # Dict preserves insertion order (Py3.7+)
        if choices:
            print("Last choices made:")
            if N == 0:
                # Show all, in original order
                last_n = list(choices.items())
            else:
                last_n = list(islice(reversed(choices.items()), N))[::-1]
            for key, value in last_n:
                if value is True:
                    q.print(f"🔓 (Safe) {key}", style="fg:green")
                else:
                    q.print(f"🔒 (Unsafe) {key}", style="fg:red")
            print() # Extra newline for spacing

    in_file = choose_file("Select a file to generate safe columns from:")
    if not in_file:
        print("No file selected.")
        return
    try:
        df = read_file(in_file)
        cols = df.columns.tolist()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
    
    if not q.confirm("Ready to loop through every column for inspection? (This may take a while, grab some ☕)", default=True).ask():
        print("Maybe another time...")
        return
    
    safe_columns = {}
    for col in cols:
        clear_console()
        preview_last_choices(safe_columns, N=5)
        try:
            safe_columns[col] = inspect_column_safety(df[col])
        except KeyboardInterrupt:
            print("Operation cancelled by user.")
            return
        except Exception as e:
            print(f"Error inspecting column '{col}': {e}")
            if q.confirm("Mark this column as unsafe and continue?", default=True).ask():
                safe_columns[col] = False
            else:
                return
    
    clear_console()
    preview_last_choices(safe_columns)
    out_file = q.text("Enter output filename for safe columns:", default="safe_columns").ask()
    if not out_file.endswith('.json'):
        out_file += '.json'
    with open(out_file, "w") as f:
        json.dump([k for k, v in safe_columns.items() if v], f, indent=4)
    print(f"✅ Safe columns file created: {out_file}")


def main():
    print(splash_screen)
    try:
        choice = q.select(
            message="Choose an operation:",
            choices=[
                "1[Split] Export Safe version of Internal (Source) File.",
                "2[Stitch] Import and Merge External (Returned) File.",
                "3[Generate] Create Safe Columns File.",
                "0[Exit] Quit the program."
            ]
        ).ask()
        if not choice:
            return
        choice = choice.split('[')[0]
        if choice == "0":
            print("Goodbye!")
            return
        elif choice == "1":
            export_safe()
        elif choice == "2":
            import_merge()
        elif choice == "3":
            create_safe_columns_file()
        else:
            print("Invalid choice.")
    except KeyboardInterrupt:
        spinner.warn("Operation cancelled by user.")


if __name__ == "__main__":
    main()