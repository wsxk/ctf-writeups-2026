#!/bin/bash

rm les_dist.tar.gz
rm -rf les_dist/

mkdir les_dist

cp -R roms/ les_dist/roms
cp WRAM.bin.dist les_dist/WRAM.bin
cp wromwarp.c les_dist/
cp wromwarp les_dist/
cp Makefile les_dist/
cp les_logo.txt les_dist/

tar -czvf les_dist.tar.gz les_dist/

rm -rf les_dist/
