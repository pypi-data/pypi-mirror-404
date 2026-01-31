from textwrap import dedent

import pangumd

from .utils import get_fixture_path


def test_strong_emphasis():
    assert pangumd.spacing_text('Hello**你好**吗') == 'Hello **你好**吗'
    assert pangumd.spacing_text('今天的天气**很不错**哦') == '今天的天气**很不错**哦'
    assert pangumd.spacing_text('这是\n**bold**字体') == '这是\n**bold** 字体'
    assert pangumd.spacing_text('这是**bold**,字体') == '这是 **bold**, 字体'
    assert pangumd.spacing_text('这是**bo*加*ld**,字体') == '这是 **bo *加* ld**, 字体'


def test_function_call_not_modified():
    assert (
        pangumd.spacing_text('用`function_call(param1, param2)`函数')
        == '用 `function_call(param1, param2)`函数'
    )
    assert (
        pangumd.spacing_text('用`function_call(param1): return`函数')
        == '用 `function_call(param1): return` 函数'
    )


def test_indent_after_blank_line():
    text = dedent("""
    据我所知目前的几种规范落地工具：

    - [openspec](https://github.com/Fission-AI/OpenSpec)
    - [github/spec-kit: 💫 Toolkit to help you get started with Spec-Driven Development](https://github.com/github/spec-kit)

    我目前仅仅使用过 openspec。""")
    assert pangumd.spacing_text(text) == text


def test_link_not_modified():
    text = dedent("""
    - [分享个人在用的 IFLOW 编程全局提示词](https://vibex.iflow.cn/t/topic/257) 等
    - [awesome-cursor-rules-mdc/rules-mdc/python.mdc](https://github.com/sanjeed5/awesome) 参考价值""")
    assert pangumd.spacing_text(text) == text


def test_list_item_with_checkbox():
    text = dedent("""
    ### 面试资料

    - [ ] [Python/SQL/Django 面試題 - HackMD](https://hackmd.io/@_FqBW8dGS8a5ZqhdMwvpuA/ByYoWaxfD#Python%E7%89%B9%E6%80%A7%EF%BC%9A)
    - [ ] [taizilongxu/interview_python: 关于 Python 的面试题](https://github.com/taizilongxu/interview_python)""")
    assert pangumd.spacing_text(text) == text


def test_code_block_not_modified():
    text = dedent("""
    重命名原来的文件夹：

    ```shell
    mv $HOME/桌面 $HOME/Desktop
    mv $HOME/下载 $HOME/Downloads
    mv $HOME/模板 $HOME/Templates
    mv $HOME/公共 $HOME/Public
    mv $HOME/文档 $HOME/Documents
    mv $HOME/音乐 $HOME/Music
    mv $HOME/图片 $HOME/Pictures
    mv $HOME/视频 $HOME/Videos
    ```""")
    assert pangumd.spacing_text(text) == text


def test_all():
    filepath = get_fixture_path('all.md')
    formatted_filepath = get_fixture_path('all_formatted.md')

    with (
        open(filepath, encoding='utf-8') as f_raw,
        open(formatted_filepath, encoding='utf-8') as f_formatted,
    ):
        markdown_content = f_raw.read()
        fixed_content = f_formatted.read()

    spaced_content = pangumd.spacing(markdown_content)
    assert spaced_content == fixed_content
