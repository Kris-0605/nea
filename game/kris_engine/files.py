from tqdm import tqdm
# My favourite progress bar
import os
# Used for file operations
from PIL import Image
# Used for image scaling when building
from io import BytesIO
# Used to return object in memory as buffer that acts like a file object
import atexit
# Close the KAP file on program termination
from math import log2
# Used for calculating number of options to check for RLE brute

class KAP:
# Presenting the KAP file: Kris's Asset Package!
# Now you can put all the textures and assets for your Kris's Engine application in one file
# Along with essential information about things like texture quality
# Compressed with run length encoding!

# A KAB file is structured in two parts: a string portion and a byte portion
# Some rules about the string portion:
# - All integers are unsigned and most significant bit first
# - All strings are UTF-8
# - A 0 byte is eight bits with a value 0

# The file begins with a 16-bit integer magic byte, 1993
# This helps verify that we're loading the right file type
# Then, an 8-bit integer representing the number of texture quality options available
# Then, for as many qualities as the integer specified:
    # string data detailing the name of the setting
    # a 0 byte
    # a non-zero 8-bit integer that the texture quality should be assigned to

# Then, there's a 32-bit integer detailing how many textures there are
# Each entry of the rest of the string portion is structured as follows:
# string data detailing the name of the file
# 0 byte
# 8-bit integer representing how many texture qualities the file has
# if this byte is 0:
    # 64-bit integer, indicating the pointer at which the file data starts in bytes
    # 64-bit integer, indicating the size of the file in bytes
# if this byte is greater than 0, repeat the following for the value of the byte:
    # 8-bit integer corresponding to a texture quality
    # 64-bit integer, indicating the pointer at which the file data starts in bytes
    # 64-bit integer, indicating the size of the file in bytes
# Then the corresponding files will be dumped as RLE bytes into the files at their corresponding pointers

