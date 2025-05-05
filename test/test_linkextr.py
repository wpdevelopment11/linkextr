from contextlib import _RedirectStream, redirect_stdout
from textwrap import dedent
from unittest.mock import patch

import io
import os
import shutil
import tempfile
import unittest

import linkextr

class FrontMatterTest(unittest.TestCase):
    def test_without_frontmatter(self):
        result = linkextr.frontmatter_split([])
        self.assertEqual(result, ([], []))

        lines = ["", ""]
        result = linkextr.frontmatter_split(lines)
        self.assertEqual(result, ([], lines))

        lines = [" ", "foobar"]
        result = linkextr.frontmatter_split(lines)
        self.assertEqual(result, ([], lines))

        lines = [" ", "foobar", "second line"]
        result = linkextr.frontmatter_split(lines)
        self.assertEqual(result, ([], lines))

        lines = ["foobar"]
        result = linkextr.frontmatter_split(lines)
        self.assertEqual(result, ([], lines))

        lines = ["foobar", "second line"]
        result = linkextr.frontmatter_split(lines)
        self.assertEqual(result, ([], lines))

    def test_unterminated_frontmatter(self):
        lines = ["---"]
        result = linkextr.frontmatter_split(lines)
        self.assertEqual(result, ([], lines))

        lines = ["", "---"]
        result = linkextr.frontmatter_split(lines)
        self.assertEqual(result, ([], lines))

        lines = ["", "---", "foobar"]
        result = linkextr.frontmatter_split(lines)
        self.assertEqual(result, ([], lines))

        lines = ["---", "foobar"]
        result = linkextr.frontmatter_split(lines)
        self.assertEqual(result, ([], lines))

    def test_frontmatter_leading_space(self):
        leading_space_start = dedent("""\
        \x20---
        title: "Python tutorial for beginners"
        slug: "python-tutorial"
        ---

        Python is dynamically typed
        """).splitlines(keepends=True)

        result = linkextr.frontmatter_split(leading_space_start)

        self.assertEqual(result, ([], leading_space_start))

        leading_space_end = dedent("""\
        ---
        title: "Python tutorial for beginners"
        slug: "python-tutorial"
        \x20---

        Python is dynamically typed
        """).splitlines(keepends=True)

        result = linkextr.frontmatter_split(leading_space_end)

        self.assertEqual(result, ([], leading_space_end))

    def test_frontmatter_trailing_space(self):
        front_only = dedent("""\
        ---
        title: "Python tutorial for beginners"
        slug: "python-tutorial"
        ---
        """).splitlines(keepends=True)

        trailing_space_start = dedent("""\
        ---\x20
        title: "Python tutorial for beginners"
        slug: "python-tutorial"
        ---

        Python is dynamically typed
        """).splitlines(keepends=True)

        result = linkextr.frontmatter_split(trailing_space_start)

        self.assertEqual(result, (front_only, ["\n", "Python is dynamically typed\n"]))

        trailing_space_end = dedent("""\
        ---
        title: "Python tutorial for beginners"
        slug: "python-tutorial"
        ---\x20

        Python is dynamically typed
        """).splitlines(keepends=True)

        result = linkextr.frontmatter_split(trailing_space_end)

        self.assertEqual(result, (front_only, ["\n", "Python is dynamically typed\n"]))

    def test_frontmatter(self):
        front_only = dedent("""\
        ---
        title: "Python tutorial for beginners"
        slug: "python-tutorial"
        ---
        """).splitlines(keepends=True)

        result = linkextr.frontmatter_split(front_only)

        self.assertEqual(result, (front_only, []))

        front_only_empty_line = dedent("""\

        ---
        title: "Python tutorial for beginners"
        slug: "python-tutorial"
        ---
        """).splitlines(keepends=True)

        result = linkextr.frontmatter_split(front_only_empty_line)

        self.assertEqual(result, (front_only, []))

        front_only_empty_line_after = dedent("""\
        ---
        title: "Python tutorial for beginners"
        slug: "python-tutorial"
        ---

        """).splitlines(keepends=True)

        result = linkextr.frontmatter_split(front_only_empty_line_after)

        self.assertEqual(result, (front_only, ["\n"]))

        front_with_text = dedent("""\
        ---
        title: "Python tutorial for beginners"
        slug: "python-tutorial"
        ---
        Python is dynamically typed programming language.
        """).splitlines(keepends=True)

        result = linkextr.frontmatter_split(front_with_text)

        self.assertEqual(result, (front_only, ["Python is dynamically typed programming language.\n"]))

        front_with_multiline_text = dedent("""\
        ---
        title: "Python tutorial for beginners"
        slug: "python-tutorial"
        ---
        Python is dynamically typed programming language
        with extensive standard library and active community.
        """).splitlines(keepends=True)

        result = linkextr.frontmatter_split(front_with_multiline_text)

        self.assertEqual(result, (front_only, ["Python is dynamically typed programming language\n",
                                               "with extensive standard library and active community.\n"]))

        front_with_text_after_empty_line = dedent("""\
        ---
        title: "Python tutorial for beginners"
        slug: "python-tutorial"
        ---

        Python is dynamically typed programming language.
        """).splitlines(keepends=True)

        result = linkextr.frontmatter_split(front_with_text_after_empty_line)

        self.assertEqual(result, (front_only, ["\n", "Python is dynamically typed programming language.\n"]))

        front_with_multi_text_after_empty_line = dedent("""\
        ---
        title: "Python tutorial for beginners"
        slug: "python-tutorial"
        ---

        Python is dynamically typed programming language
        with extensive standard library and active community.
        """).splitlines(keepends=True)

        result = linkextr.frontmatter_split(front_with_multi_text_after_empty_line)

        self.assertEqual(result, (front_only, ["\n", "Python is dynamically typed programming language\n",
                                               "with extensive standard library and active community.\n"]))

        front_with_multi_text_after_empty_lines = dedent("""\
        ---
        title: "Python tutorial for beginners"
        slug: "python-tutorial"
        ---


        Python is dynamically typed programming language
        with extensive standard library and active community.
        """).splitlines(keepends=True)

        result = linkextr.frontmatter_split(front_with_multi_text_after_empty_lines)

        self.assertEqual(result, (front_only, ["\n", "\n", "Python is dynamically typed programming language\n",
                                               "with extensive standard library and active community.\n"]))

