LIB_NAME = librtk
CFLAGS = -DDLL -DTRACE -std=gnu99 -Wall -W -O3 -Wno-unused-but-set-variable -Wno-unused-parameter
SOURCES := $(wildcard *.c)
OBJS := $(patsubst %.c,%.o,$(SOURCES))

all: librtk.a

librtk.a: $(OBJS)
	$(AR) rcs $@ $(OBJS)

%.o: %.c
	@$(CC) $(CFLAGS) -c $<

.PHONY: clean all
clean:
	rm -rf *.o *.a
