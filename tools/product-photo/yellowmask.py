import sys, cv2, numpy as np
src, out_rgba, out_dbg = sys.argv[1:4]
img = cv2.imread(src); h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
yel = cv2.inRange(hsv, (18, 90, 110), (38, 255, 255))
yel = cv2.morphologyEx(yel, cv2.MORPH_CLOSE, np.ones((9,9),np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(yel)
k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); comp = (lab==k).astype(np.uint8)*255
# bag runs off the bottom of the frame: close the border along the bottom edge
ys, xs = np.nonzero(comp[h-20:, :])
if xs.size: comp[h-3:, xs.min():xs.max()+1] = 255
# fill interior: everything enclosed by yellow border
cnts,_ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
filled = np.zeros_like(comp); cv2.drawContours(filled, cnts, -1, 255, -1)
# grabcut refine
gc = np.full((h,w), cv2.GC_BGD, np.uint8)
gc[cv2.dilate(filled, np.ones((25,25),np.uint8))>0] = cv2.GC_PR_BGD
gc[filled>0] = cv2.GC_PR_FGD
gc[cv2.erode(filled, np.ones((31,31),np.uint8))>0] = cv2.GC_FGD
bg = np.zeros((1,65)); fg = np.zeros((1,65))
cv2.grabCut(img, gc, None, bg, fg, 5, cv2.GC_INIT_WITH_MASK)
m = np.where((gc==cv2.GC_FGD)|(gc==cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
n, lab, st, _ = cv2.connectedComponentsWithStats(m); k = 1+np.argmax(st[1:, cv2.CC_STAT_AREA]); m = (lab==k).astype(np.uint8)*255
cnts,_ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
m = np.zeros_like(m); cv2.drawContours(m, cnts, -1, 255, -1)
# interior is guaranteed product (enclosed by yellow border); grabcut only trims outer edge
inner = cv2.erode(filled, np.ones((15,15),np.uint8))
m = np.maximum(cv2.bitwise_and(m, filled), inner)
cnts,_ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
m = np.zeros_like(m); cv2.drawContours(m, cnts, -1, 255, -1)
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5,5),np.uint8))
a = cv2.GaussianBlur(m, (3,3), 0)
cv2.imwrite(out_rgba, np.dstack([img, a]))
dbg = img.copy(); dbg[m==0] = (dbg[m==0]*0.25).astype(np.uint8); cv2.imwrite(out_dbg, dbg)
x,y,bw,bh = cv2.boundingRect(m); print("bbox", x,y,bw,bh, "img", w,h, "touches_bottom", y+bh>=h-1)