class FindLinksTest(unittest.TestCase):
    def test_findlinks_email(self):
        input = [
            "[my email](john@exmaple.com)",
            "[with_host](https://example.com/page/1)"
        ]
        expected = {"https://example.com/page/1"}
        result = linkextr.findlinks(input)

        self.assertEqual(result, expected)

    def test_findlinks_image(self):
        input = [
            "[with_host](https://example.com/page/1)",
            "![image_example](https://cool.test/images/1.jpg)"
        ]

        expected = {"https://example.com/page/1"}
        result = linkextr.findlinks(input)

        self.assertEqual(result, expected)

        expected = {"https://example.com/page/1", "https://cool.test/images/1.jpg"}
        result = linkextr.findlinks(input, images=True)

        self.assertEqual(result, expected)

    def test_findlinks_fragment(self):
        input = [
            "[with_host](https://example.com/page/1)",
            "[with_fragment](https://example.com/page/2#world)"
        ]

        expected = {"https://example.com/page/1", "https://example.com/page/2"}
        result = linkextr.findlinks(input)

        self.assertEqual(result, expected)

    def test_findlinks_without_scheme(self):
        input = ["[link](//example.com/page/1)"]
        expected = {"https://example.com/page/1"}
        result = linkextr.findlinks(input)

        self.assertEqual(result, expected)

    def test_findlinks_prefix(self):
        input = [
            "[without_host](/blog/article)",
            "[with_host](https://example.com/page/1)",
            "[relative](blog-post.html)"
        ]

        expected = {"https://example.com/page/1"}
        result = linkextr.findlinks(input)

        self.assertEqual(result, expected)

        expected = {"https://myprefix.test/blog/article", "https://example.com/page/1"}

        prefix = "https://myprefix.test"

        result = linkextr.findlinks(input, prefix=prefix)
        self.assertEqual(result, expected)

        result = linkextr.findlinks(input, prefix=prefix + "/")
        self.assertEqual(result, expected)

        result = linkextr.findlinks(input, prefix=prefix + "//")
        self.assertEqual(result, expected)

    def test_findlinks_mailto(self):
        input = [
            "[my email](mailto:john@exmaple.com)",
            "[with_host](https://example.com/page/1)"
        ]
        expected = {"https://example.com/page/1"}

        result = linkextr.findlinks(input)

        self.assertEqual(result, expected)

    def test_findlinks_alluri(self):
        input = [
            "[my email](mailto:john@exmaple.com)",
            "[relative](blog-post.html)",
            "[with_host](https://example.com/page/1)",
            "[empty](#hello_world)"
        ]

        expected = {"https://example.com/page/1"}
        result = linkextr.findlinks(input)
        self.assertEqual(result, expected)

        expected = {"https://example.com/page/1", "blog-post.html"}
        result = linkextr.findlinks(input, alluri=True)
        self.assertEqual(result, expected)

