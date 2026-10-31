"""
Brainrot Recovery - Mobile App Server & API
Run this server to access and install the Brainrot Recovery app on your smartphone.
"""

import os
import sys
import socket
from pathlib import Path
from flask import Flask, jsonify, request, render_template, send_from_directory

# Import tracker logic
import tracker

# Initialize backend DB and load curriculum on startup
tracker.init_db()
tracker.ensure_data_loaded()

app = Flask(__name__, static_folder="static", template_folder="templates")


def get_local_ip():
    """Detects the computer's local network IP on Wi-Fi."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


@app.route("/")
def index():
    """Serves the mobile-responsive web application."""
    return render_template("index.html")


@app.route("/manifest.json")
def manifest():
    """Serves PWA manifest."""
    return send_from_directory("static", "manifest.json", mimetype="application/manifest+json")


@app.route("/sw.js")
def service_worker():
    """Serves PWA Service Worker."""
    response = send_from_directory("static", "sw.js", mimetype="application/javascript")
    response.headers["Service-Worker-Allowed"] = "/"
    return response


@app.route("/api/summary", methods=["GET"])
def get_summary():
    """Returns real-time curriculum metrics."""
    with tracker.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM topics")
        total = cursor.fetchone()["total"]

        cursor.execute("SELECT status, COUNT(*) AS cnt FROM topics GROUP BY status")
        counts = {row["status"]: row["cnt"] for row in cursor.fetchall()}

    covered = counts.get("Covered", 0)
    in_progress = counts.get("In Progress", 0)
    revision = counts.get("Needs Revision", 0)
    not_started = counts.get("Not Started", 0)

    pct_covered = round((covered / total * 100), 1) if total > 0 else 0

    return jsonify({
        "total": total,
        "covered": covered,
        "in_progress": in_progress,
        "revision": revision,
        "not_started": not_started,
        "pct_covered": pct_covered
    })


@app.route("/api/topics", methods=["GET"])
def get_topics():
    """Returns all curriculum topics."""
    with tracker.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, technology, section, topic, subtopics,
                   vyavastha_app, status, date_covered, practice_notes, priority
            FROM topics
            ORDER BY id ASC
        """)
        rows = [dict(row) for row in cursor.fetchall()]

    return jsonify(rows)


@app.route("/api/topics/<int:topic_id>", methods=["POST"])
def update_topic(topic_id):
    """Updates a topic's status, date covered, and practice notes."""
    data = request.get_json() or {}
    new_status = data.get("status")
    new_date = data.get("date_covered") or None
    new_notes = data.get("practice_notes") or None

    if new_status not in tracker.VALID_STATUSES:
        return jsonify({"success": False, "error": f"Invalid status: {new_status}"}), 400

    with tracker.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE topics
            SET status = ?, date_covered = ?, practice_notes = ?
            WHERE id = ?
        """, (new_status, new_date, new_notes, topic_id))
        conn.commit()

    return jsonify({"success": True})


@app.route("/api/export-excel", methods=["POST"])
def export_excel():
    """Syncs SQLite database back to the Excel file."""
    try:
        tracker.export_progress_to_excel()
        return jsonify({"success": True, "message": "Excel exported successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def run_mobile_server():
    """Starts the Flask server with friendly instructions."""
    local_ip = get_local_ip()
    port = int(os.environ.get("PORT", 5000))

    print("\n" + "=" * 65)
    print("       BRAINROT RECOVERY — MOBILE APP SERVER")
    print("=" * 65)
    print(f"Computer access    : http://localhost:{port}")
    print(f"Phone Wi-Fi access : http://{local_ip}:{port}")
    print("-" * 65)
    print("HOW TO INSTALL ON YOUR PHONE:")
    print(f"1. Make sure your phone is connected to the same Wi-Fi.")
    print(f"2. Open Chrome (Android) or Safari (iPhone).")
    print(f"3. Type this URL: http://{local_ip}:{port}")
    print(f"4. Tap 'Install App' or 'Add to Home screen'.")
    print("   The Brainrot Recovery icon will appear on your home screen!")
    print("=" * 65 + "\n")

    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    run_mobile_server()
