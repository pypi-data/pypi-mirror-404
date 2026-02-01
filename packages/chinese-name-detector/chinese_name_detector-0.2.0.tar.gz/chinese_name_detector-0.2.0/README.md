# chinese-name-detector：中文字符与姓氏检测利器


`chinese-name-detector`（原 `cndetect`）是一个专为中文环境设计的轻量级检测工具。它能够智能识别文本中的**中文字符**以及**常见的中文姓氏**（支持汉字识别与拼音识别）。

无论你是需要批量处理 Excel 表格的非技术人员，还是希望在代码中集成姓名检测功能的开发者，`chinese-name-detector` 都能为你提供简单、高效的解决方案。

---

## 🌟 核心特性

- **双接口支持**：既有简洁的命令行工具（CLI），也有功能完备的 Python 调用接口（API）。
- **智能识别**：支持汉字姓氏（如“王”、“欧阳”）和拼音姓氏（如“Wang”、“Ouyang”）。
- **多模式匹配**：提供 `overall` (整体)、`component` (分步) 和 `strict` (严格) 三种检测模式，精准应对各种复杂格式与混合噪声。
- **混合格式支持**：能够从 `wangxm133`、`li_abc`、`Davdgao` 等混合字符串中准确提取姓氏。
- **精准匹配**：拼音识别支持“独立单词”模式与“组件匹配”模式，有效避免如 `Alice` 中的 `li` 被误判。
- **Excel 友好**：支持一键扫描 Excel 文件并自动生成带有检测结果的新表格。
- **隐私保护**：内置日志打码功能，自动隐藏敏感姓名信息。

---

## 📥 安装指南

### 系统要求
- **Python 版本**：Python 3.8 或更高版本（支持 Windows, macOS, Linux）。

### 安装命令
打开你的终端或命令提示符，输入以下命令即可一键安装：

```bash
pip install chinese-name-detector
```

---

## 🚀 快速上手 (命令行 CLI)

安装完成后，你可以直接在终端使用 `cndetect` 命令。

### 1. 检测单条文本
输入一段文字，查看是否包含中文字符及姓氏。
```bash
cndetect single "张三"
cndetect single "Bruce Wang"

# 使用自定义姓氏 (支持逗号分隔或 JSON 列表)
cndetect single "Bruce Wayne" --custom-names "Wayne,Kent"
# 排除特定姓氏
cndetect single "Bruce Wang" --exclude-names "Wang"

# 切换匹配模式 (overall, component, strict)
cndetect single "Wang123" --match-mode component
```

### 2. 批量扫描 Excel 文件
指定一个 Excel 文件及其中的某一列，工具会自动识别并保存结果。
```bash
# -c 参数用于指定 Excel 中需要检测的列名
cndetect batch data.xlsx -c "姓名"

# 批量模式也支持自定义和排除姓氏
cndetect batch data.xlsx -c "姓名" --custom-names '["Wayne", "慕容"]'
```
*执行后，会生成一个名为 `data_cn.xlsx` 的新文件，其中会新增一列结果：*
- **ChineseDetector**：如果识别为姓名（包含中文或命中姓氏），则保留原始值，否则为空。

### 3. 使用配置文件执行任务
当你有很多文件需要处理，或者有特定的配置需求时，可以使用配置模式。
```bash
# 生成一个默认配置模板 cndetect.yaml
cndetect config

# 修改配置文件后，按配置批量运行
cndetect run -c cndetect.yaml
```

---

## 🛠️ Python API 使用教程

如果你是一名开发者，可以将 `cndetect` 集成到你的 Python 项目中。

```python
import cndetect as cnd
import pandas as pd

# --- 场景 1：单条检测 (多模式) ---
# 默认 overall 模式
result = cnd.detect("Wang Xiaoming")

# 使用 component 模式识别混合格式 (如从账号中提取姓氏)
result_mixed = cnd.detect("wangxm133", mode="component")
print(f"混合格式提取结果: {result_mixed.family_name}") # wang

# 使用 strict 模式排除英文同音词干扰
result_strict = cnd.detect("He Wang", mode="strict")
print(f"严格模式结果: {result_strict.family_name}") # Wang (自动忽略英文词 He)

# --- 场景 2：自定义与排除 ---
result_custom = cnd.detect("Bruce Wayne", custom_names=["Wayne"])
print(f"识别到自定义姓氏: {result_custom.family_name}") # Wayne

result_exclude = cnd.detect("Bruce Wang", exclude_names=["Wang"])
print(f"由于被排除，姓氏结果为: {result_exclude.family_name}") # None

# --- 场景 3：处理 Pandas DataFrame ---
data = {'name': ["王小明", "Jack Chen", "Alibaba", "Alice"]}
df = pd.DataFrame(data)

# 批量检测指定的列
df_out = cnd.detect_batch(df, column="name")

# 查看结果
# df_out 会包含原有的列，以及新增的 'ChineseDetector' 列（API 调用默认仍保留 HasChinese 和 FamilyName 供参考）
print(df_out)
# 注：Alibaba 里的 'ba' 和 Alice 里的 'li' 不会被误识别，因为它们不是独立单词。
```

---

## ⚙️ 配置说明 (chinese-name-detector.yaml)

你可以通过 YAML 配置文件灵活定义工具的行为。工具会按以下顺序查找配置：`命令行 -c 参数` > `当前目录 cndetect.yaml` > `~/.config/cndetect/config.yaml`。

### 详细参数手册

