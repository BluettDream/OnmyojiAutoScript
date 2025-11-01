from cached_property import cached_property
from enum import Enum
from module.base.debouncer import Debouncer

from typing import List, Optional, Any, Set, Callable, Dict
from pydantic import BaseModel, PrivateAttr, Field, ConfigDict
from weakref import WeakSet, ref


class ChangeInfo:
    """字段变化信息"""

    def __init__(self, path: List[str], new_v, old_v, field_type: type, source: 'ObservableModel' = None):
        self.path = path
        self.new_v = new_v
        self.old_v = old_v
        self.field_type = field_type
        self.source = source

    def update(self, info: 'ChangeInfo'):
        self.path = info.path
        self.new_v = info.new_v
        self.old_v = info.old_v
        self.field_type = info.field_type
        self.source = info.source

    def __str__(self) -> str:
        info = {
            "source": type(self.source).__name__ if self.source else None,
            "path": ".".join(self.path),
            "new_v": self.new_v,
            "old_v": self.old_v,
            "field_type": self.field_type.__name__ if self.field_type else None,
        }
        return str(info)

    def __repr__(self) -> str:
        return str(self)


class NotifyParentHandler:
    def __init__(self, info: ChangeInfo, context: Optional[dict] = None):
        self._info = info
        self._context = context or {}
        self._resolved = True

    def notify(self, info: ChangeInfo = None, context: Optional[dict] = None):
        """
        继续传递变更消息到父级
        :param info: 变更消息
        :param context: 上下文
        """
        if context:
            self._context.update(context)
        if info:
            self._info.update(info)
        self._resolved = False

    def resolve(self):
        """终止继续通知"""
        self._resolved = True

    @property
    def resolved(self) -> bool:
        return self._resolved

    @property
    def context(self) -> Dict:
        return self._context

    @property
    def info(self) -> ChangeInfo:
        return self._info


class ObservableModel(BaseModel):
    """
    观察者模型
    1. 使用弱引用避免循环引用
    2. 支持深层嵌套的自动监听和冒泡
    3. 初始化时自动绑定所有子对象
    4. 支持 list 和 dict 中的嵌套对象
    """

    # 使用弱引用存储父对象
    _parent_ref: ref = PrivateAttr()
    _parent_field: str = PrivateAttr()
    _is_notifying: bool = PrivateAttr(default=False)
    _child_handlers: Set[Any] = PrivateAttr(default_factory=lambda: WeakSet())

    model_config = ConfigDict(ignored_types=(cached_property, Debouncer,), arbitrary_types_allowed=True)

    def model_post_init(self, __context):
        """pydantic初始化后自动绑定所有子对象（包括深层嵌套）"""
        super().model_post_init(__context)
        # 递归绑定所有字段
        for field_name in self.model_fields.keys():
            value = getattr(self, field_name, None)
            if value is not None:
                self._bind_child(field_name, value)

    def __setattr__(self, name: str, value):
        # 跳过Pydantic构造阶段
        if not getattr(self, "model_fields", None):
            return object.__setattr__(self, name, value)

        model_fields = getattr(self, "model_fields", {})

        if name in model_fields:
            old_value = getattr(self, name, None)
            field_info = model_fields.get(name)
            # 先解绑旧的子对象
            self._unbind_child(old_value)
            # 赋值
            ret = super().__setattr__(name, value)
            # 绑定新的子对象
            self._bind_child(name, value)
            # 通知变化
            if old_value != value and not self._is_notifying:
                field_type = field_info.annotation if field_info else type(value)
                self._is_notifying = True
                try:
                    info = ChangeInfo(path=[name], new_v=value, old_v=old_value, field_type=field_type, source=self)
                    self._notify_change(info)
                except Exception as e:
                    raise e
                finally:
                    self._is_notifying = False
            return ret
        # 不是pydantic模型走fallback
        return object.__setattr__(self, name, value)

    def _bind_child(self, field_name: str, value: Any):
        """为子对象递归绑定父引用（支持 ObservableModel、list、dict）"""
        if isinstance(value, ObservableModel):
            # 使用弱引用存储父对象
            object.__setattr__(value, "_parent_ref", ref(self))
            object.__setattr__(value, "_parent_field", field_name)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, ObservableModel):
                    object.__setattr__(item, "_parent_ref", ref(self))
                    object.__setattr__(item, "_parent_field", f"{field_name}[{i}]")
        elif isinstance(value, dict):
            for k, item in value.items():
                if isinstance(item, ObservableModel):
                    object.__setattr__(item, "_parent_ref", ref(self))
                    object.__setattr__(item, "_parent_field", f"{field_name}['{k}']")

    def _unbind_child(self, value: Any):
        """解绑子对象"""
        if isinstance(value, ObservableModel):
            object.__setattr__(value, "_parent_ref", None)
            object.__setattr__(value, "_parent_field", None)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, ObservableModel):
                    object.__setattr__(item, "_parent_ref", None)
                    object.__setattr__(item, "_parent_field", None)
        elif isinstance(value, dict):
            for item in value.values():
                if isinstance(item, ObservableModel):
                    object.__setattr__(item, "_parent_ref", None)
                    object.__setattr__(item, "_parent_field", None)

    def _notify_change(self, info: ChangeInfo, ctx: Optional[dict] = None):
        """
        变化通知：逐级通知到父对象，并触发回调
        """
        handler = NotifyParentHandler(info, ctx)
        # 调用自己的 on_change
        try:
            self.on_change(handler)
        except RecursionError as e:
            print(f"FATAL: RecursionError in {self.__class__.__name__}.on_change (Path: {'.'.join(info.path)})")
            raise e
        # 处理结束或到达顶层, 停止通知
        if handler.resolved or not getattr(self, '_parent_ref', None):
            return
        # 向上通知到父对象
        parent = self._parent_ref()  # 解引用弱引用
        if parent is not None and isinstance(parent, ObservableModel):
            info = handler.info
            ctx = handler.context
            # 构建完整路径
            if self._parent_field:
                # 如果 path 已经包含了父字段名，不再重复添加
                if info.path and info.path[0] != self._parent_field:
                    info.path = [self._parent_field] + info.path
            # 递归通知父对象
            parent._notify_change(info, ctx)

    def on_change(self, handler: NotifyParentHandler):
        """字段变更回调函数, 当字段变更时自动触发该函数
        :param handler: 父级通知处理器
        """
        handler.notify()


