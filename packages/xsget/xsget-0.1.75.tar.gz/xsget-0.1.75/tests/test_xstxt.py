# Copyright (C) 2021,2022,2023,2024,2025,2026 Kian-Meng Ang
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# pylint: disable=C0114,C0116

import argparse
import logging
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import regex as re
from bs4 import BeautifulSoup

from xsget.chapter import Chapter
from xsget.xstxt import (
    DEFAULT_CONFIG_FILE,
    ConfigFileHandler,
    _compile_regex_replacements,
    _read_and_extract_chapter,
    _run_monitor,
    extract_body,
    extract_chapter,
    extract_title,
    generate_book,
    generate_multiple_txt,
    generate_single_txt,
    get_html_files,
    main,
    search_and_replace,
    wrap,
)

# Taken from: https://zh.wikisource.org/wiki/詩經/關雎
CTEXT = """\
　　孔子論《詩》，以《關雎》為始。言太上者民之父母，后夫人之
行不侔乎天地，則無以奉神靈之统而理萬物之宜，故《詩》曰：「窈
窕淑女，君子好逑。」言能致其貞淑，不贰其操，情欲之感無介乎容
儀，晏私之意不形乎動静，夫然後可以配至尊而為宗廟主。此綱紀之
首、王教之端也。
"""


def test_get_html_files_sorted_in_natural_order(tmpdir):
    for name in ["200", "2", "100"]:
        tmpdir.join(f"{name}.html").write("")

    path = str(tmpdir)
    assert get_html_files([f"{path}/*.html"], 0, []) == [
        Path(f"{path}/2.html"),
        Path(f"{path}/100.html"),
        Path(f"{path}/200.html"),
    ]


def test_get_html_files_exclude_filter(tmpdir):
    for name in ["a", "2", "xyz"]:
        tmpdir.join(f"{name}.html").write("")

    path = str(tmpdir)
    assert get_html_files([f"{path}/*.html"], 0, [f"{path}/xyz.html"]) == [
        Path(f"{path}/2.html"),
        Path(f"{path}/a.html"),
    ]


def test_get_single_html_file(tmpdir):
    single = tmpdir.join("single.html")
    single.write("")

    path = str(tmpdir)
    assert get_html_files([f"{path}/single.html"], 0, []) == [
        Path(f"{path}/single.html"),
    ]


def test_get_html_files_by_limit(tmpdir):
    for i in range(5):
        tmpdir.join(f"{i}.html").write("")

    path = str(tmpdir)
    assert get_html_files([f"{path}/*.html"], 3, []) == [
        Path(f"{path}/0.html"),
        Path(f"{path}/1.html"),
        Path(f"{path}/2.html"),
    ]


def test_get_no_html_files(caplog):
    path = "foobar/*.html"
    assert get_html_files([path], 0, []) == []
    assert f"No input files found in: {path}" in caplog.text


def test_get_html_files_with_non_existent_exclude(caplog):
    # Create some dummy files
    path = "temp_dir"
    Path(path).mkdir(exist_ok=True)
    Path(path, "file1.html").touch()
    Path(path, "file2.html").touch()

    # Call with a non-existent exclude pattern
    result = get_html_files(
        [f"{path}/*.html"],
        0,
        [f"{path}/non_existent_*.html"],
    )
    assert len(result) == 2  # Both files should still be included
    assert (
        f"No exclude files found in: {path}/non_existent_*.html" in caplog.text
    )

    # Clean up
    shutil.rmtree(path)


async def test_extract_chapter():
    html = """
        <html>
        <head><title>My Title</title></head>
        <body>
            <div id="content">My Content</div>
        </body>
        </html>
    """
    config = argparse.Namespace(
        title_css_path="title",
        body_css_path="div#content",
        html_replace=[],
        compiled_html_replace=[],
        debug=False,
    )
    chapter = await extract_chapter(html, config)
    chapter.filename = "123.html"
    assert chapter.filename == "123.html"
    assert chapter.title == "My Title"
    assert chapter.content == "My Content"
    assert str(chapter) == "My Title\n\nMy Content"
    assert repr(chapter) == (
        "Chapter(content='My Content', title='My Title', "
        "filename='123.html', content_path='')"
    )


