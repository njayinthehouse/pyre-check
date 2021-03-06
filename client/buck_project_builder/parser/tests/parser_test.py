# Copyright (c) 2019-present, Facebook, Inc.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import unittest
from unittest.mock import mock_open, patch

from .. import Parser, ParserException
from ...build_target import (
    NonPythonTarget,
    PythonBinary,
    PythonLibrary,
    PythonUnitTest,
    PythonWheel,
    ThriftLibrary,
)
from ...filesystem import Glob
from ...tests.test_common import identity_mapping


TARGETS_FILE_BASIC = """
load("@fbcode_macros//build_defs:python_binary.bzl", "python_binary")
load("@fbcode_macros//build_defs:python_library.bzl", "python_library")
load("@fbcode_macros//build_defs:python_unittest.bzl", "python_unittest")

variable=42

python_binary(
    name = "binary_target",
    main_module = "my.module.main",
    deps = [
        ":other_target",
        "//another/project:target",
    ],
)

python_binary(
    name = "other_target",
    main_module = "my.module.other",
    deps = [],
)

python_library(
    name = "library_target",
    base_module = "foo.bar",
    srcs = ["a.py", "b.py"],
)

python_unittest(
    name = "test_target",
    srcs = glob(["tests/*.py"]),
)

cpp_python_extension(
    name = "cpp_python_target",
    deps = [":other_target"],
)

cpp_library_external(
    name = "cpp_library_target"
)
"""

TARGETS_FILE_ERROR = """
python_binary(
    name = 1234,
)
"""

TARGETS_FILE_THRIFT = """
thrift_library(
    name = "foo",
    thrift_srcs = {
        "bar.thrift": []
    }
)
"""

TARGETS_FILE_WHEEL = """
python_wheel(
    platform_urls = {
        "py3-platform007": "platform007_1.0_url",
        "py3-gcc-5-glibc-2.23": "gcc_1.0_url",
    },
    version = "1.0",
    deps = ["//some:target"],
    external_deps = ["foo"],
)

python_wheel(
    platform_urls = {
        "py3-platform007": "platform007_2.0_url",
        "py3-gcc-5-glibc-2.23": "gcc_2.0_url",
    },
    version = "2.0",
    deps = ["//other:target"],
    external_deps = ["bar"],
)

python_wheel_default(
    platform_versions = {
        "py3-platform007": "1.0",
        "py3-gcc-5-glibc-2.23": "2.0",
    },
)

python_library(
    name="library_target",
    srcs=["a.py", "b.py"]
)
"""


class ParserTest(unittest.TestCase):
    def test_parse_file_basic(self):
        parser = Parser("/buck_root")

        with patch(
            "builtins.open", mock_open(read_data=TARGETS_FILE_BASIC)
        ) as mocked_open:
            result = parser.parse_file("my/module")
            mocked_open.assert_called_once_with("/buck_root/my/module/TARGETS", "r")
            mocked_open.reset_mock()

            self.assertEqual(result.path, "my/module")
            self.assertEqual(len(result.targets), 6)

            target = result.targets["binary_target"]
            self.assertIsInstance(target, PythonBinary)
            self.assertEqual(target.target, "//my/module:binary_target")
            self.assertListEqual(
                target.dependencies,
                ["//my/module:other_target", "//another/project:target"],
            )

            target = result.targets["other_target"]
            self.assertIsInstance(target, PythonBinary)
            self.assertEqual(target.target, "//my/module:other_target")
            self.assertListEqual(target.dependencies, [])

            target = result.targets["library_target"]
            self.assertIsInstance(target, PythonLibrary)
            self.assertEqual(target.target, "//my/module:library_target")
            self.assertDictEqual(
                target.sources.files, identity_mapping(["a.py", "b.py"])
            )
            self.assertListEqual(target.sources.globs, [])
            self.assertListEqual(target.dependencies, [])

            target = result.targets["test_target"]
            self.assertIsInstance(target, PythonUnitTest)
            self.assertEqual(target.target, "//my/module:test_target")
            self.assertDictEqual(target.sources.files, {})
            self.assertListEqual(target.sources.globs, [Glob(["tests/*.py"], [])])
            self.assertListEqual(target.dependencies, [])

            target = result.targets["cpp_python_target"]
            self.assertIsInstance(target, NonPythonTarget)
            self.assertEqual(target.target, "//my/module:cpp_python_target")
            self.assertEqual(target.dependencies, [])

            target = result.targets["cpp_library_target"]
            self.assertIsInstance(target, NonPythonTarget)
            self.assertEqual(target.target, "//my/module:cpp_library_target")
            self.assertEqual(target.dependencies, [])

            # The parser should cache files it has already parsed.
            parser.parse_file("my/module")
            mocked_open.assert_not_called()

    def test_parse_file_error(self):
        parser = Parser("/buck_root")
        with patch(
            "builtins.open", mock_open(read_data=TARGETS_FILE_ERROR)
        ) as mocked_open:
            self.assertRaises(ParserException, parser.parse_file, "my/other_module")
            mocked_open.assert_called_once_with(
                "/buck_root/my/other_module/TARGETS", "r"
            )

    def test_parse_file_thrift(self):
        parser = Parser("/buck_root")
        with patch(
            "builtins.open", mock_open(read_data=TARGETS_FILE_THRIFT)
        ) as mocked_open:
            result = parser.parse_file("my/thrift_module")
            mocked_open.assert_called_once_with(
                "/buck_root/my/thrift_module/TARGETS", "r"
            )

            self.assertEqual(result.path, "my/thrift_module")
            self.assertEqual(len(result.targets), 2)

            self.assertEqual(result.targets["foo"], result.targets["foo-py"])

            target = result.targets["foo"]
            self.assertIsInstance(target, ThriftLibrary)
            self.assertEqual(target.target, "//my/thrift_module:foo")
            self.assertListEqual(target._thrift_sources, ["bar.thrift"])
            self.assertFalse(target._include_json_converters)

    def test_parse_file_wheel(self):
        parser = Parser("/buck_root")
        with patch(
            "builtins.open", mock_open(read_data=TARGETS_FILE_WHEEL)
        ) as mocked_open:
            result = parser.parse_file("my/wheel")
            mocked_open.assert_called_once_with("/buck_root/my/wheel/TARGETS", "r")

            self.assertEqual(result.path, "my/wheel")
            self.assertEqual(len(result.targets), 2)

            target = result.targets["wheel"]
            self.assertIsInstance(target, PythonWheel)
            self.assertEqual(target.target, "//my/wheel:wheel")
            self.assertDictEqual(target.sources.files, {})
            self.assertListEqual(target.sources.globs, [])
            self.assertListEqual(target.dependencies, ["//some:target"])
            self.assertListEqual(target.external_dependencies, [("foo", "foo-py")])

            # Even though the entire file must be scanned for a python_wheel,
            # other targets should still be parsed.
            target = result.targets["library_target"]
            self.assertIsInstance(target, PythonLibrary)
            self.assertEqual(target.target, "//my/wheel:library_target")
            self.assertDictEqual(
                target.sources.files, identity_mapping(["a.py", "b.py"])
            )
            self.assertListEqual(target.sources.globs, [])
            self.assertListEqual(target.dependencies, [])
            self.assertListEqual(target.external_dependencies, [])
