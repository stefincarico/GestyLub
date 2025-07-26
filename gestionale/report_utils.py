# gestionale/report_utils.py

from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
import openpyxl
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter
from django.template.loader import render_to_string
from weasyprint import HTML

def generate_excel_report(tenant_name, report_title, filters_string, kpi_data, headers, data_rows):
    """
    Funzione generica per creare un report Excel strutturato.

    Args:
        tenant_name (str): Nome dell'azienda attiva.
        report_title (str): Titolo del report.
        filters_string (str): Stringa che riassume i filtri applicati.
        kpi_data (dict): Dizionario contenente i KPI da mostrare.
        headers (list): Lista di stringhe per le intestazioni della tabella.
        data_rows (list of lists): Lista di liste, dove ogni lista interna è una riga di dati.

    Returns:
        HttpResponse: La risposta HTTP con il file Excel da scaricare.
    """
    # 1. PREPARAZIONE DELLA RISPOSTA HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    filename = f"{report_title.replace(' ', '_').lower()}_{timezone.now().strftime('%Y%m%d')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # 2. CREAZIONE DEL FILE EXCEL
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = report_title

    # 3. STILI
    title_font = Font(name='Calibri', size=16, bold=True)
    header_font = Font(name='Calibri', size=12, bold=True)
    currency_format = '"€" #,##0.00'
    date_format = 'DD/MM/YYYY'
    
    # --- INTESTAZIONE DEL REPORT ---
    current_row = 1
    worksheet.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=len(headers))
    cell = worksheet.cell(row=current_row, column=1, value=tenant_name)
    cell.font = title_font
    cell.alignment = Alignment(horizontal='center')
    current_row += 1
    
    worksheet.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=len(headers))
    cell = worksheet.cell(row=current_row, column=1, value=report_title)
    cell.alignment = Alignment(horizontal='center')
    current_row += 2 # Lascia una riga vuota

    worksheet.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=len(headers))
    worksheet.cell(row=current_row, column=1, value=f"Filtri Applicati: {filters_string}")
    current_row += 1

    worksheet.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=len(headers))
    worksheet.cell(row=current_row, column=1, value=f"Generato il: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}")
    current_row += 2

    # --- KPI ---
    if kpi_data:
        for key, value in kpi_data.items():
            label = key.replace('_', ' ').title()
            worksheet.cell(row=current_row, column=2, value=label).font = header_font
            cell = worksheet.cell(row=current_row, column=3, value=value)
            cell.number_format = currency_format
            current_row += 1
        current_row += 1

    # --- TABELLA DATI ---
    worksheet.append(headers)
    for cell in worksheet[current_row]:
        cell.font = header_font
    
    for row_data in data_rows:
        worksheet.append(row_data)
        # Applicazione formattazione condizionale (esempio)
        # Puoi aggiungere qui logica per formattare date o numeri se necessario
        # dato che i dati arrivano già pronti.

    # --- ADATTAMENTO COLONNE ---
    for col_idx in range(1, len(headers) + 1):
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

    # 4. SALVATAGGIO E RESTITUZIONE
    workbook.save(response)
    return response

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