# RLE bytes are bytes that are run length encoded.
# RLE bytes start with a byte that is comprised of two 4-bit integers
# The first represents counter_length, the second pattern_length
# These are required information to encode and decode RLE bytes
# Then, the excess. Take an example where we have a file with an odd number of bytes and pattern_length 2.
# For the algorithm to look for patterns of length 2, we need to trim the first byte off.
# So, the second byte is an 8-bit integer representing the size of the excess.
# If 0, move straight on to the data, otherwise append the following number of bytes to the front of the output.
# Then, the rest of the bytes are in the pattern of counter_length bytes, pattern_length bytes
# To decode, repeat the pattern_length bytes the value of the counter_length bytes times

    def __init__(self, path, engine=None):
        # You'll see quite a few "if engine" throughout this module
        # It can be used with or without the main Engine class being initialised
        # If the engine is initialised, the module will post log messages      
        if engine:
            engine.append_log("Files module, initialising KAP class")

        self.file_map, self.assets = {}, {}
        # Filemap tells us which KAP file an asset comes from
        # Assets contains information about where in the file the asset is and how big it is
        self.open = []
        # A list of all the KAP files that are open, stripped to their base filename
        self.load_kap(path, engine=engine)
        atexit.register(self.__del__)
        # Will close file on program termination or if the KAP object is deleted with the del keyword

    def __del__(self):
        for x in set(self.file_map.values()):
            x.close()
        # Make sure KAP files are closed

    def load_kap(self, path, engine=None):
        if engine:
            engine.append_log(f"Files module, loading KAP file {path}")

        f = open(path, "rb")
        # File stays open for reduced data access time
        qualities={}
        if not f.read(2) == b'\x07\xc9':
            raise TypeError("Magic byte not found!")
        # Checks for magic byte at start of file to confirm file is of KAP type
        for x in range(f.read(1)[0]): # 8-bit integer referring to number of textures
            name = self.string_data(path, f) # Get texture name
            qualities[f.read(1)] = name # Store with 8-bit texture ID
        for x in range(int.from_bytes(f.read(4), "big")): # For number of textures in 32-bit integer
            name = self.string_data(path, f) # Get file name
            if (num_of_qualities := f.read(1)[0]) == 0: # Get number of qualities in 8-bit integer
                # If the number of qualities is 0
                self.assets[name] = (int.from_bytes(f.read(8), "big"), int.from_bytes(f.read(8), "big"))
                # Store 64-bit integer position, 64-bit integer size
            else: # If the number of qualities is more than 0
                self.assets[name] = {} # Then where our position and size tuple would be we store a dictionary
                for y in range(num_of_qualities):
                    key = qualities[f.read(1)] # Using the 8-bit texture ID to get the string name of the quality
                    self.assets[name][key] = (int.from_bytes(f.read(8), "big"), int.from_bytes(f.read(8), "big"))
                    # Store # Store 64-bit integer position, 64-bit integer size with string name of quality as key
            self.file_map[name] = f
            # Store in file map which KAP file this texture belongs to
        self.open.append(os.path.basename(path))
        # Add the filename to the list of open files if successful

    def string_data(self, path, file):
        # String data and other data are separated by 0 bytes
        # This function will return the decoded string data of unknown length
        pointer = file.tell()
        for x in range(pointer, os.path.getsize(path)):
            # For every byte between our current position in the file and the length of the file
            # It would make sense to use a while loop that continues infinitely
            # However if we never get a definitive 0 byte to signify the end of the script the function will error
            # This way, if we reach the end of the file, we'll return None, signifying no string was found
            if file.read(1) == bytes(1): # bytes(1) in python generates our 0 byte
                # Reading one byte from the file also moves the pointer by one
                # So, this loop reads through the file until it hits a 0 byte
                file.seek(pointer)
                # Then we return to our starting point
                y = file.read(x-pointer)
                # Read everything between our starting point and the 0 byte
                file.seek(1, 1)
                # Move past the 0 byte
                return y.decode("utf-8")
                # And decode the data so it's returned as a python string object!

    def load(self, filename, quality=None, engine=None):
        pointer = self.assets[filename]
        # This shortens finding the filename in the assets dictionary to "pointer" because it's less to type
        f = self.file_map[filename]
        # This shortens finding the file object in the file map dictionary to "f" because it's less to type

        if isinstance(pointer, dict): # If the object in the assets dictionary is a dictionary then the file has qualities
            if not quality: # If the function call didn't specify a quality
                quality = list(pointer.keys())[0] # Then we pick the first one in the dictionary, which using the build function will be the highest quality
            if engine:
                engine.append_log(f"Files module, loading {filename}, quality {quality}")
            position, size = pointer[quality] # Unpack our position and size tuple for the quality that we want
        else: # If it's not a dictionary the file doesn't have qualities and assets will only have a tuple in it
            if engine:
                engine.append_log(f"Files module, loading {filename}")
            position, size = pointer # Unpack position and size tuple
        
        f.seek(position) # Move to the correct position in the file
        x = f.read(size) # Read the number of bytes that make up the file
        return BytesIO(rle_decode(x)) # Decode the RLE bytes and return them as a file-like object

