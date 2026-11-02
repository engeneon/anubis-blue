FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends g++ cmake make libssl-dev libsqlite3-dev libpq-dev python3 ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY CMakeLists.txt CMakePresets.json ./
COPY src src
COPY third_party third_party
COPY contracts contracts
COPY knowledge/synthetic.json knowledge/synthetic.json
COPY tests/fixtures tests/fixtures
COPY tests/shared tests/shared
COPY ui/dist ui/dist
# CMake's local smoke target is included in this development image.
COPY tests/core.cpp tests/core.cpp
RUN cmake -S . -B build -DANUBIS_WITH_POSTGRES=ON -DCMAKE_BUILD_TYPE=Debug && cmake --build build -j4
CMD ["python3", "tests/shared/test_postgres.py"]
