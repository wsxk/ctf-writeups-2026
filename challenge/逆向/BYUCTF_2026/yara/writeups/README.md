# Yet Another Recursive Acronym

Maybe use `--no-warnings` for quality of life.

Note: there should not be an unintended, but if you find one let the admins know

Files:
- [rule.yar](./rule.yar)

### Solve

This is a yara rule that does matching on a file to check whether or not the flag is contained within it. Many people did this manually to solve it, but it could also be done with a sat solver if you want to be fancy, just make all the conditions be met. Goal here is just to introduce you to yara and all the fun stuff that comes with it.

Flag: `byuctf{why_do3s_yara_st4nd_f0r_th4t???}`