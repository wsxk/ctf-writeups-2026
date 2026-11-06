let $a 10

loop $a
  let $b 10
  let $c 20

  # b = b - $i
  subv $b $a

  # b = b + 20
  addv $b $c

  # b = b - 5
  sub $b 5

  # b = b + 10
  add $b 5

  print $b
endloop

exit 0
