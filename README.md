# Install Redis
Firstly, install redis docker to store tracking jobs

```bash
docker pull redis

docker run --name redis -d -p 6379:6379 redis

docker exec -it redis redis-cli
```

# resource_service
- setup: source setup.sh
- run: source run.sh
