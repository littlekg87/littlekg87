import contextlib
import html
import io
from pathlib import Path
import re
import sys
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build


class BilingualSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with contextlib.redirect_stdout(io.StringIO()):
            build.main()
        cls.pages = {lang: (ROOT / '_site' / path).read_text(encoding='utf-8')
                     for lang, path in [('ko', 'index.html'), ('en', 'en/index.html')]}

    def data(self, lang, name):
        return yaml.safe_load((ROOT / '_data' / lang / (name + '.yml')).read_text(encoding='utf-8'))

    def test_records_and_links_match(self):
        for name in ['career', 'publications', 'talks', 'projects']:
            ko, en = self.data('ko', name), self.data('en', name)
            self.assertEqual(len(ko), len(en), name)
            for original, translated in zip(ko, en):
                for key in ['date', 'doi', 'kci', 'featured', 'slides', 'github']:
                    self.assertEqual(original.get(key), translated.get(key), (name, key))
                if 'period' in original:
                    self.assertEqual(original['period'].replace('현재', 'Present'), translated['period'])
                self.assertIn(html.escape(translated['title'], quote=False), html.escape(html.unescape(self.pages['en']), quote=False))

    def test_navigation_and_local_assets(self):
        self.assertIn('href="./en/"', self.pages['ko'])
        self.assertIn('href="../" lang="ko"', self.pages['en'])
        self.assertIn('href="https://kunslab.com/en/"', self.pages['en'])
        self.assertIn('href="../assets/css/site.css"', self.pages['en'])
        self.assertIn('src="../assets/img/profile.jpg"', self.pages['en'])
        for lang, page in self.pages.items():
            self.assertIn('<html lang="' + lang + '">', page)

    def test_talk_material_links(self):
        for lang in ['ko', 'en']:
            talks = self.data(lang, 'talks')
            linked = [x for x in talks if x.get('slides')]
            self.assertEqual(len(linked), 10)
            section = self.pages[lang].split('id="talks">')[1].split('</section>')[0]
            for talk in linked:
                title = html.escape(talk['title'])
                self.assertIn(f'<a class="tl" href="{talk["slides"]}">{title}</a>', section)
                label = '발표자료' if lang == 'ko' else 'Slides'
                self.assertIn(f'href="{talk["slides"]}">{label}</a>', section)
                self.assertIn(f'href="{talk["github"]}">GitHub</a>', section)

    def test_english_labels_and_forthcoming_count(self):
        page = self.pages['en']
        visible = html.unescape(re.sub('<[^>]+>', '', page))
        self.assertIsNone(re.search('[가-힣]', visible))
        self.assertIn('KCI forthcoming <span>1</span>', page)
        self.assertIn('KCI <span>6</span>', page)
        self.assertIn('Unofficial translation', page)
        self.assertNotIn('&lt;i&gt;', page)
        self.assertIn('<i>Dongbuga Yeoksa Nonchong</i> 94', page)
        self.assertIn('>Lecturer</span><span class="entry-title">', page)
        self.assertIn('>Principal Investigator</span>', page)
        self.assertIn('>교원</span>', self.pages['ko'])


if __name__ == '__main__':
    unittest.main()
