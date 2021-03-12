TARGET_NAME = rtcm_parser
LIBRTK_PATH = ../librtk
CFLAGS = -std=gnu99 -Wall -W -I$(LIBRTK_PATH)
LDFLAGS = -L$(LIBRTK_PATH) -lrtk -lm -lrt -lpthread
SOURCES := $(wildcard *.c)
OBJS := $(patsubst %.c,%.o,$(SOURCES))

ifeq ($(DEBUG),1)
  CFLAGS += -DDEBUG
endif

all: $(TARGET_NAME)

$(TARGET_NAME): $(OBJS)
	$(MAKE) -C $(LIBRTK_PATH)
	$(CC) $(OBJS) -o $@ $(CFLAGS) $(LDFLAGS)

%.o: %.c
	@$(CC) $(CFLAGS) -c $<

.PHONY: clean all
clean:
	$(MAKE) -C $(LIBRTK_PATH) clean
	rm -rf *.o $(TARGET_NAME)
