# gestionale/report_utils.py

from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
import openpyxl
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter
from django.template.loader import render_to_string
from weasyprint import HTML

# ==============================================================================
# === UTILITY PER EXPORT EXCEL                                              ===
# ==============================================================================

def generate_excel_report(tenant_name, report_title, filters_string, kpi_data, report_sections, filename_prefix='report'):
    """
    Funzione generica AVANZATA per creare un report Excel strutturato.
    Ora supporta sezioni multiple, ognuna con la sua tabella.

    Args:
        tenant_name (str): Nome dell'azienda attiva.
        report_title (str): Titolo principale del report.
        filters_string (str): Stringa che riassume i filtri applicati.
        kpi_data (dict): Dizionario con i KPI da mostrare.
        report_sections (list of dicts): Lista di sezioni. Ogni sezione è un dizionario
                                          con chiavi 'title', 'headers', 'rows'.
        filename_prefix (str, optional): Prefisso per il nome del file.
    """
    # 1. PREPARAZIONE DELLA RISPOSTA HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    timestamp = timezone.now().strftime('%Y%m%d-%H%M')
    filename = f"{timestamp}-{filename_prefix}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # 2. CREAZIONE DEL FILE EXCEL
    workbook = Workbook()
    worksheet = workbook.active
    
    # Sanificazione del titolo del foglio
    safe_sheet_title = report_title.replace(":", "-").replace("/", "-").replace("\\", "-").replace("?", "").replace("*", "").replace("[", "").replace("]", "")
    worksheet.title = safe_sheet_title[:31]
    
    # 3. DEFINIZIONE DEGLI STILI
    title_font = Font(name='Calibri', size=16, bold=True)
    header_font = Font(name='Calibri', size=12, bold=True)
    section_title_font = Font(name='Calibri', size=13, bold=True, italic=True)
    currency_format = '€ #,##0.00'
    date_format = 'DD/MM/YYYY'
    
    # 4. SCRITTURA DELL'INTESTAZIONE DEL REPORT
    current_row = 1
    # Uniamo le celle basandoci sul numero massimo di colonne che useremo
    max_cols = 1
    if report_sections:
        max_cols = max(len(s.get('headers', [])) for s in report_sections)

    worksheet.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=max_cols)
    cell = worksheet.cell(row=current_row, column=1, value=tenant_name)
    cell.font = title_font
    cell.alignment = Alignment(horizontal='center')
    current_row += 1
    
    worksheet.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=max_cols)
    cell = worksheet.cell(row=current_row, column=1, value=report_title)
    cell.alignment = Alignment(horizontal='center')
    current_row += 2

    worksheet.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=max_cols)
    worksheet.cell(row=current_row, column=1, value=f"Filtri Applicati: {filters_string}")
    current_row += 1

    worksheet.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=max_cols)
    worksheet.cell(row=current_row, column=1, value=f"Generato il: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}")
    current_row += 2

    # 5. SCRITTURA DEI KPI
    if kpi_data:
        for key, value in kpi_data.items():
            worksheet.cell(row=current_row, column=2, value=key).font = header_font
            cell = worksheet.cell(row=current_row, column=3, value=value)
            cell.number_format = currency_format
            current_row += 1
        current_row += 1

    # 6. SCRITTURA DELLE SEZIONI MULTIPLE
    for section in report_sections:
        # Aggiunge una riga vuota tra le sezioni
        current_row += 1
        
        # Titolo della sezione
        worksheet.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=max_cols)
        cell = worksheet.cell(row=current_row, column=1, value=section.get('title', ''))
        cell.font = section_title_font
        current_row += 1

        # Intestazioni della tabella
        headers = section.get('headers', [])
        worksheet.append(headers)
        for cell in worksheet[current_row]:
            cell.font = header_font
        current_row += 1
        
        # Righe di dati
        for row_data in section.get('rows', []):
            worksheet.append(row_data)
        
        current_row = worksheet.max_row # Ci posizioniamo alla fine per la prossima sezione

    # 7. ADATTAMENTO COLONNE
    for col_idx in range(1, max_cols + 1):
        column_letter = get_column_letter(col_idx)
        max_length = 0
        for cell in worksheet[column_letter]:
            if isinstance(cell, openpyxl.cell.cell.MergedCell):
                continue
            try:
                if len(str(cell.value or "")) > max_length:
                    max_length = len(str(cell.value or ""))
            except: pass
        adjusted_width = (max_length + 2)
        worksheet.column_dimensions[column_letter].width = adjusted_width

    # 8. SALVATAGGIO E RESTITUZIONE
    workbook.save(response)
    return response

# ==============================================================================
# === UTILITY PER EXPORT PDF                                              ===
# ==============================================================================

def generate_pdf_report(request, template_name, context):
    """
    Funzione generica per creare un report PDF da un template HTML.

    Args:
        request: L'oggetto richiesta di Django (necessario per render_to_string).
        template_name (str): Il percorso del template HTML da usare per il report.
        context (dict): Il dizionario di contesto con i dati da passare al template.

    Returns:
        HttpResponse: La risposta HTTP con il file PDF da scaricare.
    """
    # 1. PREPARAZIONE DELLA RISPOSTA HTTP
    response = HttpResponse(content_type='application/pdf')
    report_title = context.get('report_title', 'report')
    timestamp = timezone.now().strftime('%Y%m%d')
    filename = f"{report_title.replace(' ', '_').lower()}_{timestamp}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # 2. RENDERIZZAZIONE DEL TEMPLATE HTML IN UNA STRINGA
    # render_to_string fa esattamente come render, ma invece di restituire
    # una HttpResponse, restituisce il puro HTML come stringa.
    html_string = render_to_string(template_name, context, request=request)

    # 3. CONVERSIONE DA HTML A PDF
    # WeasyPrint prende la stringa HTML e la converte in un file PDF in memoria.
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    # 4. SCRITTURA DEL PDF NELLA RISPOSTA E RESTITUZIONE
    response.write(pdf_file)
    return response


