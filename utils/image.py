import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


def _preprocess_image(image, group_index=None):
    if not CV2_AVAILABLE:
        return image

    img_array = np.array(image)
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    denoised = cv2.bilateralFilter(enhanced, 5, 50, 50)

    rgb = cv2.cvtColor(denoised, cv2.COLOR_GRAY2RGB)
    from PIL import Image
    return Image.fromarray(rgb, mode="RGB")
