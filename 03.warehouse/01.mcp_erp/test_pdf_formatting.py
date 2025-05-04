from fpdf import FPDF
import os

# Dummy GPT-4 replies simulating documentation output
replies = [
    "Object Name: AP.AP_INVOICES_ALL\n\nThe AP.AP_INVOICES_ALL object is a table in an Oracle ERP system that contains detailed information about all the invoices processed in the Accounts Payable (AP) module. This table serves as a central repository for invoice data, which is crucial for financial reporting, vendor payment tracking, and auditing purposes.\n\nColumn Descriptions:\n\n1. INVOICE_ID: This is a unique identifier for each invoice in the system. It is likely an auto-incrementing integer.\n2. LAST_UPDATE_DATE: This timestamp indicates the most recent date and time when the invoice record was updated.",
    "3. LAST_UPDATED_BY: The ID of the user who last updated the invoice record.\n4. VENDOR_ID: The unique identifier for the vendor associated with the invoice.\n5. INVOICE_NUM: The invoice number as provided by the vendor.\n6. SET_OF_BOOKS_ID: Identifies the set of books (ledger) to which this invoice belongs.",
    "7. INVOICE_CURRENCY_CODE: The currency code for the invoice.\n8. PAYMENT_CURRENCY_CODE: The currency code used for payment.\n9. PAYMENT_CROSS_RATE: The exchange rate used if the payment currency differs from the invoice currency.\n10. INVOICE_AMOUNT: The total amount of the invoice.\n\nThis table does not appear to have explicit relationships with other tables based on the provided data. However, it can be inferred that there may be relationships with other tables in the AP module, such as those containing payment terms, payment methods, account codes, users, purchase orders, and recurring payments."
]

all_replies = "\n\n".join(replies)

font_path = "03.warehouse/01.mcp_erp/DejaVuSans.ttf"
bold_font_path = "03.warehouse/01.mcp_erp/dejavu-sans-bold.ttf"
output_pdf = "03.warehouse/01.mcp_erp/table_docs/AP_AP_INVOICES_ALL_documentation_test.pdf"

pdf = FPDF()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_font("DejaVu", "", font_path, uni=True)
pdf.add_font("DejaVu", "B", bold_font_path, uni=True)

# Add a bold, black title at the top center
pdf.set_font("DejaVu", 'B', 16)
pdf.set_text_color(0, 0, 0)
pdf.cell(0, 15, "Documentation: AP.AP_INVOICES_ALL", ln=True, align='C')
pdf.ln(5)

pdf.set_font("DejaVu", size=12)

for paragraph in all_replies.split('\n\n'):
    for line in paragraph.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf.ln(5)

pdf.output(output_pdf)
print(f"Test PDF saved to {output_pdf}") 