class MainFuncTest(unittest.TestCase):
    def setUp(self):
        self.input = dedent("""\
        [without_host](/blog/article)

        [with_host](https://example.com/page/1)

        [relative](blog-post.html)

        ![image_example](https://cool.test/images/1.jpg)
        """)

        self.secondinput = dedent("""\
        [link text](https://localhost)

        [relative](archive/blog-post.html)

        Foobar
        Some other text
        """)

        self.nullstdout = open(os.devnull, "w", encoding="utf-8")

    def tearDown(self):
        self.nullstdout.close()

    @patch('linkextr.findlinks')
    def test_path_arg_stdin(self, findlinks):
        stdin = io.StringIO(self.input)
        with redirect_stdin(stdin), redirect_stdout(self.nullstdout):
            linkextr.main([])

        findlinks.assert_called_once()

        lines = findlinks.call_args.args[0]

        self.assertEqual(lines, self.input.splitlines(keepends=True))

    @patch('linkextr.findlinks')
    def test_path_arg_single_file(self, findlinks):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as input:
            input.write(self.input)

        with redirect_stdout(self.nullstdout):
            linkextr.main([input.name])

        findlinks.assert_called_once()

        lines = findlinks.call_args.args[0]

        self.assertEqual(lines, self.input.splitlines(keepends=True))

        os.unlink(input.name)

    @patch('linkextr.findlinks')
    def test_path_arg_multiple_files(self, findlinks):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as input:
            input.write(self.input)

        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as secondinput:
            secondinput.write(self.secondinput)

        with redirect_stdout(self.nullstdout):
            linkextr.main([input.name, secondinput.name])

        self.assertEqual(findlinks.call_count, 2)

        firstlines = findlinks.call_args_list[0].args[0]

        self.assertEqual(firstlines, self.input.splitlines(keepends=True))

        secondlines = findlinks.call_args_list[1].args[0]

        self.assertEqual(secondlines, self.secondinput.splitlines(keepends=True))

        os.unlink(input.name)
        os.unlink(secondinput.name)

    @patch('linkextr.findlinks')
    def test_path_arg_dir(self, findlinks):
        def write_file(name, contents):
            path = os.path.join(temp_dir, name)
            with open(path, "w", encoding="utf-8") as file:
                file.write(contents)
        temp_dir = tempfile.mkdtemp()
        write_file("first.md", self.input)
        write_file("second.md", self.secondinput)

        with redirect_stdout(self.nullstdout):
            linkextr.main([temp_dir])

        self.assertEqual(findlinks.call_count, 2)

        # glob returns results in arbitrary order
        all_lines = []
        all_lines.extend(findlinks.call_args_list[0].args[0])
        all_lines.extend(findlinks.call_args_list[1].args[0])
        all_lines.sort()

        expected = []
        expected.extend(self.input.splitlines(keepends=True))
        expected.extend(self.secondinput.splitlines(keepends=True))
        expected.sort()

        self.assertEqual(all_lines, expected)

        shutil.rmtree(temp_dir)

    @patch('linkextr.findlinks')
    def test_output_option(self, findlinks):
        def check_output(run, findlinks_returns, expected):
            findlinks.reset_mock()
            os.truncate(output.name, 0)

            findlinks.side_effect = findlinks_returns
            calls_num = len(findlinks_returns)

            run(calls_num)

            self.assertEqual(findlinks.call_count, calls_num)

            with open(output.name, encoding="utf-8") as out:
                lines = [line.removesuffix("\n") for line in out]

            self.assertEqual(lines, sorted(list(expected)))

        def run_with_output_opt(input_num):
            inputs = [os.devnull] * input_num
            args = inputs + ["--output", output.name]
            linkextr.main(args)

        def run_with_stdout(input_num):
            with (open(output.name, "w", encoding="utf-8") as out,
                  redirect_stdout(out)):
                inputs = [os.devnull] * input_num
                linkextr.main(inputs)

        with tempfile.NamedTemporaryFile(delete=False) as output:
            pass

        areturn = {"https://example.com/blog/post", "https://localhost"}
        breturn = {"https://example.com/blog/post", "https://cool.test/hello/world"}

        union = {"https://example.com/blog/post", "https://localhost", "https://cool.test/hello/world"}

        check_output(run_with_output_opt, [areturn], areturn)
        check_output(run_with_output_opt, [areturn, breturn], union)

        check_output(run_with_stdout, [areturn], areturn)
        check_output(run_with_stdout, [areturn, breturn], union)

        os.unlink(output.name)

    @patch('linkextr.findlinks')
    def test_prefix_option(self, findlinks):
        linkextr.main([os.devnull])
        prefixarg = findlinks.call_args.kwargs["prefix"]
        self.assertIsNone(prefixarg)

        findlinks.reset_mock()

        prefix = "https://foobar.test"
        linkextr.main([os.devnull, "--prefix", prefix])
        prefixarg = findlinks.call_args.kwargs["prefix"]
        self.assertEqual(prefixarg, prefix)

    @patch('linkextr.findlinks')
    def test_flags(self, findlinks):
        def test_flag(flag):
            linkextr.main([os.devnull])
            flagval = findlinks.call_args.kwargs[flag]
            self.assertFalse(flagval)

            findlinks.reset_mock()

            linkextr.main([os.devnull, f"--{flag}"])
            flagval = findlinks.call_args.kwargs[flag]
            self.assertTrue(flagval)

        test_flag("alluri")
        test_flag("images")

class redirect_stdin(_RedirectStream):
    _stream = "stdin"
