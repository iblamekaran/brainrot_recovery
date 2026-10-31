"""
Brainrot Recovery — Study Tracker
A terminal-based study tracker integrating SQLite and Excel.
Helps reclaim your focus and master Core Java & JDBC.
"""

import os
import sys
import shutil
import sqlite3
import datetime
from pathlib import Path

# Enable UTF-8 on Windows stdout if supported, otherwise fallback to ASCII safely
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import openpyxl
except ImportError:
    openpyxl = None

# Constants & Configuration
DB_PATH = Path("brainrot_recovery.db")
OLD_DB_PATH = Path("vyavastha_tracker.db")
EXCEL_FILE = Path("Vyavastha_Core_Java_JDBC_Progress_Tracker.xlsx")

# Migrate old database if present
if not DB_PATH.exists() and OLD_DB_PATH.exists():
    try:
        shutil.copy2(OLD_DB_PATH, DB_PATH)
    except Exception:
        pass

VALID_STATUSES = [
    "Not Started",
    "In Progress",
    "Covered",
    "Needs Revision"
]


def get_db_connection():
    """Connects to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the SQLite schema."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                technology TEXT NOT NULL,
                section TEXT NOT NULL,
                topic TEXT NOT NULL,
                subtopics TEXT,
                vyavastha_app TEXT,
                status TEXT NOT NULL DEFAULT 'Not Started',
                date_covered TEXT,
                practice_notes TEXT,
                priority TEXT,
                excel_row INTEGER
            )
        """)
        conn.commit()


def import_topics_from_excel(excel_path=EXCEL_FILE):
    """Imports topics from the Excel tracker if database is empty."""
    if not openpyxl:
        print("[!] Warning: openpyxl is not installed. Run 'pip install -r requirements.txt'")
        return 0

    if not os.path.exists(excel_path):
        xlsx_candidates = list(Path(".").glob("*Progress*.xlsx"))
        if xlsx_candidates:
            excel_path = xlsx_candidates[0]
        else:
            return 0

    try:
        wb = openpyxl.load_workbook(excel_path, data_only=True)
        sheet_name = "Progress Tracker" if "Progress Tracker" in wb.sheetnames else wb.sheetnames[0]
        ws = wb[sheet_name]
    except Exception as e:
        print(f"[!] Error loading Excel file: {e}")
        return 0

    topics_to_insert = []
    # Row 4 is header, data starts at row 5
    for row_idx in range(5, ws.max_row + 1):
        tech = ws.cell(row=row_idx, column=1).value
        section = ws.cell(row=row_idx, column=2).value
        topic = ws.cell(row=row_idx, column=3).value
        subtopics = ws.cell(row=row_idx, column=4).value
        app = ws.cell(row=row_idx, column=5).value
        status = ws.cell(row=row_idx, column=6).value or "Not Started"
        date_cov = ws.cell(row=row_idx, column=7).value
        notes = ws.cell(row=row_idx, column=8).value
        priority = ws.cell(row=row_idx, column=9).value

        # Only insert rows that have a topic name
        if topic and str(topic).strip():
            if isinstance(date_cov, (datetime.date, datetime.datetime)):
                date_str = date_cov.strftime("%Y-%m-%d")
            elif date_cov:
                date_str = str(date_cov).strip()
            else:
                date_str = None

            topics_to_insert.append((
                str(tech).strip() if tech else "Core Java",
                str(section).strip() if section else "",
                str(topic).strip(),
                str(subtopics).strip() if subtopics else "",
                str(app).strip() if app else "",
                str(status).strip() if status else "Not Started",
                date_str,
                str(notes).strip() if notes else None,
                str(priority).strip() if priority else "Core",
                row_idx
            ))

    if topics_to_insert:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO topics (
                    technology, section, topic, subtopics,
                    vyavastha_app, status, date_covered,
                    practice_notes, priority, excel_row
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, topics_to_insert)
            conn.commit()

    return len(topics_to_insert)


