# Brainrot Recovery — Focus & Study Tracker

<p align="center">
  <img src="static/logo.png" alt="Brainrot Recovery Logo" width="130" style="border-radius: 26px;" />
</p>

<p align="center">
  <em>Reclaim your focus. Master Core Java & JDBC. Defeat brainrot.</em>
</p>

<p align="center">
  <a href="https://brainrot-recovery-1.onrender.com">
    <img src="https://img.shields.io/badge/Live_App-Render-7C3AED?style=for-the-badge&logo=render&logoColor=white" alt="Live App on Render" />
  </a>
  <a href="https://github.com/iblamekaran/brainrot_recovery">
    <img src="https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub Repo" />
  </a>
</p>

<p align="center">
  <strong>🔗 Live Web & Mobile App:</strong> <a href="https://brainrot-recovery-1.onrender.com">https://brainrot-recovery-1.onrender.com</a>
</p>

---

> ⚡ **About This Project**:  
> I vibecoded this project and I made this for myself to lock in, beat brainrot, and track my daily study journey across Core Java and JDBC. Whether studying on desktop or on my phone, this keeps me accountable with persistent SQLite tracking and Excel synchronization.

---

## 🎨 Themes: Dark & Light Mode

* 🌙 **Dark Mode (Default)**: Deep obsidian & purple workspace aesthetic built for deep focus and late-night coding sessions.
* ☀️ **Light Mode**: Clean, crisp lavender & slate daylight aesthetic.
* 💾 **Smart Persistence**: Your theme selection is automatically saved in `localStorage` across visits and app launches.

---

## 📱 Live Mobile App (PWA)

The app is deployed live on Render with full HTTPS and offline PWA capability. You can install it straight to your phone's home screen:

1. Open **[https://brainrot-recovery-1.onrender.com](https://brainrot-recovery-1.onrender.com)** on your smartphone.
2. **On Android (Google Chrome)**: Tap the **📲 Install App** button on the header (or tap Chrome's menu `⋮` → **"Install app"** / **"Add to Home screen"**).
3. **On iPhone (Safari)**: Tap the **Share icon** (square with upward arrow) → **"Add to Home Screen"**.
4. The **Brainrot Recovery** brain logo will appear on your phone's home screen and launch in full-screen standalone mode.

---

## 🚀 3 Ways to Run

1. 🌐 **Live Cloud App**: Visit [https://brainrot-recovery-1.onrender.com](https://brainrot-recovery-1.onrender.com) anytime from any device.
2. 🖥️ **Desktop Dashboard UI**: Modern purple workspace desktop interface built with Python Tkinter (`python app.py`).
3. 💻 **Terminal CLI**: Fast terminal-based study tracker (`python tracker.py`).

All interfaces share persistent SQLite database tracking (`brainrot_recovery.db`) and synchronize bi-directionally with your Excel roadmap (`Vyavastha_Core_Java_JDBC_Progress_Tracker.xlsx`).

---

## 🖥️ How to Run Locally

### 1. Clone & Install
```bash
git clone https://github.com/iblamekaran/brainrot_recovery.git
cd brainrot_recovery
pip install -r requirements.txt
```

### 2. Run Desktop UI (Tkinter)
```bash
python app.py
```
* Purple workspace dashboard theme with live metric cards (*Total Topics*, *Covered*, *In Progress*, *Needs Revision*).
* Real-time search, filters, topic details, and Excel export.

### 3. Run Mobile Server Locally
```bash
python server.py
```

### 4. Run Terminal CLI
```bash
python tracker.py
```

---

## 📁 Project Structure

```text
brainrot_recovery/
├── server.py                                        # Mobile App server & API (Flask / Gunicorn)
├── app.py                                           # Desktop Graphical UI (Tkinter) + WSGI bridge
├── tracker.py                                       # Terminal CLI Application
├── requirements.txt                                 # Dependencies (openpyxl, Flask, Pillow, gunicorn)
├── render.yaml                                      # Render deployment configuration
├── README.md                                        # Documentation
├── brainrot_recovery.db                             # SQLite database (auto-created & synced)
├── Vyavastha_Core_Java_JDBC_Progress_Tracker.xlsx  # Original Excel tracker
├── static/
│   ├── logo.png                                     # Master Brainrot Recovery logo
│   ├── favicon.png                                  # Favicon
│   ├── icon-192.png                                 # 192px mobile home screen icon
│   ├── icon-512.png                                 # 512px mobile splash screen icon
│   ├── manifest.json                                # PWA mobile manifest
│   ├── sw.js                                        # Offline service worker
│   ├── app.css                                      # Purple workspace mobile styles
│   └── app.js                                       # Mobile app logic & sync
└── templates/
    └── index.html                                   # Mobile web app template
```
