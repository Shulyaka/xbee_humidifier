.PHONY: all lib mpy test

all : lib mpy

lib :
	$(MAKE) -C $@

mpy : $(patsubst %.py, %.mpy, $(wildcard *.py))

clean :
	rm -f *.mpy
	$(MAKE) -C lib clean

%.mpy : %.py
	mpy-cross -mno-unicode -msmall-int-bits=31 -O3 $<

test :
	tox -e micropython
