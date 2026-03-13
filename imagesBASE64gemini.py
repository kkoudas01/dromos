import os
import base64
import mimetypes
import io
from bs4 import BeautifulSoup
from PIL import Image
from tkinter import filedialog, Tk

def compress_and_convert_to_base64(image_path, max_width=1200, quality=85):
    """Συμπιέζει την εικόνα και τη μετατρέπει σε Base64."""
    try:
        # Έλεγχος αν είναι SVG (τα SVG δεν χρειάζονται Pillow/συμπίεση)
        if image_path.lower().endswith('.svg'):
            with open(image_path, "rb") as f:
                binary_data = f.read()
            base64_str = base64.b64encode(binary_data).decode('utf-8')
            return f"data:image/svg+xml;base64,{base64_str}"

        img = Image.open(image_path)
        img_format = img.format
        
        # Resize αν η εικόνα είναι πολύ μεγάλη
        if img.width > max_width:
            change_ratio = max_width / float(img.width)
            new_height = int(float(img.height) * float(change_ratio))
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        buffer = io.BytesIO()
        if img_format == 'PNG':
            img.save(buffer, format="PNG", optimize=True)
        else:
            img.save(buffer, format="JPEG", quality=quality, optimize=True)
            
        binary_data = buffer.getvalue()
        base64_utf8_str = base64.b64encode(binary_data).decode('utf-8')
        
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type: mime_type = "image/jpeg"
            
        return f"data:{mime_type};base64,{base64_utf8_str}"
    except Exception as e:
        print(f"  [!] Σφάλμα στην εικόνα {image_path}: {e}")
        return None

def process_html_files():
    # 1. Εμφάνιση παραθύρου επιλογής φακέλου
    root = Tk()
    root.withdraw() # Κρύβουμε το κύριο παράθυρο του Tkinter
    root.attributes('-topmost', True) # Φέρνουμε το παράθυρο μπροστά
    
    input_folder = filedialog.askdirectory(title="Επίλεξε τον φάκελο με τα HTML αρχεία")
    root.destroy()

    if not input_folder:
        print("Δεν επιλέχθηκε φάκελος. Τερματισμός.")
        return

    # 2. Δημιουργία φακέλου εξόδου (προσθέτουμε το _BASE64 στο όνομα)
    output_folder = input_folder + "_BASE64"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    print(f"Ξεκινάει η επεξεργασία στον φάκελο: {input_folder}")
    print(f"Τα αρχεία θα αποθηκευτούν στο: {output_folder}\n")

    for filename in os.listdir(input_folder):
        if filename.endswith(".html"):
            file_path = os.path.join(input_folder, filename)
            print(f"Επεξεργασία: {filename}...")

            with open(file_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")

            for img_tag in soup.find_all("img"):
                src = img_tag.get("src")
                if src and not src.startswith("data:"):
                    # Κατασκευή διαδρομής εικόνας (σχετική με το HTML)
                    img_full_path = os.path.join(input_folder, src)
                    
                    if os.path.exists(img_full_path):
                        base64_data = compress_and_convert_to_base64(img_full_path)
                        if base64_data:
                            img_tag["src"] = base64_data
                            print(f"  - Ενσωματώθηκε: {src}")
                    else:
                        print(f"  - ΠΡΟΣΟΧΗ: Δεν βρέθηκε η εικόνα {src}")

            # Αποθήκευση
            with open(os.path.join(output_folder, filename), "w", encoding="utf-8") as f:
                f.write(str(soup))

    print(f"\nΟλοκληρώθηκε! Έτοιμα τα αρχεία στο: {output_folder}")

# Εκτέλεση του προγράμματος
if __name__ == "__main__":
    process_html_files()