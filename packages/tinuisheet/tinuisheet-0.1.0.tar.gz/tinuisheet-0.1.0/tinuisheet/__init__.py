from tinui import BasicTinUI
from tinui.TinUI import TinUIString

class TinUISheet:
	ui:BasicTinUI = None
	uid:TinUIString = None
	titles = [] # [[item, back, width, x, tag],...]
	data = [] # [[[item, back, tag, level],...],...]
	endy = 0
	selected = -1
	selected_item = None

	def __init__(self, ui:BasicTinUI, pos:tuple, width=300, height=300, minwidth=100, maxwidth=300, font=('微软雅黑', 12),
			     fg='black', bg='white', itemfg='#1a1a1a', itembg='#f9f9f9', headbg='#f0f0f0',
				 itemactivefg='#191919', itemactivebg='#f0f0f0', itemonfg='#191919', itemonbg='#e0e0e0',
				 headfont=('微软雅黑', 14),
				 anchor='nw'):
		self.ui = ui
		self.width = width
		self.height = height
		self.fg = fg
		self.bg = bg
		self.headbg = headbg
		self.itemfg = itemfg
		self.itembg = itembg
		self.itemactivefg = itemactivefg
		self.itemactivebg = itemactivebg
		self.itemonfg = itemonfg
		self.itemonbg = itemonbg
		self.font = font
		self.headfont = headfont
		self.minwidth = minwidth
		self.maxwidth = maxwidth

		self.box = BasicTinUI(ui, bg=bg)
		uid = ui.create_window(pos, window = self.box, width=width-8, height=height-8, anchor=anchor)
		self._ui = uid
		self.uid = TinUIString(f"tinuisheet-{uid}")
		ui.addtag_withtag(self.uid, uid)

		bbox = ui.bbox(uid)
		self.scv = ui.add_scrollbar((bbox[2], bbox[1]), self.box, bbox[3]-bbox[1], "y")[-1]
		ui.addtag_withtag(self.uid, self.scv)
		self.sch = ui.add_scrollbar((bbox[0], bbox[3]), self.box, bbox[2]-bbox[0], "x")[-1]
		ui.addtag_withtag(self.uid, self.sch)

		back = ui.add_back((), (self.uid,), fg=bg, bg=bg, linew=0)
		ui.addtag_withtag(self.uid, back)

		self.box.bind("<MouseWheel>", self.__scroll)
		self.__scroll_region()
	
	def __scroll(self, event):
		if event.delta > 0:
			if event.state & 1:
				self.box.xview_scroll(-1, 'units')
			else:
				self.box.yview_scroll(-1, 'units')
		else:
			if event.state & 1:
				self.box.xview_scroll(1, 'units')
			else:
				self.box.yview_scroll(1, 'units')

	def __scroll_region(self):
		bbox = self.box.bbox('all')
		if not bbox:
			self.ui.itemconfig(self._ui, width = self.width, height = self.height)
			return
		self.box.config(scrollregion = bbox)
		if bbox[2]-bbox[0] < self.width:
			self.ui.itemconfig(self._ui, height = self.height)
		else:
			self.ui.itemconfig(self._ui, height = self.height-8)
		if bbox[3]-bbox[1] < self.height:
			self.ui.itemconfig(self._ui, width = self.width)
		else:
			self.ui.itemconfig(self._ui,width = self.width-8)
	
	def __move_nw(self, tag, pos):
		bbox = self.box.bbox(tag)
		if not bbox:
			return
		x, y = pos
		dx = x - bbox[0]
		dy = y - bbox[1]
		self.box.move(tag, dx, dy)
		return dx, dy

	def set_heads(self, heads):
		if self.titles and heads.__len__() != self.titles.__len__():
			# 标题已经存在时，不能直接修改标题数量
			raise ValueError("new heads count must be equal to old heads count")
		for item, back, _, _, tag in self.titles:
			self.box.delete(item)
			self.box.delete(back)
			self.box.dtag(tag)
		self.titles.clear()

		x = 0
		for head in heads:
			this_width = self.maxwidth
			_this_width = this_width
			if isinstance(head, str):
				title = head
				_this_width = self.minwidth
			elif isinstance(head, dict):
				title = head.get('title', '')
				this_width = head.get('width', self.maxwidth)
			else:
				raise ValueError("head must be str or dict")
			item = self.box.add_paragraph((x,0), title, fg=self.fg, width=this_width, font=self.headfont)
			tag = f'tinuisheet-head-{item}'
			self.box.addtag_withtag(tag, item)
			bbox = self.box.bbox(item)
			width = min(this_width, max(bbox[2]-bbox[0], _this_width))
			height = bbox[3]-bbox[1]
			backbbox = (x, 3, x+width, 3, x+width, height-3, x, height-3)
			back = self.box.create_polygon(backbbox, fill=self.headbg, outline=self.headbg, width=9, tags=tag)
			self.box.tag_raise(item)			
			dx, _ = self.__move_nw(tag, (x,0))
			self.titles.append([item, back, width, x+dx, tag])
			bbox = self.box.bbox(tag)
			x = bbox[2]+1
			self.endy = max(self.endy, bbox[3]+4)
		
		self.__scroll_region()
	
	def set_head(self, index:int, head):
		if index >= self.titles.__len__():
			raise ValueError("index out of range")
		
		_this_width = this_width = self.maxwidth
		if isinstance(head, str):
			title = head
			_this_width = self.minwidth
		elif isinstance(head, dict):
			title = head.get('title', '')
			this_width = head.get('width', self.maxwidth)
		else:
			raise ValueError("head must be str or dict")
		item = self.titles[index][0]
		self.box.itemconfig(item, text=title, width=this_width)
		bbox = self.box.bbox(item)
		width = min(this_width, max(bbox[2]-bbox[0], _this_width))
		# height = bbox[3]-bbox[1] # 暂不考虑高度重绘
		x = self.titles[index][3]
		coords = self.box.coords(self.titles[index][1])
		coords[2] = coords[4] = x+width
		self.box.coords(self.titles[index][1], coords)
		dx = self.titles[index][2] - width
		self.titles[index][2] = width
		self.__move_left(index+1, dx)

		for items in self.data:
			item = items[index]
			self.box.itemconfig(item[0], width=width)
			coords = self.box.coords(item[1])
			coords[2] = coords[4] = x+width
			self.box.coords(item[1], coords)

		self.__scroll_region()
	
	def __line_enter(self, this_list):
		item, back, _, level = this_list
		if level == self.selected:
			return
		self.box.itemconfig(item, fill=self.itemonfg)
		self.box.itemconfig(back, fill=self.itemonbg, outline=self.itemonbg)
		for i, b, _, _ in self.data[level]:
			if b == back:
				continue
			self.box.itemconfig(i, fill=self.itemactivefg)
			self.box.itemconfig(b, fill=self.itemactivebg, outline=self.itemactivebg)
	
	def __line_leave(self, this_list):
		if isinstance(this_list, int):
			level = this_list
		else:
			_, _, _, level = this_list
		if level == self.selected:
			return
		for item, back, _, _ in self.data[level]:
			self.box.itemconfig(item, fill=self.itemfg)
			self.box.itemconfig(back, fill=self.itembg, outline=self.itembg)
	
	def __line_select(self, this_list):
		item, _, _, level = this_list
		old_level = self.selected
		self.selected = -1
		self.__line_enter(this_list)
		if old_level != -1 and old_level != level:
			self.__line_leave(old_level)
		self.selected = level
		self.selected_item = item
	
	def append_content(self, content):
		if content.__len__() != self.titles.__len__():
			raise ValueError("content count must be equal to heads count")
		
		level = self.data.__len__()
		items = []
		for i, text in enumerate(content):
			width = self.titles[i][2]
			x = self.titles[i][3]
			item = self.box.add_paragraph((x,self.endy), text, fg=self.itemfg, width=width, font=self.font)
			tag = f'tinuisheet-item-{item}'
			self.box.addtag_withtag(tag, item)
			bbox = self.box.bbox(item)
			backbbox = (x, bbox[1]+3, x+width, bbox[1]+3, x+width, bbox[3]-3, x, bbox[3]-3)
			back = self.box.create_polygon(backbbox, fill=self.itembg, outline=self.itembg, width=9, tags=tag)
			self.box.tag_raise(item)
			this_list = [item, back, tag, level]
			self.box.tag_bind(tag, '<Enter>', lambda e, t=this_list: self.__line_enter(t))
			self.box.tag_bind(tag, '<Leave>', lambda e, t=this_list: self.__line_leave(t))
			self.box.tag_bind(tag, '<Button-1>', lambda e, t=this_list: self.__line_select(t))
			items.append(this_list)
			endy = max(self.endy, bbox[3]+6)
		self.data.append(items)
		self.endy = endy

		self.__scroll_region()
	
	def set_contents(self, index:int, contents:list):
		if contents.__len__() != self.titles.__len__():
			raise ValueError("content count must be equal to heads count")
		
		items = self.data[index]
		i = 0
		for item, _, _, _ in items:
			self.box.itemconfig(item, text=contents[i])
			i += 1
		
		self.__scroll_region()
	
	def set_content(self, index:int, index2:int, content:str):
		item = self.data[index][index2][0]
		self.box.itemconfig(item, text=content)
	
	def get_selected(self):
		if self.selected_item:
			return self.box.itemcget(self.selected_item, 'text')
		return None
	
	def __move_up(self, index:int, height:int):
		for items in self.data[index:]:
			for item in items:
				self.box.move(item[2], 0, -height)
				item[3] -= 1

	def delete_row(self, index:int):
		if index >= self.data.__len__():
			return

		if self.selected == index:
			self.selected = -1
			self.selected_item = None
		elif self.selected > index:
			self.selected -= 1
		
		items = self.data[index]
		maxheight = 0
		for _, _, tag, _ in items:
			bbox = self.box.bbox(tag)
			maxheight = max(maxheight, bbox[3]-bbox[1])
			self.box.delete(tag)
			self.box.dtag(tag)
		self.endy -= maxheight

		self.__move_up(index+1, maxheight)
		
		self.data.pop(index)
		self.__scroll_region()
	
	def __move_left(self, index:int, width:int):
		for items in self.titles[index:]:
			self.box.move(items[-1], -width, 0)
			items[3] -= width
		for items in self.data:
			for item in items[index:]:
				self.box.move(item[2], -width, 0)
	
	def delete_col(self, index:int):
		if index >= self.titles.__len__():
			return
		
		if self.titles.__len__() == 1:
			self.selected = -1
			self.selected_item = None
			self.data.clear()
			self.endy = 0
			self.box.delete('all')
			self.titles.clear()
			self.__scroll_region()
			return

		bbox = self.box.bbox(self.titles[index][-1])
		width = bbox[2]-bbox[0]
		self.__move_left(index+1, width+1)
		title = self.titles.pop(index)
		self.box.delete(title[-1])

		for col_items in self.data:
			_, _, tag, _ = col_items[index]
			self.box.delete(tag)
			self.box.dtag(tag)
			col_items.pop(index)


if __name__ == "__main__":
	from tkinter import Tk

	def test(_):
		# tus.delete_col(0)
		# tus.delete_row(0)
		tus.set_head(0, {'title':'α', 'width':200})
		tus.set_head(1, 'bbb')
		# tus.append_content(['三','444','555',' ',' '])
		pass

	root = Tk()
	root.geometry("400x400")

	ui = BasicTinUI(root)
	ui.pack(expand=True, fill='both')
	tus = TinUISheet(ui, (15,15))

	tus.set_heads(['a',{'title':'b','width':200},'c',' ',' ',' '])
	# tus.set_head(1, 'bbb')
	tus.append_content(['一','222','333',' ',' ',' '])
	tus.append_content(['四','555','666',' ',' ',' '])
	tus.append_content(['七','888','999',' ',' ',' '])
	tus.append_content(['万','000','111',' ',' ',' '])
	tus.append_content(['三','444','555',' ',' ',' '])
	tus.set_contents(1, ['Ⅳ','⑤','陆',' ',' ',' '])
	tus.set_content(2, 2, '玖')
	# ui.after(2000, lambda: print(tus.get_selected()))

	ui.add_button((10,350), text='test', command=test)

	root.mainloop()
