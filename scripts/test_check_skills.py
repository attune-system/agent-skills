import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from check_skills import PageIds, check, check_page


class CheckSkillsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "README.md").write_text("# Skills\n[Example](example/SKILL.md)\n")
        self.skill = self.root / "example"
        self.skill.mkdir()
        self.path = self.skill / "SKILL.md"
        self.path.write_text(
            "---\nname: example\ndescription: Example skill\n---\n"
            "[Docs](https://docs.attunedev.org/reference/yaml/)\n"
        )

    def append(self, text):
        self.path.write_text(self.path.read_text() + text)

    def test_valid_skill_and_examples(self):
        self.append('```yaml\nvalue: true\n```\n```json\n{"value":true}\n```\n')
        errors, skills, examples, pages = check(self.root)
        self.assertEqual(errors, [])
        self.assertEqual((skills, examples, pages), (1, 2, 1))

    def test_empty_repository_is_an_error(self):
        self.path.unlink()
        self.assertIn("No root skill directories found", check(self.root)[0])

    def test_bad_frontmatter_name(self):
        self.path.write_text(self.path.read_text().replace("name: example", "name: wrong"))
        self.assertTrue(any("name must match" in error for error in check(self.root)[0]))

    def test_skill_must_be_indexed(self):
        (self.root / "README.md").write_text("# Skills\n")
        self.assertTrue(any("skill missing from index" in error for error in check(self.root)[0]))

    def test_skill_cannot_depend_on_files_outside_its_directory(self):
        self.append("[Shared reference](../README.md)\n")
        errors = check(self.root)[0]
        self.assertTrue(any("link leaves independently installable skill" in error
                            for error in errors))

    def test_nested_reference_can_link_back_to_its_own_skill(self):
        reference = self.skill / "references/details.md"
        reference.parent.mkdir()
        reference.write_text("[Skill](../SKILL.md)\n")
        self.append("[Reference](references/details.md)\n")
        self.assertEqual(check(self.root)[0], [])

    def test_broken_link_and_reference_file(self):
        self.append("[Reference](references/details.md)\n")
        self.assertTrue(any("broken local link" in error for error in check(self.root)[0]))
        reference = self.skill / "references/details.md"
        reference.parent.mkdir()
        reference.write_text("```json\nnot json\n```\n")
        self.assertTrue(any("invalid json example" in error for error in check(self.root)[0]))

    def test_links_inside_code_are_not_followed(self):
        self.append("```text\n[not a link](missing.md)\n```\n")
        self.assertEqual(check(self.root)[0], [])

    def test_bad_yaml_and_unclosed_fence(self):
        self.append("```yaml\nvalue: [\n```\n```text\nunclosed\n")
        errors = check(self.root)[0]
        self.assertTrue(any("invalid yaml example" in error for error in errors))
        self.assertTrue(any("unclosed code fence" in error for error in errors))

    def test_ids_and_network_failure(self):
        parser = PageIds()
        parser.feed('<h2 id="ack-contract">Ack</h2>')
        self.assertEqual(parser.ids, {"ack-contract"})
        with patch("check_skills.urlopen", side_effect=OSError("offline")):
            errors = check_page(("https://docs.attunedev.org/", set()))
        self.assertTrue(any("offline" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