#### 1. 基础姓氏配置
| 参数路径 | 类型 | 默认值 | 说明与示例 |
| :--- | :--- | :--- | :--- |
| `family_name_path` | 字符串 | `null` | **自定义姓氏文件路径**。指向一个每行包含一个姓氏的 `.txt` 文件。若设置，将作为基础库使用。 |
| `custom_family_names` | 数组 | `[]` | **动态正向匹配列表**。在不修改文件的情况下，额外增加需要识别的姓氏。<br>示例：`["MyName", "特有姓"]` |
| `exclude_family_names` | 数组 | `[]` | **动态反向排除列表**。强制不识别某些特定的字符串。<br>示例：`["SomeFakeName"]` |

#### 2. 匹配模式配置 (`matching.*`)
| 参数路径 | 类型 | 默认值 | 说明与示例 |
| :--- | :--- | :--- | :--- |
| `matching.mode` | 字符串 | `"overall"` | **匹配模式**。可选值：<br>- `overall`: 默认模式，整体匹配。<br>- `component`: 分步匹配，先拆分组件再识别，适合混合格式。<br>- `strict`: 严格模式，仅匹配库内词且要求首字母大写，排除常见英文单词干扰。 |

#### 3. Excel 批量处理配置 (`excel.*`)
| 参数路径 | 类型 | 默认值 | 说明与示例 |
| :--- | :--- | :--- | :--- |
| `excel.paths` | 数组 | `[]` | **待处理文件列表**。仅在 `cndetect run` 模式下生效。<br>示例：`["data1.xlsx", "data2.xlsx"]` |
| `excel.column` | 字符串 | `"Name"` | **默认检测列名**。Excel 中需要进行姓名扫描的列标题。 |
| `excel.output_suffix` | 字符串 | `"_cn"` | **输出文件名后缀**。生成的检测结果文件名会在原名后增加此后缀。 |
| `excel.output_dir` | 字符串 | `null` | **输出目录**。指定结果文件保存的文件夹。若为 `null` 则保存在原文件同目录。 |

#### 3. 日志与审计配置 (`log.*`)
| 参数路径 | 类型 | 默认值 | 说明与示例 |
| :--- | :--- | :--- | :--- |
| `log.level` | 字符串 | `"INFO"` | **日志级别**。可选 `DEBUG`, `INFO`, `WARNING`, `ERROR`。 |
| `log.file` | 字符串 | `null` | **日志保存路径**。若指定，日志将写入该文件（支持自动创建目录）。 |
| `log.rotation` | 字符串 | `"1 MB"` | **日志轮转触发大小**。单个日志文件达到多大时自动切分。 |
| `log.retention` | 字符串 | `"7 days"` | **日志保留时间**。过期日志将自动清理。 |
| `log.redact_names` | 布尔值 | `true` | **隐私脱敏开关**。开启后，日志中的姓名将被打码（如 `张*`），不影响 Excel 结果。 |

---

## 🔍 匹配规则详解

`chinese-name-detector` 提供三种检测深度，你可以根据数据质量选择最合适的模式：

### 1. 模式特性对比

| 模式 | 核心逻辑 | 识别能力 | 防误报能力 | 适用场景 |
| :--- | :--- | :--- | :--- | :--- |
| **`overall`** | 全文子串扫描 + 单词边界校验 | 强 (支持全名/缩写) | 中 (易受同音词干扰) | 标准姓名格式，如 `Wang Xiaoming` |
| **`component`** | 分词后组件匹配 + 子串提取 | 极强 (支持混合格式) | 高 (杜绝子串包含) | 账号、邮箱或带数字的混合数据 |
| **`strict`** | 分词 + 库匹配 + 首字母/黑名单 | 一般 (仅匹配库内词) | 极高 (过滤英文词) | 噪音极大的英文文本环境 |

### 2. 识别示例

*   **混合格式提取** (`component` 模式)：
    - `Davdgao` -> **gao** (识别结尾姓氏)
    - `wangxm133` -> **wang** (识别开头姓氏)
    - `alibaba` -> **None** (非开头/结尾且非独立词)

*   **独立性校验** (全模式支持)：
    - ✅ `Alice Li` -> **Li**
    - ❌ `Lily` -> **None** (字母 `li` 被包含在单词内部)

*   **黑名单过滤** (`strict` 模式)：
    - ✅ `He Wang` -> **Wang** (自动过滤英文常用词 `He`)
    - ❌ `he wang` -> **None** (全小写在严格模式下被视为普通单词)

---

## ❓ 常见问题 (FAQ)

**Q: 为什么我的 Excel 列没被识别？**
A: 请确保你在使用 `batch` 命令时通过 `-c` 参数准确输入了列名，注意大小写和空格。

**Q: 识别出的拼音姓氏大小写不对？**
A: `chinese-name-detector` 默认会返回文本中原本的大小写样式，但匹配过程是忽略大小写的。

**Q: 如何添加一些特殊的复姓？**
A: 你可以使用 `cndetect config` 生成配置文件，在 `family_name_path` 中指定你自己的姓氏文件。

---

## ⚠️ 注意事项

- **数据隐私**：在处理包含敏感个人信息的文件时，请确保遵守相关数据隐私法规。工具内置的日志打码仅针对日志文件，不会修改你的原始 Excel 数据。
- **环境隔离**：建议在 Python 虚拟环境中安装，以避免依赖冲突。

---

## 📄 许可证

本项目采用 [MIT](LICENSE) 许可证。
