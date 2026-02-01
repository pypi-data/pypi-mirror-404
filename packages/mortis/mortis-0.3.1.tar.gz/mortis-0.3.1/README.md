# mortis

`mortis` 是一个基于 **Pydantic V2** 开发的 Arcaea 数据处理库，以类型安全、面向对象的方式实现 AFF 谱面文件和 songlist 歌曲数据文件的解析、验证与操作，全程保障数据类型的合法性。

## 核心特性
- **AFF 谱面处理**: 完整解析 AFF 文件结构，通过 `AFFEvent` 子类（`Tap`/`Timing`/`Arc` 等）实现面向对象的事件操作；
- **Songlist 解析**: 支持读取、验证、修改 songlist 歌曲数据文件，通过 `SonglistItem` 统一管理歌曲元信息；
- **类型安全**: 基于 Pydantic V2 实现数据校验，杜绝非法数据格式，运行时自动抛出类型错误；
- **极简 API**: 核心功能导出至根模块，无需深入目录结构即可快速调用。

## 环境要求
项目在以下环境中开发，未进行向下兼容测试和相关优化。未来可能做出相应优化，届时需要的最低版本将相应下调。

- Python >= 3.12
- pydantic >= 2.12.0
	- 项目依赖于 Pydantic V2 进行数据验证等，用户使用前应对其有一定了解。

## 安装
通过 pip 从 PyPI 安装: 
```bash
pip install mortis
```

如果希望参与开发: 
```bash
git clone https://github.com/IzayoiArika/mortis.git
cd mortis
pip install -e .
```

## 快速使用
以下示例覆盖 `mortis` 的核心场景，复制即可运行（需提前准备一个 Arcaea 的 `.aff` 文件）。

### 示例 1: 统计 AFF 文件中的 Tap 数量
```python
import os
from mortis import AFF, Tap

aff_path = ... # 替换为实际 AFF 文件路径
aff = AFF.load_from_path(aff_path) # 解析 AFF 文件

# 遍历所有事件，统计 Tap 数量
tap_count = 0
for event in aff.iter_events():
	if isinstance(event, Tap):
		tap_count += 1
# 一行解决: tap_count = sum(isinstance(event, Tap) for event in aff.iter_events())
print(f"Tap 数量: {tap_count}")
```

### 示例 2: 镜像 AFF 中的所有物件并保存
```python
from mortis import AFF, GameObjectEvent

aff = AFF.load_from_path(aff_path)
# 遍历事件并镜像翻转所有游戏对象
for event in aff.iter_events():
	if isinstance(event, GameObjectEvent):
		event.mirror()
# 保存修改后的 AFF 文件
aff.dump_to_path(aff_path)
# 或指定新路径: aff.dump_to_path(another_path)
```

### 示例 3: 检查 TimingGroup 是否使用 anglex/angley
```python
from mortis import AFF

aff = AFF.load_from_path(aff_path)
# 遍历所有 TimingGroup，检查anglex/angley字段
for idx, group in enumerate(aff.iter_groups()):
	if group.anglex is not None:
		print(f"TimingGroup #{idx} 使用了 anglex; 值为 {group.anglex}")
	if group.angley is not None:
		print(f"TimingGroup #{idx} 使用了 angley; 值为 {group.angley}")
```

### 示例 4: 解析 songlist 歌曲数据
```python
from mortis import SonglistItem

songlist_path = ... # 替换为实际 songlist 路径
song_item = SonglistItem.load_from_path(songlist_path) # 解析 songlist
# 访问歌曲属性
print(f"歌曲 ID: {song_item.id}")
print(f"所有难度: {song_item.difficulties}")
print(f"背景图: {song_item.bg}")
```

## 贡献指南
若存在项目尚未支持的官方特性，欢迎提交 Issue 或 PR。

1. Fork 本仓库并克隆到本地
2. 创建特性分支：git checkout -b feature/xxxx
3. 在本地进行代码测试，确保功能正确工作
4. 提交代码，进行 Pull Request

项目遵循 PEP 8 代码规范。

## 项目结构
多数用户无需关注内部结构，**所有公开 API 均已导出至根模块 `mortis`**，直接通过 `from mortis import XXX` 导入即可。

```text
mortis/
├── aff/                  # AFF 谱面处理模块
│   ├── events/           # 各类 AFF 事件（Tap/Hold/Arc 等）的定义
│   ├── lexer/            # AFF 词法分析器
│   ├── types/            # AFF 相关数据类型（坐标/缓动函数等）
│   ├── aff.py            # AFF 文件核心操作类
│   └── timinggroup.py    # TimingGroup 类
├── songlist/             # songlist 歌曲数据处理模块
│   ├── item.py           # SonglistItem 核心类
│   ├── diffs.py          # 难度相关定义
│   ├── bgs.py            # 背景图相关定义
│   └── types.py          # songlist 数据类型
├── globalcfg.py          # 全局配置
└── utils.py              # 通用工具函数
```

## 常见问题 (FAQ)
- **Q: 目前对 AFF/songlist 的支持是否齐全？**
- A: 尚在完善，但已能满足多数基本功能需求。
- **Q: 支持 Arcaea 最新版本的 AFF/songlist 特性吗？**
- A: 会尽量跟进更新。

## 许可证
本项目基于 **GNU General Public License v3 (GPLv3)** 开源，详见 [LICENSE](LICENSE) 文件。

## Trivia
项目名称 `mortis` 来自《BanG Dream! Ave Mujica》若叶睦在乐队中的成员代号<del>及第二人格自称</del>。

该名称与本项目的用途没有任何关联，使用该名称纯粹是出于个人喜好。

<del>小睦超可爱，总有一天所有人都会厨上小睦的</del>