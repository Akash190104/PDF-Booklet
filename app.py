import streamlit as st
import math
import io
import fitz  # PyMuPDF

def create_4up_cut_stack_pdf(file_bytes: bytes) -> bytes:
    """
    Rearranges the pages of an input PDF into a 4-up layout on A4 paper.
    Each A4 page is divided into four quadrants with a margin.
    The pages are placed in "cut-and-stack" order:
      - For each output sheet (index i), the quadrants are filled by pages:
        i, i+total_sheets, i+2*total_sheets, i+3*total_sheets.
    Each input page is scaled (preserving its aspect ratio) to fit inside its quadrant.
    """
    # A4 dimensions in points
    A4_WIDTH = 595.0
    A4_HEIGHT = 842.0
    margin = 10  # margin in points inside each quadrant

    # Open the input PDF from bytes using PyMuPDF
    input_pdf = fitz.open(stream=file_bytes, filetype="pdf")
    num_pages = input_pdf.page_count

    # Calculate how many A4 sheets are needed (each sheet holds 4 pages)
    total_sheets = math.ceil(num_pages / 4)

    # Prepare the output PDF document
    output_pdf = fitz.open()

    # Define the target quadrants (with margins) on an A4 sheet.
    # The A4 page is divided into 4 equal parts:
    #   - Quadrant 0 (top-left)
    #   - Quadrant 1 (top-right)
    #   - Quadrant 2 (bottom-left)
    #   - Quadrant 3 (bottom-right)
    # In a coordinate system where (0,0) is the bottom left:
    quadrant_rects = [
        # Top-left quadrant:
        fitz.Rect(margin,
                  A4_HEIGHT/2 + margin,
                  A4_WIDTH/2 - margin,
                  A4_HEIGHT - margin),
        # Top-right quadrant:
        fitz.Rect(A4_WIDTH/2 + margin,
                  A4_HEIGHT/2 + margin,
                  A4_WIDTH - margin,
                  A4_HEIGHT - margin),
        # Bottom-left quadrant:
        fitz.Rect(margin,
                  margin,
                  A4_WIDTH/2 - margin,
                  A4_HEIGHT/2 - margin),
        # Bottom-right quadrant:
        fitz.Rect(A4_WIDTH/2 + margin,
                  margin,
                  A4_WIDTH - margin,
                  A4_HEIGHT/2 - margin)
    ]

    # Process each A4 sheet (output page)
    for sheet in range(total_sheets):
        # Create a new blank A4 page in the output PDF.
        output_page = output_pdf.new_page(width=A4_WIDTH, height=A4_HEIGHT)

        # For each quadrant (0 to 3)
        for q in range(4):
            # Compute the corresponding input page index based on cut-and-stack ordering.
            page_index = sheet + q * total_sheets
            if page_index < num_pages:
                # Load the input page.
                src_page = input_pdf.load_page(page_index)
                src_rect = src_page.rect  # source page dimensions
                src_width = src_rect.width
                src_height = src_rect.height

                # Get the target quadrant rectangle.
                target_rect = quadrant_rects[q]

                # Calculate the scale factor to fit the source page into the target quadrant
                # while preserving the aspect ratio.
                scale = min(target_rect.width / src_width, target_rect.height / src_height)
                new_width = src_width * scale
                new_height = src_height * scale

                # Center the scaled page within the target quadrant.
                new_x0 = target_rect.x0 + (target_rect.width - new_width) / 2
                new_y0 = target_rect.y0 + (target_rect.height - new_height) / 2
                new_rect = fitz.Rect(new_x0, new_y0, new_x0 + new_width, new_y0 + new_height)

                # Draw the input page onto the output page in the calculated rectangle.
                output_page.show_pdf_page(new_rect, input_pdf, page_index)

    # Write the output PDF to bytes.
    output_bytes = output_pdf.write()
    return output_bytes

def main():
    st.title("Quarter-Size Booklet (4-up Cut-and-Stack) PDF Imposition")
    st.write("""
    1. Upload a PDF.
    2. This tool rearranges its pages into a 4-up (quarter of A4) layout in cut-and-stack order.
    3. Download and print the result on A4 paper (double-sided).
    4. After printing, cut horizontally and then vertically to obtain four stacks of quarter-sized pages in the proper order.
    """)

    uploaded_file = st.file_uploader("Upload your PDF file", type=["pdf"])
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        output_pdf_bytes = create_4up_cut_stack_pdf(file_bytes)
        st.download_button(
            label="Download 4-up PDF",
            data=output_pdf_bytes,
            file_name="4up_booklet.pdf",
            mime="application/pdf"
        )

if __name__ == "__main__":
    main()