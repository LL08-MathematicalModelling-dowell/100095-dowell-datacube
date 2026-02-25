import io
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


def generate_pdf_report(data: dict, db_id: str, days: int) -> bytes:
    """
    Generate a PDF analytics report.
    data: dictionary containing 'historical' and 'today_hourly' from dashboard
    and optional 'storage' stats.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter),
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=14, leading=20))
    styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT, fontSize=10, leading=12))
    
    story = []
    
    # Title
    title = Paragraph(f"Analytics Report for Database: {db_id}", styles['Center'])
    story.append(title)
    story.append(Spacer(1, 0.2*inch))
    
    # Date range
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    date_range = Paragraph(f"Date Range: {start_date} to {end_date}", styles['Right'])
    story.append(date_range)
    story.append(Spacer(1, 0.3*inch))
    
    # Storage summary
    storage = data.get('storage', {})
    if storage:
        story.append(Paragraph("Storage Statistics", styles['Heading2']))
        storage_data = [
            ["Metric", "Value"],
            ["Document Count", str(storage.get('doc_count', 'N/A'))],
            ["Data Size (MB)", str(storage.get('size_mb', 'N/A'))],
            ["Storage Size (MB)", str(storage.get('storage_mb', 'N/A'))],
            ["Index Size (MB)", str(storage.get('index_size_mb', 'N/A'))],
        ]
        t = Table(storage_data, colWidths=[2*inch, 2*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(t)
        story.append(Spacer(1, 0.3*inch))
    
    # Historical daily summaries
    historical = data.get('historical', [])
    if historical:
        story.append(Paragraph("Daily Activity Summary", styles['Heading2']))
        # Build table: Date, Total Ops, Avg Latency, Error Count
        hist_data = [["Date", "Total Ops", "Avg Latency (ms)", "Errors"]]
        for day in historical:
            # day is already JSON-serializable from service
            date_str = day.get('date', '')
            if isinstance(date_str, datetime):
                date_str = date_str.strftime("%Y-%m-%d")
            hist_data.append([
                date_str,
                str(day.get('total_ops', 0)),
                f"{day.get('avg_latency', 0):.2f}",
                str(day.get('error_count', 0))
            ])
        t = Table(hist_data, colWidths=[1.5*inch, 1*inch, 1.5*inch, 1*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(t)
        story.append(Spacer(1, 0.3*inch))
    
    # Today's hourly trend
    hourly = data.get('today_hourly', [])
    if hourly:
        story.append(Paragraph("Today's Hourly Activity", styles['Heading2']))
        hour_data = [["Hour", "Operations", "Avg Latency (ms)"]]
        for h in hourly:
            hour_data.append([
                f"{h.get('_id', '')}:00",
                str(h.get('ops', 0)),
                f"{h.get('latency', 0):.2f}"
            ])
        t = Table(hour_data, colWidths=[1*inch, 1.5*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(t)
    
    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes