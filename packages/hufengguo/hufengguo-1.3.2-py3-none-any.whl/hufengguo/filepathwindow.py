from os.path import exists, isdir, isfile
from tkinter import Button, Entry, filedialog, Frame, Label, StringVar, Tk, Toplevel
from tkinter.messagebox import askyesno, showinfo
import sys

# 仅在 Windows 上尝试导入 windnd
if sys.platform == "win32":
    try:
        import windnd  # pip install windnd
        WINDND_AVAILABLE = True
    except ImportError:
        WINDND_AVAILABLE = False
        print("提示：未安装windnd库，拖拽功能不可用")
else:
    WINDND_AVAILABLE = False


class MyFilePathWindow:
    def __init__(self, title, file1flag=True, file2flag=True, parent=None):
        """
        初始化文件路径选择窗口
        
        Args:
            title: 窗口标题
            file1flag: 第一个路径是否为文件（True）或目录（False）
            file2flag: 第二个路径是否为文件（True）或目录（False）
            parent: 父窗口，如果为None则创建独立窗口
        """
        self.parent = parent
        self.file1flag = file1flag
        self.file2flag = file2flag
        
        # 根据是否有父窗口决定创建方式
        if parent is None:
            # 独立模式：创建主窗口
            self.root = Tk()
            self.root.withdraw()  # 隐藏主窗口
            self.window = Toplevel(self.root)
        else:
            # 集成模式：作为子窗口
            self.window = Toplevel(parent)
            self.root = None  # 不需要额外的root
        
        self.window.title(title)
        
        # 显示两个文本框的提示信息
        sdrag = "" if self.parent else "、拖拽"
        sfp1 = "文件" if self.file1flag else "目录"
        self.msg1 = f"请选择{sdrag}{sfp1}或输入{sfp1}全路径名到此文本框"
        sfp2 = "文件" if self.file2flag else "目录"
        self.msg2 = f"请选择{sdrag}{sfp2}或输入{sfp2}全路径名到此文本框"
        self.fnin_var = StringVar(value=self.msg1)
        self.fnout_var = StringVar(value=self.msg2)
        self.fnout_selected_value = None

        # 构建界面
        self._build_interface()

        # 窗口属性
        self.window.resizable(True, False)
        self.window.update_idletasks()
        self.window.minsize(self.window.winfo_width(), self.window.winfo_height())
        
        # 居中显示
        self._center_window()

        # 绑定关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self.on_cancel)

        # 拖拽支持（仅 Windows 且 windnd 可用时）
        self._setup_drag()

        # 常用文件类型
        self.filetypes = [
            ("文本文件", ".txt"),
            ("Python文件", ".py"),
            ("C/C++文件", (".c", ".cpp")),
            ("Word文件", (".docx", ".doc")),
            ("Excel文件", (".xlsx", ".xls")),
            ("PowerPoint文件", (".pptx", ".ppt")),
            ("PDF文件", "*.pdf"),
            ("图片文件", (".bmp", ".jpg", ".jpeg", ".png")),
            ("压缩文件", (".rar", ".zip", ".7z")),
            ("音频文件", (".mp3", ".m4a", ".wma", ".wav")),
            ("视频文件", (".mp4", ".wmv")),
            ("所有文件", "*.*"),
        ]

        self.result = (None, None)
        self._is_modal = False  # 标记是否为模态窗口

    def _build_interface(self):
        """构建界面组件"""
        # 输入路径
        frame1 = Frame(self.window)
        frame1.pack(fill="x", padx=10, pady=15)
        Label(frame1, text="输入文件：" if self.file1flag else "输入目录：").pack(side="left")
        self.entry1 = Entry(frame1, textvariable=self.fnin_var, width=50)
        self.entry1.pack(side="left", expand=True, fill="x", padx=5)
        Button(frame1, text="浏览…", command=self.open_file_read).pack(side="right")

        # 输出路径
        frame2 = Frame(self.window)
        frame2.pack(fill="x", padx=10, pady=0)
        Label(frame2, text="输出文件：" if self.file2flag else "输出目录：").pack(side="left")
        self.entry2 = Entry(frame2, textvariable=self.fnout_var, width=50)
        self.entry2.pack(side="left", expand=True, fill="x", padx=5)
        Button(frame2, text="浏览…", command=self.open_file_write).pack(side="right")

        # 确认和取消按钮
        frame3 = Frame(self.window, height=30)
        frame3.pack(pady=10, fill="x")
        frame3.pack_propagate(False)
        btn_ok = Button(frame3, text="确认选择", command=self.on_ok)
        btn_cancel = Button(frame3, text="取消选择", command=self.on_cancel)
        btn_ok.place(relx=1/3, rely=0.3, anchor="center")
        btn_cancel.place(relx=2/3, rely=0.3, anchor="center")

    def _center_window(self):
        """将窗口居中显示"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        
        if self.parent:
            # 相对于父窗口居中
            x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (width // 2)
            y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (height // 2)
        else:
            # 屏幕居中
            x = (self.window.winfo_screenwidth() // 2) - (width // 2)
            y = (self.window.winfo_screenheight() // 2) - (height // 2)
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def _setup_drag(self):
        """设置拖拽功能"""
        if not WINDND_AVAILABLE or self.parent is not None:
            return

        def dragged_in(files):
            path = files[0].decode("utf-8") if isinstance(files[0], bytes) else files[0]
            if self.file1flag:
                if isfile(path):
                    self.fnin_var.set(path)
                else:
                    showinfo("提醒", "要拖拽文件，不能拖拽目录")
            else:
                if isdir(path):
                    self.fnin_var.set(path)
                else:
                    showinfo("提醒", "要拖拽目录，不能拖拽文件")

        def dragged_out(files):
            path = files[0].decode("utf-8") if isinstance(files[0], bytes) else files[0]
            
            if self.file2flag:  # 需要文件
                if isdir(path):
                    showinfo("提醒", "要拖拽文件，不能拖拽目录")
                    return
            else:  # 需要目录
                if isfile(path):
                    showinfo("提醒", "要拖拽目录，不能拖拽文件")
                    return

            if exists(path):
                msg = "目录已经存在" if isdir(path) else "文件已经存在"
                if not askyesno(msg, "其中的数据可能会被覆盖，是否继续？"):
                    return
            self.fnout_var.set(path)
            self.fnout_selected_value = path

        try:
            windnd.hook_dropfiles(self.entry1, func=dragged_in, force_unicode=True)
            windnd.hook_dropfiles(self.entry2, func=dragged_out, force_unicode=True)
        except Exception as e:
            print(f"拖拽功能初始化失败: {e}")

    def open_file_read(self):
        """打开输入文件/目录"""
        if self.file1flag:
            path = filedialog.askopenfilename(
                title="选择一个要读取的文件",
                initialdir="/",
                filetypes=self.filetypes
            )
        else:
            path = filedialog.askdirectory(
                title="选择一个要读取的目录",
                initialdir="/"
            )
        if path:
            self.fnin_var.set(path)

    def open_file_write(self):
        """打开输出文件/目录"""
        if self.file2flag:
            path = filedialog.asksaveasfilename(
                title="选择一个要保存的文件",
                initialdir="/",
                filetypes=self.filetypes
            )
            self.fnout_var.set(path)
        else:
            path = filedialog.askdirectory(
                title="选择一个要保存的目录",
                initialdir="/"
            )
            if path:
                # 检查目录是否已存在
                if isdir(path):
                    if not askyesno("目录已经存在", "该目录下的数据可能会被覆盖，是否继续？"):
                        return
                self.fnout_var.set(path)
                self.fnout_selected_value = path

    def on_ok(self):
        """确认按钮事件"""
        fnin = self.fnin_var.get()
        fnout = self.fnout_var.get()

        # 判断两个文本框是否为空
        if fnin == self.msg1 or fnout == self.msg2:
            showinfo("提示", "请填写有效的路径！")
            return
        
        # 判断输入路径
        if not exists(fnin):
            showinfo("提示", ("输入文件" if self.file1flag else "输入目录") + "不存在！")
            return
        else:
            if self.file1flag and isdir(fnin):
                showinfo("提示", f"路径 {fnin} 应该是一个文件，不能是一个目录！")
                return
            if not self.file1flag and isfile(fnin):
                showinfo("提示", f"路径 {fnin} 应该是一个目录，不能是一个文件！")
                return

        # 判断输出路径
        if exists(fnout):
            if self.file2flag:
                if isdir(fnout):
                    showinfo("提示", f"路径 {fnout} 应该是一个文件，不能是一个已经存在的目录！")
                    return
                else:
                    if self.fnout_selected_value != fnout:
                        if not askyesno("警告", f"文件 {fnout} 已经存在，\n该文件中的数据可能会被覆盖，是否继续？"):
                            return
            else:
                if isfile(fnout):
                    showinfo("提示", f"路径 {fnout} 应该是一个目录，不能是一个已经存在的文件！")
                    return
                else:
                    if self.fnout_selected_value != fnout:
                        if not askyesno("警告", f"目录 {fnout} 已经存在，\n该目录下的数据可能会被覆盖，是否继续？"):
                            return
            
        self.result = (fnin, fnout)
        
        if self._is_modal:
            self.window.destroy()
        else:
            self.window.destroy()
            if self.root:
                self.root.quit()

    def on_cancel(self):
        """取消按钮事件"""
        self.result = (None, None)
        if self._is_modal:
            self.window.destroy()
        else:
            self.window.destroy()
            if self.root:
                self.root.quit()

    def show(self):
        """
        统一入口：自动判断独立模式或集成模式
        
        - 若 parent=None：独立模式，创建自己的 Tk 主窗口
        - 若 parent!=None：集成模式，作为模态对话框嵌入
        
        返回 (fnin, fnout) 或 (None, None)
        """
        if self.parent is None:
            # ===== 独立模式 =====
            self._is_modal = False
            self.root.mainloop()
            self.root.destroy()
            return self.result
        else:
            # ===== 集成模式 =====
            self._is_modal = True
            
            # 关键修复：在 Windows 上不调用 transient()，避免窗口不显示在任务栏
            if sys.platform != "win32":
                self.window.transient(self.parent)
            
            self.window.grab_set()      # 模态锁定
            self.window.wait_window()   # 等待关闭
            return self.result


