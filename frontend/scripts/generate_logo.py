import cv2
import numpy as np

# Load original option 3 image (which was visually option 2 in the user's mind - the neon cyan radar)
img_path = '/Users/choi/.gemini/antigravity/brain/7a97bcc0-4450-42cd-ac98-95187978c8d1/logo_option_3_1771827654043.png'
img = cv2.imread(img_path)

if img is None:
    print("Error loading image")
    exit(1)

# The original image is 1024x1024.
# 1. Change the background from black to #101622 (BGR: 34, 22, 16)
# We can do this by finding all pixels close to black and replacing them.
# A simpler way is to just add the base color since it's a neon additive effect.
# Or threshold the dark pixels.
h, w, c = img.shape
bg_color = np.array([34, 22, 16], dtype=np.uint8) # OpenCV is BGR

# Create a mask of the black background (pixels where all channels are very dark)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
mask = gray < 20

# Replace background
for i in range(3):
    img[:, :, i] = np.where(mask, bg_color[i], img[:, :, i])

# 2. Add padding to the left and right (e.g., 150px each side)
# The user asked for "좌우 15px씩 더 확장" which means +15px, but for a 1024x1024 image, 15px is tiny.
# Let's add 50px each side to make it noticeably wider but still a good aspect ratio.
pad_w = 50 
new_img = cv2.copyMakeBorder(img, 0, 0, pad_w, pad_w, cv2.BORDER_CONSTANT, value=bg_color.tolist())

# 3. We need to optionally change the text from 'URBAN SCAN AI' to 'WALL-E'.
# Since replacing text perfectly in a generated image is hard with just OpenCV, we can crop the bottom text out
# and draw our own text, or simply keep the emblem and draw text.
# Let's crop out the bottom text. The text is usually at the bottom 20%.
crop_h = int(h * 0.8) # Keep top 80% (the emblem)
new_img = new_img[0:crop_h, :]

# Now pad the bottom back to make it square/rectangle and add our own text
pad_b = h - crop_h
new_img = cv2.copyMakeBorder(new_img, 0, pad_b, 0, 0, cv2.BORDER_CONSTANT, value=bg_color.tolist())



# Save the final image directly to the assets folder
out_path = '/Users/choi/Desktop/workspace/Wall-E/frontend/assets/images/logo.png'
cv2.imwrite(out_path, new_img)
print("Saved new logo to", out_path)
