```shell
docker run -d -p "0.0.0.0:$pub_tcp:8888" -p "0.0.0.0:$pub_udp:8889/udp" -h "pwn" --name="pwn" --restart always pwn 
```