def rle_encode(bytedata, counter_length, pattern_length):
    if counter_length == 0 or pattern_length == 0:
        return bytes(1) + bytedata
    # Sometimes, the best encoding is no encoding at all
    # If either paramter is 0 the algorithm can't work so we just return the raw bytes with the encoding byte at the front
    if x := (len(bytedata) % pattern_length): # If excess, trim off front and store
        excess = bytedata[:x]
        data = bytedata[x:]
    else:
        excess = b''
        data = bytedata
    dat, counter = data[0:pattern_length], 0
    # Get a the number of bytes of length pattern_length from the front of the data
    # dat will be used to store whatever the last byte was for comparing
    # counter will be used to store how many times that byte has been seen
    out = [
        int((counter_length << 4) + pattern_length).to_bytes(1, "big"),
        int(len(excess)).to_bytes(1, "big"),
        excess
        ] + [b'']*(len(bytedata)*2)
    out_position = 3
    # Our output is a list to take advantage of a fun python quirk
    # So at the front of the list is the thing we need at the front of the file
    # In order to store the two 4-bit integers within a single byte in python
    # we need to take counter length, and shift it up 4 bits so it has 4 bits of empty space.
    # Then, we can add our pattern_length
    # The next byte stores how long the excess is in bytes
    # And then the excess data itself is added
    # The rest of the list is made up off empty bytes
    # This takes advantage of a quirk of python. When appending to a bytes object,
    # Python has to copy the entire object to an entirely new space in memory whenever it gets bigger.
    # This causes significant slowdown as the file increases in size, making the code unable to run.
    # The same applies to appending to lists, but to a lesser extent.
    # To counter this, we create a list that is bigger than we will need full of empty bytes objects
    # Then instead of expanding the list we use out_position to overwrite existing values, which is faster
    # because python does not have to find a new space in memory to store the list.
    # The list is filled with twice as many empty bytes objects as bytes in the bytedata
    # because the maximum length we could need to store would be a counter of 1 on every single byte
    # Then if the list is big we can iterate through it to write it to a file, 
    # or use bytes.join if the system we're on has enough memory.
    max_counter_capacity = 2**(counter_length*8)-1
    # Calculates the maximum value of an unsigned integer with size x bytes
    for a in tqdm(iterable=range(0, len(data), pattern_length), desc=f"RLE compression, counter_length {counter_length}, pattern_length {pattern_length}") if len(bytedata) > 10_000_000 else range(0, len(data), pattern_length):
    # Starts at 0, counts up through the length of the data with a step of pattern_length.
    # Creates a progress bar if the file is bigger than 10MB.
        x = data[a:a+pattern_length] # Get a chunk of data of size pattern length
        if x == dat: # If it's the same as the last byte
            if counter == max_counter_capacity: # And we've hit the maximum amount of repeats that the counter can store
                # Put the counter and data into our output
                out[out_position] = counter.to_bytes(counter_length, "big") + dat
                # Reset the counter and move forward to the next slot in the output
                counter = 1
                out_position += 1
            else:
                # If the counter isn't at it's maximum size increment the counter
                counter += 1
        else: # If it's different then the previous bit of data has stopped repeating
            # So we put that data and the number of times it repeated into the output
            out[out_position] = counter.to_bytes(counter_length, "big") + dat
            # Reset the counter and set the variable for the previous bit of data to our current bit of data
            counter = 1
            dat = x
            out_position += 1
    # Return our list of output data to be combined into a bytes object later (it may not be worth it)
    out[out_position] = counter.to_bytes(counter_length, "big") + dat
    return out

def rle_decode(bytedata):
    # Two 4-bit integers contained within the first byte, so we used AND and bit shifting to get the two separate numbers
    counter_length = (bytedata[0] & 0b11110000) >> 4
    pattern_length = bytedata[0] & 0b00001111
    if counter_length == 0 or pattern_length == 0:
        return bytedata[1:] # No compression, so no decompression either, just trim the 0 byte from the front!
    # Here we have a byte representing the number of bytes of excess, so we trim that excess from the front
    if bytedata[1] == 0:
        excess = b''
        data = bytedata[2:]
    else:
        excess = bytedata[2:bytedata[1]+2]
        data = bytedata[bytedata[1]+2:]
    iterator = range(0, len(bytedata), counter_length+pattern_length)
    out = [excess] + [b'']*len(iterator)
    out_position = 1
    for x in iterator:
        dat = data[x:x+counter_length+pattern_length] # Get a chunk of data
        # Repeat the data for the number of times the pattern length specifies
        out[out_position] = (int.from_bytes(dat[:counter_length], "big") * dat[counter_length:])
        out_position += 1
    # Convert our list of bytes into one bytes object and return it
    return b''.join(out)

def rle_brute(bytedata): # Function for testing many compression settings and seeing which is the most effective
    z = rle_encode(bytedata, 0, 0) # No compression at all is our baseline
    out = ([z], len(z)) # Used to store the smallest output data and its size
    best_pattern_length = 0 # Once we've tested every pattern length with counter length 1, we only need to test every counter length with that pattern length
    a = int(log2(len(bytedata))/8) # Calculates how many pattern lengths need to be tested based on the size of the file being compressed
    if len(bytedata) > 1_000_000: # Use a progress bar if the file being compressed is larger than 1MB
        pbar = tqdm(desc="Compressing large file, please wait...", total=15+a-1)
    for x in range(1, 16):
        # Test all pattern lengths
        y = rle_encode(bytedata, 1, x)
        # Get size of output file by summing lengths, because function returns a list of bytes that will need to be combined
        length = sum(len(z) for z in y)
        if length < out[1]: # Store it if it's smaller than the smallest currently recorded
            out = (y, length)
            best_pattern_length = x
        try: pbar.update()
        except: pass
    if best_pattern_length:
        # Test all counter_lengths up to the one that would encapsulate the entire size of the file
        for x in range(1, a+1 if a < 15 else 16): # (Unless you are somehow compressing a super big file and then it maxes out at 15)
            y = rle_encode(bytedata, x, best_pattern_length)
            length = sum(len(z) for z in y)
            if length < out[1]:
                out = (y, length)
            try: pbar.update()
            except: pass
    else:
        try: pbar.update(a-1)
        except: pass
    # If the compressed data is less than 50MB then we combine it now and return it as a single bytes object
    # Otherwise, you would need several gigabytes in order to use .join, so you must iterate through the list of bytes in order to write it to a file
    return b''.join(out[0]) if out[1] < 50_000_000 else out[0]

