CC ?= gcc
CFLAGS ?= -O2 -Wall -Wextra -Werror -std=c11 -fPIC

all: libhgst_runtime.so check-abi

libhgst_runtime.so: hgst_inprocess_bridge.c hgst_runtime_abi.h hgst_algebra.h
	$(CC) $(CFLAGS) -shared -o $@ hgst_inprocess_bridge.c -lm

check-abi:
	$(CC) $(CFLAGS) -fsyntax-only hgst_inprocess_bridge.c -lm
	$(CC) $(CFLAGS) -fsyntax-only hgst_baremetal_sovereignty_core.c -lm
	$(CC) $(CFLAGS) -fsyntax-only hgst_opportunity_engine.c -lm
	$(CC) $(CFLAGS) -fsyntax-only hgst_rsi_engine.c -lm

clean:
	rm -f libhgst_runtime.so
