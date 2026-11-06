# RCaaS

RCaaS (Rev Chall as a Service)

Files:
- [rcaas](./rcaas)

### Solve

This challenge installs itself as a service and then runs the checks as that service on a specific file on the system. You could probably patch it so that you don't have to do that, but it's not too hard to just let it run as a service. I just ran the installer and then worked from there for my checks. It does the checks in the `run()` function, so just find that and undo it. I used z3 for that, which was chill

Public CTF probably make the checks more complex and maybe even strip the binary?

Flag: `byuctf{s3rv1c3s_c4n_3_r3v3rs3_3ng1n33r3d_t00}`