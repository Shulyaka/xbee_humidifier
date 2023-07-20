.PHONY: all lib mpy test

all : lib mpy

lib :
	$(MAKE) -C $@

mpy : $(patsubst %.py, %.mpy, $(wildcard *.py))

clean :
	rm -f *.mpy
	$(MAKE) -C lib clean

%.mpy : %.py
	mpy-cross $<

test :
	tox -e micropython
