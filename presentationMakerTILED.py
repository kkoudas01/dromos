# -*- coding: utf-8 -*-

import os
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import shutil
from PIL import Image

# --- Πρότυπο HTML v2.1 (Διορθωμένο) ---
# Ενημερωμένο πρότυπο που συναρμολογεί τα tiles στο lightbox
# αντί να φορτώνει την πρωτότυπη εικόνα.
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="el">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Εκπαιδευτική Παρουσίαση - Tiles</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Open+Sans:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary-color: #6a8fd8; --secondary-color: #a37cf0; --background-color: #0f0f13; --surface-color: #1e1e2a; --text-color: #e0e0e8; --header-color: #ffffff; --highlight-color: #6a8fd8; --shadow-color: rgba(106, 143, 216, 0.3); --card-bg: #252536; --card-hover: #2e2e45;
        }}
        body {{
            font-family: 'Roboto', 'Open Sans', sans-serif; background-color: var(--background-color); color: var(--text-color); margin: 0; padding: 0; line-height: 1.6; font-size: 1.05em; background-image: radial-gradient(circle at 10% 20%, #1e1e2a 0%, #0f0f13 100%);
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 30px 25px; }}
        .back-button {{ display: inline-flex; align-items: center; padding: 12px 24px; margin-bottom: 30px; background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; transition: all 0.3s ease; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); border: none; font-size: 1em; }}
        .back-button:hover {{ transform: translateY(-2px); box-shadow: 0 6px 16px var(--shadow-color); background: linear-gradient(135deg, var(--secondary-color), var(--primary-color)); }}
        .back-button::before {{ content: "←"; margin-right: 8px; font-size: 1.1em; }}
        .intro-paragraph {{ background-color: var(--surface-color); padding: 25px; border-radius: 12px; border-left: 6px solid var(--primary-color); margin-bottom: 40px; font-size: 1.1em; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); line-height: 1.7; }}
        .intro-paragraph strong {{ color: var(--highlight-color); font-weight: 600; }}
        .gallery-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 25px; }}
        .gallery-item {{
            position: relative; overflow: hidden; border-radius: 12px; cursor: pointer; box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2); transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); background-color: var(--card-bg); border: 1px solid rgba(255, 255, 255, 0.05);
            aspect-ratio: 16 / 9;
        }}
        .gallery-item:hover {{
            transform: translateY(-5px) scale(1.02); box-shadow: 0 10px 25px var(--shadow-color); border-color: rgba(106, 143, 216, 0.3);
        }}
        .tile-grid {{ display: grid; width: 100%; height: 100%; gap: 1px; }}
        .tile-grid img {{ width: 100%; height: 100%; display: block; object-fit: cover; }}
        .gallery-item::after {{
            content: attr(data-comment); position: absolute; bottom: 0; left: 0; right: 0; background: linear-gradient(transparent, rgba(0, 0, 0, 0.8)); color: white; padding: 20px 15px 15px; font-size: 1em; text-align: center; opacity: 0; transition: opacity 0.3s ease;
        }}
        .gallery-item:hover::after {{ opacity: 1; }}
        footer {{ text-align: center; margin-top: 60px; padding: 25px; color: rgba(200, 200, 220, 0.6); font-size: 0.95em; border-top: 1px solid rgba(255, 255, 255, 0.1); }}
        
        .lightbox {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(15, 15, 20, 0.95); z-index: 1000; display: none; justify-content: center; align-items: center; padding: 20px; box-sizing: border-box; opacity: 0; transition: opacity 0.4s ease; }}
        .lightbox.show {{ display: flex; opacity: 1; }}
        .lightbox-content {{ position: relative; max-width: 90vw; max-height: 90vh; display: flex; flex-direction: column; align-items: center; animation: fadeInZoom 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }}
        
        #lightbox-tile-container {{
             max-width: 100%; max-height: 80vh;
        }}

        .lightbox-tile-grid {{
            display: grid;
            width: 100%;
            line-height: 0;
            box-shadow: 0 0 30px rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            overflow: hidden;
        }}
        .lightbox-tile-grid img {{
            width: 100%; height: auto; display: block;
        }}
        
        @keyframes fadeInZoom {{ from {{ opacity: 0; transform: scale(0.9); }} to {{ opacity: 1; transform: scale(1); }} }}
        .lightbox-close, .lightbox-prev, .lightbox-next {{ position: absolute; color: white; font-size: 40px; font-weight: bold; cursor: pointer; user-select: none; z-index: 1001; background-color: rgba(30, 30, 42, 0.7); border-radius: 50%; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; transition: all 0.3s ease; }}
        .lightbox-close {{ top: 25px; right: 25px; font-size: 35px; }}
        .lightbox-prev, .lightbox-next {{ top: 50%; transform: translateY(-50%); padding: 5px; }}
        .lightbox-prev:hover, .lightbox-next:hover, .lightbox-close:hover {{ background-color: var(--primary-color); transform: translateY(-50%) scale(1.1); }}
        .lightbox-close:hover {{ transform: scale(1.1); }}
        .lightbox-prev {{ left: 25px; }}
        .lightbox-next {{ right: 25px; }}
        .lightbox-caption {{ color: white; background: rgba(40, 40, 55, 0.8); padding: 12px 20px; border-radius: 8px; font-size: 1.1em; text-align: center; margin-top: 15px; max-width: 80%; line-height: 1.5; }}
        @media (max-width: 768px) {{
            .gallery-grid {{ grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; }}
            .intro-paragraph {{ padding: 20px; font-size: 1em; }}
            .lightbox-close, .lightbox-prev, .lightbox-next {{ width: 40px; height: 40px; font-size: 30px; }}
            .lightbox-close {{ top: 15px; right: 15px; }}
        }}
    </style>
