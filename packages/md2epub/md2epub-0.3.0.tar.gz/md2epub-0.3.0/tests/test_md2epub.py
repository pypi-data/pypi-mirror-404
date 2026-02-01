
import os
import shutil
import pytest
from click.testing import CliRunner
from unittest import mock
from pathlib import Path
from md2epub.cli import main
from md2epub.converter import md_to_html
from md2epub.epub_builder import EpubBuilder
from md2epub.css_template import KDP_CSS

# --- Test Converter ---

def test_md_to_html_basic():
    md = "# Hello\n\nWorld"
    html = md_to_html(md)
    assert "<h1>Hello</h1>" in html
    assert "<p>World</p>" in html

def test_md_to_html_separators():
    md = "Paragraph 1\n\n***\n\nParagraph 2\n\nxxx\n\nParagraph 3"
    html = md_to_html(md)
    assert '<div class="asterisk-break">***</div>' in html
    assert '<div class="scene-break">xxx</div>' in html

def test_md_to_html_code_block():
    md = "```python\nprint('hello')\n```"
    html = md_to_html(md)
    # python-markdown fenced_code usually produces <pre><code class="language-python"> or similar
    assert "<pre>" in html
    assert "print('hello')" in html

# --- Test CLI (Integration with Cookiecutter mocked) ---

# --- Test CLI (Integration with Cookiecutter mocked) ---

@mock.patch('cookiecutter.main.cookiecutter')
def test_cli_init(mock_cookiecutter):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['init', 'mybook'])
        assert result.exit_code == 0
        assert "Initializing book in mybook" in result.output
        mock_cookiecutter.assert_called_once()
        # Verify call args include 'mybook' and template path
        args, kwargs = mock_cookiecutter.call_args
        assert kwargs['output_dir'] == 'mybook'
        assert 'templates/cookiecutter-book' in args[0]

@mock.patch('md2epub.epub_builder.EpubBuilder')
def test_cli_compile(mock_builder):
    # Setup mock
    instance = mock_builder.return_value
    instance.build.return_value = "output.epub"
    
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create dummy directory
        Path("mybook").mkdir()
        
        result = runner.invoke(main, ['compile', 'mybook'])
        assert result.exit_code == 0
        assert "Compiling book from mybook" in result.output
        assert "Successfully compiled to output.epub" in result.output
        
        mock_builder.assert_called_with('mybook')
        instance.build.assert_called_once()

# --- Test Builder (Integration) ---

@pytest.fixture
def sample_project(tmp_path):
    # Setup a manual project structure resembling what cookiecutter would make
    project_dir = tmp_path / "book"
    project_dir.mkdir()
    
    # Metadata
    metadata = """
title: Test Book
author: Tester
cover_image: cover.png
front_matter:
  - title.md
  - copyright.md
  - dedication.md
chapters:
  - chapter_1.md
    """
    (project_dir / "metadata.yaml").write_text(metadata, encoding='utf-8')
    
    # Files
    (project_dir / "title.md").write_text("# Title Page", encoding='utf-8')
    (project_dir / "copyright.md").write_text("# Copyright", encoding='utf-8')
    (project_dir / "dedication.md").write_text("# Dedication", encoding='utf-8')
    (project_dir / "chapter_1.md").write_text("# Chapter One\n\nContent", encoding='utf-8')
    
    # Cover (fake png)
    (project_dir / "cover.png").write_bytes(b'fakeimage')
    
    return project_dir

