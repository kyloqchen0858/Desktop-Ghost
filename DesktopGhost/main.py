import os
import time
from datetime import datetime
from pathlib import Path
import customtkinter as ctk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import tkinter as tk

# --- 配置区 ---
# 获取当前用户的桌面路径
DESKTOP_PATH = Path(os.path.join(os.path.expanduser("~"), "Desktop"))
TODO_FILE_NAME = "todo.txt"
TODO_PATH = DESKTOP_PATH / TODO_FILE_NAME

# 自定义番茄钟/提醒时间 (24小时制)
POPUP_TIME = "09:00"

# 设置 CustomTkinter 外观
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class FileChangeHandler(FileSystemEventHandler):
    """文件监听器"""
    def __init__(self, callback):
        self.callback = callback

    def on_modified(self, event):
        if str(event.src_path).endswith(TODO_FILE_NAME):
            self.callback()

class DesktopGhost(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- 1. 核心状态变量 ---
        self.is_mini_mode = False       # 当前是否为胶囊模式
        self.capsule_pos = None         # 记忆胶囊模式的位置 (x, y)
        self.cached_tasks = []          # 缓存的任务列表数据
        self.current_task_index = 0     # 胶囊模式下当前显示的任务索引
        
        self.window_width = 300
        self.full_height = 400
        self.mini_height = 50
        self.last_scroll_time = 0  # <--- 【新增这行】初始化滚动时间

        # --- 2. 窗口基础设置 ---
        self.title("Desktop Ghost")
        self.attributes("-alpha", 0.85)
        self.attributes("-topmost", True)
        self.overrideredirect(True)
        self.configure(fg_color="#1a1a1a")

        # --- 3. UI 组件初始化 ---
        # 3.1 完整模式组件
        self.label_title = ctk.CTkLabel(
            self, 
            text="👻 DESKTOP GHOST", 
            font=("Consolas", 16, "bold"), 
            text_color="#5e5eff"
        )
        
        self.scroll_frame = ctk.CTkScrollableFrame(
            self, 
            fg_color="transparent", 
            width=280, 
            height=320
        )
        self.checkboxes = []

        # 3.2 胶囊模式组件
        self.mini_label = ctk.CTkLabel(
            self,
            text="",
            font=("Microsoft YaHei", 12, "bold"),
            text_color="#ffffff",
            cursor="hand2"
        )

        # --- 4. 事件绑定 ---
        # 拖拽相关
        self.x_offset = 0
        self.y_offset = 0
        self.bind("<Button-1>", self.start_move)
        self.bind("<B1-Motion>", self.do_move)
        
        # 双击切换模式
        self.bind("<Double-Button-1>", self.toggle_mode)
        
        # 右键退出
        self.bind("<Button-3>", self.show_context_menu)

        # 鼠标滚轮切换任务 (Windows)
        self.bind("<MouseWheel>", self.on_mini_scroll)
        # Linux 兼容 (Button-4/5)
        self.bind("<Button-4>", lambda e: self.on_mini_scroll(e, direction=1))
        self.bind("<Button-5>", lambda e: self.on_mini_scroll(e, direction=-1))

        # 为子控件绑定事件，确保交互无死角
        for widget in [self.label_title, self.mini_label]:
            widget.bind("<Button-1>", self.start_move)
            widget.bind("<B1-Motion>", self.do_move)
            widget.bind("<Double-Button-1>", self.toggle_mode)
            widget.bind("<MouseWheel>", self.on_mini_scroll)

        # --- 5. 启动逻辑 ---
        self.ensure_todo_file()
        self.refresh_data()          # 读取数据
        self.switch_to_full_center() # 默认启动：屏幕中央显示完整列表
        self.start_file_watcher()
        self.start_timer_check()
        
        self.last_scroll_time = 0  # 初始化滚动时间戳

    # --- 模式切换核心逻辑 ---

    def toggle_mode(self, event=None):
        """在 屏幕中央完整模式 与 记忆位置胶囊模式 之间切换"""
        if self.is_mini_mode:
            self.switch_to_full_center()
        else:
            self.switch_to_capsule_mode()

    def switch_to_full_center(self):
        """切换到：完整模式 + 屏幕居中"""
        self.is_mini_mode = False
        
        # 1. 隐藏胶囊组件，显示完整组件
        self.mini_label.pack_forget()
        self.label_title.pack(pady=(15, 10))
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # 2. 计算屏幕中心坐标
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - self.window_width) // 2
        y = (screen_h - self.full_height) // 2

        # 3. 设置几何
        self.geometry(f"{self.window_width}x{self.full_height}+{x}+{y}")
        self.refresh_full_ui()

    def switch_to_capsule_mode(self):
        """切换到：胶囊模式 + 记忆位置 (默认右下角)"""
        self.is_mini_mode = True

        # 1. 隐藏完整组件，显示胶囊组件
        self.label_title.pack_forget()
        self.scroll_frame.pack_forget()
        self.mini_label.pack(fill="both", expand=True, padx=20)

        # 2. 确定位置
        if self.capsule_pos:
            x, y = self.capsule_pos
        else:
            # 默认右下角
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            x = screen_w - self.window_width - 20
            y = screen_h - self.mini_height - 60
            self.capsule_pos = (x, y)

        # 3. 设置几何
        self.geometry(f"{self.window_width}x{self.mini_height}+{x}+{y}")
        self.update_mini_label()

    # --- 交互逻辑 ---

    def start_move(self, event):
        self.x_offset = event.x
        self.y_offset = event.y

    def do_move(self, event):
        x = event.x_root - self.x_offset
        y = event.y_root - self.y_offset
        self.geometry(f"+{x}+{y}")

        # 如果在胶囊模式下拖拽，实时记录位置
        if self.is_mini_mode:
            self.capsule_pos = (x, y)

    def on_mini_scroll(self, event, direction=None):
        """胶囊模式下：鼠标滚轮切换显示的任务 (修复版：防止双重触发跳帧)"""
        if not self.is_mini_mode or not self.cached_tasks:
            return

        # --- 【新增】防抖检查 ---
        import time
        current_time = time.time()
        # 如果距离上次滚动不足 0.15 秒，视为重复信号，直接忽略
        if current_time - getattr(self, 'last_scroll_time', 0) < 0.15:
            return
        self.last_scroll_time = current_time
        # ----------------------
            
        # 确定滚动方向
        if direction is None:
            # Windows Event
            if event.delta > 0:
                direction = 1  # 上一条
            else:
                direction = -1 # 下一条
        
        # 循环切换索引
        new_index = self.current_task_index - direction 
        
        # 处理边界循环
        if new_index < 0:
            new_index = len(self.cached_tasks) - 1
        elif new_index >= len(self.cached_tasks):
            new_index = 0
            
        self.current_task_index = new_index
        self.update_mini_label()
    
    def show_context_menu(self, event):
        menu = tk.Menu(self, tearoff=0, bg="#1a1a1a", fg="white")
        menu.add_command(label="退出程序", command=self.on_closing)
        menu.tk_popup(event.x_root, event.y_root)

    # --- 数据处理 ---

    def refresh_data(self):
        """只读取数据到内存，不更新UI"""
        if not TODO_PATH.exists():
            self.cached_tasks = []
            return

        try:
            with open(TODO_PATH, "r", encoding="utf-8") as f:
                self.cached_tasks = [line.strip() for line in f.readlines() if line.strip()]
        except Exception as e:
            print(f"读取异常: {e}")
            self.cached_tasks = []

    def refresh_ui_router(self):
        """根据当前模式分发刷新指令"""
        self.refresh_data()
        if self.is_mini_mode:
            self.update_mini_label()
        else:
            self.refresh_full_ui()

    def update_mini_label(self):
        if not self.cached_tasks:
            self.mini_label.configure(text="� All Clear")
            return
            
        # 确保索引安全
        if self.current_task_index >= len(self.cached_tasks):
            self.current_task_index = 0
            
        task_text = self.cached_tasks[self.current_task_index]
        # 添加索引提示 (1/5)
        display_text = f"[{self.current_task_index + 1}/{len(self.cached_tasks)}] {task_text}"
        self.mini_label.configure(text=display_text)

    def refresh_full_ui(self):
        # 清理旧控件
        for cb in self.checkboxes:
            cb.destroy()
        self.checkboxes.clear()

        for line in self.cached_tasks:
            cb = ctk.CTkCheckBox(
                self.scroll_frame,
                text=line,
                font=("Microsoft YaHei", 12),
                checkbox_height=20,
                checkbox_width=20,
                border_width=2,
                text_color="#cccccc"
            )
            cb.configure(command=lambda c=cb, t=line: self.on_task_check(c, t))
            cb.pack(fill="x", pady=4, padx=5)
            self.checkboxes.append(cb)

    def on_task_check(self, checkbox, text):
        if checkbox.get() == 1:
            checkbox.configure(font=("Microsoft YaHei", 12, "overstrike"), text_color="gray")
            self.after(500, lambda: self.delete_task(text))

    def delete_task(self, text):
        # 从缓存删除并写回文件
        if text in self.cached_tasks:
            # 只删除第一个匹配
            self.cached_tasks.remove(text)
            # 写回文件
            try:
                with open(TODO_PATH, "w", encoding="utf-8") as f:
                    # 补回换行符
                    f.writelines([f"{t}\n" for t in self.cached_tasks])
            except Exception as e:
                print(f"写入失败: {e}")
            
            # Watchdog 会触发 refresh_ui_router，这里不需要手动调用

    # --- 系统逻辑 ---

    def start_file_watcher(self):
        self.observer = Observer()
        # 注意：Watchdog 回调需要在主线程执行 UI 更新
        event_handler = FileChangeHandler(lambda: self.after(0, self.refresh_ui_router))
        self.observer.schedule(event_handler, str(DESKTOP_PATH), recursive=False)
        self.observer.start()

    def start_timer_check(self):
        """每秒检查时间，触发番茄钟/提醒"""
        now = datetime.now().strftime("%H:%M")
        
        # 如果时间匹配，且当前不是完整显示状态 (防止已经在操作了还一直重置)
        # 这里逻辑稍微调整：只要到了时间，强制弹窗，无论当前什么状态
        # 为了避免一分钟内重复触发，我们可以加个标志位，或者简单地每分钟只触发一次？
        # 为简化，这里每秒检查，如果当前不在前台/中央，则弹出。
        
        # 简单逻辑：如果到了 POPUP_TIME 且当前是 Mini 模式，则弹出。
        # 如果已经在 Full 模式，是否重置到中央？需求说“强制将窗口还原到屏幕中央”。
        
        if now == POPUP_TIME:
            # 只有当秒数为 00 时触发一次，避免一分钟内连续触发
            if datetime.now().second == 0:
                print(f"⏰ 时间到！触发提醒: {POPUP_TIME}")
                self.switch_to_full_center()
                self.focus_force()
                self.attributes("-topmost", True)

        self.after(1000, self.start_timer_check)

    def ensure_todo_file(self):
        if not TODO_PATH.exists():
            try:
                with open(TODO_PATH, "w", encoding="utf-8") as f:
                    f.write("Welcome to Ghost\n双击切换胶囊模式\n滚动滚轮切换任务\n")
            except: pass

    def on_closing(self):
        if hasattr(self, 'observer'):
            self.observer.stop()
            self.observer.join()
        self.destroy()

if __name__ == "__main__":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except: pass
    
    app = DesktopGhost()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()