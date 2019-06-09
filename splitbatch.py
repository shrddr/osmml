import random
import pathlib
import os
import tarfile

VALID_SHARE = 0.1
TEST_SHARE = 0.1

if __name__ == "__main__":
    
    src = pathlib.Path('lamps/train')
    cdirs = [x for x in src.iterdir() if x.is_dir()]
    for cdir in cdirs:
        cat = cdir.parts[-1]
        files = list(cdir.glob("*.jpg"))
        random.shuffle(files)
        
        count = len(files)
        vsize = round(count * VALID_SHARE)
        tsize = round(count * TEST_SHARE)
        
        valids = files[:vsize]
        tests = files[vsize:vsize+tsize]
        
        vdir = cdir.parents[1] / "valid" / cat
        tdir = cdir.parents[1] / "test" / cat
        vdir.mkdir(parents=True, exist_ok=True)
        tdir.mkdir(parents=True, exist_ok=True)
        print(vdir)
    
        for src in valids:
            os.rename(src, vdir / src.name)
            
        for src in tests:
            os.rename(src, tdir / src.name)
        
    tarball = "./lamps-orig.tar"
    if os.path.exists(tarball):
        os.remove(tarball)
    tar = tarfile.open(tarball, "w")
    tar.add("./lamps")
    tar.close()