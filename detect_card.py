import cv2
import numpy as np


# order points : top-left, top-right, bottom-right, bottom-left
def order_points(pts):
    pts = pts.reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")
    
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]       # top left
    rect[2] = pts[np.argmax(s)]       # bottom-right
    
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]    # top-right
    rect[3] = pts[np.argmax(diff)]    # bottom-left
    
    return rect


img = cv2.imread("images/id_card.jpg")
if img is None:
    print("ERROR: Image not loaded")
    exit()

orig = img.copy()

# Preprocessing
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blur = cv2.GaussianBlur(gray, (5, 5), 0)
edges = cv2.Canny(blur, 50, 150)

cv2.imwrite("output/edges_debug.jpg", edges)
print("Edges Saved")

contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

contours = sorted(contours, key=cv2.contourArea, reverse=True)

card_contour = None

for cnt in contours:
    area = cv2.contourArea(cnt)
    
    # Ignore very small contours
    if area < 1000:
        continue
    
    peri = cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
    
    if len(approx) == 4:
        card_contour = approx
        break

if card_contour is None:
    print("Card Contour NOT detected")
    exit()

print("Card contour detected")

# Draw contour
cv2.drawContours(img, [card_contour], -1, (0, 255, 0), 3)

# Perspective Transform
rect = order_points(card_contour)
(tl, tr, br, bl) = rect

widthA = np.linalg.norm(br - bl)
widthB = np.linalg.norm(tr - tl)
maxWidth = int(max(widthA, widthB))

heightA = np.linalg.norm(tr - br)
heightB = np.linalg.norm(tl - bl)
maxHeight = int(max(heightA, heightB))

dst = np.array([
    [0, 0],
    [maxWidth - 1, 0],
    [maxWidth - 1, maxHeight - 1],
    [0, maxHeight - 1]
], dtype="float32")

M = cv2.getPerspectiveTransform(rect, dst)
warped = cv2.warpPerspective(orig, M, (maxWidth, maxHeight))

# Save outputs
cv2.imwrite("output/detected_card.jpg", img)
cv2.imwrite("output/warped_card.jpg", warped)

print("Output images saved successfully")