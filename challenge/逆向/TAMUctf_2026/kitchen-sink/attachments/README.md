# kitchen sink

Author: `flocto`

sometimes you just have to throw the whole kitchen sink at them

maybe this way it won't get slopped

## Solution

lowkey no solution just get the flag lol...

### jk heres a summary

after cleaning up the CFF, you can chuck the algorithm at slop which will probably identify it as a Walsh-Hadamard transform. This is easily invertible, just use `sympy.ifwht` and decode the resulting bytes to get the flag.

flag:
`gigem{h0pefu11Y_This_0n3_last5_m0Re_thaN_4n_h0ur...}`
