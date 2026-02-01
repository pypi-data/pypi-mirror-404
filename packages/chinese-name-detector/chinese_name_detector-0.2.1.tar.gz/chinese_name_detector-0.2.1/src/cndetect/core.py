import re
from dataclasses import dataclass
from typing import List, Optional, Iterable, Union
from pathlib import Path
import pandas as pd
from .logger import logger, redact_name
from .config import settings

@dataclass
class DetectResult:
    text: str
    has_chinese: bool
    family_name: Optional[str] = None

class ChineseNameDetect:
    def __init__(self, 
                 family_names_path: Optional[str] = None, 
                 pinyin_names_path: Optional[str] = None,
                 custom_names: Optional[List[str]] = None,
                 exclude_names: Optional[List[str]] = None,
                 mode: str = "overall"):
        self.mode = mode
        self.family_names = self.load_family_names(family_names_path)
        self.pinyin_family_names = self.load_pinyin_family_names(pinyin_names_path)
        
        # 合并自定义姓氏
        if custom_names:
            # 区分汉字和拼音
            cn_custom = [n for n in custom_names if re.search(r'[\u4e00-\u9fff]', n)]
            py_custom = [n.lower() for n in custom_names if not re.search(r'[\u4e00-\u9fff]', n)]
            
            self.family_names = sorted(list(set(self.family_names + cn_custom)), key=len, reverse=True)
            self.pinyin_family_names = sorted(list(set(self.pinyin_family_names + py_custom)), key=len, reverse=True)
            
        # 排除特定姓氏
        if exclude_names:
            exclude_set = {n.lower() for n in exclude_names}
            self.family_names = [n for n in self.family_names if n not in exclude_set and n.lower() not in exclude_set]
            self.pinyin_family_names = [n for n in self.pinyin_family_names if n.lower() not in exclude_set]

        self.pinyin_syllables = self.load_pinyin_syllables()
        # Unicode range for Chinese characters
        self.cn_regex = re.compile(r'[\u4e00-\u9fff]')
        # 预编译拼音检测正则：确保姓氏是独立的“单词”
        if self.pinyin_family_names:
            pinyin_pattern = "|".join(re.escape(n) for n in self.pinyin_family_names)
            self.pinyin_regex = re.compile(rf'(?<![a-zA-Z])({pinyin_pattern})(?![a-zA-Z])', re.IGNORECASE)
        else:
            self.pinyin_regex = None
        
        # 缩写格式正则: X. 或 Y. (不加结尾 \b，因为点号本身不是 word 字符)
        self.abbr_regex = re.compile(r'\b[A-Z]\.')

    def load_family_names(self, path: Optional[str] = None) -> List[str]:
        if path is None:
            # Load default
            path = Path(__file__).parent / "data" / "family.txt"
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                names = [line.strip() for line in f if line.strip()]
                # Sort by length descending to match longest first (e.g. 欧阳 before 欧)
                return sorted(names, key=len, reverse=True)
        except Exception as e:
            logger.warning(f"Failed to load family names from {path}: {e}. Falling back to default.")
            if path != Path(__file__).parent / "data" / "family.txt":
                return self.load_family_names(None)
            return []

    def load_pinyin_family_names(self, path: Optional[str] = None) -> List[str]:
        if path is None:
            path = Path(__file__).parent / "data" / "pinyin_family.txt"
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                names = [line.strip().lower() for line in f if line.strip()]
                # Sort by length descending to match longest first
                return sorted(names, key=len, reverse=True)
        except Exception as e:
            logger.warning(f"Failed to load pinyin family names from {path}: {e}")
            return []

    def load_pinyin_syllables(self) -> set:
        path = Path(__file__).parent / "data" / "pinyin_syllables.txt"
        try:
            with open(path, "r", encoding="utf-8") as f:
                return {line.strip().lower() for line in f if line.strip()}
        except Exception:
            return set()

    def is_pinyin_word(self, word: str) -> bool:
        """判断一个单词是否由合法的拼音音节组成 (如 Jinduan, Guangfu)"""
        word = word.lower()
        if not word or not word.isalpha():
            return False
        
        n = len(word)
        dp = [False] * (n + 1)
        dp[0] = True
        
        for i in range(1, n + 1):
            # 拼音音节长度通常在 1 到 6 之间
            for j in range(max(0, i - 6), i):
                if dp[j] and word[j:i] in self.pinyin_syllables:
                    dp[i] = True
                    break
        return dp[n]

    def detect(self, text: str, mode: Optional[str] = None) -> DetectResult:
        if not text or not isinstance(text, str):
            return DetectResult(text=str(text), has_chinese=False)
        
        current_mode = mode or self.mode
        has_chinese = bool(self.cn_regex.search(text))
        found_family = None
        
        if has_chinese:
            # 中文字符检测：识别成中文姓氏
            for name in self.family_names:
                if name in text:
                    found_family = name
                    break
        else:
            if current_mode == "component":
                found_family = self._detect_component(text)
            elif current_mode == "strict":
                found_family = self._detect_strict(text)
            else:
                found_family = self._detect_overall(text)
        
        return DetectResult(text=text, has_chinese=has_chinese, family_name=found_family)

    def _detect_overall(self, text: str) -> Optional[str]:
        """整体匹配模式：原有逻辑的整合"""
        found_family = None
        # 1. 尝试标准拼音姓氏匹配（捕获所有位置）
        if self.pinyin_regex:
            candidates = []
            for match in self.pinyin_regex.finditer(text):
                candidate = match.group()
                start, end = match.span()
                # 排除单字母缩写（如 A.）
                if len(candidate) == 1 and end < len(text) and text[end] == '.':
                    continue
                candidates.append((candidate, start))
            
            # 优先取第一个匹配（通常为姓氏）
            if candidates:
                found_family = candidates[0][0]
        
        # 2. 如果没匹配到姓氏，尝试"缩写+拼音"逻辑 (如 Jinduan C., Li M. Wang)
        if not found_family and self.abbr_regex.search(text):
            words = re.findall(r'\b[a-zA-Z]{2,}\b', text)
            pinyin_words = [w for w in words if self.is_pinyin_word(w)]
            if pinyin_words:
                found_family = pinyin_words[0]
        
        # 3. 如果还是没匹配到，尝试"纯拼音全名"逻辑 (如 Haijun Zhai, Mary Wang Smith)
        if not found_family:
            words = re.findall(r'\b[a-zA-Z]+\b', text)
            if 2 <= len(words) <= 4:
                pinyin_words = [w for w in words if self.is_pinyin_word(w)]
                if 1 <= len(pinyin_words) <= 2:
                    found_family = pinyin_words[0]
                elif len(pinyin_words) >= 3 and len(pinyin_words) == len(words):
                    found_family = pinyin_words[-1]
        return found_family

    def _detect_component(self, text: str) -> Optional[str]:
        """分步处理模式：按组件拆分匹配，支持混合格式子串提取"""
        ENGLISH_HOMONYMS = {'he', 'she', 'me', 'do', 'go', 'to', 'in', 'am', 'is', 'are'}
        # 拆分出汉字块或字母数字块
        tokens = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', text)
        for token in tokens:
            # 仅处理字母部分
            pure = re.sub(r'[^a-zA-Z]', '', token)
            if len(pure) < 2:
                continue
            
            lower_pure = pure.lower()

            # 1. 精确匹配
            if any(lower_pure == f.lower() for f in self.pinyin_family_names):
                return pure
            
            # 2. 混合格式子串匹配 (如 Davdgao, zhangyx123)
            # 逻辑：姓氏必须位于字母块的开头或结尾，以排除 alibaba 类误报
            for surname in self.pinyin_family_names:
                s_len = len(surname)
                if s_len < 2: continue
                
                # 开头匹配 (如 zhangyx)
                if lower_pure.startswith(surname.lower()):
                    # 检查是否为独立单词边界（后接非字母，已由 pure 保证）或属于混合格式
                    return pure[:s_len]
                
                # 结尾匹配 (如 Davdgao)
                if lower_pure.endswith(surname.lower()):
                    return pure[-s_len:]
            
            # 3. 检查是否是拼音词
            if self.is_pinyin_word(pure):
                return pure
        return None

    def _detect_strict(self, text: str) -> Optional[str]:
        """严格模式：仅匹配标准拼音库且排除高频英文干扰词"""
        ENGLISH_HOMONYMS = {'he', 'she', 'me', 'do', 'go', 'to', 'in', 'am', 'is', 'are'}
        tokens = re.findall(r'\b[a-zA-Z]{2,}\b', text)
        for token in tokens:
            if token.lower() in ENGLISH_HOMONYMS:
                continue
            # 必须在标准库中
            if any(token.lower() == f.lower() for f in self.pinyin_family_names):
                # 且首字母大写以确认身份
                if token[0].isupper():
                    return token
        return None

    def detect_batch(self, data: Union[Iterable[str], pd.DataFrame, pd.Series], column: Optional[str] = None) -> pd.DataFrame:
        if isinstance(data, pd.DataFrame):
            if column is None:
                raise ValueError("Column name must be specified when passing a DataFrame.")
            if column not in data.columns:
                # Basic similarity check could be added here
                raise ValueError(f"Column '{column}' not found in DataFrame. Available columns: {list(data.columns)}")
            
            series = data[column]
        elif isinstance(data, pd.Series):
            series = data
        else:
            series = pd.Series(data)

        def _row_detect(val):
            res = self.detect(str(val))
            has_cn = "✅" if res.has_chinese else "❌"
            fam_name = res.family_name if res.family_name else ""
            
            # ChineseDetector 逻辑
            detector_val = val if (res.has_chinese or fam_name) else ""
            
            return pd.Series({
                "HasChinese": has_cn,
                "FamilyName": fam_name,
                "ChineseDetector": detector_val
            })

        results = series.apply(_row_detect)
        
        if isinstance(data, pd.DataFrame):
            df_out = pd.concat([data, results], axis=1)
            return df_out
        else:
            df_out = pd.concat([series, results], axis=1)
            df_out.columns = ["Original", "HasChinese", "FamilyName", "ChineseDetector"]
            return df_out

# Singleton instance for easy access
_detector = None

def get_detector(family_names_path: Optional[str] = None, 
                 pinyin_names_path: Optional[str] = None,
                 custom_names: Optional[List[str]] = None,
                 exclude_names: Optional[List[str]] = None,
                 mode: Optional[str] = None):
    global _detector
    # 确定最终模式
    final_mode = mode or (settings.matching.mode if settings else "overall")
    
    # 如果传入了任何自定义参数，或者模式不匹配，我们创建一个新的实例
    if _detector is None or family_names_path or pinyin_names_path or custom_names or exclude_names or _detector.mode != final_mode:
        _detector = ChineseNameDetect(family_names_path, pinyin_names_path, custom_names, exclude_names, mode=final_mode)
    return _detector
