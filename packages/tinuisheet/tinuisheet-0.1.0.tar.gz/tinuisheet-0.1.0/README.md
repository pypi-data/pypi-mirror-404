# TinUISheet

[TinUI](https://github.com/Smart-Space/TinUI)的高级表格控件。

> [!warning]
>
> 当前TinUISheet仍处于早期开发状态，虽已经可用于TinUI，但是其实例参数、使用方法、效果等仍可能会有变动。

---

# 使用

## TinUISheet类

```python
TinUISheet(
    ui:BasicTinUI, pos:tuple, width=300, height=300, minwidth=100, maxwidth=300,
    font=('微软雅黑', 12),
    fg='black', bg='white', itemfg='#1a1a1a', itembg='#f9f9f9', headbg='#f0f0f0',
    itemactivefg='#191919', itemactivebg='#f0f0f0',
    itemonfg='#191919', itemonbg='#e0e0e0',
    headfont=('微软雅黑', 14),
    anchor='nw'
)
```

- fg-文本颜色
- bg-表格背景色
- itemfg-数据文本颜色
- itembg-数据背景色
- headbg-表栏背景色
- itemactivefg-响应鼠标整行文本颜色
- itemactivebg-响应鼠标整行背景色
- itemonfg-选中时文本颜色
- itemonbg-选中时背景颜色

> [!note]
>
> 标准配色随时可能变动，建议自行指定颜色。

**set_heads(heads)**

设置整个表头文本。

> 对于`heads`中的一项，如果为`dict`，则有如下结构：
>
> ```json
> {
>     'title': 'TITLE',
>     'width': WIDTH-INT // 宽度
> }
> ```

**set_head(index:int, head)**

设置某个表头文本。

> head可以为`str`，也可以同上为`dict`。

**append_content(content)**

加入一行数据。

**set_contents(index:int, contents:list)**

设置一行数据（从表头栏下一行开始记为`0`）。

**set_content(index:int, index2:int, content:str)**

设置`index`行`index2`列的数据。

**get_selected()**

获取当前选中块的文本，无则返回`None`。

**delete_row(index:int)**

删除某行。

**delete_col(index:int)**

删除某列。