(* Copyright (c) 2016-present, Facebook, Inc.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree. *)

open Ast
open Analysis
open Interprocedural

type t = {
  is_obscure: bool;
  call_target: Callable.t;
  model: TaintResult.call_model
}
[@@deriving show, sexp]

exception InvalidModel of string

val get_callsite_model : call_target:[< Callable.t ] -> t

val get_global_model : resolution:Resolution.t -> expression:Expression.t -> t option

val parse
  :  resolution:Resolution.t ->
  source:string ->
  configuration:Configuration.t ->
  TaintResult.call_model Callable.Map.t ->
  TaintResult.call_model Callable.Map.t
