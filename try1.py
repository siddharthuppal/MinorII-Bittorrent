import math
from bitstring import BitArray

no_of_pieces 	= int(math.ceil(float(4)/float(2)))
pieces_status 	= BitArray(no_of_pieces)


print pieces_status