def ensure_data_loaded():
    """Checks if DB has topics; if not, loads from Excel."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM topics")
        count = cursor.fetchone()["total"]

    if count == 0:
        imported = import_topics_from_excel()
        if imported > 0:
            print(f"[OK] Successfully imported {imported} topics into Brainrot Recovery database!")
        else:
            print("[INFO] Note: No topics found in Excel file to import.")


def make_progress_bar(percentage, length=24):
    """Creates a visual progress bar using ASCII characters."""
    filled = int(length * percentage / 100)
    bar = "=" * filled + "-" * (length - filled)
    return f"[{bar}] {percentage:.1f}%"


def print_topic_table(rows, show_details=False):
    """Nicely formats a list of topic rows in standard ASCII."""
    if not rows:
        print("\nNo topics found matching your criteria.")
        return

    print("\n" + "=" * 90)
    print(f"{'ID':<4} | {'Tech':<9} | {'Section':<28} | {'Topic':<26} | {'Status'}")
    print("-" * 90)

    for row in rows:
        status_tag = row['status']
        sec_truncated = (row['section'][:25] + "...") if len(row['section']) > 28 else row['section']
        top_truncated = (row['topic'][:23] + "...") if len(row['topic']) > 26 else row['topic']
        print(f"{row['id']:<4} | {row['technology']:<9} | {sec_truncated:<28} | {top_truncated:<26} | {status_tag}")

        if show_details:
            if row['date_covered'] or row['practice_notes']:
                date_part = f"Date: {row['date_covered']}" if row['date_covered'] else ""
                notes_part = f"Notes: {row['practice_notes']}" if row['practice_notes'] else ""
                extra = " | ".join(filter(None, [date_part, notes_part]))
                print(f"     +-- {extra}")

    print("=" * 90)
    print(f"Total topics shown: {len(rows)}")


def view_all_topics():
    """Displays all topics with pagination and detail view options."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM topics ORDER BY id ASC")
        rows = cursor.fetchall()

    if not rows:
        print("\nNo topics currently in database.")
        return

    page_size = 15
    total_pages = (len(rows) + page_size - 1) // page_size
    current_page = 1

    while True:
        start_idx = (current_page - 1) * page_size
        end_idx = start_idx + page_size
        page_rows = rows[start_idx:end_idx]

        print(f"\n--- Topics List (Page {current_page} of {total_pages}) ---")
        print_topic_table(page_rows)

        print("\nOptions: [N]ext Page | [P]revious Page | [A]ll at once | [D]etail view by ID | [B]ack to menu")
        choice = input("Enter choice: ").strip().lower()

        if choice == 'n':
            if current_page < total_pages:
                current_page += 1
            else:
                print("You are on the last page.")
        elif choice == 'p':
            if current_page > 1:
                current_page -= 1
            else:
                print("You are on the first page.")
        elif choice == 'a':
            print_topic_table(rows, show_details=True)
            input("\nPress Enter to continue...")
            break
        elif choice == 'd':
            topic_id_str = input("Enter Topic ID to inspect: ").strip()
            if topic_id_str.isdigit():
                show_single_topic_details(int(topic_id_str))
            else:
                print("Invalid topic ID.")
        elif choice in ('b', 'q', 'exit', ''):
            break
        else:
            print("Invalid option. Please choose N, P, A, D, or B.")


def show_single_topic_details(topic_id):
    """Displays comprehensive info for a single topic."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM topics WHERE id = ?", (topic_id,))
        topic = cursor.fetchone()

    if not topic:
        print(f"[!] Topic ID #{topic_id} not found.")
        return None

    print("\n" + "=" * 65)
    print(f"  TOPIC #{topic['id']}: {topic['topic']}")
    print("=" * 65)
    print(f"Technology     : {topic['technology']}")
    print(f"Section        : {topic['section']}")
    print(f"Priority       : {topic['priority']}")
    print(f"Subtopics      : {topic['subtopics']}")
    print(f"Application    : {topic['vyavastha_app']}")
    print(f"Status         : {topic['status']}")
    print(f"Date Covered   : {topic['date_covered'] or 'Not yet covered'}")
    print(f"Practice Notes : {topic['practice_notes'] or 'No notes recorded'}")
    print("=" * 65)
    return topic


def update_topic():
    """Allows user to update status, date covered, and practice notes."""
    print("\n========== UPDATE A TOPIC ==========")
    topic_id_input = input("Enter Topic ID (Serial Number) to update (or 'c' to cancel): ").strip()
    if topic_id_input.lower() == 'c' or not topic_id_input:
        return

    if not topic_id_input.isdigit():
        print("[!] Error: Topic ID must be a numeric serial number.")
        return

    topic_id = int(topic_id_input)
    topic = show_single_topic_details(topic_id)
    if not topic:
        return

    print("\nSelect new status:")
    print("  1. Not Started")
    print("  2. In Progress")
    print("  3. Covered")
    print("  4. Needs Revision")
    print(f"  [Press Enter to keep current: '{topic['status']}']")
    status_choice = input("Enter choice (1-4) or press Enter: ").strip()

    status_map = {
        "1": "Not Started",
        "2": "In Progress",
        "3": "Covered",
        "4": "Needs Revision"
    }

    if status_choice in status_map:
        new_status = status_map[status_choice]
    elif status_choice == "":
        new_status = topic['status']
    else:
        print("[!] Invalid status choice. Status unchanged.")
        new_status = topic['status']

    # Date covered
    default_date = datetime.date.today().strftime("%Y-%m-%d")
    current_date = topic['date_covered'] or ""
    if new_status == "Covered" and not current_date:
        prompt_date = f"Enter completion date (YYYY-MM-DD) [Default: {default_date}]: "
        date_input = input(prompt_date).strip()
        new_date = date_input if date_input else default_date
    else:
        prompt_date = f"Enter completion date (YYYY-MM-DD) [Current: '{current_date}', Enter to keep]: "
        date_input = input(prompt_date).strip()
        new_date = date_input if date_input else current_date

    if new_date == "":
        new_date = None

    # Practice notes
    current_notes = topic['practice_notes'] or ""
    print(f"\nCurrent notes: {current_notes if current_notes else 'None'}")
    print("Enter new practice notes / comments (or press Enter to keep current):")
    notes_input = input("> ").strip()
    new_notes = notes_input if notes_input else current_notes
    if new_notes == "":
        new_notes = None

    # Save to SQLite database
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE topics
            SET status = ?, date_covered = ?, practice_notes = ?
            WHERE id = ?
        """, (new_status, new_date, new_notes, topic_id))
        conn.commit()

    print("\n" + "-" * 50)
    print(f"[OK] Topic #{topic_id} ('{topic['topic']}') successfully updated!")
    print(f"     Status : {new_status}")
    print(f"     Date   : {new_date or 'None'}")
    print(f"     Notes  : {new_notes or 'None'}")
    print("-" * 50)