# --------------------Example------------------

class ItemType(str, Enum):
    A = 'a'
    B = 'b'
    C = 'c'


class Item(ObservableModel):
    name: str
    num: int
    type: ItemType = Field(default=ItemType.A)

    def on_change(self, handler):
        print(f"[Item] {handler.info}")
        if isinstance(handler.info.new_v, ItemType):
            if handler.info.new_v == ItemType.B:
                handler.notify()
            return
        if handler.info.new_v < 0:
            handler.resolve()
        elif 100 < handler.info.new_v < 200:
            handler.notify(context={"validated": True})
        else:
            handler.notify()


class Config(ObservableModel):
    item: Item
    item_list: List[Item]
    item_dict: Dict[str, Item]

    def on_change(self, handler):
        print(f"[Config] received: {handler.info}, ctx={handler.context}")
        if handler.info.new_v and handler.info.new_v is int and handler.info.new_v < 200:
            handler.resolve()
        else:
            pass


if __name__ == '__main__':
    cfg = Config(item=Item(name="x", num=1), item_list=[Item(name="y", num=2), Item(name="z", num=3)],
                 item_dict={"a": Item(name="a", num=4)})
    print(f'{"-" * 7} All receive num update {"-" * 7}')
    cfg.item.num = 42
    print(f'{"-" * 7} All receive list update {"-" * 7}')
    cfg.item_list[0].num = 52
    print(f'{"-" * 7} Only Item receive num update {"-" * 7}')
    cfg.item.num = -2
    print(f'{"-" * 7} Config receive ctx {"-" * 7}')
    cfg.item_list[1].num = 150
    print(f'{"-" * 7} Notify auto stop {"-" * 7}')
    cfg.item_list[0].num = 300
    print(f'{"-" * 7} Only Item receive dict update {"-" * 7}')
    cfg.item_dict["a"].num = -3
    # normal type is not observable_model, can't observable
    cfg.item_dict["a"] = Item(name='b', num=4)
    print(f'{"-" * 7} All receive enum update {"-" * 7}')
    cfg.item.type = ItemType.B
    print(f'{"-" * 7} All receive getattr update {"-" * 7}')
    item = getattr(cfg, 'item')
    item.num = 62
