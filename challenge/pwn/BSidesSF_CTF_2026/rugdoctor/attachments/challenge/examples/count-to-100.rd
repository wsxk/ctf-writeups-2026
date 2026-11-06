let $a 10
loop $a
  letv $c $a
  let $c 10
  subv $c $a
  mul $c 10

  let $b 10
  loop $b
    add $c 1
    print $c
  endloop
endloop

exit 0