def view_topics_by_status():
    """Filters topics by status."""
    print("\n========== VIEW TOPICS BY STATUS ==========")
    print("1. Not Started")
    print("2. In Progress")
    print("3. Covered")
    print("4. Needs Revision")
    print("0. Back")

    choice = input("Select status (1-4): ").strip()
    status_map = {
        "1": "Not Started",
        "2": "In Progress",
        "3": "Covered",
        "4": "Needs Revision"
    }

    if choice not in status_map:
        return

    selected_status = status_map[choice]

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM topics
            WHERE status = ?
            ORDER BY id ASC
        """, (selected_status,))
        rows = cursor.fetchall()

    print(f"\n--- Topics with status: '{selected_status}' ({len(rows)} topics) ---")
    print_topic_table(rows, show_details=True)


def search_topics():
    """Searches topics by keyword in topic name, subtopics, section, or notes."""
    print("\n========== SEARCH TOPICS ==========")
    query = input("Enter search keyword (e.g. 'OOP', 'JDBC', 'thread', 'list'): ").strip()
    if not query:
        print("Empty search query.")
        return

    with get_db_connection() as conn:
        cursor = conn.cursor()
        search_pattern = f"%{query}%"
        cursor.execute("""
            SELECT * FROM topics
            WHERE topic LIKE ?
               OR subtopics LIKE ?
               OR section LIKE ?
               OR vyavastha_app LIKE ?
               OR practice_notes LIKE ?
            ORDER BY id ASC
        """, (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern))
        rows = cursor.fetchall()

    print(f"\n--- Search results for '{query}' ({len(rows)} matching) ---")
    print_topic_table(rows, show_details=True)


def view_progress_summary():
    """Displays overall completion percentage, status breakdown, and tech breakdown."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM topics")
        total = cursor.fetchone()['total']

        if total == 0:
            print("\nNo topics loaded in tracker.")
            return

        cursor.execute("SELECT status, COUNT(*) as cnt FROM topics GROUP BY status")
        status_counts = {row['status']: row['cnt'] for row in cursor.fetchall()}

        # Counts by technology
        cursor.execute("""
            SELECT technology,
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'Covered' THEN 1 ELSE 0 END) as covered,
                   SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_prog,
                   SUM(CASE WHEN status = 'Needs Revision' THEN 1 ELSE 0 END) as revision,
                   SUM(CASE WHEN status = 'Not Started' THEN 1 ELSE 0 END) as not_started
            FROM topics
            GROUP BY technology
        """)
        tech_stats = cursor.fetchall()

        # Counts by section
        cursor.execute("""
            SELECT technology, section,
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'Covered' THEN 1 ELSE 0 END) as covered
            FROM topics
            GROUP BY technology, section
            ORDER BY id ASC
        """)
        section_stats = cursor.fetchall()

    covered = status_counts.get("Covered", 0)
    in_progress = status_counts.get("In Progress", 0)
    revision = status_counts.get("Needs Revision", 0)
    not_started = status_counts.get("Not Started", 0)

    pct_covered = (covered / total * 100) if total > 0 else 0
    pct_in_prog = (in_progress / total * 100) if total > 0 else 0
    pct_rev = (revision / total * 100) if total > 0 else 0
    pct_not_started = (not_started / total * 100) if total > 0 else 0

    print("\n" + "=" * 65)
    print("            BRAINROT RECOVERY PROGRESS SUMMARY")
    print("=" * 65)
    print(f"\nOverall Progress: {make_progress_bar(pct_covered, length=30)}")
    print(f"Total Topics    : {total}")
    print(f"  - Covered       : {covered:<3} ({pct_covered:>5.1f}%)")
    print(f"  - In Progress   : {in_progress:<3} ({pct_in_prog:>5.1f}%)")
    print(f"  - Needs Revision: {revision:<3} ({pct_rev:>5.1f}%)")
    print(f"  - Not Started   : {not_started:<3} ({pct_not_started:>5.1f}%)")

    print("\n" + "-" * 65)
    print("BREAKDOWN BY TECHNOLOGY:")
    print("-" * 65)
    for t in tech_stats:
        t_total = t['total']
        t_cov = t['covered']
        t_pct = (t_cov / t_total * 100) if t_total > 0 else 0
        print(f"* {t['technology']:<12} : {make_progress_bar(t_pct, length=15)}  ({t_cov}/{t_total} covered)")
        print(f"    In Progress: {t['in_prog']} | Needs Revision: {t['revision']} | Not Started: {t['not_started']}")

    print("\n" + "-" * 65)
    print("BREAKDOWN BY SECTION:")
    print("-" * 65)
    for s in section_stats:
        s_total = s['total']
        s_cov = s['covered']
        s_pct = (s_cov / s_total * 100) if s_total > 0 else 0
        bar = "=" * int(10 * s_cov / s_total) + "-" * (10 - int(10 * s_cov / s_total))
        print(f"  [{bar}] {s_cov:>2}/{s_total:<2}  {s['technology']} > {s['section']}")

    print("=" * 65)


