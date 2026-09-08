CC ?= cc
CFLAGS ?= -O2 -Wall -Wextra -Werror -std=c11 -fPIC

check-abi:
	$(CC) $(CFLAGS) -fsyntax-only hgst_inprocess_bridge.c
	$(CC) $(CFLAGS) -fsyntax-only hgst_baremetal_sovereignty_core.c
	$(CC) $(CFLAGS) -fsyntax-only hgst_opportunity_engine.c
	$(CC) $(CFLAGS) -fsyntax-only hgst_rsi_engine.c
