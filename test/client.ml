[@@@ai_disclosure "ai-generated"]
[@@@ai_provider "Anthropic, OpenAI"]

module B = Melange_bigarray

let () =
  let a =
    B.Array2.init B.float64 B.c_layout 3 4 (fun i j -> float ((i * 4) + j))
  in
  let row = B.Array2.slice_left a 1 in
  B.Array1.fill row 17.;
  let g = B.genarray_of_array2 a in
  let copy = B.Genarray.create B.float64 B.c_layout [| 3; 4 |] in
  B.Genarray.blit g copy;
  assert (B.Ops.equal g copy && B.Ops.hash g = B.Ops.hash copy);
  assert (B.Array2.get a 1 3 = 17.);
  let bytes =
    Bigarray.Array1.init Bigarray.int8_unsigned Bigarray.c_layout 256 Fun.id
  in
  let module S = Bytesrw.Bytes.Slice in
  let slice = S.of_bigbytes bytes in
  let data = S.to_string slice in
  String.iteri (fun i c -> assert (Char.code c = i)) data;
  let restored = S.to_bigbytes slice in
  Bigarray.Array1.set restored 0 255;
  assert (Bigarray.Array1.get bytes 0 = 0);
  Bigarray.Array1.set bytes 1 250;
  assert (Char.code (String.get (S.to_string slice) 1) = 1);
  let sub = Bigarray.Array1.sub bytes 16 32 in
  assert (String.length (S.to_string (S.of_bigbytes sub)) = 32);
  let reader = Bytesrw.Bytes.Reader.of_slice ~slice_length:7 slice in
  assert (Bytesrw.Bytes.Reader.to_string reader = data);
  assert (
    S.is_eod
      (S.of_bigbytes_or_eod
         (Bigarray.Array1.create Bigarray.int8_unsigned Bigarray.c_layout 0)));
  print_endline "installed general + bytesrw client: passed"
