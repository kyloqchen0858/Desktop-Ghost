# 👻 Desktop Ghost

A minimalist to-do widget that floats like a ghost on your Windows desktop. No databases, no clouds—just you, a text file, and your focus.

---

## ✨ Key Features

- **🎯 Dual View Modes**
  - **Full Mode**: Starts center-stage, displaying your complete task list.
  - **Capsule Mode**: Double-click to shrink the widget into a mini "pill" that shows only one task at a time.
  - **Smart Memory**: The widget remembers exactly where you left it in Capsule Mode.

- **🖱️ Seamless Interaction**
  - **Draggable**: Click and hold anywhere on the window to move it around.
  - **Scroll to Switch**: In Capsule Mode, use your mouse wheel to cycle through tasks instantly.
  - **Right-Click Menu**: Access the context menu to exit the application.
  - **Satisfaction**: Check a box to see a strikethrough animation; the task vanishes from your file after 0.5 seconds.

- **⏰ Smart Workflow**
  - **Daily Focus**: Automatically pops up to the center of your screen at `09:00 AM` (configurable) to remind you of your goals.
  - **File-Driven**: Real-time sync with `todo.txt` on your desktop.
  - **Bi-Directional**: Edit the text file with Notepad, and the widget updates instantly. Update the widget, and the file saves automatically.

---

## 🚀 Quick Start

### Option 1: Run via Python
1. **Install Dependencies**
   ```bash
   pip install customtkinter watchdog
   ```
2. **Run the App**
   ```bash
   python main.py
   ```

### Option 2: Build as EXE (Recommended)
1. **Install PyInstaller**
   ```bash
   pip install pyinstaller
   ```
2. **Build the Standalone App**
   ```bash
   pyinstaller --noconsole --onefile --name "Desktop Ghost" main.py
   ```
3. **Locate File**
   Find `Desktop Ghost.exe` in the `dist` folder. Double-click to run!

---

## ⚙️ Auto-Start Setup

Want Ghost to greet you every morning?
1. Press `Win + R`, type `shell:startup`, and hit Enter.
2. Create a shortcut for `Desktop Ghost.exe` and drag it into this folder.
3. **Done!** It will now launch automatically on boot.

---

## 📖 Controls Guide

| Action | Control Method |
| :--- | :--- |
| **Move Window** | Click & hold anywhere to drag |
| **Switch Mode** | Double-click anywhere on the window |
| **Cycle Tasks** | Scroll mouse wheel (in Capsule Mode) |
| **Complete Task** | Click the checkbox |
| **Exit App** | Right-click anywhere on the window |

---

## 🎨 Configuration

You can customize the widget settings at the top of `main.py`:

```python
POPUP_TIME = "09:00"        # Change daily reminder time (24h format)
ctk.set_appearance_mode("Dark") # Change to "Light" for light mode
```

---

## 📁 File Structure

- `main.py` - The core application script.
- `todo.txt` - Your task list (automatically created on your Desktop).
- `requirements.txt` - Python dependencies.

<br>

<div align="center">
  Made with ❤️ by Kylo & Antigravity
  <br>
  <i>Let this little ghost guide your productivity!</i>
</div>
