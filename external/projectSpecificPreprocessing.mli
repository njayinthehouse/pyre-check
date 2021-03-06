(* Copyright (c) 2016-present, Facebook, Inc.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree. *)

type state

val initial : File.Handle.t list -> state

val preprocess : state:state -> Ast.Source.t -> Ast.Source.t
