# $Id: makefile,v 1.8 2010/03/24 13:17:06 stoecker Exp $
# probably works not with all compilers. Thought this should be easy
# fixable. There is nothing special at this source.

ifdef windir
CC   = gcc
OPTS = -std=gnu99 -Wall -W -O3 -DWINDOWSVERSION 
LIBS = -lwsock32 -lcurl
else
OPTS = -std=gnu99 -Wall -W -O3 
LIBS = -lcurl
endif
DEBUG_OPTS = -DNTRIPCLIENT_DEBUG_LOG
TARGET_NAME = ntripclient

ntripclient: ntripclient.c serial.c
	$(CC) $(OPTS) ntripclient.c -o $@ $(LIBS)

debug: ntripclient.c serial.c
	$(CC) $(OPTS) $(DEBUG_OPTS) ntripclient.c -o $(TARGET_NAME) $(LIBS)

.PHONY : debug

clean:
	$(RM) ntripclient core*

.PHONY : clean

archive:
	zip -9 ntripclient.zip ntripclient.c makefile README serial.c

.PHONY : archive

tgzarchive:
	tar -czf ntripclient.tgz ntripclient.c makefile README serial.c

.PHONY : tgzarchive
