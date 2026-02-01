import csv
import os
import sys

if sys.platform != "darwin":
    raise RuntimeError("apple_clr_pallete requires macOS (Cocoa / AppKit)")
from Cocoa import NSColor, NSColorList


def make_clr_palette(
    csv_path=None,
    output_path=None,
    palette_name="CSV Palette"
):
    """Create a macOS .clr color palette file from a CSV.

    Args:
        csv_path: Path to CSV with 'hex_code' and 'tags' columns.
            Defaults to colorsheet.csv in parent directory.
        output_path: Where to save the .clr file.
            Defaults to pridepy.clr in parent directory.
        palette_name: Name shown in macOS color picker.

    Returns:
        Path to the generated .clr file.
    """
    # If no CSV path is provided, default to colorsheet.csv next to this script
    if csv_path is None:
        base_dir = os.path.dirname(os.getcwd())
        csv_path = os.path.join(base_dir, "colorsheet.csv")

    # If no output path is provided, place the .clr next to the script
    if output_path is None:
        base_dir = os.path.dirname(os.getcwd())
        output_path = os.path.join(base_dir, "pridepy.clr")

    cl = NSColorList.alloc().initWithName_(palette_name)

    def hex_to_color(h):
        h = h.lstrip("#")
        r = int(h[0:2], 16) / 255.0
        g = int(h[2:4], 16) / 255.0
        b = int(h[4:6], 16) / 255.0
        return NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, 1.0)

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=",")

        for row in reader:
            hex_code = row["hex_code"]
            tags = row["tags"]

            tag_key = "-".join(tag.strip() for tag in tags.split(";") if tag.strip())
            color = hex_to_color(hex_code)
            cl.setColor_forKey_(color, tag_key)

    cl.writeToFile_(output_path)
    return output_path

if __name__ == "__main__":
    make_clr_palette()
