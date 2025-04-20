from flask import Flask, render_template, request, send_file, redirect, url_for
from weasyprint import HTML
import datetime
import os
import smtplib
from email.message import EmailMessage
from flask_mail import Mail, Message


app = Flask(__name__)

@app.route('/')
def invoice_form():
    return render_template('form.html')

@app.route('/generate_invoice', methods=['POST'])
def generate_invoice():
    try:
        customer_name = request.form['customer_name']
        customer_email = request.form['email']

        # Fetch descriptions, amounts, and currencies
        descriptions = request.form.getlist('description')
        amounts = request.form.getlist('amount')
        currencies = request.form.getlist('currency')

        # New lines to fetch tax and discount from form
        taxes = request.form.getlist('tax')
        discounts = request.form.getlist('discount')

        # Build items with full data
        items = []
        for desc, amt, curr, tax, disc in zip(descriptions, amounts, currencies, taxes, discounts):
            amt = float(amt)
            tax = float(tax)
            disc = float(disc)
            
            # Calculate tax and discount amounts
            tax_amount = amt * (tax / 100)
            discount_amount = amt * (disc / 100)
            subtotal = amt + tax_amount - discount_amount

            items.append({
                "description": desc,
                "amount": amt,
                "currency": curr,
                "tax": tax,
                "discount": disc,
                "subtotal": round(subtotal, 2)
            })

        # Calculate total from subtotals
        total = sum(item["subtotal"] for item in items)

        # Date
        date = datetime.datetime.now().strftime("%Y-%m-%d")

        # Generate HTML for the invoice
        html_out = render_template(
            "invoice.html",
            customer_name=customer_name,
            date=date,
            items=items,
            total=total,
            pdf=True  # 👈 Add this line
        )

        # Save the PDF
        if not os.path.exists('invoices'):
            os.makedirs('invoices')

        pdf_filename = f"{customer_name.replace(' ', '_')}_{date}.pdf"
        pdf_path = os.path.join("invoices", pdf_filename)
        HTML(string=html_out, base_url=request.root_url).write_pdf(pdf_path)

        # Send the invoice via email
        send_invoice_email(customer_email, pdf_path)

        # Return the PDF to the user
        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        return f"Error generating invoice: {e}"

def send_invoice_email(to_email, pdf_path):
    from_email = 'your_email@gmail.com'
    email_password = 'yszc yzun ktzt svxc'  # Paste the 16-character app password here

    msg = EmailMessage()
    msg['Subject'] = 'Your Invoice from Mythri Clinic'
    msg['From'] = from_email
    msg['To'] = to_email
    msg.set_content('Thank you for your visit! Please find your invoice attached.')

    with open(pdf_path, 'rb') as f:
        pdf_data = f.read()
    msg.add_attachment(pdf_data, maintype='application', subtype='pdf', filename='invoice.pdf')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(from_email, email_password)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Error sending email: {e}")

@app.route('/search_invoice', methods=['POST'])
def search_invoice():
    search_name = request.form['search_name'].lower()
    matched_files = []

    if os.path.exists('invoices'):
        for filename in os.listdir('invoices'):
            if search_name in filename.lower():
                matched_files.append(filename)

    return render_template('form.html', invoices=matched_files)

@app.route('/download/<filename>')
def download_invoice(filename):
    return send_file(os.path.join('invoices', filename), as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)    