@pytest.mark.asyncio
async def test_extract_chapter_with_html_replace():
    html = """
        <html>
        <head><title>My Title</title></head>
        <body>
            <div id="content">
            &nbsp;&nbsp;&nbsp;&nbsp;Paragraph1
            <br/><br />
            &nbsp;&nbsp;&nbsp;&nbsp;Paragraph2
            <br/>
            <br />
            &nbsp;&nbsp;&nbsp;&nbsp;Paragraph3
            </div>
        </body>
        </html>
    """
    raw_replacements = [
        ("<br/>", "11"),
        ("<br />", "22"),
        ("&nbsp;&nbsp;", "33"),
    ]
    compiled_replacements = [
        (re.compile(r"<br/>", re.MULTILINE), r"11"),
        (re.compile(r"<br />", re.MULTILINE), r"22"),
        (re.compile(r"&nbsp;&nbsp;", re.MULTILINE), r"33"),
    ]
    config = argparse.Namespace(
        title_css_path="title",
        body_css_path="div#content",
        html_replace=raw_replacements,
        compiled_html_replace=compiled_replacements,
        debug=False,
    )
    chapter = await extract_chapter(html, config)

    match_regex = (
        "My Title\n\n"
        r"\n\s+3333Paragraph1"
        r"\n\s+1122"
        r"\n\s+3333Paragraph2"
        r"\n\s+11"
        r"\n\s+22"
        r"\n\s+3333Paragraph3"
    )
    assert re.match(match_regex, str(chapter))


async def test_extract_chapter_without_css_path():
    html = """
        <html>
        <head><title>My Title</title></head>
        <body>
            <div id="content">My Content</div>
        </body>
        </html>
    """
    config = argparse.Namespace(
        title_css_path=None,
        body_css_path=None,
        html_replace=[],
        compiled_html_replace=[],
        debug=False,
    )
    chapter = await extract_chapter(html, config)
    assert chapter.title == ""
    assert chapter.content == ""
    assert str(chapter) == ""
    assert (
        repr(chapter)
        == "Chapter(content='', title='', filename='', content_path='')"
    )


def test_generate_single_txt(tmpdir):
    chapters = [
        Chapter("MyTitle1", "MyContent1"),
        Chapter("MyTitle2", "MyContent2"),
    ]

    config = argparse.Namespace(
        book_title="Book Title",
        book_author="Book Author",
        output=str(Path(tmpdir, "book.txt")),
        txt_replace=(),
        compiled_txt_replace=[],
        width=60,
        indent_chars="",
        paragraph_separator="\n\n",
        fullwidth=False,
        language="zh",
        output_dir="output",
        gettext_func=lambda x: x,
    )
    generate_single_txt(chapters, config)

    with Path(config.output).open(encoding="utf8") as file:
        content = file.read()
        assert content == (
            "---\n"
            "书名：Book Title\n"
            "作者：Book Author\n"
            "---\n\n"
            "MyTitle1\n\nMyContent1\n\n"
            "MyTitle2\n\nMyContent2"
        )


def test_generate_single_txt_with_search_and_replace(tmpdir):
    book = [
        Chapter("MyTitle1", "MyContent1"),
        Chapter("MyTitle2", "MyContent2"),
    ]

    raw_replacements = [
        ("Title", "TITLE"),
        ("My", "YY"),
    ]
    compiled_replacements = [
        (re.compile(r"Title", re.MULTILINE), r"TITLE"),
        (re.compile(r"My", re.MULTILINE), r"YY"),
    ]
    config = argparse.Namespace(
        book_title="Book Title",
        book_author="Book Author",
        output=str(Path(tmpdir, "book.txt")),
        txt_replace=raw_replacements,
        compiled_txt_replace=compiled_replacements,
        width=60,
        indent_chars="",
        paragraph_separator="\n\n",
        fullwidth=False,
        language="zh",
        output_dir="output",
        gettext_func=lambda x: x,
    )
    generate_single_txt(book, config)

    with Path(config.output).open(encoding="utf8") as file:
        content = file.read()
        assert content == (
            "---\n"
            "书名：Book Title\n"
            "作者：Book Author\n"
            "---\n\n"
            "YYTITLE1\n\n"
            "YYContent1\n\n"
            "YYTITLE2\n\n"
            "YYContent2"
        )