</head>
<body>

    <div class="container">
        <a href="../index.html" class="back-button">Επιστροφή</a>
        <p class="intro-paragraph">
            <strong>Καλώς ήρθατε!</strong> Αυτή είναι η παρουσίαση που δημιουργήθηκε από τα κομμάτια των εικόνων. Κάντε κλικ σε οποιαδήποτε εικόνα για να την δείτε σε πλήρη ανάλυση.
        </p>
        
        <div class="gallery-grid">
            {gallery_content}
        </div>
    </div>

    <footer>
        Παρουσίαση PowerPoint - Κώστας Κούδας 
    </footer>

    <div id="lightbox" class="lightbox">
        <span class="lightbox-close">&times;</span>
        <a class="lightbox-prev">&#10094;</a>
        <a class="lightbox-next">&#10095;</a>
        <div class="lightbox-content">
            <div id="lightbox-tile-container"></div>
            <div id="lightbox-caption" class="lightbox-caption"></div>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            const galleryItems = document.querySelectorAll('.gallery-item');
            const lightbox = document.getElementById('lightbox');
            const lightboxTileContainer = document.getElementById('lightbox-tile-container');
            const lightboxCaption = document.getElementById('lightbox-caption');
            const closeBtn = document.querySelector('.lightbox-close');
            const prevBtn = document.querySelector('.lightbox-prev');
            const nextBtn = document.querySelector('.lightbox-next');

            let currentImageIndex = 0;

            function showLightbox() {{
                lightbox.classList.add('show');
                document.body.style.overflow = 'hidden';
                document.addEventListener('keydown', handleKeyPress);
            }}

            function hideLightbox() {{
                lightbox.classList.remove('show');
                document.body.style.overflow = '';
                document.removeEventListener('keydown', handleKeyPress);
                lightboxTileContainer.innerHTML = ''; // Καθαρισμός για εξοικονόμηση μνήμης
            }}

            function updateImage(index) {{
                if (index < 0 || index >= galleryItems.length) return;

                const itemElement = galleryItems[index];
                const baseFilename = itemElement.dataset.baseFilename;
                const rows = parseInt(itemElement.dataset.rows);
                const cols = parseInt(itemElement.dataset.cols);
                const aspectRatio = parseFloat(itemElement.dataset.aspectRatio);

                // Καθαρισμός του περιεχομένου
                lightboxTileContainer.innerHTML = '';
                
                // Δημιουργία του πλέγματος για το lightbox
                const grid = document.createElement('div');
                grid.className = 'lightbox-tile-grid';
                grid.style.gridTemplateColumns = 'repeat(' + cols + ', 1fr)';
                grid.style.aspectRatio = aspectRatio;

                // Προσθήκη των tiles στο πλέγμα
                for (let r = 0; r < rows; r++) {{
                    for (let c = 0; c < cols; c++) {{
                        const img = document.createElement('img');
                        img.src = 'tiles/' + baseFilename + '_tile_' + r + '_' + c + '.png';
                        img.alt = 'Tile ' + r + '-' + c + ' for ' + baseFilename;
                        grid.appendChild(img);
                    }}
                }}

                lightboxTileContainer.appendChild(grid);
                lightboxCaption.textContent = itemElement.dataset.comment;
                currentImageIndex = index;

                prevBtn.style.display = index === 0 ? 'none' : 'flex';
                nextBtn.style.display = index === galleryItems.length - 1 ? 'none' : 'flex';
            }}

            galleryItems.forEach((item, index) => {{
                item.addEventListener('click', () => {{
                    updateImage(index);
                    showLightbox();
                }});
            }});

            closeBtn.addEventListener('click', hideLightbox);
            
            prevBtn.addEventListener('click', (e) => {{
                e.stopPropagation();
                updateImage(currentImageIndex - 1);
            }});
            
            nextBtn.addEventListener('click', (e) => {{
                e.stopPropagation();
                updateImage(currentImageIndex + 1);
            }});

            function handleKeyPress(e) {{
                if (e.key === 'Escape') hideLightbox();
                if (e.key === 'ArrowLeft' && currentImageIndex > 0) {{
                    updateImage(currentImageIndex - 1);
                }}
                if (e.key === 'ArrowRight' && currentImageIndex < galleryItems.length - 1) {{
                    updateImage(currentImageIndex + 1);
                }}
            }}
        }});
    </script>
