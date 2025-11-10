"""
PDF Generator for Nested Dictionaries
Converts any nested dictionary structure to a well-formatted PDF document.
"""
import json
import traceback
from pathlib import Path
from fpdf import FPDF


class DocumentPDF(FPDF):
    """Custom PDF class with header and footer."""
    
    def header(self):
        """Optional header - kept minimal."""
        pass
    
    def footer(self):
        """Add page numbers to footer."""
        self.set_y(-12)
        self.set_font("Helvetica", size=8)
        self.cell(0, 6, f"Page {self.page_no()}", align="C")


def normalize_text(value, max_len=2000, unicode_support=True):
    """
    Convert any Python object to a safe string for PDF output.
    
    Args:
        value: Any Python object (str, int, float, dict, list, etc.)
        max_len: Maximum length before truncation
        unicode_support: Whether Unicode characters should be preserved (False = replace with ASCII)
    
    Returns:
        str: Safe string representation
    """
    if value is None:
        return ""
    
    if isinstance(value, str):
        s = value
    else:
        try:
            s = json.dumps(value, ensure_ascii=False, indent=2)
        except Exception:
            s = str(value)
    
    # Replace non-breaking spaces
    s = s.replace("\xa0", " ")
    
    # If no Unicode support (Helvetica fallback), replace Unicode characters
    if not unicode_support:
        # Replace em dash with regular dash
        s = s.replace("—", "-").replace("–", "-")
        # Replace other common Unicode characters
        s = s.replace(""", '"').replace(""", '"')
        s = s.replace("'", "'").replace("'", "'")
        s = s.replace("…", "...")
        s = s.replace("•", "*")  # Bullet point
        s = s.replace("€", "EUR").replace("£", "GBP").replace("¥", "JPY")
        # Remove any remaining non-ASCII characters that might cause issues
        s = s.encode('ascii', 'replace').decode('ascii')
    
    # Insert zero-width spaces to help with word breaking for long URLs/tokens
    s = s.replace("/", "/\u200b").replace("-", "-\u200b")
    if unicode_support:
        s = s.replace("—", "—\u200b")
    
    # Limit extremely long strings
    if len(s) > max_len:
        return s[:max_len//2] + "\n\n...[truncated]...\n\n" + s[-max_len//2:]
    
    return s


def safe_multicell(pdf: FPDF, text: str, lh: float = 6.0, indent: int = 0):
    """
    Safely write text to PDF with multiple fallback strategies.
    
    Args:
        pdf: FPDF instance
        text: Text to write
        lh: Line height
        indent: Left indentation in mm
    """
    if text is None:
        text = ""
    if not isinstance(text, str):
        text = str(text)

    if not text.strip():
        return

    # Apply indentation
    if indent > 0:
        pdf.cell(indent)
    
    try:
        pdf.multi_cell(
            w=0,
            h=lh,
            txt=text,
            new_x="LMARGIN",
            new_y="NEXT",
            max_line_height=pdf.font_size
        )
    except Exception:
        # Try breaking URLs and long tokens
        t = text.replace("http", "http\u200b").replace("www.", "www.\u200b")
        try:
            pdf.multi_cell(
                w=0,
                h=lh,
                txt=t,
                new_x="LMARGIN",
                new_y="NEXT",
                max_line_height=pdf.font_size
            )
        except Exception:
            # Final fallback: truncate
            trunc = (text[:1000] + "\n\n...[truncated]...") if len(text) > 1000 else text
            try:
                pdf.multi_cell(
                    w=0,
                    h=lh,
                    txt=trunc,
                    new_x="LMARGIN",
                    new_y="NEXT",
                    max_line_height=pdf.font_size
                )
            except Exception:
                # Last resort: error message
                pdf.multi_cell(
                    w=0,
                    h=lh,
                    txt="[Error rendering text — see logs]",
                    new_x="LMARGIN",
                    new_y="NEXT"
                )


def format_key(key: str) -> str:
    """Format dictionary keys for display (snake_case to Title Case)."""
    return key.replace("_", " ").title()


def setup_font(pdf: FPDF):
    """
    Setup font with Unicode support if available.
    Registers both regular and bold variants if DejaVu fonts are found.
    
    Args:
        pdf: FPDF instance to configure
    
    Returns:
        bool: True if Unicode font (DejaVu) was successfully registered, False otherwise
    """
    dejavu_regular_paths = [
        "dejavu-ttf/DejaVuSans.ttf",
        "./DejaVuSans.ttf"
    ]
    
    dejavu_bold_paths = [
        "dejavu-ttf/DejaVuSans-Bold.ttf",
        "./DejaVuSans-Bold.ttf"
    ]
    
    # Try to register regular DejaVu font
    regular_path = None
    for path in dejavu_regular_paths:
        if Path(path).exists():
            try:
                pdf.add_font("DejaVu", "", path, uni=True)
                regular_path = path
                break
            except Exception:
                continue
    
    # If regular font found, try to register bold variant
    if regular_path:
        bold_registered = False
        for path in dejavu_bold_paths:
            if Path(path).exists():
                try:
                    pdf.add_font("DejaVu", "B", path, uni=True)
                    bold_registered = True
                    break
                except Exception:
                    continue
        
        # Set the font (regular)
        pdf.set_font("DejaVu", size=12)
        return True
    
    # Fallback to Helvetica (no Unicode support)
    pdf.set_font("Helvetica", size=12)
    return False


def filter_founder_qa(data):
    """
    Recursively filter out founder_qa_transcript from the dictionary.
    
    Args:
        data: Dictionary to filter
    
    Returns:
        dict: Filtered dictionary with founder_qa_transcript keys removed
    """
    if not isinstance(data, dict):
        return data
    
    filtered = {}
    for key, value in data.items():
        # Skip founder_qa_transcript key
        if key == "founder_qa_transcript":
            continue
        
        # Recursively filter nested dictionaries
        if isinstance(value, dict):
            filtered[key] = filter_founder_qa(value)
        elif isinstance(value, list):
            # Filter list items if they are dictionaries
            filtered[key] = [
                filter_founder_qa(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            filtered[key] = value
    
    return filtered


def dict_to_pdf(data: dict, title: str = "Document", max_depth: int = 20) -> bytes:
    """
    Convert any nested dictionary to a PDF file.
    
    This function handles:
    - Nested dictionaries of any depth
    - Lists containing primitives, dictionaries, or other lists
    - Strings, numbers, booleans, and null values
    - Long text with automatic wrapping and truncation
    - Unicode characters (when DejaVu font is available)
    
    Args:
        data: The nested dictionary to convert (can be any depth)
        title: Title for the PDF document
        max_depth: Maximum nesting depth to prevent infinite recursion (default: 20)
    
    Returns:
        bytes: PDF file as bytes, ready for Streamlit download_button
    
    Example:
        >>> data = {"key1": {"nested": "value"}, "key2": [1, 2, 3]}
        >>> pdf_bytes = dict_to_pdf(data, title="My Report")
        >>> st.download_button("Download", pdf_bytes, "report.pdf", "application/pdf")
    """
    # Filter out founder_qa_transcript before rendering
    data = filter_founder_qa(data)
    
    pdf = DocumentPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Setup font with Unicode support - track if we have it
    has_unicode_font = setup_font(pdf)
    font_family = "DejaVu" if has_unicode_font else "Helvetica"
    
    # Title
    try:
        pdf.set_font(font_family, "B" if has_unicode_font else "", 18)
    except Exception:
        # If bold fails, use regular
        pdf.set_font(font_family, "", 18)
    
    title_text = normalize_text(title, unicode_support=has_unicode_font)
    safe_multicell(pdf, title_text, lh=8)
    pdf.ln(6)
    
    def render_value(
        value,
        key_path: str = "",
        depth: int = 0,
        indent: int = 0,
        is_list_item: bool = False
    ):
        """
        Recursively render any value to the PDF.
        
        Args:
            value: The value to render (dict, list, or primitive)
            key_path: Path of keys for error reporting
            depth: Current nesting depth
            indent: Visual indentation level in mm
            is_list_item: Whether this is an item in a list
        """
        if depth > max_depth:
            safe_multicell(pdf, "[Maximum depth exceeded]", indent=indent)
            return
        
        try:
            # Handle None
            if value is None:
                safe_multicell(pdf, "(null)", lh=5, indent=indent)
                pdf.ln(1)
                return
            
            # Handle dictionaries
            if isinstance(value, dict):
                if not value:
                    empty_text = normalize_text("(empty dictionary)", unicode_support=has_unicode_font)
                    safe_multicell(pdf, empty_text, lh=5, indent=indent)
                    pdf.ln(1)
                    return
                
                # Render each key-value pair
                for i, (k, v) in enumerate(value.items()):
                    key_display = format_key(k)
                    
                    # Set bold font for keys (only if Unicode font supports it)
                    try:
                        pdf.set_font(font_family, "B" if has_unicode_font else "", 11)
                    except Exception:
                        pdf.set_font(font_family, "", 11)
                    
                    # Add spacing between dictionary items
                    if i > 0:
                        pdf.ln(1)
                    
                    # Write key with indentation
                    key_text = normalize_text(f"{key_display}:", unicode_support=has_unicode_font)
                    safe_multicell(pdf, key_text, lh=6, indent=indent)
                    
                    # Reset font for value
                    pdf.set_font(font_family, "", 10)
                    
                    # Recursively render value
                    new_path = f"{key_path}.{k}" if key_path else k
                    render_value(v, new_path, depth + 1, indent + 8, False)
                
                pdf.ln(0.5)
                return
            
            # Handle lists
            if isinstance(value, list):
                if not value:
                    empty_text = normalize_text("(empty list)", unicode_support=has_unicode_font)
                    safe_multicell(pdf, empty_text, lh=5, indent=indent)
                    pdf.ln(1)
                    return
                
                # Render each list item
                for i, item in enumerate(value):
                    # Add spacing between list items
                    if i > 0:
                        pdf.ln(0.5)
                    
                    # Handle nested structures in lists
                    if isinstance(item, dict):
                        # For dictionaries in lists, show "Item N:" label
                        try:
                            pdf.set_font(font_family, "B" if has_unicode_font else "", 10)
                        except Exception:
                            pdf.set_font(font_family, "", 10)
                        item_text = normalize_text(f"Item {i+1}:", unicode_support=has_unicode_font)
                        safe_multicell(pdf, item_text, lh=5, indent=indent)
                        pdf.set_font(font_family, "", 10)
                        render_value(item, f"{key_path}[{i}]" if key_path else f"[{i}]", depth + 1, indent + 8, True)
                    elif isinstance(item, list):
                        # For nested lists, show "List {i+1}:" and render recursively
                        try:
                            pdf.set_font(font_family, "B" if has_unicode_font else "", 10)
                        except Exception:
                            pdf.set_font(font_family, "", 10)
                        list_text = normalize_text(f"List {i+1}:", unicode_support=has_unicode_font)
                        safe_multicell(pdf, list_text, lh=5, indent=indent)
                        pdf.set_font(font_family, "", 10)
                        render_value(item, f"{key_path}[{i}]" if key_path else f"[{i}]", depth + 1, indent + 8, True)
                    else:
                        # Primitive values - use bullet point (or * if no Unicode)
                        text = normalize_text(item, unicode_support=has_unicode_font)
                        bullet = "•" if has_unicode_font else "*"
                        safe_multicell(pdf, f"{bullet} {text}", lh=5, indent=indent)
                
                pdf.ln(0.5)
                return
            
            # Handle primitive values (str, int, float, bool, etc.)
            text = normalize_text(value, unicode_support=has_unicode_font)
            safe_multicell(pdf, text, lh=5, indent=indent)
            pdf.ln(1)
        
        except Exception as e:
            # Error handling
            pdf.set_font(font_family, "", 9)
            error_msg = f"[Error rendering {key_path}: {str(e)[:100]}]"
            safe_multicell(pdf, error_msg, indent=indent)
            pdf.ln(1)
            print(f"Failed to render {key_path}: {e}")
            traceback.print_exc()
    
    # Render the entire dictionary
    pdf.set_font(font_family, "", 10)
    render_value(data)

    # Return PDF as bytes
    pdf_bytes = pdf.output(dest="S")
    # pdf.output(dest="S") already returns bytes/bytearray, convert to bytes if needed
    if isinstance(pdf_bytes, bytearray):
        return bytes(pdf_bytes)
    return pdf_bytes


# Keep the old function name for backward compatibility
def build_deal_note_pdf(analysis: dict, company_name: str) -> bytes:
    """
    Legacy function for backward compatibility.
    Converts analysis dictionary to PDF with company name as title.
    
    Args:
        analysis: Analysis dictionary
        company_name: Company name for the title
    
    Returns:
        bytes: PDF file as bytes
    """
    title = f"Deal Note — {company_name}" if company_name else "Deal Note"
    return dict_to_pdf(analysis, title=title)