def test_chapter_model_to_str():
    fixture_and_result = [
        (Chapter("MyTitle", "MyContent"), "MyTitle\n\nMyContent"),
        (Chapter("MyTitle", ""), "MyTitle"),
        (Chapter(title="MyTitle"), "MyTitle"),
        (Chapter("", "MyContent"), "MyContent"),
        (Chapter(content="MyContent"), "MyContent"),
        (Chapter(), ""),
    ]
    for fixture, result in fixture_and_result:
        assert str(fixture) == result


def test_compile_regex_replacements_with_invalid_regex():
    with pytest.raises(re.error):
        _compile_regex_replacements([("[", "")])


def test_search_and_replace_with_empty_regexs():
    content = "This is some content."
    result = search_and_replace(content, [])
    assert result == content


def test_wrap_by_width():
    config = argparse.Namespace(
        width=20,
        indent_chars="",
        paragraph_separator="\n\n",
        fullwidth=False,
    )
    first_line = wrap(CTEXT, config).split("\n", maxsplit=1)[0]
    assert first_line == "\u3000\u3000孔子論《詩》，以"


def test_wrap_with_empty_content():
    config = argparse.Namespace(
        width=20,
        indent_chars="",
        paragraph_separator="\n\n",
        fullwidth=False,
    )
    assert wrap("", config) == ""
    assert wrap("   ", config) == ""  # `wrap` strips whitespace for width > 0


def test_no_wrap():
    config = argparse.Namespace(
        width=0,
        indent_chars="",
        paragraph_separator="\n",
        fullwidth=False,
    )
    first_line = wrap(CTEXT, config).split("\n", maxsplit=1)[0]
    assert first_line == (
        "\u3000\u3000孔子論《詩》，以《關雎》為始。言太上者民之父母，后夫人之"
    )


def test_wrap_with_indent_characters():
    config = argparse.Namespace(
        width=20,
        indent_chars="0000",
        paragraph_separator="\n",
        fullwidth=False,
    )
    first_line = wrap(CTEXT, config).split("\n", maxsplit=1)[0]
    assert first_line == "0000孔子論《詩》"


async def test_extract_title_no_match():
    html = "<html><head><title>My Title</title></head><body></body></html>"
    soup = BeautifulSoup(html, features="lxml")
    title = extract_title(soup, "h1")  # Non-existent CSS path
    assert title == ""


async def test_extract_title_empty_element():
    html = "<html><head><title></title></head><body></body></html>"
    soup = BeautifulSoup(html, features="lxml")
    title = extract_title(
        soup,
        "title",
    )  # Existing CSS path, but empty element
    assert title == ""


async def test_extract_body_no_match():
    html = "<html><body><p>Content</p></body></html>"
    soup = BeautifulSoup(html, features="lxml")
    body = extract_body(soup, "div#content")  # Non-existent CSS path
    assert body == ""


async def test_extract_body_empty_element():
    html = "<html><body><div id='content'></div></body></html>"
    soup = BeautifulSoup(html, features="lxml")
    body = extract_body(
        soup,
        "div#content",
    )  # Existing CSS path, but empty element
    assert body == ""


