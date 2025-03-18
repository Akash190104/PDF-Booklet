import streamlit as st
import math
import io
import fitz  # PyMuPDF

def create_doublesided_4up_imposed_pdf(file_bytes: bytes) -> bytes:
    """
    Creates a double-sided 4-up imposed PDF for cut-and-stack assembly.
    
    Each physical A4 sheet (when printed duplex) yields 2 pages:
      • Front side quadrants (from top-left, top-right, bottom-left, bottom-right):
          For sheet j: [2*j+1, (2*j+1)+gap, (2*j+1)+2*gap, (2*j+1)+3*gap]
      • Back side quadrants:
          For sheet j: [2*j+2, (2*j+2)+gap, (2*j+2)+2*gap, (2*j+2)+3*gap]
    
    Here gap = 2*(number_of_sheets) - 1, where number_of_sheets = ceil(total_pages/8).
    This ordering makes, for example, a 101-page book impose as:
      Front of sheet 0:  1, 26, 51, 76  
      Back  of sheet 0:  2, 27, 52, 77  
    (and so on)
    """
    # Open the input PDF
    src_pdf = fitz.open(stream=file_bytes, filetype="pdf")
    total_input = src_pdf.page_count
    # If the total page count is odd, add a blank page (to make it even)
    if total_input % 2 == 1:
        total_input += 1

    # Each physical sheet holds 8 mini pages (4 on the front, 4 on the back)
    sheets = math.ceil(total_input / 8)
    gap = 2 * sheets - 1  # gap between mini pages in a sheet

    # A4 dimensions (points) and margin (points)
    A4_WIDTH = 595.0
    A4_HEIGHT = 842.0
    margin = 10

    # Define quadrant rectangles on an A4 page (coordinates: (x0, y0, x1, y1); origin at bottom-left)
    quad_rects = [
        # Top-left quadrant:
        fitz.Rect(margin, A4_HEIGHT/2 + margin, A4_WIDTH/2 - margin, A4_HEIGHT - margin),
        # Top-right quadrant:
        fitz.Rect(A4_WIDTH/2 + margin, A4_HEIGHT/2 + margin, A4_WIDTH - margin, A4_HEIGHT - margin),
        # Bottom-left quadrant:
        fitz.Rect(margin, margin, A4_WIDTH/2 - margin, A4_HEIGHT/2 - margin),
        # Bottom-right quadrant:
        fitz.Rect(A4_WIDTH/2 + margin, margin, A4_WIDTH - margin, A4_HEIGHT/2 - margin)
    ]

    # Create the output PDF
    out_pdf = fitz.open()

    # For each physical sheet (indexed j = 0 ... sheets-1)
    for j in range(sheets):
        # Calculate front side page numbers for this sheet
        front_q0 = 2 * j + 1
        front_q1 = front_q0 + gap
        front_q2 = front_q0 + 2 * gap
        front_q3 = front_q0 + 3 * gap
        front_pages = [front_q0, front_q1, front_q2, front_q3]
        
        # Create the front side page
        front_page = out_pdf.new_page(width=A4_WIDTH, height=A4_HEIGHT)
        for idx, p in enumerate(front_pages):
            if p <= src_pdf.page_count:
                front_page.show_pdf_page(quad_rects[idx], src_pdf, p - 1)
        
        # Calculate back side page numbers for this sheet
        back_q0 = 2 * j + 2
        back_q1 = back_q0 + gap
        back_q2 = back_q0 + 2 * gap
        back_q3 = back_q0 + 3 * gap
        back_pages = [back_q0, back_q1, back_q2, back_q3]
        
        # Create the back side page
        back_page = out_pdf.new_page(width=A4_WIDTH, height=A4_HEIGHT)
        for idx, p in enumerate(back_pages):
            if p <= src_pdf.page_count:
                back_page.show_pdf_page(quad_rects[idx], src_pdf, p - 1)
    
    # Write the output PDF to bytes and return
    output_buffer = io.BytesIO()
    out_pdf.save(output_buffer)
    output_buffer.seek(0)
    return output_buffer.read()


def main():
    st.title("Double-Sided 4-Up Imposition (Cut-and-Stack)")
    st.write("""
    Upload a PDF and this tool will rearrange its pages into a double-sided 4-up layout.
    
    
    When printed duplex on A4, cut along the midlines, and then stacked appropriately,
    the mini pages will assemble into the correct reading order.
    """)
    
    uploaded_file = st.file_uploader("Upload your PDF file", type=["pdf"])
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        output_pdf_bytes = create_doublesided_4up_imposed_pdf(file_bytes)
        st.download_button(
            label="Download Imposed PDF",
            data=output_pdf_bytes,
            file_name="4up_doublesided_imposed.pdf",
            mime="application/pdf"
        )

if __name__ == "__main__":
    main()