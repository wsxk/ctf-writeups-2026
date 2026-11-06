let $a 10

loop $a
  let $b 5
  subv $b $a

  if $b
    print $b
  endif
endloop

exit 0