def export_progress_to_excel(excel_path=EXCEL_FILE):
    """Exports SQLite progress back to the Excel workbook."""
    if not openpyxl:
        print("[!] openpyxl is required to export to Excel. Run 'pip install -r requirements.txt'")
        return

    if not os.path.exists(excel_path):
        xlsx_candidates = list(Path(".").glob("*Progress*.xlsx"))
        if xlsx_candidates:
            excel_path = xlsx_candidates[0]
        else:
            print(f"[!] Target Excel tracker '{excel_path}' not found.")
            return

    print(f"\n[INFO] Exporting progress to '{excel_path}'...")

    try:
        wb = openpyxl.load_workbook(excel_path)
        sheet_name = "Progress Tracker" if "Progress Tracker" in wb.sheetnames else wb.sheetnames[0]
        ws = wb[sheet_name]

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM topics ORDER BY id ASC")
            topics = cursor.fetchall()

        # Update rows
        updated_count = 0
        for topic in topics:
            row_idx = topic['excel_row']
            if not row_idx or row_idx < 5:
                row_idx = topic['id'] + 4

            if row_idx <= ws.max_row:
                ws.cell(row=row_idx, column=6).value = topic['status']
                ws.cell(row=row_idx, column=7).value = topic['date_covered']
                ws.cell(row=row_idx, column=8).value = topic['practice_notes']
                updated_count += 1

        wb.save(excel_path)
        print(f"[OK] Successfully exported {updated_count} topics to '{excel_path}'!")
        print("     Summary formulas in Excel will now reflect your updated progress.")
    except PermissionError:
        print(f"[!] Error: Unable to save to '{excel_path}'. Please close Excel if the file is currently open.")
    except Exception as e:
        print(f"[!] Error during Excel export: {e}")


def main_menu():
    """Main terminal interface menu."""
    init_db()
    ensure_data_loaded()

    while True:
        print("\n========== BRAINROT RECOVERY ==========")
        print("1. View all topics")
        print("2. Update a topic")
        print("3. View topics by status")
        print("4. Search topics")
        print("5. View progress summary")
        print("6. Export progress to Excel")
        print("0. Exit")
        print("=======================================")

        try:
            choice = input("Enter your choice (0-6): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye! Reclaim your focus with Brainrot Recovery.")
            break

        if choice == "1":
            view_all_topics()
        elif choice == "2":
            update_topic()
        elif choice == "3":
            view_topics_by_status()
        elif choice == "4":
            search_topics()
        elif choice == "5":
            view_progress_summary()
        elif choice == "6":
            export_progress_to_excel()
        elif choice == "0":
            print("\nGoodbye! Your progress is saved in SQLite.")
            break
        else:
            print("[!] Invalid option. Please enter a number between 0 and 6.")


if __name__ == "__main__":
    main_menu()
