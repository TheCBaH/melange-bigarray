[@@@ai_disclosure "ai-generated"]
[@@@ai_provider "Anthropic, OpenAI"]

module Nativeint = Melange_bigarray.Nativeint
module Wrapped = Melange_bigarray
module Bigarray = Wrapped

let () =
  let a = Bigarray.Array1.create Bigarray.float64 Bigarray.c_layout 1 in
  a.{0} <- 3.5;
  assert (Separate.read a = 3.5);
  let b = Bigarray.Array2.create Bigarray.float64 Bigarray.c_layout 1 1 in
  b.{0, 0} <- 4.;
  assert (b.{0, 0} = 4.);
  let c = Bigarray.Array3.create Bigarray.float64 Bigarray.c_layout 1 1 1 in
  c.{0, 0, 0} <- 5.;
  assert (c.{0, 0, 0} = 5.);
  let d =
    Bigarray.Genarray.create Bigarray.float64 Bigarray.c_layout [| 1; 1; 1; 1 |]
  in
  d.{0, 0, 0, 0} <- 6.;
  assert (d.{0, 0, 0, 0} = 6.);
  let n = Bigarray.Array1.create Bigarray.nativeint Bigarray.c_layout 1 in
  Bigarray.Array1.set n 0
    (Nativeint.add (Nativeint.of_int 1) (Nativeint.of_int 2));
  assert (Nativeint.to_int (Bigarray.Array1.get n 0) = 3);
  let z = Bigarray.Array1.create Bigarray.complex64 Bigarray.c_layout 1 in
  Bigarray.Array1.set z 0 { Complex.re = 1.; im = 2. };
  assert ((Bigarray.Array1.get z 0).Complex.im = 2.);
  print_endline "provider/syntax/nativeint/complex spike passed"
