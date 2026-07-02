from django.test import SimpleTestCase

from audits.services.parser import parse_page

SAMPLE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Example Domain — a test page</title>
  <meta name="description" content="A short description used for testing the parser module.">
  <link rel="canonical" href="https://example.com/">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta property="og:title" content="Example Domain">
  <script type="application/ld+json">{"@context": "https://schema.org", "@type": "Organization", "name": "Example"}</script>
</head>
<body>
  <h1>Main heading</h1>
  <h2>Sub heading</h2>
  <p>Some visible body text used to pad out the word count for the test.</p>
  <img src="/logo.png" alt="Example logo">
  <img src="/banner.png">
  <a href="/about">About us</a>
  <a href="https://external.example/">External site</a>
  <a href="#">click here</a>
</body>
</html>
"""


class ParsePageTests(SimpleTestCase):
    def setUp(self):
        self.page = parse_page(SAMPLE_HTML, "https://example.com/")

    def test_extracts_title_and_description(self):
        self.assertEqual(self.page["title"], "Example Domain — a test page")
        self.assertIn("short description", self.page["meta_description"])

    def test_extracts_canonical(self):
        self.assertEqual(self.page["canonical_url"], "https://example.com/")

    def test_counts_headings(self):
        self.assertEqual(self.page["h1_count"], 1)
        self.assertEqual(len(self.page["headings"]), 2)

    def test_counts_images_and_missing_alt(self):
        self.assertEqual(self.page["image_count"], 2)
        self.assertEqual(len(self.page["images_missing_alt"]), 1)

    def test_classifies_internal_vs_external_links(self):
        self.assertEqual(len(self.page["internal_links"]), 1)
        self.assertEqual(len(self.page["external_links"]), 1)

    def test_parses_json_ld(self):
        self.assertEqual(len(self.page["json_ld_blocks"]), 1)
        self.assertTrue(self.page["json_ld_blocks"][0]["valid"])
        self.assertIn("Organization", self.page["json_ld_blocks"][0]["types"])

    def test_extracts_og_tags(self):
        self.assertEqual(self.page["og_tags"].get("og:title"), "Example Domain")
