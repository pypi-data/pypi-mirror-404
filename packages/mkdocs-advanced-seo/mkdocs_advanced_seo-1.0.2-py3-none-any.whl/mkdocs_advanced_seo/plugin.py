import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional, Union

from bs4 import BeautifulSoup
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from mkdocs.structure.pages import Page
from mkdocs.structure.files import File
from mkdocs.structure.files import File

# Set up logging
log = logging.getLogger("mkdocs.plugins.advanced-seo")

class AdvancedSEOPlugin(BasePlugin):
    config_scheme = (
        # Basic Meta
        ('url_base', config_options.Type(str, default='')),
        ('use_canonical_url', config_options.Type(bool, default=True)),
        ('add_schema_org_json_ld', config_options.Type(bool, default=True)),
        
        # Open Graph
        ('use_open_graph', config_options.Type(bool, default=True)),
        ('og_type', config_options.Type(str, default='website')),
        ('og_image', config_options.Type(str, default='')),
        ('og_locale', config_options.Type(str, default='en_US')),
        
        # Twitter Cards
        ('use_twitter_cards', config_options.Type(bool, default=True)),
        ('twitter_card_type', config_options.Type(str, default='summary_large_image')),
        ('twitter_image', config_options.Type(str, default='')),
        ('twitter_creator', config_options.Type(str, default='')),
        ('twitter_site', config_options.Type(str, default='')),

        # Integration compatibility
        ('support_document_dates', config_options.Type(bool, default=True)),
    )

    def on_post_page(self, output: str, page: Page, config: Dict[str, Any]) -> str:
        """
        Inject SEO meta tags into the page output.
        """
        soup = BeautifulSoup(output, 'html.parser')
        if not soup.head:
            log.warning(f"Could not find <head> in {page.file.src_path}. SEO tags not added.")
            return output

        # 1. Basic Meta Tags
        self._inject_basic_meta(soup, page, config)

        # 2. Open Graph
        if self.config['use_open_graph']:
            self._inject_open_graph(soup, page, config)

        # 3. Twitter Cards
        if self.config['use_twitter_cards']:
            self._inject_twitter_cards(soup, page, config)

        # 4. JSON-LD
        if self.config['add_schema_org_json_ld']:
            self._inject_json_ld(soup, page, config)

        return str(soup)

    def _get_page_title(self, page: Page, config: Dict[str, Any]) -> str:
        if page.title and page.title != config.get('site_name'):
             # MkDocs often appends " - Site Name" to page.title. 
             # We might want the raw title for og:title.
             # But page.title is usually just the H1.
             return page.title
        return config.get('site_name', '')

    def _get_page_description(self, page: Page, config: Dict[str, Any]) -> str:
        # 1. Check page.meta['description']
        if 'description' in page.meta:
             return str(page.meta['description'])
        
        # 2. Check config['site_description'] IF it's the homepage
        if page.is_homepage and config.get('site_description'):
            return config.get('site_description')
            
        # 3. Fallback: Site description (maybe? can be repetitive)
        # Use site description as fallback for all pages is a common strategy
        # but can lead to duplicate description issues.
        # Recommendation: Use site description only for home, or if nothing else exists.
        return config.get('site_description', '')

    def _get_canonical_url(self, page: Page, config: Dict[str, Any]) -> str:
        base = self.config['url_base'] or config.get('site_url', '')
        if not base:
            return ''
        # Ensure base doesn't end with slash and page.url doesn't start with slash (normally)
        # page.url is like 'foo/bar/'
        return base.rstrip('/') + '/' + page.url.lstrip('/')

    def _get_social_image(self, page: Page, config: Dict[str, Any]) -> Optional[str]:
        # 1. Frontmatter image
        if 'image' in page.meta:
            return self._resolve_url(page.meta['image'], config)
        
        # 2. Plugin config defaults (og_image / twitter_image)
        # Checked in caller, but here we prioritize "Smart" detection if configured
        
        # 3. MkDocs Material Social Cards Integration
        # If 'social' plugin is active, it generates images at assets/images/social/<page_url>index.png
        # We can detect if 'social' is in plugins list.
        # Note: config['plugins'] is a dict (PluginCollection)
        # Note: config['plugins'] is a dict (PluginCollection)
        if 'social' in config['plugins'] or 'material/social' in config['plugins']:
            # Construct expected path
            # The social plugin usually outputs to assets/images/social/...
            # verification: https://squidfunk.github.io/mkdocs-material/setup/setting-up-social-cards/
            path = page.url.rstrip('/')
            if path == '.':
                path = 'index'
            
            social_url = f"assets/images/social/{path}.png"
            return self._resolve_url(social_url, config)
            
        # 4. Fallback to global config
        if self.config['og_image']:
             return self._resolve_url(self.config['og_image'], config)
             
        return None

    def _inject_basic_meta(self, soup: BeautifulSoup, page: Page, config: Dict[str, Any]):
        desc = self._get_page_description(page, config)
        if desc:
            self._add_meta(soup, 'description', desc)

        # Keywords
        keywords = page.meta.get('keywords', []) or config.get('tags', []) # Support material 'tags' if present?
        # If keywords is list, join it
        if isinstance(keywords, list):
            keywords = ', '.join(map(str, keywords))
        if keywords:
            self._add_meta(soup, 'keywords', keywords)

        # Author
        author = page.meta.get('author', config.get('site_author', ''))
        if author:
            self._add_meta(soup, 'author', author)

        # Canonical
        if self.config['use_canonical_url']:
            canonical = self._get_canonical_url(page, config)
            if canonical:
                link = soup.new_tag('link', rel='canonical', href=canonical)
                soup.head.append(link)
    
    def _inject_open_graph(self, soup: BeautifulSoup, page: Page, config: Dict[str, Any]):
        title = self._get_page_title(page, config)
        desc = self._get_page_description(page, config)
        url = self._get_canonical_url(page, config)
        
        self._add_og(soup, 'og:type', self.config['og_type'])
        if title: self._add_og(soup, 'og:title', title)
        if desc: self._add_og(soup, 'og:description', desc)
        if url: self._add_og(soup, 'og:url', url)
        
        site_name = config.get('site_name')
        if site_name: self._add_og(soup, 'og:site_name', site_name)
        
        self._add_og(soup, 'og:locale', self.config['og_locale'])

        image_url = self._get_social_image(page, config)
        if image_url:
             self._add_og(soup, 'og:image', image_url)

    def _inject_twitter_cards(self, soup: BeautifulSoup, page: Page, config: Dict[str, Any]):
        self._add_meta(soup, 'twitter:card', self.config['twitter_card_type'])
        
        site = self.config['twitter_site']
        if site: self._add_meta(soup, 'twitter:site', site)
        
        creator = self.config['twitter_creator']
        if creator: self._add_meta(soup, 'twitter:creator', creator)

        title = self._get_page_title(page, config)
        if title: self._add_meta(soup, 'twitter:title', title)

        desc = self._get_page_description(page, config)
        if desc: self._add_meta(soup, 'twitter:description', desc)

        image_url = self._get_social_image(page, config)
        if image_url:
            self._add_meta(soup, 'twitter:image', image_url)

    def _inject_json_ld(self, soup: BeautifulSoup, page: Page, config: Dict[str, Any]):
        # Schema.org WebPage
        url = self._get_canonical_url(page, config)
        title = self._get_page_title(page, config)
        desc = self._get_page_description(page, config)
        
        # Dates
        date_published = self._get_date(page, config, 'created')
        date_modified = self._get_date(page, config, 'updated')
        
        author_name = page.meta.get('author', config.get('site_author', ''))
        
        schema = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": title,
            "url": url,
        }
        if desc:
            schema["description"] = desc
        if date_published:
            schema["datePublished"] = date_published
        if date_modified:
            schema["dateModified"] = date_modified
        if author_name:
            schema["author"] = {
                "@type": "Person",
                "name": author_name
            }
        
        # Breadcrumbs
        breadcrumbs = []
        if page.ancestors:
            items = []
            position = 1
            # Root
            site_url = self.config['url_base'] or config.get('site_url', '')
            items.append({
                "@type": "ListItem",
                "position": position,
                "name": config.get('site_name', 'Home'),
                "item": site_url
            })
            position += 1
            
            for ancestor in page.ancestors:
                 # Ancestors in mkdocs might be mixed, need to be careful
                 # Usually they are proper Page or Section objects
                 if hasattr(ancestor, 'url') and hasattr(ancestor, 'title'):
                     items.append({
                        "@type": "ListItem",
                        "position": position,
                        "name": ancestor.title,
                        "item": self._resolve_url(ancestor.url, config)
                     })
                     position += 1
            
            # Current page
            items.append({
                "@type": "ListItem",
                "position": position,
                "name": title,
                "item": url
            })
            
            schema["breadcrumb"] = {
                "@type": "BreadcrumbList",
                "itemListElement": items
            }

        import json
        script = soup.new_tag('script', type='application/ld+json')
        script.string = json.dumps(schema, ensure_ascii=False, indent=2)
        soup.head.append(script)

    def _get_date(self, page: Page, config: Dict[str, Any], type_: str) -> Optional[str]:
        # type_ is 'created' or 'updated'
        # Priority:
        # 1. page.meta['document_dates_' + type_] (from mkdocs-document-dates)
        # 2. page.meta['date'] (if type_ is created) or standard logic
        # 3. git timestamp (if available via other plugins)
        
        # Check explicit page meta from mkdocs-document-dates
        # keys: document_dates_created, document_dates_updated
        key = f"document_dates_{type_}"
        date_str = page.meta.get(key)
        
        if not date_str and type_ == 'updated':
            # Try recently_updated_docs config if available
            # But that is usually a list of pages.
            pass

        if date_str:
            return self._parse_date_string(date_str)
            
        return None

    def _parse_date_string(self, date_str: str) -> Optional[str]:
        # Handle 2025-07-23T07:55:08.813591+08:00
        # and other common formats
        try:
            from dateutil import parser
            dt = parser.parse(str(date_str))
            return dt.isoformat()
        except Exception as e:
            log.warning(f"Failed to parse date string '{date_str}': {e}")
            return None

    def _add_meta(self, soup: BeautifulSoup, name: str, content: str):
        # Check if already exists? (Maybe theme added it)
        # For now, just append.
        if not content: return
        tag = soup.new_tag('meta', attrs={'name': name, 'content': content})
        soup.head.append(tag)

    def _add_og(self, soup: BeautifulSoup, property: str, content: str):
        if not content: return
        tag = soup.new_tag('meta', attrs={'property': property, 'content': content})
        soup.head.append(tag)
        
    def _resolve_url(self, path: str, config: Dict[str, Any]) -> str:
        # Helper to make url absolute if it is relative
        base = self.config['url_base'] or config.get('site_url', '')
        if path.startswith('http'): 
            return path
        return base.rstrip('/') + '/' + path.lstrip('/')

