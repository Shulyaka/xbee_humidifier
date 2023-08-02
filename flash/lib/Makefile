.PHONY: all mpy

all : mpy

mpy : $(patsubst %.py, %.mpy, $(wildcard *.py))

clean :
	rm -f *.mpy

%.mpy : %.py
	mpy-cross -mno-unicode -msmall-int-bits=31 -O3 $<