def test_generate_multiple_txt(tmpdir):
    chapters = [
        Chapter("Title1", "Content1", filename="file1.html"),
        Chapter("Title2", "Content2", filename="file2.html"),
    ]
    output_dir = Path(tmpdir, "output_files")
    config = argparse.Namespace(
        output_dir=str(output_dir),
        txt_replace=[],
        compiled_txt_replace=[],
        fullwidth=False,
        width=0,
        indent_chars="",
        paragraph_separator="\n\n",
        language="en",
    )
    generate_multiple_txt(chapters, config)

    assert Path(output_dir, "file1.txt").exists()
    assert Path(output_dir, "file2.txt").exists()
    with Path(output_dir, "file1.txt").open(encoding="utf8") as f:
        assert f.read() == "Title1\n\nContent1"
    with Path(output_dir, "file2.txt").open(encoding="utf8") as f:
        assert f.read() == "Title2\n\nContent2"


@pytest.mark.asyncio
async def test_generate_book_purge(mocker, tmpdir):
    # Mock necessary functions to avoid actual file operations and async calls
    mocker.patch("xsget.xstxt.get_html_files", return_value=["dummy.html"])
    mocker.patch("xsget.xstxt.extract_chapter", return_value=Chapter("T", "C"))
    mocker.patch("xsget.xstxt.generate_single_txt")
    mocker.patch("xsget.xstxt.generate_multiple_txt")
    mocker.patch("shutil.rmtree")  # Mock rmtree

    # Mock aiofiles.open to prevent FileNotFoundError and support async with
    # Create a mock for the file handle that will be returned by aiofiles.open
    mock_file_handle = mocker.AsyncMock()
    mock_file_handle.read.return_value = b"<html><body>Content</body></html>"

    # Explicitly set __aenter__ and __aexit__ for the mock_file_handle
    # This is often not needed for AsyncMock, but can help debug stubborn
    # issues.
    mock_file_handle.__aenter__ = mocker.AsyncMock(
        return_value=mock_file_handle,
    )
    mock_file_handle.__aexit__ = mocker.AsyncMock(return_value=None)

    # Patch aiofiles.open to return this mock_file_handle directly.
    mocker.patch("aiofiles.open", return_value=mock_file_handle)

    output_dir = Path(tmpdir, "output")
    output_dir.mkdir()

    config = argparse.Namespace(
        input=["*.html"],
        limit=0,
        exclude=[],
        debug=False,
        output_dir=str(output_dir),
        output="book.txt",
        purge=True,
        yes=False,
        output_individual_file=False,
        html_replace=[],
        txt_replace=[],
        compiled_html_replace=[],
        compiled_txt_replace=[],
    )

    await generate_book(config)

    # Assert that rmtree was called with the correct path
    shutil.rmtree.assert_called_once_with(output_dir)


@pytest.mark.asyncio
async def test_read_and_extract_chapter_debug(mocker, caplog):
    caplog.set_level(logging.DEBUG)
    config = argparse.Namespace(debug=True)
    filename = Path("test.html")

    # Mock aiofiles to return content so it proceeds to completion or error
    mock_file = mocker.AsyncMock()
    # Return bytes that are valid
    mock_file.read.return_value = b"<html></html>"
    mock_file.__aenter__.return_value = mock_file
    mocker.patch("aiofiles.open", return_value=mock_file)
    mocker.patch("xsget.xstxt.extract_chapter", return_value=Chapter("T", "C"))

    await _read_and_extract_chapter(filename, config, 1, 10)

    assert "Processing file: test.html" in caplog.text


@pytest.mark.asyncio
async def test_read_and_extract_chapter_progress(mocker, capsys):
    config = argparse.Namespace(debug=False)
    filename = Path("test.html")

    mocker.patch("sys.stdout.isatty", return_value=True)

    mock_file = mocker.AsyncMock()
    mock_file.read.return_value = b"<html></html>"
    mock_file.__aenter__.return_value = mock_file
    mocker.patch("aiofiles.open", return_value=mock_file)
    mocker.patch("xsget.xstxt.extract_chapter", return_value=Chapter("T", "C"))

    await _read_and_extract_chapter(filename, config, 5, 10)

    captured = capsys.readouterr()
    assert "Processing file: test.html (50.0% - 5 / 10)" in captured.out


