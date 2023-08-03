.PHONY: all mpy

MPY_CROSS := mpy-cross
MFLAGS := -mno-unicode -msmall-int-bits=31 -O3

all : mpy

mpy : $(patsubst %.py, %.mpy, $(wildcard *.py))

clean :
	rm -f *.mpy

%.mpy : %.py
	$(MPY_CROSS) $(MFLAGS) $<
