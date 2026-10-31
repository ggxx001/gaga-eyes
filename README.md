# gaga-eyes · 给 AI 的一双眼睛和一只手

一个文件，不装插件、不改系统设置。用 Windows 自带接口截屏、移动鼠标、点击、打字。
我是 B 站 UP 主「嘎嘎大魚」，这是我给自己写的手眼，用来操作那种没有网页入口的桌面程序。

## 它能做什么

| 能力 | 实测数据（2560×1440，DPI 缩放 150%） |
| --- | --- |
| 截屏 | 一张 36 毫秒，连续约 28 帧/秒 |
| 移动鼠标 | 底层 16000 次/秒；默认每次之间 sleep 40ms（≈25 步/秒） |
| 点击 | 左键/右键，物理像素精确 |
| 打字 | 138 字符/秒，中文与英文同速（走 Unicode，不过输入法） |
| 找窗口 | 按 pid 或标题，自动提到前台 |

## 用法

```bash
python gaga-eyes.py shot out.jpg 0.45      # 截屏，第三参数是缩放（0-1），省流量
python gaga-eyes.py move 1200 800
python gaga-eyes.py click 1200 800
python gaga-eyes.py type "一行中文也能打进去"
python gaga-eyes.py key ctrl+s
python gaga-eyes.py wins                  # 列出可见窗口（pid/标题/位置）
python gaga-eyes.py                       # 打印屏幕尺寸、光标位置、INPUT 结构体大小
```

当库用：

```python
import importlib.util
spec = importlib.util.spec_from_file_location("ge", "gaga-eyes.py")
ge = importlib.util.module_from_spec(spec); spec.loader.exec_module(ge)

w = ge.focus(pid=12345)        # 或 focus("记事本")，按标题
r = w["rect"]; ge.click((r[0]+r[2])//2, (r[1]+r[3])//2)
ge.type_text("你好"); ge.key("enter")
ge.shot("screen.jpg", 0.5)
```

## 三个必须知道的坑（都是踩出来的）

1. **DPR**：先说 `SetProcessDpiAwareness(2)`。不声明的话 `SetCursorPos` 会半生效（x 动了 y 不动），截图坐标也全对不上。
2. **SendInput 结构体在 x64 上是 40 字节**。我一开始按 32 字节写，一个字符都打不进去，程序还返回成功——因为压根没检查返回值。现在每次 `SendInput` 都校验返回 == 1。
3. **找窗口别按标题模糊匹配**。我按「记事本」找，结果打进了另一个人开着的日志窗口。正解：自己起的进程拿 pid，再 `EnumWindows` + `GetWindowThreadProcessId` 按 pid 找。

## 它不是什么

- 不是视觉模型。它只负责"看见像素"和"动手"，看懂画面、决定点哪儿的还是模型本身，读一张图是要花钱的。
- 不能有后台常驻意图。没在跑的时候它就是一段代码。

MIT License.
