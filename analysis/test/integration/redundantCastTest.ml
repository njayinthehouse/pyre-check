(* Copyright (c) 2016-present, Facebook, Inc.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree. *)

open OUnit2
open IntegrationTest

let test_check_redundant_cast _ =
  assert_type_errors
    {|
      def foo(x: int) -> None:
        typing.cast(int, x)
    |}
    ["Redundant cast [22]: The value being cast is already of type `int`."];
  assert_type_errors {|
      def foo(x: str) -> None:
        typing.cast(int, x)
    |} [];
  assert_default_type_errors
    {|
      def foo(x: typing.Any) -> None:
        typing.cast(int, x)
    |}
    [];
  assert_type_errors
    {|
      def foo(x: dict[int, int]) -> None:
        typing.cast(dict[int, int], x)
    |}
    ["Redundant cast [22]: The value being cast is already of type `typing.Dict[int, int]`."];
  assert_type_errors
    {|
      def foo(x: dict[int, int]) -> None:
        typing.cast(dict[int, str], x)
    |}
    []


let () = "redundantCast" >::: ["check_redundant_cast" >:: test_check_redundant_cast] |> Test.run
