"""A compact settings popover matching the desktop app's light palette."""
import tkinter as tk


class SettingsMenu:
    def __init__(self, root, button, rows, auto):
        self.root, self.button, self.rows, self.auto = root, button, rows, auto
        self.window = None
        self.actions = []
        self.outside_binding = root.bind('<ButtonPress-1>', self.outside, add='+')
        self.move_binding = root.bind('<Configure>', self.moved, add='+')
        button.bind('<Down>', lambda event: self.show())

    def toggle(self):
        self.close() if self.window else self.show()

    def show(self):
        if self.window:
            return
        win = self.window = tk.Toplevel(self.root)
        win.withdraw(); win.overrideredirect(True); win.transient(self.root)
        win.configure(bg='#E1E7F0')
        panel = tk.Frame(win, bg='white', padx=6, pady=6)
        panel.pack(fill='both', expand=True, padx=1, pady=1)
        self.actions = []
        for index, (label, command) in enumerate(self.rows):
            if index in (2, 3):
                tk.Frame(panel, height=1, bg='#E1E7F0').pack(fill='x', padx=8, pady=4)
            row = tk.Frame(panel, bg='white', height=42)
            row.pack(fill='x')
            action = tk.Button(row, text=label, command=lambda n=index: self.invoke(n),
                               font=('Microsoft YaHei UI', 10), anchor='w', padx=13, pady=10,
                               bg='white', fg='#1C2840', activebackground='#EDF3FF', activeforeground='#1D4DA2',
                               relief='flat', bd=0, highlightthickness=1, highlightbackground='white',
                               highlightcolor='#2863E8', cursor='hand2', takefocus=True)
            action.pack(fill='both', expand=True)
            action.bind('<Enter>', lambda event, b=action: b.configure(bg='#EDF3FF', highlightbackground='#EDF3FF'))
            action.bind('<Leave>', lambda event, b=action: b.configure(bg='white', highlightbackground='white'))
            action.bind('<Return>', lambda event, n=index: self.enter(n))
            self.actions.append(action)
            if index == 1:
                self.switch = tk.Canvas(row, width=34, height=20, bg='white', highlightthickness=0, cursor='hand2')
                self.switch.place(relx=1, x=-14, rely=.5, anchor='e')
                self.switch.bind('<Button-1>', lambda event: self.invoke(1))
                self.draw_switch()
        win.bind('<Escape>', lambda event: self.close(focus_button=True))
        win.bind('<Down>', lambda event: self.shift(1))
        win.bind('<Up>', lambda event: self.shift(-1))
        win.bind('<FocusOut>', lambda event: self.root.after_idle(self.check_focus))
        win.update_idletasks()
        width = 248
        height = win.winfo_reqheight()
        x = self.button.winfo_rootx() + self.button.winfo_width() - width
        y = self.button.winfo_rooty() + self.button.winfo_height() + 7
        x = max(0, min(x, win.winfo_screenwidth() - width))
        if y + height > win.winfo_screenheight():
            y = max(0, self.button.winfo_rooty() - height - 7)
        win.geometry(f'{width}x{height}+{x}+{y}')
        win.deiconify(); win.lift(); win.focus_force()

    def draw_switch(self):
        canvas = self.switch
        canvas.delete('all')
        color = '#2863E8' if self.auto.get() else '#CAD4E2'
        canvas.create_line(10, 10, 24, 10, width=18, fill=color, capstyle='round')
        x = 24 if self.auto.get() else 10
        canvas.create_oval(x-6, 4, x+6, 16, fill='white', outline='white')

    def invoke(self, index):
        command = self.rows[index][1]
        if index == 1:
            self.auto.set(not self.auto.get())
            command()
            if self.window:
                self.draw_switch()
        else:
            self.close()
            command()

    def shift(self, step):
        focused = self.root.focus_get()
        index = self.actions.index(focused) if focused in self.actions else (-1 if step > 0 else 0)
        self.actions[(index + step) % len(self.actions)].focus_set()
        return 'break'

    def check_focus(self):
        if self.window:
            focused = self.root.focus_get()
            if focused is None or focused.winfo_toplevel() != self.window:
                self.close()

    def enter(self, index):
        self.invoke(index)
        return 'break'

    def outside(self, event):
        if self.window and event.widget != self.button:
            self.close()

    def moved(self, event):
        if event.widget == self.root:
            self.close()

    def close(self, focus_button=False):
        if self.window:
            self.window.destroy()
            self.window = None
        if focus_button:
            self.button.focus_set()
