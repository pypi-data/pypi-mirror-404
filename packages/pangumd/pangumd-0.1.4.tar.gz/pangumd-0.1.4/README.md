# pangumd

## 关于

本项目基于 [vinta/pangu.py: Paranoid text spacing in Python](https://github.com/vinta/pangu.py) 和 [frostming/marko: A markdown parser with high extensibility.](https://github.com/frostming/marko) 这两个项目实现。

这个版本在原项目的基础上，为 Markdown 语法增加了特别的适配，确保在 Markdown 文档中能正确处理文本间距。

## 对于 Markdown 适配

1.  **代码块** - 保持代码块的格式，不会添加多余的空格。
2.  **粗体文本** - 正确处理 `**粗体文本**` 语法，在粗体标记周围添加适当的间距。
3.  **斜体文本** - 支持 `*斜体文本*` 语法。
4.  **中文链接** - 为包含中文字符的超链接提供正确的间距。

### 示例

下面是一个示例，展示了 `pangumd` 如何在处理文本的同时，智能地保留 Markdown 的特定格式。

#### 处理前

```markdown
首先在**能联网**的机器安装docker，并pull 想要安装的镜像，完成后，使用 `docker save`命令导出镜像：

### 参考

1. [docker save与docker export 的区别 - jingsam](https://jingsam.github.io/2017/08/26/docker-save-and-docker-export.html#你好)
```

#### 处理后

```markdown
首先在**能联网**的机器安装 docker，并 pull 想要安装的镜像，完成后，使用 `docker save` 命令导出镜像：

### 参考

1. [docker save 与 docker export 的区别 - jingsam](https://jingsam.github.io/2017/08/26/docker-save-and-docker-export.html#你好)
```

## 安装

### 从 PyPI 安装 (推荐)

您可以使用 pip 直接从 PyPI 安装 `pangumd`：

```bash
pip install pangumd
```

### 从源代码安装 (开发者适用)

如果您想从源代码安装最新版本以进行开发：

```bash
# 克隆仓库
git clone https://github.com/kingronjan/pangumd.git
cd pangumd

# 以可编辑模式安装
pip install -e .
```

## 使用方式

### 在 Python 中使用

```python
import pangumd

new_text = pangumd.spacing_text('当你凝视着bug，bug也凝视着你')
# new_text = '当你凝视着 bug，bug 也凝视着你'

nwe_content = pangumd.spacing_file('path/to/file.txt')
# nwe_content = '与 PM 战斗的人，应当小心自己不要成为 PM'
```

### 在命令行 (CLI) 中使用

```bash
$ pangumd "请使用uname -m指令来检查你的Linux操作系统是32位还是64位"
请使用 uname -m 指令来检查你的 Linux 操作系统是 32 位还是 64 位

$ python -m pangumd "为什么小明有问题都不Google？因为他有Bing"
为什么小明有问题都不 Google？因为他有 Bing

$ echo "未来的某一天，Gmail配备的AI可能会得出一个结论：想要消灭垃圾邮件最好的办法就是消灭人类" >> path/to/file.txt
$ pangumd -f path/to/file.txt >> pangu_file.txt
$ cat pangu_file.txt
未来的某一天，Gmail 配备的 AI 可能会得出一个结论：想要消灭垃圾邮件最好的办法就是消灭人类

$ echo "心里想的是Microservice，手里做的是Distributed Monolith" | pangumd
心里想的是 Microservice，手里做的是 Distributed Monolith

$ echo "你从什么时候开始产生了我没使用Monkey Patch的错觉?" | python -m pangumd
你从什么时候开始产生了我没使用 Monkey Patch 的错覺？
```

## Pre-commit 钩子

若要将 pangumd 作为 pre-commit 钩子使用，请将以下内容添加到您的 `.pre-commit-config.yaml` 中：

```yaml
repos:
  - repo: https://github.com/kingronjan/pangumd
    rev: 0.1.4 
    hooks:
      - id: pangumd
        files: \.(md|txt)$
```

然后安装钩子：

```bash
pre-commit install
```

现在，pangumd 将在每次提交前自动在您的 Markdown 和文本文件上运行，确保中日韩 (CJK) 字符与半角字符之间有适当的间距。

## 许可证

MIT 许可证