@pytest.mark.asyncio
async def test_extract_chapter_debug(caplog):
    caplog.set_level(logging.DEBUG)
    config = argparse.Namespace(
        debug=True,
        compiled_html_replace=[],
        title_css_path="h1",
        body_css_path="p",
    )
    from bs4 import BeautifulSoup

    soup = BeautifulSoup("<h1>T</h1><p>C</p>", "html.parser")

    await extract_chapter(soup, config, "test.html")

    assert (
        "Processing Chapter(content='C', title='T', filename='test.html', content_path='')"
        in caplog.text
    )


@pytest.mark.asyncio
async def test_extract_chapter_progress(mocker, capsys):
    config = argparse.Namespace(
        debug=False,
        compiled_html_replace=[],
        title_css_path="h1",
        body_css_path="p",
    )
    mocker.patch("sys.stdout.isatty", return_value=True)
    from bs4 import BeautifulSoup

    soup = BeautifulSoup("<h1>T</h1><p>C</p>", "html.parser")

    await extract_chapter(soup, config, "test.html")

    captured = capsys.readouterr()
    assert "Processing Chapter" in captured.out


def test_wrap_negative_width():
    config = argparse.Namespace(
        width=-1, paragraph_separator="\n", indent_chars="  "
    )
    content = "Hello World"
    # width < 0 means infinite width (sys.maxsize) when indenting
    res = wrap(content, config)
    assert res == "  Hello World"


def test_generate_multiple_txt_options(tmp_path, caplog):
    caplog.set_level(logging.INFO)
    chapters = [Chapter("T", "Content", filename="ch1.html")]
    output_dir = tmp_path / "out"
    config = argparse.Namespace(
        output_dir=str(output_dir),
        output_individual_file=True,
        compiled_txt_replace=[(re.compile("Content"), "NewContent")],
        fullwidth=True,
        width=0,
        paragraph_separator="\n",
        indent_chars="",
        txt_replace=[],
    )

    generate_multiple_txt(chapters, config)

    assert (output_dir / "ch1.txt").exists()
    assert "Converting halfwidth ASCII to fullwidth" in caplog.text
    content = (output_dir / "ch1.txt").read_text(encoding="utf8")


def test_generate_single_txt_options(tmp_path, caplog):
    caplog.set_level(logging.INFO)
    chapters = [Chapter("T", "Content")]
    config = argparse.Namespace(
        output_dir=str(tmp_path),
        output="book.txt",
        compiled_txt_replace=[],
        fullwidth=True,
        width=0,
        paragraph_separator="\n",
        indent_chars="",
        book_title="BT",
        book_author="BA",
        gettext_func=lambda x: x,
    )

    generate_single_txt(chapters, config)
    assert "Converting halfwidth ASCII to fullwidth" in caplog.text


def test_main_exception(mocker, caplog):
    mocker.patch(
        "xsget.xstxt._load_config", side_effect=ValueError("Test Error")
    )

    with pytest.raises(SystemExit):
        main([])

    assert "error: Test Error" in caplog.text


@pytest.mark.asyncio
async def test_read_and_extract_chapter_undecodable(mocker, caplog):
    config = argparse.Namespace(debug=False)
    filename = Path("bad.html")

    mock_file = mocker.AsyncMock()
    mock_file.read.return_value = b"\xff"
    mock_file.__aenter__.return_value = mock_file

    mocker.patch("aiofiles.open", return_value=mock_file)

    # Mock UnicodeDammit to return None
    with patch("xsget.xstxt.UnicodeDammit") as MockDammit:
        instance = MockDammit.return_value
        instance.unicode_markup = None

        result = await _read_and_extract_chapter(filename, config, 1, 1)
        assert result is None
        assert "Skipping empty or undecodable file" in caplog.text


