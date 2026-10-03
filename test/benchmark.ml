[@@@ai_disclosure "ai-generated"]
[@@@ai_provider "Anthropic, OpenAI"]

module B = Backend.Bigarray

let sink = ref 0.

let measure name bytes f =
  f ();
  let samples =
    Array.init 7 (fun _ ->
        let before = Backend.cpu_time () in
        f ();
        Backend.cpu_time () -. before)
  in
  Array.sort compare samples;
  Printf.printf "%s\t%.9f\t%d\n" name samples.(3) bytes

let () =
  let n = 65536 in
  let a = B.Array1.init B.float64 B.c_layout n (fun i -> float i) in
  let b = B.Array1.create B.float64 B.c_layout n in
  measure "scalar" (1000000 * 8) (fun () ->
      let sum = ref 0. in
      for i = 0 to 999999 do
        sum := !sum +. B.Array1.get a (i land 65535)
      done;
      sink := !sum);
  measure "fill"
    (1000 * n * 8)
    (fun () ->
      for _ = 1 to 1000 do
        B.Array1.fill b 17.
      done);
  measure "blit"
    (1000 * n * 8)
    (fun () ->
      for _ = 1 to 1000 do
        B.Array1.blit a b
      done);
  measure "views" 0 (fun () ->
      for i = 0 to 99999 do
        sink := B.Array1.get (B.Array1.sub a (i land 32767) 16) 0
      done);
  measure "numeric" (1000000 * 24) (fun () ->
      for i = 0 to 999999 do
        let j = i land 65535 in
        B.Array1.set b j ((0.5 *. B.Array1.get a j) +. B.Array1.get b j)
      done);
  let ints = B.Array1.init B.int64 B.c_layout n Int64.of_int in
  measure "int64" (1000000 * 8) (fun () ->
      let sum = ref 0L in
      for i = 0 to 999999 do
        sum := Int64.add !sum (B.Array1.get ints (i land 65535))
      done;
      sink := Int64.to_float !sum);
  let z =
    B.Array1.init B.complex64 B.c_layout n (fun i ->
        { Complex.re = float i; im = 1. })
  in
  measure "complex" (1000000 * 16) (fun () ->
      let sum = ref 0. in
      for i = 0 to 999999 do
        let v = B.Array1.get z (i land 65535) in
        sum := !sum +. v.Complex.re +. v.Complex.im
      done;
      sink := !sum);
  if !sink = 0. then failwith "benchmark optimized away"
