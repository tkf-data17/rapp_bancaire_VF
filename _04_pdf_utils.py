from fpdf import FPDF
import datetime

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Etat de Rapprochement', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

def generate_pdf_report(ops_data, totals, solde_rectif, grand_totals, output_pdf_path, date_arrete=None):
    """
    ops_data: list of dicts {'date_str', 'libelle', 'col_C', 'col_D', 'col_E', 'col_F'}
    totals: dict {'C', 'D', 'E', 'F'}
    solde_rectif: dict {'label', 'C', 'D', 'E', 'F'}
    grand_totals: dict {'C', 'D', 'E', 'F'}
    """
    try:
        pdf = PDF(orientation='L')
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # Info block
        pdf.set_font('Arial', '', 10)
        if date_arrete:
            pdf.cell(0, 10, f"Date d'arrêté: {date_arrete}", 0, 1)
        
        # Table Header
        w = [25, 110, 30, 30, 30, 30] # Total ~255 (A4 Landscape width is 297, margin 10 -> 277)
        header_labels = ["Date", "Libellé", "Cpt Deb", "Cpt Cred", "Rel Deb", "Rel Cred"]
        # Helper to strict latin-1
        def to_latin1(s):
            try:
                return str(s).encode('latin-1', 'replace').decode('latin-1')
            except:
                return str(s)

        # Draw Header
        pdf.set_font('Arial', 'B', 10)
        pdf.set_fill_color(240, 240, 240)
        for i, h in enumerate(header_labels):
            pdf.cell(w[i], 10, to_latin1(h), 1, 0, 'C', 1)
        pdf.ln()
        
        pdf.set_font('Arial', '', 9)
        
        def fmt(x):
            if x == 0 or x == "": return ""
            try:
                return f"{float(x):,.0f}".replace(",", " ")
            except:
                return to_latin1(x)

        # Rows
        for op in ops_data:
            pdf.cell(w[0], 8, to_latin1(op.get('date_str', '')), 1)
            pdf.cell(w[1], 8, to_latin1(op.get('libelle', ''))[:60], 1)
            pdf.cell(w[2], 8, fmt(op.get('col_C', 0)), 1, 0, 'R')
            pdf.cell(w[3], 8, fmt(op.get('col_D', 0)), 1, 0, 'R')
            pdf.cell(w[4], 8, fmt(op.get('col_E', 0)), 1, 0, 'R')
            pdf.cell(w[5], 8, fmt(op.get('col_F', 0)), 1, 0, 'R')
            pdf.ln()
            
        # Totals
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(w[0]+w[1], 8, "TOTAUX", 1, 0, 'R')
        pdf.cell(w[2], 8, fmt(totals['C']), 1, 0, 'R')
        pdf.cell(w[3], 8, fmt(totals['D']), 1, 0, 'R')
        pdf.cell(w[4], 8, fmt(totals['E']), 1, 0, 'R')
        pdf.cell(w[5], 8, fmt(totals['F']), 1, 0, 'R')
        pdf.ln()

        # Solde Rectifié
        pdf.cell(w[0]+w[1], 8, to_latin1(solde_rectif['label']), 1, 0, 'R')
        pdf.cell(w[2], 8, fmt(solde_rectif['C']), 1, 0, 'R')
        pdf.cell(w[3], 8, fmt(solde_rectif['D']), 1, 0, 'R')
        pdf.cell(w[4], 8, fmt(solde_rectif['E']), 1, 0, 'R')
        pdf.cell(w[5], 8, fmt(solde_rectif['F']), 1, 0, 'R')
        pdf.ln()
        
        # Grand Totals
        pdf.cell(w[0]+w[1], 8, "TOTAUX GENERAUX", 1, 0, 'R')
        pdf.cell(w[2], 8, fmt(grand_totals['C']), 1, 0, 'R')
        pdf.cell(w[3], 8, fmt(grand_totals['D']), 1, 0, 'R')
        pdf.cell(w[4], 8, fmt(grand_totals['E']), 1, 0, 'R')
        pdf.cell(w[5], 8, fmt(grand_totals['F']), 1, 0, 'R')
        pdf.ln()
        
        if output_pdf_path:
            pdf.output(output_pdf_path)
            return True, None
        else:
            try:
                # Return bytes for in-memory usage
                # For FPDF < 2.0, output(dest='S') returns string, we encode to bytes
                # For FPDF 2.0+, output() returns bytes
                # We assume standard FPDF here based on usage
                return True, pdf.output(dest='S').encode('latin-1', errors='replace')
            except Exception as e:
                # Fallback or different FPDF version handling could go here
                print(f"PDF Memory Output Error: {e}")
                return False, None

    except Exception as e:
        print(f"PDF Generation Error: {e}")
        return False, None
