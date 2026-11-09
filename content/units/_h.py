# -*- coding: utf-8 -*-
"""单位（政权与二级单位）定义的辅助函数。每个 units/*.py 模块：
    from _h import mk
    U = []; S, T, Z = mk(U)
    S(键, 名称, 说明)            政权（kind=state，默认所属 = 自身）
    T(键, 名称, 说明)            部族、无主或松散控制地带（kind=tribe，淡填虚线，不计政权数）
    Z(键, 名称, 所属政权键, 说明)  二级单位（派系、根据地、殖民地分区等，kind=zhen）
说明可以留空，由 content/notes/*.json 补齐（键 → 说明）。
键在全部模块中必须唯一；snaps 里用 “键>政权:” 可改变某节点的所属政权。
"""
def mk(U):
    def S(k, name, note="", **kw): U.append(dict(k=k, n=name, kind="state", pol=k, note=note, **kw))
    def T(k, name, note="", **kw): U.append(dict(k=k, n=name, kind="tribe", pol=k, note=note, **kw))
    def Z(k, name, pol, note="", **kw): U.append(dict(k=k, n=name, kind="zhen", pol=pol, note=note, **kw))
    return S, T, Z
