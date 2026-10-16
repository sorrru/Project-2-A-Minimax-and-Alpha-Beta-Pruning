"""本地 Markdown -> 自包含 HTML -> PDF，不操作可见浏览器窗口。

运行：python build_report.py。需要 Markdown、pypdf 与本机 Google Chrome。
"""

import base64
import os
import re
import subprocess
import tempfile
from pathlib import Path

import markdown
from pypdf import PdfReader


CSS = """
@page {
  size: A4; margin: 15mm 17mm 17mm;
  @bottom-center { content: counter(page) " / " counter(pages); font-size: 8pt; color: #64748b; }
}
* { box-sizing: border-box; }
body { font-family: 'Songti SC', 'STSong', serif; color: #172033;
       font-size: 10.5pt; line-height: 1.5; margin: 0; }
h1, h2, strong { font-family: 'Hiragino Sans GB', 'STHeiti', sans-serif; }
h1 { font-size: 17pt; text-align: center; margin: 0 0 4pt; }
h1 + p { text-align: center; color: #475569; font-size: 8.5pt; margin: 0 0 3pt; }
h1 + p + p { text-align: center; color: #475569; margin: 0 0 10pt; }
h2 { font-size: 12pt; margin: 12pt 0 5pt; padding-bottom: 3pt;
     border-bottom: .6pt solid #bac7d4; break-after: avoid; }
p { text-align: justify; margin: 4pt 0; orphans: 3; widows: 3; break-inside: avoid; }
code { font-family: 'Menlo', monospace; font-size: 8.7pt; overflow-wrap: anywhere; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0; font-size: 9pt;
        break-inside: avoid; line-height: 1.35; }
th, td { border: .5pt solid #bcc8d2; padding: 3pt 4pt; text-align: center; }
th { font-family: 'Hiragino Sans GB', sans-serif; background: #eef3f8; font-weight: 600; }
thead { display: table-header-group; }
figure { margin: 9pt 0; break-inside: avoid; }
.keep-together { break-inside: avoid; }
figure img { display: block; width: auto; max-width: 100%; max-height: 57mm; margin: 0 auto; }
figcaption { font-size: 8.6pt; line-height: 1.4; color: #475569; text-align: center; margin-top: 4pt; }
a { color: #075985; }
@media screen {
  html { background: #e8edf2; }
  body { max-width: 210mm; margin: 24px auto; padding: 16mm 17mm; background: white;
         box-shadow: 0 4px 25px #17203322; }
}
"""


def main() -> None:
    base = Path(__file__).resolve().parent
    chrome = Path(os.environ.get("REPORT_CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"))
    if not chrome.is_file():
        raise SystemExit("未找到 Chrome；可用 REPORT_CHROME 指定可执行文件路径")
    body = markdown.markdown((base / "report.md").read_text(encoding="utf-8"), extensions=["tables"])

    def embed(match):
        relative = match.group(1)
        path = (base / relative).resolve()
        if not path.is_relative_to(base) or path.suffix.lower() != ".png":
            raise ValueError("报告图片必须是项目内的 PNG")
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f'src="data:image/png;base64,{encoded}"'

    body = re.sub(r'src="([^"]+)"', embed, body)
    body = re.sub(r'<p>(<img [^>]+>)</p>\s*<p>(图 [1-9][^<]*)</p>',
                  r'<figure>\1<figcaption>\2</figcaption></figure>', body)
    body = re.sub(
        r'(<p><strong>为何从 T2 改选 T3？</strong>.*?</p>\s*<table>.*?</table>)',
        r'<div class="keep-together">\1</div>', body, flags=re.S,
    )
    html = ('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>实验二：搜索算法实验报告</title><style>' + CSS + '</style></head><body>'
            + body + '</body></html>')
    target = base / "report.html"
    target.write_text(html, encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="project2-report-") as profile:
        subprocess.run([
            str(chrome), "--headless", "--disable-gpu", "--no-sandbox", "--no-first-run",
            "--no-default-browser-check", "--no-pdf-header-footer", "--virtual-time-budget=3000",
            f"--user-data-dir={profile}", f"--print-to-pdf={base / 'report.pdf'}", target.as_uri(),
        ], check=True, capture_output=True, text=True)
    reader = PdfReader(base / "report.pdf")
    print(f"已生成 report.html、report.pdf，共 {len(reader.pages)} 页。")
    for i, page in enumerate(reader.pages, 1):
        print(f"第 {i} 页：{len(page.extract_text())} 个文本字符")


if __name__ == "__main__":
    main()
