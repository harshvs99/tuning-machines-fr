# robust_deal_note_pdf.py
import io
from pathlib import Path
from fpdf import FPDF, errors as fpdf_errors
import textwrap
import traceback
import json

# --- Helpers to normalize text and handle long tokens ---
def normalize_to_text(value, max_len=2000):
    """Convert any Python object to a safe string for PDF output."""
    if value is None:
        return ""
    if isinstance(value, str):
        s = value
    else:
        try:
            s = json.dumps(value, ensure_ascii=False, indent=2)
        except Exception:
            s = str(value)
    # Replace NBSP
    s = s.replace("\xa0", " ")
    # Insert soft-break hint after slashes/hyphens to help fpdf wrap long URLs/tokens
    s = s.replace("/", "/\u200b").replace("-", "-\u200b")
    # Replace em dashes
    s = s.replace("—", "—\u200b")
    
    # Limit extremely long contiguous strings (e.g., base64)
    if len(s) > max_len:
        # try to keep JSON shape: show start and end
        return s[:max_len//2] + "\n\n...[truncated]...\n\n" + s[-max_len//2:]
    return s

# --- Safe multi-cell writer for fpdf2 ---
def safe_multicell(pdf: FPDF, text: str, lh: float = 6.0):
    """Write text with wrapping; guarantee we pass a string and handle failures."""
    if text is None:
        text = ""
    if not isinstance(text, str):
        text = str(text)

    # small safety: skip empty
    if text.strip() == "":
        return

    # attempt write with attempts to mitigate errors
    try:
        pdf.multi_cell(w=0, h=lh, txt=text, new_x="LMARGIN", new_y="NEXT", max_line_height=pdf.font_size)
    except Exception as e:
        # try to break long tokens by inserting zero-width spaces aggressively
        t = text.replace("http", "http\u200b").replace("www.", "www.\u200b")
        try:
            pdf.multi_cell(w=0, h=lh, txt=t, new_x="LMARGIN", new_y="NEXT", max_line_height=pdf.font_size)
            return
        except Exception:
            # final fallback: truncate and write
            trunc = (text[:1000] + "\n\n...[truncated]...") if len(text) > 1000 else text
            try:
                pdf.multi_cell(w=0, h=lh, txt=trunc, new_x="LMARGIN", new_y="NEXT", max_line_height=pdf.font_size)
            except Exception as e2:
                # If that still fails, write an error line (must be short ASCII)
                pdf.multi_cell(w=0, h=lh, txt="[Error rendering text — see logs]", new_x="LMARGIN", new_y="NEXT")

# --- Utility to pretty-render lists and dicts ---
def write_kv(pdf: FPDF, d: dict):
    for k, v in d.items():
        safe_multicell(pdf, f"{k}:")
        safe_multicell(pdf, normalize_to_text(v), lh=5)

def write_bullets(pdf: FPDF, items):
    for it in items:
        text = normalize_to_text(it)
        # indent bullet
        pdf.cell(6)  # small left indent
        safe_multicell(pdf, f"• {text}")

# --- PDF builder ---
class DealPDF(FPDF):
    def header(self):
        # optional header - minimal to avoid space issues
        pass
    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", size=8)
        self.cell(0, 6, f"Page {self.page_no()}", align="C")

def build_deal_note_pdf(analysis: dict, company_name: str) -> bytes:
    pdf = DealPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Register DejaVu font if file exists in repo folder (improves unicode handling)
    dejavu_paths = [
        "dejavu-ttf/DejaVuSans.ttf",
        "./DejaVuSans.ttf",
        "dejavu-ttf/DejaVuSans-Bold.ttf"
    ]
    font_registered = False
    for p in dejavu_paths:
        if Path(p).exists():
            try:
                pdf.add_font("DejaVu", "", p, uni=True)
                pdf.set_font("DejaVu", size=12)
                font_registered = True
                break
            except Exception:
                font_registered = False

    if not font_registered:
        # fallback to Helvetica (may not render some unicode)
        pdf.set_font("Helvetica", size=12)

    # Title
    company = company_name
    safe_multicell(pdf, f"Deal Note — {company}")
    pdf.ln(2)
    pdf.set_font(pdf.font_family, size=11)

    # A helper to walk keys safely and report path on failure
    def safe_write(path, value):
        try:
            if isinstance(value, dict):
                write_kv(pdf, value)
            elif isinstance(value, list):
                write_bullets(pdf, value)
            else:
                safe_multicell(pdf, normalize_to_text(value))
        except Exception as e:
            # write a short error line and record in console
            pdf.multi_cell(0, 6, txt=f"[Failed to render field: {path}]")
            print(f"Failed to render {path}: {e}")
            traceback.print_exc()

    # Example layout: iterate main sections
    sections = [
        ("Founder Analysis", ["founder_analysis"]),
        ("Industry Analysis", ["industry_analysis"]),
        ("Product Analysis", ["product_analysis"]),
        ("Externalities & Risks", ["externalities_analysis"]),
        ("Competition Analysis", ["competition_analysis"]),
        ("Financial Analysis", ["financial_analysis"]),
        ("Synergy Analysis", ["synergy_analysis"]),
    ]

    for title, keys in sections:
        pdf.set_font(pdf.font_family, "B", 13)
        safe_multicell(pdf, title)
        pdf.ln(1)
        pdf.set_font(pdf.font_family, size=11)
        for key in keys:
            val = analysis.get(key)
            if not val:
                # maybe nested under l1_analysis_report
                val = analysis.get("l1_analysis_report", {}).get(key)
            if not val:
                # skip gracefully
                safe_multicell(pdf, "(No data)")
                continue

            # write common expected fields neatly
            # If it's a dict with assessment, show rating + score first
            if isinstance(val, dict):
                rating = val.get("assessment", {}).get("rating") or val.get("assessment", {}).get("score") or val.get("assessment", {}).get("rationale")
                # show quick header for ratings if present
                if "assessment" in val:
                    ass = val["assessment"]
                    if isinstance(ass, dict):
                        r = ass.get("rating")
                        s = ass.get("score")
                        if r or s is not None:
                            safe_multicell(pdf, f"Rating: {r}  |  Score: {s}")
                # Now write main summary keys if available
                for subk in ["summary", "key_strengths", "identified_gaps", "core_product_offering", "problem_solved", "value_proposition_qualitative", "value_proposition_quantitative", "identified_risks", "direct_competitors", "unit_economics", "analyst_sizing", "three_year_viability_check", "potential_synergies"]:
                    if subk in val:
                        v = val[subk]
                        pdf.set_font(pdf.font_family, "B", 11)
                        safe_multicell(pdf, subk.replace("_", " ").title() + ":")
                        pdf.set_font(pdf.font_family, size=11)
                        safe_write(f"{key}.{subk}", v)
                # finally write any leftover keys
                leftover = {k:v for k,v in val.items() if k not in ["summary","key_strengths","identified_gaps","core_product_offering","problem_solved","value_proposition_qualitative","value_proposition_quantitative","identified_risks","direct_competitors","unit_economics","analyst_sizing","three_year_viability_check","potential_synergies","assessment"]}
                if leftover:
                    pdf.set_font(pdf.font_family, "B", 11)
                    safe_multicell(pdf, "Other Details:")
                    pdf.set_font(pdf.font_family, size=11)
                    safe_write(f"{key}.other", leftover)
            else:
                safe_write(key, val)

        pdf.ln(2)

    # Final metadata
    pdf.set_font(pdf.font_family, "B", 12)
    safe_multicell(pdf, "Metadata:")
    pdf.set_font(pdf.font_family, size=10)
    sources = analysis.get("source_pitch_deck_urls") or analysis.get("l1_analysis_report", {}).get("source_pitch_deck_urls", [])
    safe_write("metadata.sources", sources)

    return pdf.output(dest="S").encode("utf-8", errors="ignore")


def dict_to_pdf(data: dict, title: str = "Document", max_depth: int = 10) -> bytes:
    """
    Convert any nested dictionary to a PDF file.
    
    Args:
        data: The nested dictionary to convert
        title: Title for the PDF document
        max_depth: Maximum nesting depth to prevent infinite recursion
    
    Returns:
        bytes: PDF file as bytes, ready for download
    """
    pdf = DealPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Register DejaVu font if file exists in repo folder (improves unicode handling)
    dejavu_paths = [
        "dejavu-ttf/DejaVuSans.ttf",
        "./DejaVuSans.ttf",
        "dejavu-ttf/DejaVuSans-Bold.ttf"
    ]
    font_registered = False
    for p in dejavu_paths:
        if Path(p).exists():
            try:
                pdf.add_font("DejaVu", "", p, uni=True)
                pdf.set_font("DejaVu", size=12)
                font_registered = True
                break
            except Exception:
                font_registered = False
    
    if not font_registered:
        # fallback to Helvetica (may not render some unicode)
        pdf.set_font("Helvetica", size=12)
    
    # Title
    pdf.set_font(pdf.font_family, "B", 16)
    safe_multicell(pdf, title)
    pdf.ln(4)
    pdf.set_font(pdf.font_family, size=11)
    
    def render_value(value, key_path: str = "", depth: int = 0, indent: int = 0):
        """
        Recursively render any value (dict, list, or primitive) to the PDF.
        
        Args:
            value: The value to render
            key_path: Path of keys for error reporting
            depth: Current nesting depth
            indent: Visual indentation level (in mm)
        """
        if depth > max_depth:
            safe_multicell(pdf, "[Maximum depth exceeded]")
            return
        
        try:
            if value is None:
                safe_multicell(pdf, "(null)")
                pdf.ln(1)
            
            elif isinstance(value, dict):
                if not value:  # Empty dict
                    safe_multicell(pdf, "(empty dictionary)")
                    pdf.ln(1)
                else:
                    for k, v in value.items():
                        # Format key nicely
                        key_display = k.replace("_", " ").title()
                        
                        # Set font for key
                        pdf.set_font(pdf.font_family, "B", 11)
                        
                        # Add indentation
                        if indent > 0:
                            pdf.cell(indent)
                        
                        # Write key
                        safe_multicell(pdf, f"{key_display}:")
                        
                        # Reset font for value
                        pdf.set_font(pdf.font_family, size=10)
                        
                        # Recursively render value with increased depth and indent
                        render_value(v, f"{key_path}.{k}" if key_path else k, depth + 1, indent + 8)
                        pdf.ln(0.5)
            
            elif isinstance(value, list):
                if not value:  # Empty list
                    safe_multicell(pdf, "(empty list)")
                    pdf.ln(1)
                else:
                    for i, item in enumerate(value):
                        # Add indentation
                        if indent > 0:
                            pdf.cell(indent)
                        
                        # If item is a dict or list, render it recursively without bullet
                        if isinstance(item, (dict, list)):
                            pdf.set_font(pdf.font_family, size=10)
                            safe_multicell(pdf, f"Item {i+1}:", lh=5)
                            render_value(item, f"{key_path}[{i}]" if key_path else f"[{i}]", depth + 1, indent + 8)
                        else:
                            # Primitive value - use bullet point
                            pdf.set_font(pdf.font_family, size=10)
                            text = normalize_to_text(item)
                            safe_multicell(pdf, f"• {text}", lh=5)
                        pdf.ln(0.5)
            
            else:
                # Primitive value (str, int, float, bool, etc.)
                text = normalize_to_text(value)
                if indent > 0:
                    pdf.cell(indent)
                safe_multicell(pdf, text, lh=5)
                pdf.ln(1)
        
        except Exception as e:
            # Error handling - write error message
            pdf.set_font(pdf.font_family, size=9)
            error_msg = f"[Error rendering {key_path}: {str(e)}]"
            safe_multicell(pdf, error_msg)
            pdf.ln(1)
            print(f"Failed to render {key_path}: {e}")
            traceback.print_exc()
    
    # Render the entire dictionary
    render_value(data)
    
    return pdf.output(dest="S").encode("utf-8", errors="ignore")