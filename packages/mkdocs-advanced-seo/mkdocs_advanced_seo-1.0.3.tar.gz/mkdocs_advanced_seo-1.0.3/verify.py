import os
import sys
from bs4 import BeautifulSoup

def verify_site():
    # Check Home Page (General defaults)
    index_path = 'site/index.html'
    if not os.path.exists(index_path):
        print(f"Error: {index_path} not found.")
        sys.exit(1)
        
    with open(index_path, 'r', encoding='utf-8') as f:
        soup_home = BeautifulSoup(f, 'html.parser')
        
    # Check Test Page (Specific features)
    test_path = 'site/test-seo/index.html'
    if not os.path.exists(test_path):
        print(f"Error: {test_path} not found.")
        sys.exit(1)
        
    with open(test_path, 'r', encoding='utf-8') as f:
        soup_test = BeautifulSoup(f, 'html.parser')

    errors = []

    def check(soup, name, content, attr='name', msg_prefix=''):
        found = False
        for tag in soup.find_all('meta', attrs={attr: name}):
            if tag.get('content') == content:
                found = True
                break
        if not found:
            actual = [t.get('content') for t in soup.find_all('meta', attrs={attr: name})]
            errors.append(f"{msg_prefix} Missing {attr}='{name}'. Expected '{content}', found {actual}")

    # --- Verify Home Page ---
    # Should use site_description fallback
    check(soup_home, 'description', 'The comprehensive, deep, and robust SEO plugin for MkDocs.', msg_prefix='[HOME]')
    # Should use site_name in title (or "Home - site_name")
    # Our plugin uses config['site_name'] if page title is same or empty? 
    # Actually logic: if page.title != site_name return page.title else site_name. 
    # For index, page.title is usually "MkDocs Advanced SEO Plugin" (from H1).
    check(soup_home, 'og:title', 'MkDocs Advanced SEO Plugin', attr='property', msg_prefix='[HOME]')
    
    # Canonical Checks
    # Should use site_url as base
    # Home page url is '.' -> ''
    # Expect: https://raineblog.dpdns.org/mkdocs-advanced-seo/
    canonical_home = soup_home.find('link', rel='canonical')
    if not canonical_home:
         errors.append("[HOME] Missing canonical check")
    elif canonical_home['href'] != 'https://raineblog.dpdns.org/mkdocs-advanced-seo/':
         errors.append(f"[HOME] Incorrect canonical: {canonical_home['href']}")
    # Since 'social' plugin is active, expected: assets/images/social/index.png
    # URL base: https://raineblog.dpdns.org/mkdocs-advanced-seo/
    social_url = 'https://raineblog.dpdns.org/mkdocs-advanced-seo/assets/images/social/index.png'
    # We can't guarantee 'social' plugin actually runs in this env if dependencies missing, 
    # but we can check if our plugin *tried* to generate the URL (it doesn't check file existence).
    # Wait, our plugin logic: "if 'social' in config['plugins']".
    # So if we installed mkdocs-material, it should be there.
    check(soup_home, 'og:image', social_url, attr='property', msg_prefix='[HOME]')

    # --- Verify Test Page ---
    # Custom description
    check(soup_test, 'description', 'Deep testing description', msg_prefix='[TEST]')
    # Custom image (frontmatter overrides social)
    check(soup_test, 'og:image', 'https://raineblog.dpdns.org/mkdocs-advanced-seo/assets/custom.jpg', attr='property', msg_prefix='[TEST]')
    
    # JSON-LD Dates
    script_tag = soup_test.find('script', type='application/ld+json')
    if not script_tag:
        errors.append("[TEST] Missing JSON-LD")
    else:
        import json
        try:
            data = json.loads(script_tag.string)
            if data.get('datePublished') != '2025-07-23T07:55:08.813591+08:00':
                errors.append(f"[TEST] Incorrect datePublished: {data.get('datePublished')}")
            # dateModified might vary if we didn't mock it well? 
            # In test-seo.md we set document_dates_updated: 2025-07-23T07:55:08.813591+00:00
            # Note: The +00:00 offset might be normalized to Z or +00:00.
            # Python isoformat() keeps +00:00 usually.
            expected_mod = '2025-07-23T07:55:08.813591+00:00'
            if data.get('dateModified') != expected_mod:
                 errors.append(f"[TEST] Incorrect dateModified: {data.get('dateModified')}")
        except Exception as e:
            errors.append(f"[TEST] JSON-LD error: {e}")

    if errors:
        print("Verification FAILED:")
        for e in errors:
            print(f"- {e}")
        sys.exit(1)
    else:
        print("Verification PASSED!")

if __name__ == "__main__":
    verify_site()
