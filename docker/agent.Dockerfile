FROM alpine:3.20
# openssl for the service's contained gate; the rest of busybox is already here.
RUN apk add --no-cache openssl
CMD ["sleep", "infinity"]
