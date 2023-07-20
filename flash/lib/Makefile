.PHONY: all mpy

all : mpy

mpy : $(patsubst %.py, %.mpy, $(wildcard *.py))

clean :
	rm -f *.mpy

%.mpy : %.py
	mpy-cross $<
