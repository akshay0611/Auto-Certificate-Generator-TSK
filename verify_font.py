
import os
from pathlib import Path
from pdf_generator import generate_certificate, render_preview_image
from config import get_certificate_settings, get_app_config

def main():
    settings = get_certificate_settings()
    config = get_app_config()
    template_path = config["PDF_TEMPLATE_PATH"]
    
    registration = {
        "id": "123456789",
        "full_name": "MARIPI AKSHAI NAIDU",
        "workshop_id": "WS001",
        "workshop_title": "Hackers vs Defenders: How Cybersecurity is Shaping the Digital World",
        "created_at": "2024-01-01"
    }
    
    try:
        pdf_bytes = generate_certificate(registration, settings, template_path)
        
        pdf_path = Path("output/test_ibm_font.pdf")
        pdf_path.parent.mkdir(exist_ok=True)
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"PDF saved to {pdf_path}")
        
        png_bytes = render_preview_image(pdf_bytes)
        
        output_path = Path("output/test_ibm_font.png")
        with open(output_path, "wb") as f:
            f.write(png_bytes)
        print(f"Preview saved to {output_path}")
        
        # Also check which font name is in the settings
        print(f"Font name in settings: {settings['name']['font_name']}")
        print(f"Font size for workshop: {settings['workshop']['font_size']}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