# Function used for the creation of KAP files
# qualities is a dictionary: {quality name: float scale} where the float is the multiplier with which images should be scaled
# with_quality is a list of filenames
# without_quality is a list of filenames
# out_path is a string specifying the output file path
def build(qualities, with_quality, without_quality, out_path, compress=True):
    print("Building KAP file...")
    zero = bytes(1) # eight 0 bits
    if len(qualities) > 255:
        raise OverflowError("Too many qualities! Why do you need that many?")
    elif len(qualities) == 0:
        quality_ids = {"empty":int(1).to_bytes(1, "big")}
    else:
        # unique integer are generated by incrementing
        quality_ids = {y:x.to_bytes(1, "big") for x,y in enumerate(qualities.keys(), start=1)}
    pointers = {}
    with open(out_path, "wb") as f:
        f.write(b'\x07\xc9') # Magic byte 1993
        f.write(len(qualities).to_bytes(1, "big"))
        for x in qualities: # For each quality write it's name and ID
            f.write(x.encode("utf-8"))
            f.write(zero)
            f.write(quality_ids[x])
        # 32-bit integer, how many textures in total (counting quality variants as the same texture)
        f.write((len(without_quality)+len(with_quality)).to_bytes(4, "big"))
        for x in without_quality: # Until we've compressed the data we don't know the location and sizes so we leave a blank placeholder
            f.write(x.encode("utf-8"))
            f.write(zero*2)
            pointers[x] = f.tell()
            f.write(zero*16)
        for x in with_quality:
            f.write(x.encode("utf-8"))
            f.write(zero)
            f.write(len(qualities).to_bytes(1, "big"))
            pointers[x] = {}
            for y in qualities:
                f.write(quality_ids[y])
                pointers[x][y] = f.tell()
                f.write(zero*16)
        for x in tqdm(iterable=without_quality, desc="Dumping raw data for assets without quality"):
            with open(x, "rb") as y:
                raw = y.read()
                raw = rle_brute(raw) if compress else rle_encode(raw, 0, 0)
                # Write the compressed data to the file, then go back to the file's location in the header and write it's location and size
                pointer = f.tell()
                f.seek(pointers[x])
                f.write(pointer.to_bytes(8, "big"))
                f.write(len(raw).to_bytes(8, "big"))
                f.seek(0, 2)
                # If it's a list of bytes that is too big to combine we iterate through that list, otherwise we write the bytes object
                if type(raw) == list:
                    for z in raw:
                        f.write(z)
                else:
                    f.write(raw)
        for x in tqdm(iterable=with_quality, desc="Dumping raw data for assets with quality"):
            raw = Image.open(x)
            for y in qualities:
                # The same as before but now we are resizing the images to different texture qualities and storing information about each quality
                out_raw = BytesIO()
                out = raw.resize((int(round(raw.width*qualities[y], 0)) or 1, int(round(raw.height*qualities[y], 0)) or 1)) if qualities[y] != 1 else raw
                out.save(out_raw, "png", optimize=True)
                out_raw = rle_brute(out_raw.getvalue()) if compress else rle_encode(out_raw.getvalue(), 0, 0)
                pointer = f.tell()
                f.seek(pointers[x][y])
                f.write(pointer.to_bytes(8, "big"))
                f.write(len(out_raw).to_bytes(8, "big"))
                f.seek(0, 2)
                if type(out_raw) == list:
                    for z in out_raw:
                        f.write(z)
                else:
                    f.write(out_raw)
    print("Done!")