@pytest.mark.asyncio
async def test_generate_book_output_individual(mocker):
    config = argparse.Namespace(
        input=["*.html"],
        limit=0,
        exclude=[],
        debug=False,
        output_dir="out",
        purge=False,
        output_individual_file=True,
        yes=False,
    )

    mocker.patch("xsget.xstxt.get_html_files", return_value=[Path("1.html")])
    mocker.patch(
        "xsget.xstxt._read_and_extract_chapter",
        return_value=Chapter("T", "C", filename="1.txt"),
    )
    mock_gen_multi = mocker.patch("xsget.xstxt.generate_multiple_txt")

    mocker.patch("sys.stdout.isatty", return_value=True)
    mocker.patch(
        "os.get_terminal_size", return_value=os.terminal_size((80, 24))
    )

    await generate_book(config)

    mock_gen_multi.assert_called_once()


def test_run_monitor(mocker):
    config = argparse.Namespace(config="config.toml")

    mock_observer = mocker.patch("xsget.xstxt.Observer")
    mock_observer_instance = mock_observer.return_value
    mock_observer_instance.is_alive.side_effect = [True, False]

    _run_monitor(config)

    mock_observer_instance.start.assert_called_once()
    mock_observer_instance.stop.assert_called_once()


def test_config_file_handler(mocker):
    # Important: _load_config returns a Namespace.
    # self.config.config is accessed in on_modified.
    config = argparse.Namespace(config="test_config.toml", debug=False)
    handler = ConfigFileHandler(config)

    event = MagicMock()
    event.src_path = DEFAULT_CONFIG_FILE  # "xstxt.toml"

    mocker.patch("xsget.xstxt._load_config", return_value=config)
    mocker.patch("xsget.xstxt.generate_book")

    handler.on_modified(event)

    # Need to check call on the module function, but it's imported in this test file
    # `generate_book` is imported. `xstxt.generate_book` patch will work if
    # ConfigFileHandler calls it from the module.
    # In `src/xsget/xstxt.py`: `asyncio.run(generate_book(config), debug=config.debug)`
    # Since `ConfigFileHandler` is defined in `xstxt.py`, it sees `generate_book` in globals.

    # Let's verify the patch target. `mocker.patch("xsget.xstxt.generate_book")`
    # this mocks the function in the module. ConfigFileHandler uses that.

    # We can assert on the mock.
    # But wait, we didn't capture the mock object here.
    # mocker.patch returns the mock.
    mock_gen = mocker.patch("xsget.xstxt.generate_book")
    # Wait, I already patched it above but didn't assign.
    # Let's re-patch with variable.

    # Actually, in the previous code block I did:
    # mocker.patch("xsget.xstxt.generate_book")
    # handler.on_modified(event)
    # xstxt.generate_book.assert_called_once() -> this referred to the imported module `xstxt` in the temp file.
    # Here I don't have `xstxt` module imported entirely, I imported functions.

    # So I should change how I assert.
    # `xsget.xstxt.generate_book` is being patched. this replaces the object in sys.modules.
    # `from xsget.xstxt import generate_book` in this test file might still point to original if imported before patch?
    # Mocker handles this if setup correctly.

    # Safest way:
    mock_generate_book = mocker.patch("xsget.xstxt.generate_book")

    handler.on_modified(event)

    mock_generate_book.assert_called_once()


def test_main_monitor(mocker):
    config = argparse.Namespace(debug=False, monitor=True)
    mocker.patch("xsget.xstxt._load_config", return_value=config)
    mocker.patch("xsget.xstxt.generate_book")
    mock_run_monitor = mocker.patch("xsget.xstxt._run_monitor")

    main([])

    mock_run_monitor.assert_called_once()


def test_config_file_handler_ignore_other_files(mocker):
    config = argparse.Namespace()
    handler = ConfigFileHandler(config)

    event = MagicMock()
    event.src_path = "other.xml"

    # Needs to be mocked because it's imported in the module scope
    mock_load = mocker.patch("xsget.xstxt._load_config")

    handler.on_modified(event)

    mock_load.assert_not_called()
