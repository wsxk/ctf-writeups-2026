# Syntax

Welcome to the RugDoctor JIT compiler!

Connect to the RugDoctor service on port 9898. Send code. Press ctrl-d. Observe
as your code runs in our secure sandbox!

RugDoctor is a simple procedural language. Blank lines are ignored. Comments are
denoted with `;` or `#` at the start of the line (comments after instructions
aren't supported).

There are four variables: `$A`, `$B`, `$C`, and `$D`.

The instructions are:

* `LET $VAR <int32>` - assign an immediate value to a variable
* `LETV $VAR1 $VAR2` - copy a variable to another variable
* `ADD $VAR <int32>` - add an immediate value to a variable
* `ADDV $VAR1 $VAR2` - add two variables together (result is stored in `$VAR1`)
* `SUB $VAR <int32>` - subtract an immediate value from a variable
* `SUBV $VAR1 $VAR2` - subtract `$VAR2` from `$VAR1` (result is stored in `$VAR1`)
* `MUL $VAR <int32>` - multiply a variable by an immediate value
* `PRINT $VAR` - print the variable (as a number)
* `PRINTCHAR $VAR` - print the variable (as a character)
* `LOOP $VAR ... ENDLOOP` - loop `$VAR` times, deducting 1 from `$VAR` each iteration (always executes once)
* `IF $VAR ... ENDIF` - only run the given block if `$VAR` is non-zero
* `EXIT <int32>` - exit with an immediate value as the exit code

Don't forget to `EXIT` at the end of your code!
