
import os
import yaml
from pathlib import Path
from ebooklib import epub
from md2epub.converter import md_to_html
from md2epub.css_template import KDP_CSS

class EpubBuilder:
    def __init__(self, project_dir):
        self.project_dir = Path(project_dir)
        self.metadata_path = self.project_dir / "metadata.yaml"
        self.metadata = self._load_metadata()
        self.book = epub.EpubBook()
        self.chapters = []

    def _load_metadata(self):
        if not self.metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {self.metadata_path}")
        with open(self.metadata_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _read_file(self, filename):
        path = self.project_dir / filename
        if not path.exists():
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def build(self, output_filename=None):
        # Set Metadata
        self.book.set_identifier(self.metadata.get('id', 'book_id'))
        self.book.set_title(self.metadata.get('title', 'Untitled'))
        self.book.set_language(self.metadata.get('language', 'en'))
        author = self.metadata.get('author')
        if author:
            self.book.add_author(author)

        # CSS
        nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=KDP_CSS)
        self.book.add_item(nav_css)

        # Helper lists for TOC and Spine
        # We will build the spine items list strictly
        spine_items = [] # We start empty. 'nav' (EpubNav) will be added where appropriate, or not in linear flow.
        
        # Cover
        # ebooklib set_cover adds the item and usually sets it to linear=False or handles it.
        # But user wants strict ordering in the book flow.
        # set_cover usually makes it the first item in spine if not specified? 
        # Actually set_cover just adds the image item and sets meta cover.
        # We need an HTML cover page to be part of the flow if "Strict ordering: Cover" implies a page.
        # Usually EbookLib's set_cover is enough for "Cover" concept.
        # BUT if user wants "Cover (this page include the image)" as the *first page*:
        # We should ensure nothing comes before it.
        cover_image = self.metadata.get('cover_image')
        if cover_image:
             cover_path = self.project_dir / cover_image
             if cover_path.exists():
                 with open(cover_path, 'rb') as f:
                     self.book.set_cover("cover.png", f.read()) # Auto adds valid cover page usually? 
                     # set_cover adds an image item, and creates a cover.xhtml if configured? 
                     # No, set_cover only sets the image. We often need a wrapper page for it.
                     # Actually ebooklib doesn't auto-create cover.xhtml unless requested or via guide.
                     # Let's create a cover html manually to be safe and explicit.
                     cover_html = '<html><head></head><body><div style="text-align:center;"><img src="cover.png" alt="Cover"/></div></body></html>'
                     cover_page = epub.EpubHtml(title="Cover", file_name="cover.xhtml", lang='en')
                     cover_page.set_content(cover_html)
                     cover_page.add_item(nav_css)
                     self.book.add_item(cover_page)
                     spine_items.append(cover_page)

        # Helper to find file
        front_matter_files = self.metadata.get('front_matter', [])
        def find_file(partial_name):
            for f in front_matter_files:
                if partial_name in f.lower():
                    return f
            return None
            
        def create_chapter(filename, title):
            content = self._read_file(filename)
            if content:
                html_content = md_to_html(content)
                full_html = f'<html><head></head><body>{html_content}</body></html>'
                item = epub.EpubHtml(title=title, file_name=f'{Path(filename).stem}.xhtml', lang='en')
                item.set_content(full_html)
                item.add_item(nav_css)
                self.book.add_item(item)
                return item
            return None

        # Title
        title_file = find_file("title")
        if title_file:
            item = create_chapter(title_file, "Title Page")
            if item: spine_items.append(item)

        # Copyright
        copyright_file = find_file("copyright")
        if copyright_file:
            item = create_chapter(copyright_file, "Copyright")
            if item: spine_items.append(item)

        # TOC Placeholder (Will insert here later, need chapters first)
        toc_position = len(spine_items)

        # Dedication
        dedication_file = find_file("dedication")
        dedication_item = None
        if dedication_file:
            dedication_item = create_chapter(dedication_file, "Dedication")
            if dedication_item: spine_items.append(dedication_item)

        # Acknowledgement
        ack_file = find_file("ack")
        ack_item = None
        if ack_file:
            ack_item = create_chapter(ack_file, "Acknowledgement")
            if item: spine_items.append(ack_item)

        # Chapters
        chapter_files = self.metadata.get('chapters', [])
        toc_entries = [] # List of inputs for TOC (url, title)
        
        for ch_file in chapter_files:
            raw_content = self._read_file(ch_file)
            chapter_title = "Chapter"
            if raw_content:
                for line in raw_content.split('\n'):
                    if line.startswith('# '):
                        chapter_title = line[2:].strip()
                        break
            
            item = create_chapter(ch_file, chapter_title)
            if item:
                spine_items.append(item)
                toc_entries.append(item)

        # Generate TOC Page
        # We want to link to Chapters. Should we also link to Dedication/Ack?
        # Usually TOC links to actual content.
        # Let's include Dedication/Ack if they exist? Typically yes.
        # But Dedication comes *after* TOC.
        
        toc_html_content = ["<h1>Table of Contents</h1>", "<nav><ul>"]
        
        # Add Dedication to TOC if exists
        if dedication_item:
             toc_html_content.append(f'<li><a href="{dedication_item.file_name}">{dedication_item.title}</a></li>')

        # Add Acknowledgement to TOC if exists
        if ack_item:
             toc_html_content.append(f'<li><a href="{ack_item.file_name}">{ack_item.title}</a></li>')

        for entry in toc_entries:
            toc_html_content.append(f'<li><a href="{entry.file_name}">{entry.title}</a></li>')
        
        toc_html_content.append("</ul></nav>")
        
        toc_page = epub.EpubHtml(title="Table of Contents", file_name="toc.xhtml", lang='en')
        toc_page.set_content(f'<html><head></head><body>{"".join(toc_html_content)}</body></html>')
        toc_page.add_item(nav_css)
        self.book.add_item(toc_page)
        
        # Insert TOC at reserved position
        spine_items.insert(toc_position, toc_page)

        # Finalize structure
        self.book.toc = toc_entries # This is for the NCX/Logical TOC
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())

        self.book.spine = spine_items

        if not output_filename:
            output_filename = f"{self.metadata.get('title', 'book').replace(' ', '_')}.epub"
        
        epub.write_epub(output_filename, self.book, {})
        return output_filename
