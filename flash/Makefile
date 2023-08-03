.PHONY: all lib mpy test

MPY_CROSS := mpy-cross
TOX := tox
MFLAGS := -mno-unicode -msmall-int-bits=31 -O3

all : lib mpy

lib :
	$(MAKE) -C $@

mpy : $(patsubst %.py, %.mpy, $(wildcard *.py))

clean :
	rm -f *.mpy
	$(MAKE) -C lib clean

%.mpy : %.py
	$(MPY_CROSS) $(MFLAGS) $<

test :
	$(TOX) -e micropython
