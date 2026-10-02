[@@@ai_disclosure "ai-generated"]
[@@@ai_provider "Anthropic, OpenAI"]

module B = Melange_bigarray

let () =
  let a = B.Array1.of_array B.int B.c_layout [| 1; 2; 3 |] in
  let v = B.genarray_of_array1 (B.Array1.sub a 1 2) in
  let c =
    B.genarray_of_array1 (B.Array1.of_array B.int B.c_layout [| 2; 3 |])
  in
  Printf.printf "generic_equal_view_copy=%b\n" (v = c);
  Printf.printf "ops_equal_view_copy=%b\n" (B.Ops.equal v c);
  Printf.printf "generic_compare_view_copy=%d\n" (compare v c);
  Printf.printf "generic_hash_view=%d\n" (Hashtbl.hash v);
  Printf.printf "generic_hash_copy=%d\n" (Hashtbl.hash c);
  let before = Hashtbl.hash v in
  ignore (B.Interop.export_shared v);
  Printf.printf "generic_hash_changed_on_share=%b\n" (before <> Hashtbl.hash v);
  Printf.printf "ops_hash_view_copy=%b\n" (B.Ops.hash v = B.Ops.hash c);
  let n =
    B.genarray_of_array1 (B.Array1.of_array B.float64 B.c_layout [| nan |])
  in
  Printf.printf "generic_nan_self=%b\n" (n = n);
  Printf.printf "ops_nan_self=%b\n" (B.Ops.equal n n)