def test_epub_builder_build(sample_project, tmp_path):
    output_epub = tmp_path / "output.epub"
    builder = EpubBuilder(sample_project)
    
    # Build
    generated_path = builder.build(str(output_epub))
    
    assert os.path.exists(output_epub)
    
    # Inspect content (using ebooklib to read back would be ideal, or just checking zip content)
    import zipfile
    with zipfile.ZipFile(output_epub, 'r') as zf:
        files = zf.namelist()
        print(files)
        # Check essential files
        assert 'EPUB/content.opf' in files
        assert 'EPUB/toc.ncx' in files
        assert 'EPUB/style/nav.css' in files
        
        # Check Front Matter Files
        assert 'EPUB/title.xhtml' in files
        assert 'EPUB/copyright.xhtml' in files
        assert 'EPUB/dedication.xhtml' in files
        assert 'EPUB/chapter_1.xhtml' in files
        
        # Check generated TOC
        assert 'EPUB/toc.xhtml' in files
        
        # Check Cover
        # Ebooklib might name it differently or place it in OEBPS/ or EPUB/
        # Check content.opf for spine order
        opf_content = zf.read('EPUB/content.opf').decode('utf-8')
        
        # Verify Spine Order (rough check via regex or string finding)
        # Format: <itemref idref="..."/>
        # We expect: Cover -> Title -> Copyright -> TOC -> Dedication -> Chapter
        
        # We can find all itemref idrefs
        import re
        spine_refs = re.findall(r'<itemref idref="([^"]+)"', opf_content)
        
        # Mapping filenames to ids is internal to ebooklib, usually it generates ids like 'chapter_1' or 'item_...'
        # But we can verify existence of items.
        
        # Let's verify TOC content
        toc_content = zf.read('EPUB/toc.xhtml').decode('utf-8')
        assert 'href="dedication.xhtml">Dedication</a>' in toc_content
        assert 'href="chapter_1.xhtml">Chapter One</a>' in toc_content


def test_epub_builder_order_logic(sample_project):
    # This test verifies the spine list construction without creating full epub if possible,
    # or by inspecting the builder object state before write.
    # EbookLib writing is complex to mock out entirely, but we can verify builder.chapters/spine
    
    builder = EpubBuilder(sample_project)
    
    # Mocking write_epub to avoid actual write and just inspect state
    with mock.patch('ebooklib.epub.write_epub'):
        builder.build("dummy.epub")
        
        spine = builder.book.spine
        # spine is a list of items or strings ('nav')
        
        # We expect:
        # 0: Cover (EpubHtml)
        # 1: Title
        # 2: Copyright
        # 3: TOC
        # 4: Dedication
        # 5: Chapter
        # 'nav' (ncx/nav) might be separate in ebooklib spine handling or added.
        # In my code: spine_items = ['nav'] ... insert(0, cover) ... append others
        # Wait, if I insert cover at 0, 'nav' becomes 1. 
        # Cover -> Nav -> Title? No, Nav (HTML TOC or NCX) usually isn't in reading order spine for Kindle? 
        # Actually 'nav' in ebooklib usually refers to the NAV document for EPUB3.
        # Strict user order: Cover, Title, Copyright, *visible TOC*, Dedication...
        # My code: spine_items = ['nav']. insert(0, cover). 
        # Result: [Cover, 'nav', Title, Copyright, TOC_Page, Dedication...]
        # KDP might process 'nav' (hidden NAV) differently.
        # KDP Visible TOC is just an HTML page.
        
        filenames = []
        for item in spine:
            if hasattr(item, 'file_name'):
                filenames.append(item.file_name)
            else:
                filenames.append(str(item))
                
        # With current code:
        # spine_items = ['nav']
        # insert(0, cover) -> [cover, 'nav']
        # append title -> [cover, 'nav', title]
        # append copyright -> [cover, 'nav', title, copyright]
        # insert(len, toc) => insert at end? No, insert at len(spine_items) which is current end.
        # so [..., copyright, toc_page]
        # append dedication -> [..., toc_page, dedication]
        
        print(filenames)
        
        assert 'cover.xhtml' in filenames[0]
        # 'nav' (string or item) was removed from initial list.
        assert 'title.xhtml' in filenames[1]
        assert 'copyright.xhtml' in filenames[2]
        assert 'toc.xhtml' in filenames[3]
        assert 'dedication.xhtml' in filenames[4]
        assert 'chapter_1.xhtml' in filenames[5]

