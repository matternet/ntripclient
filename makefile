TARGET_NAME = ntripclient
CFLAGS = -std=gnu99 -Wall -W -O3
LDFLAGS = -lcurl
SOURCES := $(wildcard *.c)
OBJS := $(patsubst %.c,%.o,$(SOURCES))

ifeq ($(DEBUG),1)
  CFLAGS += -DDEBUG
endif

all: $(TARGET_NAME)

$(TARGET_NAME): $(OBJS)
	$(CC) $(OBJS) -o $@ $(CFLAGS) $(LDFLAGS)

%.o: %.c
	@$(CC) $(CFLAGS) -c $<

.PHONY: clean all
clean:
	rm *.o $(TARGET_NAME)
