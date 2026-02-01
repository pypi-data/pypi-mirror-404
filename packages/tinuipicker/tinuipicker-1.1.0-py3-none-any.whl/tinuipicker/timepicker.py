from datetime import datetime
from itertools import islice

from tinui import BasicTinUI
from tinui.TinUI import TinUIString


class TinUITimePicker:
    def __init__(self, tinui, pos, font=("微软雅黑", 10), is_24h=True, now = datetime.now(), command=None, anchor='nw', **kwargs):
        self.self = tinui
        self.pos = pos
        self.font = font
        self.is_24h = is_24h
        self.command = command
        self.anchor = anchor
        
        # 样式配置（复刻源码颜色）
        self.cfg = {
            "fg": kwargs.get("fg", "#1b1b1b"),
            "bg": kwargs.get("bg", "#fbfbfb"),
            "outline": kwargs.get("outline", "#ececec"),
            "activefg": kwargs.get("activefg", "#1b1b1b"),
            "activebg": kwargs.get("activebg", "#f6f6f6"),
            "onbg": kwargs.get("onbg", "#3748d9"),
            "onfg": kwargs.get("onfg", "#eaecfb"),
            "buttonfg": kwargs.get("buttonfg", "#1a1a1a"),
            "buttonbg": kwargs.get("buttonbg", "#f9f9f9"),
            "buttonactivefg": kwargs.get("buttonactivefg", "#1a1a1a"),
            "buttonactivebg": kwargs.get("buttonactivebg", "#f3f3f3"),
            "buttononfg": kwargs.get("buttononfg", "#5d5d5d"),
            "buttononbg": kwargs.get("buttononbg", "#f5f5f5"),
        }

        # 初始数值逻辑
        
        if self.is_24h:
            self.res_hour = str(now.hour).zfill(2)
            self.res_ampm = ""
        else:
            h = now.hour
            self.res_ampm = "AM" if h < 12 else "PM"
            h12 = h % 12
            self.res_hour = str(12 if h12 == 0 else h12).zfill(2)
            
        self.res_minute = str(now.minute).zfill(2)
        self.res_second = str(now.second).zfill(2)

        # 1. 绘制主画布触发器
        self._build_trigger()
        # 2. 初始化弹出窗口 (单次构建)
        self._setup_picker_ui()

    def _get_time_str(self):
        """生成显示的格式化字符串"""
        base = f"{self.res_hour}:{self.res_minute}:{self.res_second}"
        return f"{self.res_ampm} {base}".strip()

    def _build_trigger(self):
        """在主画布创建带圆角的触发框"""
        time_text = self._get_time_str()
        txtest = self.self.create_text(self.pos, text=time_text, font=self.font)
        bbox = self.self.bbox(txtest)
        self.self.delete(txtest)
        
        tw, th = bbox[2]-bbox[0] + 10, bbox[3]-bbox[1] + 10
        x, y = self.pos
        
        # 使用源码 polygon + width=9 模拟圆角
        self.out_line = self.self.create_polygon((x,y, x+tw,y, x+tw,y+th, x,y+th), fill=self.cfg['outline'], outline=self.cfg['outline'], width=9)
        self.back = self.self.create_polygon((x+1,y+1, x+tw-1,y+1, x+tw-1,y+th-1, x+1,y+th-1), fill=self.cfg['bg'], outline=self.cfg['bg'], width=9)
        self.main_text = self.self.create_text((x + tw/2, y + th/2), text=time_text, fill=self.cfg['fg'], font=self.font)

        uid = f"timepicker-{self.main_text}"
        self.uid = TinUIString(uid)
        for i in (self.out_line, self.back, self.main_text): self.self.addtag_withtag(uid, i)
        self.self.tag_bind(uid, "<Enter>", lambda e: self.self.itemconfig(self.back, fill=self.cfg['activebg'], outline=self.cfg['activebg']))
        self.self.tag_bind(uid, "<Leave>", lambda e: self.self.itemconfig(self.back, fill=self.cfg['bg'], outline=self.cfg['bg']))
        self.self.tag_bind(uid, "<Button-1>", self.show)

        self.self._BasicTinUI__auto_anchor(uid, self.pos, self.anchor)
        self.uid.layout = lambda x1, y1, x2, y2, expand=False: self.self._BasicTinUI__auto_layout(
            uid, (x1, y1, x2, y2), self.anchor
        )

    def _setup_picker_ui(self):
        """初始化 Toplevel 弹出层及其内部选择列"""
        # 根据制式动态计算宽度
        col_widths = [50, 60, 60, 60] if not self.is_24h else [60, 60, 60]
        width = sum(col_widths) + (len(col_widths) * 3) + 12
        height = 260
        
        self.picker, self.bar = self.self._BasicTinUI__ui_toplevel(width, height, "#01FF11", lambda e: self.picker.withdraw())
        self.picker.bind("<Escape>", lambda e: self.picker.withdraw())
        self.picker.bind("<FocusOut>", lambda e: self.picker.withdraw())

        # 绘制背景框
        self.bar._BasicTinUI__ui_polygon(((13, 13), (width - 13, height - 11)), fill=self.cfg['bg'], outline=self.cfg['bg'], width=17)
        self.bar.lower(self.bar._BasicTinUI__ui_polygon(((12, 12), (width - 12, height - 10)), fill=self.cfg['outline'], outline=self.cfg['outline'], width=17))

        # 选中的背景元素
        self.sel_backs = []

        # 数据集准备
        data_sets = []
        if not self.is_24h:
            data_sets.append(["AM", "PM"]) # AM/PM 列
            data_sets.append([str(h).zfill(2) for h in range(1, 13)]) # 12小时
        else:
            data_sets.append([str(h).zfill(2) for h in range(0, 24)]) # 24小时
            
        data_sets.append([str(m).zfill(2) for m in range(0, 60)]) # 分
        data_sets.append([str(s).zfill(2) for s in range(0, 60)]) # 秒

        self.pickerbars = []
        curr_x = 8
        initial_vals = ([self.res_ampm, self.res_hour] if not self.is_24h else [self.res_hour]) + [self.res_minute, self.res_second]

        for i, items in enumerate(data_sets):
            pb = self.self.__class__(self.picker, bg=self.cfg['bg'], highlightthickness=0)
            pb.place(x=curr_x, y=10, width=col_widths[i], height=height - 60)
            pb.newres = initial_vals[i]
            self.pickerbars.append(pb)
            self._loaddata(pb, items, col_widths[i], i)
            curr_x += col_widths[i] + 3

        self._build_buttons(self.bar, width, height)

        # 最大屏幕尺寸
        self.maxx = self.self.winfo_screenwidth()
        self.maxy = self.self.winfo_screenheight()

    def _loaddata(self, box, items, mw, col_type):
        """填充列数据并绑定滚动与点击"""
        box.delete("all")
        box.choices = {}
        y_ptr = 5
        for i in items:
            text_id = box.create_text((mw/2, y_ptr + 2), text=i, fill=self.cfg['fg'], font=self.font, anchor="n")
            bbox = box.bbox(text_id)
            back_id = box.create_rectangle((3, bbox[1] - 4, 3 + mw - 6, bbox[3] + 4), width=0, fill=self.cfg['bg'])
            box.tkraise(text_id)
            
            is_sel = (i == box.newres)
            if is_sel:
                self.sel_backs.append(back_id)
                box.itemconfig(back_id, fill=self.cfg['onbg'])
                box.itemconfig(text_id, fill=self.cfg['onfg'])

            box.choices[text_id] = [i, text_id, back_id, is_sel]
            
            for tid in (text_id, back_id):
                box.tag_bind(tid, "<Button-1>", lambda e, t=text_id, b=box: self._pick_sel_it(b, t, col_type))
                box.tag_bind(tid, "<Enter>", lambda e, t=text_id, b=box: self._pick_mouse(b, t, True))
                box.tag_bind(tid, "<Leave>", lambda e, t=text_id, b=box: self._pick_mouse(b, t, False))
            y_ptr = bbox[3] + 8
        
        box.config(scrollregion=box.bbox("all"))
        box.bind("<MouseWheel>", lambda e: box.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    def _pick_mouse(self, box, t, is_enter):
        data = box.choices[t]
        if not data[3]:
            box.itemconfig(data[2], fill=self.cfg['activebg'] if is_enter else self.cfg['bg'])

    def _pick_sel_it(self, box, t, col_type):
        """切换选中项视觉效果"""
        for tid, data in box.choices.items():
            data[3] = (tid == t)
            if data[3]:
                fill_bg = self.cfg['onbg']
                fill_fg = self.cfg['onfg']
                self.sel_backs[col_type] = data[2]
            else:
                fill_bg = self.cfg['bg']
                fill_fg = self.cfg['fg']
            box.itemconfig(data[2], fill=fill_bg)
            box.itemconfig(data[1], fill=fill_fg)
        box.newres = box.choices[t][0]

    def _build_buttons(self, bar, width, height):
        """创建确定/取消按钮，使用 Fluent 图标字符"""
        mid = (width - 9) / 2
        ok = bar.add_button2((mid/2 + 4, height-22), text="\ue73e", font="{Segoe Fluent Icons} 12",
            fg=self.cfg['buttonfg'], bg=self.cfg['buttonbg'], line='',
            activefg=self.cfg['buttonactivefg'], activebg=self.cfg['buttonactivebg'], activeline=self.cfg['outline'],
            onfg=self.cfg['buttononfg'], onbg=self.cfg['buttononbg'], online=self.cfg['buttononbg'],
            command=self._confirm, anchor="center")
        no = bar.add_button2((mid + mid/2 + 4, height-22), text="\ue711", font="{Segoe Fluent Icons} 12",
            fg=self.cfg['buttonfg'], bg=self.cfg['buttonbg'], line='',
            activefg=self.cfg['buttonactivefg'], activebg=self.cfg['buttonactivebg'], activeline=self.cfg['outline'],
            onfg=self.cfg['buttononfg'], onbg=self.cfg['buttononbg'], online=self.cfg['buttononbg'],
            command=lambda e: self.picker.withdraw(), anchor="center")
        
        # 调整背景色块坐标，使其平铺底部
        bar.coords(ok[1], (9, height-35, mid-5, height-35, mid-5, height-9, 9, height-9))
        bar.coords(ok[2], (8, height-34, mid-4, height-34, mid-4, height-8, 8, height-8))
        bar.coords(no[1], (mid+5, height-35, width-9, height-35, width-9, height-9, mid+5, height-9))
        bar.coords(no[2], (mid+4, height-34, width-8, height-34, width-8, height-8, mid+4, height-8))

    def show(self, event):
        """动画显示弹出框"""
        # 选中项居中
        for i in range(len(self.pickerbars)):
            bbox = self.pickerbars[i].bbox(self.sel_backs[i])
            centery = (bbox[1] + bbox[3]) / 2
            view_centery = self.pickerbars[i].winfo_height() / 2
            scroll_region = self.pickerbars[i].cget("scrollregion").split()
            scroll_y1, scroll_y2 = int(scroll_region[1]), int(scroll_region[3])
            total_height = scroll_y2 - scroll_y1
            self.pickerbars[i].yview_moveto((centery - view_centery)/total_height)

        bbox = self.self.bbox(self.out_line)
        sx, sy = event.x_root - (event.x - bbox[0]), event.y_root - (event.y - bbox[3])
        
        self.picker.geometry(f"+{int(sx)-3}+{int(sy)}")
        self.picker.attributes("-alpha", 0)
        self.picker.deiconify()
        self.picker.focus_set()
        # 淡入动画
        for i in range(1, 11):
            self.picker.after(i * 20, lambda a=i/10: self.picker.attributes("-alpha", a))

    def _confirm(self, e=None):
        """保存结果并更新界面"""
        vals = [pb.newres for pb in self.pickerbars]
        if self.is_24h:
            self.res_hour, self.res_minute, self.res_second = vals
        else:
            self.res_ampm, self.res_hour, self.res_minute, self.res_second = vals
            
        full_time = self._get_time_str()
        self.self.itemconfig(self.main_text, text=full_time)
        if self.command: self.command(full_time)
        self.picker.withdraw()
    
    def set_time(self, hour:int=None, minute:int=None, second:int=None):
        base_index = 0 if self.is_24h else 1
        if hour is not None:
            if not self.is_24h:
                if hour > 12:
                    hour -= 12
                    _, t, _, _ = next(islice(self.pickerbars[0].choices.values(), 1, 2))
                else:
                    _, t, _, _ = next(islice(self.pickerbars[0].choices.values(), 0, 1))
                self._pick_sel_it(self.pickerbars[0], t, 0)
            _, t, _, _ = next(islice(self.pickerbars[base_index].choices.values(), hour-1, hour))
            self._pick_sel_it(self.pickerbars[base_index], t, base_index)
        if minute is not None:
            index = minute
            _, t, _, _ = next(islice(self.pickerbars[base_index+1].choices.values(), index, index+1))
            self._pick_sel_it(self.pickerbars[base_index+1], t, base_index+1)
        if second is not None:
            index = second
            _, t, _, _ = next(islice(self.pickerbars[base_index+2].choices.values(), index, index+1))
            self._pick_sel_it(self.pickerbars[base_index+2], t, base_index+2)
        self._confirm()


if __name__ == "__main__":
    from tkinter import Tk
    from tinui import ExpandPanel, HorizonPanel
    root = Tk()
    root.geometry('400x400')

    ui = BasicTinUI(root)
    ui.pack(fill='both', expand=True)
    ttp = TinUITimePicker(ui, (10,10), font=("Segoe UI", 12), is_24h=False, now=datetime(1,1,1,6,23,45), command=print, anchor='center')
    ttp.set_time(16,0,19)

    rp = ExpandPanel(ui)
    hp = HorizonPanel(ui)
    rp.set_child(hp)
    hp.add_child(ttp.uid, 150)

    ep = ExpandPanel(ui)
    hp.add_child(ep, weight=1)
    # ep.set_child(tdp.uid)

    def update(e):
        rp.update_layout(5,5,e.width-5,e.height-5)
    ui.bind('<Configure>',update)

    root.mainloop()
