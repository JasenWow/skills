import re
from typing import List, Tuple, Dict
import argparse

class HeaderTracker:
    """跟踪 Markdown 文档的标题层级（H1~H6）"""
    def __init__(self):
        self.active_headers: Dict[int, str] = {}

    def update_from_text(self, text: str):
        """扫描文本更新标题状态"""
        matches = re.findall(r'^(#{1,6})\s+(.+)$', text, re.MULTILINE)
        for hashes, title in matches:
            level = len(hashes)
            self.active_headers[level] = title.strip()
            # 清除比当前级别低的标题
            for k in list(self.active_headers.keys()):
                if k > level:
                    del self.active_headers[k]

    def get_headers(self) -> str:
        headers = [self.active_headers[k] for k in sorted(self.active_headers.keys())]
        return ' > '.join(headers)


class TextSplitter:
    """将长文本切分为 chunk，同时保留标题上下文和保护区域"""
    def __init__(self, chunk_size: int = 200, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.header_tracker = HeaderTracker()
        self.separators = ["\n\n\n", "\n\n", "\n", "。", "！", "？"]
        self.protect_patterns = [
            r'\$\$[\s\S]*?\$\$',      # LaTeX 公式
            r'```[\s\S]*?```',        # 代码块
            r'!\[.*?\]\(.*?\)',       # 图片
            r'\[.*?\]\(.*?\)',        # 链接
            r'[ ]*(?:\|[^|\n]*)+\|',  # 表格行
        ]

    def extract_protected_ranges(self, text: str) -> List[Tuple[int, int]]:
        """找出受保护区域"""
        matches = []
        for pattern in self.protect_patterns:
            for m in re.finditer(pattern, text):
                matches.append((m.start(), m.end()))
        matches.sort()
        return matches

    def split_preserving_protected(self, text: str, protected: List[Tuple[int, int]]) -> List[str]:
        """
        按分隔符切分文本，保护受保护区域不被拆分
        """
        segments = []
        last_index = 0

        for start, end in protected:
            # 受保护区域前的文本切分
            if start > last_index:
                segments.extend(self.recursive_split(text[last_index:start]))
            # 直接添加受保护区域
            segments.append(text[start:end])
            last_index = end

        # 剩余文本
        if last_index < len(text):
            segments.extend(self.recursive_split(text[last_index:]))

        return segments

    def recursive_split(self, text: str) -> List[str]:
        """递归按分隔符切分文本"""
        text = text.strip()
        if not text:
            return []

        if len(text) <= self.chunk_size:
            return [text]

        for sep in self.separators:
            if sep in text:
                parts = text.split(sep)
                result = []
                for part in parts:
                    result.extend(self.recursive_split(part))
                return result

        # 最终按合理长度切分
        result = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            result.append(text[start:end])
            start = end
        return result

    def merge_chunks(self, segments: List[str]) -> List[str]:
        """将段落合并成 chunk，带重叠"""
        chunks = []
        current_chunk = ""
        for segment in segments:
            if len(current_chunk) + len(segment) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                # 重叠部分
                overlap = current_chunk[-self.chunk_overlap:] if self.chunk_overlap < len(current_chunk) else current_chunk
                current_chunk = overlap + segment
            else:
                current_chunk += segment

        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    def split(self, text: str) -> List[str]:
        """主入口函数"""
        # 1. 先扫描标题，建立全局标题树
        self.header_tracker.update_from_text(text)

        # 2. 提取保护区
        protected = self.extract_protected_ranges(text)

        # 3. 分段，保护受保护区域
        segments = self.split_preserving_protected(text, protected)

        # 4. 合并段落生成 chunk
        chunks = self.merge_chunks(segments)

        # 5. 添加标题上下文
        final_chunks = []
        for chunk in chunks:
            headers = self.header_tracker.get_headers()
            final_chunks.append(f"{headers}\n\n{chunk}" if headers else chunk)

        return final_chunks


def run(file_path: str) :
    """markdown file path"""
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    splitter = TextSplitter(chunk_size=200, chunk_overlap=50)
    chunks = splitter.split(text)

    for i, chunk in enumerate(chunks):
        print(f"--- Chunk {i+1} ---\n{chunk}\n")

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="Split a markdown file into chunks.")
    argparser.add_argument("file_path", type=str, help="Path to the markdown file to be split.")
    args = argparser.parse_args()
    run(args.file_path)
