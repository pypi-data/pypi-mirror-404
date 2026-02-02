# MkDocs Advanced SEO Plugin

Welcome to the official documentation for **mkdocs-advanced-seo**. This plugin provides a comprehensive, deep, and robust SEO solution for MkDocs sites.

## Core Features

- **Automated Meta Tags**: Intelligent generation of description, keywords, and author tags.
- **Social Media Ready**: Full support for Open Graph and Twitter Cards.
- **Smart Integration**: Auto-detects social images from `mkdocs-material` and dates from `mkdocs-document-dates`.
- **Structured Data**: JSON-LD generation for better Google Rich Results.

## Installation

```bash
pip install mkdocs-advanced-seo
```

## Quick Start

In your `mkdocs.yml`:

```yaml
plugins:
  - advanced-seo:
      url_base: https://your-site.com
```

That's it! The plugin will auto-configure based on your `site_name`, `site_description`, and other standard MkDocs settings.

## Configuration Reference

| Option | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `url_base` | `str` | `site_url` | Base URL for canonical links. |
| `use_canonical_url` | `bool` | `true` | Enable canonical URL tags. |
| `use_open_graph` | `bool` | `true` | Enable Open Graph tags. |
| `use_twitter_cards` | `bool` | `true` | Enable Twitter Cards. |
| `add_schema_org_json_ld` | `bool` | `true` | Inject JSON-LD structured data. |
| `og_type` | `str` | `website` | Default Open Graph type. |
| `support_document_dates` | `bool` | `true` | Use dates from other plugins. |

## Social Cards Integration

If you use `mkdocs-material` with the social plugin:

```yaml
plugins:
  - social
  - advanced-seo
```

The plugin will automatically detect generated social card images and use them for `og:image` and `twitter:image`. No extra configuration required!

## License

MIT License.
