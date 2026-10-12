# Build stage
FROM rust:bookworm AS builder

WORKDIR /usr/src/app

# Configure Debian apt to use Tsinghua mirror for faster downloads in China (Builder stage)
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# Install cmake which is required for compiling boring-sys2/rquest
RUN apt-get update && apt-get install -y cmake clang

# Configure Cargo to use rsproxy mirror for faster builds
RUN mkdir -p .cargo && \
    echo '[source.crates-io]\n\
replace-with = "rsproxy-sparse"\n\
[source.rsproxy-sparse]\n\
registry = "sparse+https://rsproxy.cn/index/"\n\
[registries.rsproxy]\n\
index = "https://rsproxy.cn/crates.io-index"\n\
[net]\n\
git-fetch-with-cli = true' > .cargo/config.toml

COPY . .

# Build the application
RUN cargo build --release --locked

# Runtime stage
FROM debian:bookworm-slim

# Configure Debian apt to use Tsinghua mirror for faster downloads in China
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# Install necessary CA certificates for rquest to make HTTPS requests
RUN apt-get update && \
    apt-get install -y ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the compiled binary from the builder stage
COPY --from=builder /usr/src/app/target/release/SoSearch /app/SoSearch

ENV PORT=10080
EXPOSE 10080

CMD ["./SoSearch"]
