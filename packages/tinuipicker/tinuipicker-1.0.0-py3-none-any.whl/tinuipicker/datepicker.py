from tkinter import Tk
import calendar
from datetime import datetime

from tinui import BasicTinUI
from tinui.TinUI import TinUIString


pickerlight = {
    'fg':'#1b1b1b','bg':'#fbfbfb',
    'outline':'#ececec','activefg':'#1b1b1b',
    'activebg':'#f6f6f6','onfg':'#eaecfb','onbg':'#0067C0',
    'buttonfg':'#1a1a1a','buttonbg':'#fbfbfb',
    'buttonactivefg':'#1a1a1a','buttonactivebg':'#f0f0f0',
    'buttononfg':'#1a1a1a','buttononbg':'#f3f3f3',
}

pickerdark = {
    'fg':'#cfcfcf','bg':'#2d2d2d','outline':'#3c3c3c',
    'activefg':'#ffffff','activebg':'#323232',
    'onfg':'#000000','onbg':'#4CC2FF',
    'buttonfg':'#ffffff','buttonbg':'#2d2d2d',
    'buttonactivefg':'#ffffff','buttonactivebg':'#383838',
    'buttononfg':'#ffffff','buttononbg':'#343434',
}


class TinUIDatePicker:
    def __init__(self, tinui, pos, font=("微软雅黑", 10), command=None, 
                 year_range=(2000, 2030), now=datetime.today(), anchor='nw', **kwargs):
        self.self = tinui  # 这里的 self 是 BasicTinUI 实例
        self.pos = pos
        self.font = font
        self.command = command
        self.year_range = year_range
        self.anchor = anchor
        
        # 继承源码中的默认配色
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

        self.res_year, self.res_month, self.res_day = str(now.year), str(now.month).zfill(2), str(now.day).zfill(2)
        
        # 1. 绘制触发器 (完全复刻源码的 polygon 逻辑)
        self._build_trigger()

        # 2. 预先初始化弹出窗口及其内部组件 (只做一次)
        self._setup_picker_ui()

    def _build_trigger(self):
        # 计算文本尺寸以确定外框大小
        temp_text = f"{self.res_year}-{self.res_month}-{self.res_day}"
        txtest = self.self.create_text(self.pos, text=temp_text, font=self.font)
        bbox = self.self.bbox(txtest)
        self.self.delete(txtest)
        
        tw, th = bbox[2]-bbox[0] + 10, bbox[3]-bbox[1] + 10
        x, y = self.pos
        
        # 源码风格的圆角边框 (通过 polygon 和 width=9 模拟)
        self.out_line = self.self.create_polygon(
            (x, y, x+tw, y, x+tw, y+th, x, y+th), 
            fill=self.cfg['outline'], outline=self.cfg['outline'], width=9
        )
        self.back = self.self.create_polygon(
            (x+1, y+1, x+tw-1, y+1, x+tw-1, y+th-1, x+1, y+th-1),
            fill=self.cfg['bg'], outline=self.cfg['bg'], width=9
        )
        self.main_text = self.self.create_text(
            (x + tw/2, y + th/2), text=temp_text, fill=self.cfg['fg'], font=self.font
        )
        
        # 绑定事件
        uid = f"datepicker-{self.main_text}"
        self.uid = TinUIString(uid)
        for i in (self.out_line, self.back, self.main_text):
            self.self.addtag_withtag(uid, i)
            
        self.self.tag_bind(uid, "<Enter>", lambda e: self.self.itemconfig(self.back, fill=self.cfg['activebg'], outline=self.cfg['activebg']))
        self.self.tag_bind(uid, "<Leave>", lambda e: self.self.itemconfig(self.back, fill=self.cfg['bg'], outline=self.cfg['bg']))
        self.self.tag_bind(uid, "<Button-1>", self.show)

        self.self._BasicTinUI__auto_anchor(uid, self.pos, self.anchor)
        self.uid.layout = lambda x1, y1, x2, y2, expand=False: self.self._BasicTinUI__auto_layout(
            uid, (x1, y1, x2, y2), self.anchor
        )

    def _loaddata(self, box, items, mw, col_type):
        """刷新指定列的内容"""
        box.delete("all")
        box.choices = {}
        y_ptr = 5
        for i in items:
            text_id = box.create_text((self.col_widths[col_type]/2, y_ptr + 2), text=i, fill=self.cfg['fg'], font=self.font, anchor="n")
            bbox = box.bbox(text_id)
            back_id = box.create_rectangle((3, bbox[1] - 4, 3 + mw, bbox[3] + 4), width=0, fill=self.cfg['bg'])
            box.tkraise(text_id)
            
            # 记录并标记初始选中
            is_sel = (i == box.newres)
            if is_sel:
                self.sel_backs[col_type] = back_id
                box.itemconfig(back_id, fill=self.cfg['onbg'])
                box.itemconfig(text_id, fill=self.cfg['onfg'])

            box.choices[text_id] = [i, text_id, back_id, is_sel]
            
            for tid in (text_id, back_id):
                box.tag_bind(tid, "<Button-1>", lambda e, t=text_id, b=box, ct=col_type: self._pick_sel_it(b, t, ct))
                box.tag_bind(tid, "<Enter>", lambda e, t=text_id, b=box: self._pick_mouse(b, t, True))
                box.tag_bind(tid, "<Leave>", lambda e, t=text_id, b=box: self._pick_mouse(b, t, False))
            y_ptr = bbox[3] + 8
        
        box.config(scrollregion=box.bbox("all"))
        box.bind("<MouseWheel>", lambda e: box.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    def _pick_mouse(self, box, t, is_enter):
        """处理悬停效果"""
        data = box.choices[t] # [val, txt, back, is_sel]
        if data[3]: return # 已选中不处理
        color = self.cfg['activebg'] if is_enter else self.cfg['bg']
        box.itemconfig(data[2], fill=color)

    def _pick_sel_it(self, box, t, col_type):
        """处理点击选中"""
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
        # 年月变动刷新日
        if col_type < 2:
            self._update_days()

    def _update_days(self):
        y, m = self.pickerbars[0].newres, self.pickerbars[1].newres
        days = [str(d).zfill(2) for d in range(1, calendar.monthrange(int(y), int(m))[1] + 1)]
        # 如果之前的日期超限（如31号变30号），重置为最后一天
        if int(self.pickerbars[2].newres) > len(days):
            self.pickerbars[2].newres = days[-1]
        self._loaddata(self.pickerbars[2], days, 60, 2)

    def _setup_picker_ui(self):
        """核心：一次性初始化 Toplevel 窗口和三列选择器"""
        width, height = 230, 260
        # 调用 TinUI 私有方法创建顶层窗口
        self.picker, self.bar = self.self._BasicTinUI__ui_toplevel(width, height, "#01FF11", lambda e: self.picker.withdraw())
        self.picker.bind("<Escape>", lambda e: self.picker.withdraw())
        self.picker.bind("<FocusOut>", lambda e: self.picker.withdraw())
        
        # 绘制背景
        self.bar._BasicTinUI__ui_polygon(((13, 13), (width - 13, height - 11)), fill=self.cfg['bg'], outline=self.cfg['bg'], width=17)
        self.bar.lower(self.bar._BasicTinUI__ui_polygon(((12, 12), (width - 12, height - 10)), fill=self.cfg['outline'], outline=self.cfg['outline'], width=17))

        # 选中的背景元素
        self.sel_backs = [None, None, None]

        self.pickerbars = []
        self.col_widths = [80, 60, 60]
        curr_x = 8
        for i in range(3):
            # 每一列都是一个 BasicTinUI 画布
            pb = BasicTinUI(self.picker, bg=self.cfg['bg'], highlightthickness=0)
            pb.place(x=curr_x, y=10, width=self.col_widths[i], height=height - 60)
            pb.newres = [self.res_year, self.res_month, self.res_day][i]
            pb.choices = {}
            self.pickerbars.append(pb)
            curr_x += self.col_widths[i] + 5

        self._build_buttons(self.bar, width, height)
        # 初始化静态数据：年、月
        years = [str(y) for y in range(self.year_range[0], self.year_range[1]+1)]
        months = [str(m).zfill(2) for m in range(1, 13)]
        self._loaddata(self.pickerbars[0], years, 80, 0)
        self._loaddata(self.pickerbars[1], months, 60, 1)

        # 屏幕最大尺寸
        self.maxx = self.self.winfo_screenwidth()
        self.maxy = self.self.winfo_screenheight()

    def show(self, event):
        """只负责定位和显示"""
        # 根据当前年月刷新“日”列表 (处理闰年)
        self._update_days()

        # 选中项居中
        for i in range(3):
            bbox = self.pickerbars[i].bbox(self.sel_backs[i])
            centery = (bbox[1] + bbox[3]) / 2
            view_centery = self.pickerbars[i].winfo_height() / 2
            scroll_region = self.pickerbars[i].cget("scrollregion").split()
            scroll_y1, scroll_y2 = int(scroll_region[1]), int(scroll_region[3])
            total_height = scroll_y2 - scroll_y1
            self.pickerbars[i].yview_moveto((centery - view_centery)/total_height)
        
        # 计算显示位置 (复刻源码 show)
        bbox = self.self.bbox(self.out_line)
        sx, sy = event.x_root - (event.x - bbox[0]), event.y_root - (event.y - bbox[3])
        if sx+240 > self.maxx:
            sx = self.maxx-240
        if sy+275 > self.maxy:
            sy = self.maxy-275
        
        # 动画显示
        self.picker.geometry(f"240x275+{int(sx)-3}+{int(sy)}")
        self.picker.attributes("-alpha", 0)
        self.picker.deiconify()
        self.picker.focus_set()
        for i in range(1, 11):
            self.picker.after(i * 20, lambda a=i/10: self.picker.attributes("-alpha", a))

    def _build_buttons(self, bar, width, height):
        # 确定按钮 (\ue73e)
        ok = bar.add_button2(((width-9)/4, height-22), text="\ue73e", font="{Segoe Fluent Icons} 12",
            fg=self.cfg['buttonfg'], bg=self.cfg['buttonbg'], line='',
            activefg=self.cfg['buttonactivefg'], activebg=self.cfg['buttonactivebg'], activeline=self.cfg['outline'],
            onfg=self.cfg['buttononfg'], onbg=self.cfg['buttononbg'], online=self.cfg['buttononbg'],
            command=self._confirm, anchor="center")
        # 取消按钮 (\ue711)
        no = bar.add_button2((3*(width-9)/4, height-22), text="\ue711", font="{Segoe Fluent Icons} 12",
            fg=self.cfg['buttonfg'], bg=self.cfg['buttonbg'], line='',
            activefg=self.cfg['buttonactivefg'], activebg=self.cfg['buttonactivebg'], activeline=self.cfg['outline'],
            onfg=self.cfg['buttononfg'], onbg=self.cfg['buttononbg'], online=self.cfg['buttononbg'],
            command=lambda e: self.picker.withdraw(), anchor="center")
        
        # 调整按钮背景框 (源码中的 coords 调整逻辑)
        mid = (width - 9) / 2
        bar.coords(ok[1], (9, height-35, mid-5, height-35, mid-5, height-9, 9, height-9))
        bar.coords(ok[2], (8, height-34, mid-4, height-34, mid-4, height-8, 8, height-8))
        bar.coords(no[1], (mid+5, height-35, width-9, height-35, width-9, height-9, mid+5, height-9))
        bar.coords(no[2], (mid+4, height-34, width-8, height-34, width-8, height-8, mid+4, height-8))

    def _confirm(self, e=None):
        self.res_year = self.pickerbars[0].newres
        self.res_month = self.pickerbars[1].newres
        self.res_day = self.pickerbars[2].newres
        
        full_date = f"{self.res_year}-{self.res_month}-{self.res_day}"
        self.self.itemconfig(self.main_text, text=full_date)
        if self.command:
            self.command(full_date)
        self.picker.withdraw()


if __name__ == "__main__":
    from tinui import ExpandPanel, HorizonPanel
    root = Tk()
    root.geometry('400x400')

    ui = BasicTinUI(root)
    ui.pack(fill='both', expand=True)
    tdp = TinUIDatePicker(ui, (10,10), font=("Segoe UI", 12), now=datetime(2026, 2, 19), command=print, anchor='center', **pickerlight)

    rp = ExpandPanel(ui)
    hp = HorizonPanel(ui)
    rp.set_child(hp)
    hp.add_child(tdp.uid, 150)

    ep = ExpandPanel(ui)
    hp.add_child(ep, weight=1)
    # ep.set_child(tdp.uid)

    def update(e):
        rp.update_layout(5,5,e.width-5,e.height-5)
    ui.bind('<Configure>',update)

    root.mainloop()