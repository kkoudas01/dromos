import os
import base64
import mimetypes
import tkinter as tk
from tkinter import filedialog, messagebox
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup

# Παράμετροι συμπίεσης
MAX_WIDTH = 1024
MAX_HEIGHT = 1024
JPEG_QUALITY = 85

def resize_image_if_needed(image_path):
    """Ανοίγει την εικόνα, ελέγχει αν χρειάζεται αλλαγή μεγέθους και επιστρέφει bytes, mime type."""
    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None:
        mime_type = 'image/octet-stream'

    with Image.open(image_path) as img:
        if getattr(img, 'is_animated', False):
            print(f"  Animated GIF, δεν αλλάζουμε μέγεθος.")
            with open(image_path, 'rb') as f:
                return f.read(), mime_type

        original_width, original_height = img.size
        if original_width <= MAX_WIDTH and original_height <= MAX_HEIGHT:
            print(f"  Δεν χρειάζεται resize ({original_width}x{original_height})")
            with open(image_path, 'rb') as f:
                return f.read(), mime_type

        ratio = min(MAX_WIDTH / original_width, MAX_HEIGHT / original_height)
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        print(f"  Resize: {original_width}x{original_height} -> {new_width}x{new_height}")

        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        buffer = BytesIO()

        if mime_type == 'image/jpeg':
            img_resized.save(buffer, format='JPEG', quality=JPEG_QUALITY, optimize=True)
        elif mime_type == 'image/png':
            img_resized.save(buffer, format='PNG', optimize=True)
        elif mime_type == 'image/gif' and not getattr(img, 'is_animated', False):
            img_resized.save(buffer, format='GIF', optimize=True)
        else:
            format = mime_type.split('/')[-1].upper()
            if format == 'JPG':
                format = 'JPEG'
            img_resized.save(buffer, format=format)

        return buffer.getvalue(), mime_type

def encode_image_to_base64(image_path):
    """Διαβάζει την εικόνα (με πιθανή συμπίεση) και επιστρέφει data URI."""
    img_data, mime_type = resize_image_if_needed(image_path)
    encoded = base64.b64encode(img_data).decode('utf-8')
    return f"data:{mime_type};base64,{encoded}"

def process_html_file(html_path, input_folder, output_folder):
    """Διαβάζει ένα HTML αρχείο, αντικαθιστά τις εικόνες με base64 και αποθηκεύει το αποτέλεσμα."""
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    img_tags = soup.find_all('img')
    modified = False

    for img in img_tags:
        src = img.get('src')
        if not src:
            continue

        if src.startswith(('http://', 'https://', 'data:')):
            continue

        img_abs_path = os.path.join(input_folder, src)
        if not os.path.exists(img_abs_path):
            print(f"Προσοχή: Η εικόνα {img_abs_path} δεν βρέθηκε. Αγνοείται.")
            continue

        try:
            print(f"Επεξεργασία: {src}")
            data_uri = encode_image_to_base64(img_abs_path)
            img['src'] = data_uri
            modified = True
        except Exception as e:
            print(f"Σφάλμα στην επεξεργασία της {src}: {e}")

    if modified:
        relative_path = os.path.relpath(html_path, input_folder)
        output_path = os.path.join(output_folder, relative_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        print(f"Αποθηκεύτηκε: {output_path}")
    else:
        print(f"Δεν βρέθηκαν εικόνες προς ενσωμάτωση στο {html_path}")

def select_folder():
    """Ανοίγει διάλογο επιλογής φακέλου και επιστρέφει τη διαδρομή."""
    root = tk.Tk()
    root.withdraw()  # Απόκρυψη του κύριου παραθύρου
    folder = filedialog.askdirectory(title="Επιλέξτε τον φάκελο που περιέχει τα HTML και τις εικόνες")
    root.destroy()
    return folder

def main():
    # Επιλογή φακέλου εισόδου
    input_folder = select_folder()
    if not input_folder:
        print("Δεν επιλέχθηκε φάκελος. Τερματισμός.")
        return

    # Δημιουργία ονόματος φακέλου εξόδου: input_folder + "BASE64"
    base_name = os.path.basename(input_folder)
    parent_dir = os.path.dirname(input_folder)
    output_folder = os.path.join(parent_dir, base_name + "BASE64")

    print(f"Φάκελος εισόδου: {input_folder}")
    print(f"Φάκελος εξόδου: {output_folder}")

    # Δημιουργία φακέλου εξόδου
    os.makedirs(output_folder, exist_ok=True)

    # Επεξεργασία όλων των .html / .htm αρχείων αναδρομικά
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.lower().endswith(('.html', '.htm')):
                html_path = os.path.join(root, file)
                process_html_file(html_path, input_folder, output_folder)

    print("Η διαδικασία ολοκληρώθηκε.")
    # Εμφάνιση μηνύματος ολοκλήρωσης
    messagebox.showinfo("Ολοκλήρωση", f"Η επεξεργασία ολοκληρώθηκε.\nΤα αρχεία αποθηκεύτηκαν στον φάκελο:\n{output_folder}")

if __name__ == "__main__":
    main()