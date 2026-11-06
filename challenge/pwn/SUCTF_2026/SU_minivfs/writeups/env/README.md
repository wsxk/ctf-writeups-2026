# Build

```bash
docker build -t "mini_vfs" .
```

# Run

```bash
docker run -d -p "0.0.0.0:10000:9999" -h "mini_vfs" --name="mini_vfs" mini_vfs
```
