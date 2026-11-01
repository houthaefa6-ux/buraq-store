import sys, numpy as np
from PIL import Image
src, out = sys.argv[1:3]
im = Image.open(src).convert("RGBA"); a = np.array(im)[:,:,3]
ys, xs = np.nonzero(a > 0); x0,x1,y0,y1 = xs.min(), xs.max()+1, ys.min(), ys.max()+1
crop = im.crop((x0,y0,x1,y1)); w,h = crop.size
side = int(round(max(w/0.86, h/0.78)))
c = Image.new("RGBA", (side, side), (0,0,0,0))
c.paste(crop, ((side-w)//2, (side-h)//2)); c.save(out, optimize=True)
op = np.nonzero(np.array(crop)[:,:,3]==255)
print("canvas", side, "crop", w, h, "opaque product w/h frac", (np.ptp(op[1])+1)/side, (np.ptp(op[0])+1)/side)