</body>
</html>
"""

def create_tiled_presentation():
    """
    Κύρια συνάρτηση που εκτελεί όλη τη διαδικασία:
    1. Επιλογή φακέλων εισόδου/εξόδου.
    2. Λήψη ρυθμίσεων για το πλέγμα.
    3. Επεξεργασία εικόνων (τεμαχισμός και αποθήκευση).
    4. Δημιουργία του τελικού αρχείου HTML που βασίζεται αποκλειστικά στα tiles.
    """
    root = tk.Tk()
    root.withdraw()

    input_dir = filedialog.askdirectory(title="Επιλέξτε τον φάκελο με τις εικόνες")
    if not input_dir:
        messagebox.showinfo("Ακύρωση", "Η διαδικασία ακυρώθηκε.")
        return

    output_dir_base = os.path.join(os.path.dirname(input_dir), f"{os.path.basename(input_dir)}_Tiled")
    if os.path.exists(output_dir_base):
        if not messagebox.askyesno("Προειδοποίηση", f"Ο φάκελος '{output_dir_base}' υπάρχει ήδη. Θέλετε να αντικατασταθεί;"):
            return
        shutil.rmtree(output_dir_base)
    
    output_dir_tiles = os.path.join(output_dir_base, "tiles")
    os.makedirs(output_dir_tiles)
    
    try:
        rows = simpledialog.askinteger("Ρυθμίσεις Πλέγματος", "Πόσες σειρές πλακιδίων (rows);", initialvalue=4, minvalue=1, maxvalue=20)
        cols = simpledialog.askinteger("Ρυθμίσεις Πλέγματος", "Πόσες στήλες πλακιδίων (columns);", initialvalue=4, minvalue=1, maxvalue=20)
        if not rows or not cols:
            messagebox.showinfo("Ακύρωση", "Η διαδικασία ακυρώθηκε.")
            return
    except (ValueError, TypeError):
        messagebox.showinfo("Ακύρωση", "Μη έγκυρη τιμή. Η διαδικασία ακυρώθηκε.")
        return

    print(f"Επιλεγμένος φάκελος: {input_dir}")
    print(f"Φάκελος εξόδου: {output_dir_base}")
    print(f"Πλέγμα: {rows}x{cols}")
    
    try:
        image_files = sorted([f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))])
    except FileNotFoundError:
        messagebox.showerror("Σφάλμα", f"Δεν βρέθηκε ο φάκελος: {input_dir}")
        return
        
    if not image_files:
        messagebox.showerror("Σφάλμα", "Δεν βρέθηκαν εικόνες στον επιλεγμένο φάκελο.")
        shutil.rmtree(output_dir_base)
        return

    gallery_html_content = ""

    for i, filename in enumerate(image_files):
        try:
            print(f"Επεξεργασία εικόνας ({i+1}/{len(image_files)}): {filename}...")
            filepath = os.path.join(input_dir, filename)
            
            with Image.open(filepath) as img:
                width, height = img.size
                if width == 0 or height == 0:
                    print(f"Παράλειψη εικόνας με μηδενικές διαστάσεις: {filename}")
                    continue
                
                aspect_ratio = width / height
                tile_width = width // cols
                tile_height = height // rows

                base_filename = os.path.splitext(filename)[0]

                comment = f"Διαφάνεια {i + 1}"
                
                gallery_html_content += f'\n<!-- Slide {i+1}: {filename} -->\n'
                # Προσθήκη data-* attributes για χρήση από τη JavaScript
                gallery_html_content += (
                    f'<div class="gallery-item" '
                    f'data-comment="{comment}" '
                    f'data-base-filename="{base_filename}" '
                    f'data-rows="{rows}" '
                    f'data-cols="{cols}" '
                    f'data-aspect-ratio="{aspect_ratio:.4f}">'
                    f'\n'
                )
                gallery_html_content += f'    <div class="tile-grid" style="grid-template-columns: repeat({cols}, 1fr);">\n'
                
                for r in range(rows):
                    for c in range(cols):
                        box = (c * tile_width, r * tile_height, (c + 1) * tile_width, (r + 1) * tile_height)
                        tile = img.crop(box)
                        
                        tile_filename = f"{base_filename}_tile_{r}_{c}.png"
                        tile.save(os.path.join(output_dir_tiles, tile_filename), "PNG")
                        
                        tile_path = f"tiles/{tile_filename}"
                        gallery_html_content += f'        <img src="{tile_path}" alt="Tile {r}-{c}">\n'

                gallery_html_content += '    </div>\n</div>\n'
        except Exception as e:
            print(f"Σφάλμα κατά την επεξεργασία του αρχείου {filename}: {e}")
            messagebox.showwarning("Σφάλμα Αρχείου", f"Δεν ήταν δυνατή η επεξεργασία του αρχείου: {filename}\n\n{e}")

    final_html = HTML_TEMPLATE.format(gallery_content=gallery_html_content)
    
    html_filepath = os.path.join(output_dir_base, "presentationTILES.html")
    with open(html_filepath, 'w', encoding='utf-8') as f:
        f.write(final_html)
        
    print(f"\nΗ διαδικασία ολοκληρώθηκε!")
    print(f"Η παρουσίαση δημιουργήθηκε εδώ: {html_filepath}")
    messagebox.showinfo("Επιτυχία", f"Η παρουσίαση δημιουργήθηκε με επιτυχία στον φάκελο:\n{output_dir_base}")

if __name__ == "__main__":
    create_tiled_presentation()

