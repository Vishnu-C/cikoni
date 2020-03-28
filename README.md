# cikoni
FreeCAD scripts for cikoni

DIAMETER/LENGTH RELATIONSHIP
L <= 5xD => Green

5xD < L < 8xD => Yellow

L >= 8xD => Orange

HOLE INCREMENTS
holes with with diameter that are an increment of 0.1 mm for diameters up to 10 mm and 0.5 mm above that AND minimum D>2mm: Green or other color according to above criteria

All others: Yellow or red according to above criteria

So the hole would only be green if the L<=5xD AND the has a diameter that is an increment of 0,1
for example
D=10,5 an L=30 -> Green
D=10,4, L=30 -> Yellow
D=10,5; L=60 -> Yellow

# Report format

Total number of holes: Nt= z
Number of green holes: Ng= y
Number of yellow holes: Ny= x
Number of orange holes: No= w
Number of holes with off-standard diameter: Nn= v
Number of holes with L <= 5d: L0= u
Number of holes with 5d < L < 8d: L5= t
Number of holes with L > 8d: L8= s

Detected holes:
H1 Hole position (xyz) Diameter_1 length_1 L/D Y/N (right increment/std)
Hi Hole position (xyz) Diameter_i length_i L/D Y/N (right increment/std)
Hn Hole position (xyz) Diameter_n length_n L/D Y/N (right increment/std)