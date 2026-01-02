import streamlit as st
from jinja2 import Template
from datetime import date
import io
import os
from xhtml2pdf import pisa

# --------------------------------------------------
# Indian number formatting
# --------------------------------------------------
def format_inr(num):
    s = f"{num:.2f}"
    integer, decimal = s.split(".")
    if len(integer) > 3:
        last3 = integer[-3:]
        rest = integer[:-3]
        rest = ",".join([rest[max(i-2,0):i] for i in range(len(rest), 0, -2)][::-1])
        integer = rest + "," + last3
    return integer + "." + decimal

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="Glimmer & Grace Invoice Generator",
    layout="centered"
)

st.title("Glimmer & Grace – Invoice Generator")

# --------------------------------------------------
# Session state
# --------------------------------------------------
if "invoice_items" not in st.session_state:
    st.session_state.invoice_items = []

# --------------------------------------------------
# Invoice details
# --------------------------------------------------
c1, c2 = st.columns(2)
invoice_no = c1.text_input("Invoice Number", "001").strip()
invoice_date = c2.date_input("Invoice Date", date.today())
customer_name = st.text_input("Customer Name").strip().title()

# --------------------------------------------------
# Add item
# --------------------------------------------------
st.subheader("Add Item")

with st.form("add_item_form", clear_on_submit=True):
    desc = st.text_input("Particulars")
    price = st.number_input("Price per item (Rs.)", min_value=0.0, step=0.01)
    qty = st.number_input("Quantity", min_value=1, step=1)
    add_btn = st.form_submit_button("➕ Add Item")

if add_btn and desc.strip():
    st.session_state.invoice_items.append({
        "desc": desc.strip().title(),
        "price": price,
        "qty": qty,
        "amount": price * qty
    })

# --------------------------------------------------
# Show items
# --------------------------------------------------
if st.session_state.invoice_items:
    st.subheader("Items")

    for i, it in enumerate(st.session_state.invoice_items):
        cols = st.columns([5, 1.5, 1, 1.5, 0.5])
        cols[0].write(it["desc"])
        cols[1].write(f"Rs. {format_inr(it['price'])}")
        cols[2].write(it["qty"])
        cols[3].write(f"Rs. {format_inr(it['amount'])}")

        if cols[4].button("❌", key=f"del_{i}"):
            st.session_state.invoice_items.pop(i)
            st.rerun()

# --------------------------------------------------
# HTML TEMPLATE (STRICT CSS)
# --------------------------------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
@page { size: A4; margin: 1in; }

body {
    font-family: Helvetica;
    font-size: 12px;
}

.container {
    width: 100%;
}

.header {
    text-align: center;
}

hr {
    border: 0;
    border-top: 1px solid #000;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 12px;
}

th, td {
    border: 1px solid #000;
    padding: 6px;
    text-align: center;
}

.desc { text-align: left; }
.right { text-align: right; }

.footer {
    margin-top: 40px;
    text-align: center;
    font-style: italic;
}
</style>
</head>

<body>

<div class="container">

<div class="header">
    <img src="logo.png" width="70"><br>
    <b style="font-size:18px;">Glimmer and Grace</b><br>
    Mumbai, India<br>
    glimmerandgrace.india@gmail.com<br>
    +91 9702060534 / +91 9819759104
</div>

<hr>

<b>Invoice Number:</b> {{ invoice_no }}<br>
<b>Invoice Date:</b> {{ invoice_date }}<br><br>

<b>Customer Name:</b> {{ customer_name }}

<table>
<tr>
    <th style="width:40%">Particulars</th>
    <th style="width:20%">Price (Rs.)</th>
    <th style="width:20%">Qty</th>
    <th style="width:20%">Amount (Rs.)</th>
</tr>

{% for i in items %}
<tr>
    <td class="desc">{{ i.desc }}</td>
    <td>{{ i.price_fmt }}</td>
    <td>{{ i.qty }}</td>
    <td>{{ i.amount_fmt }}</td>
</tr>
{% endfor %}

<tr>
    <td colspan="3" class="right"><b>Total</b></td>
    <td><b>{{ total_fmt }}</b></td>
</tr>
</table>

<h3>Grand Total: Rs. {{ total_fmt }}</h3>

<div class="footer">
Thank you for allowing us to craft your timeless elegance!

</div>

</div>

</body>
</html>
"""

# --------------------------------------------------
# PDF helper
# --------------------------------------------------
def link_callback(uri, rel):
    return os.path.abspath(uri)

# --------------------------------------------------
# Generate
# --------------------------------------------------
if st.button("📄 Generate Invoice"):
    if not st.session_state.invoice_items:
        st.warning("Add at least one item.")
        st.stop()

    total = sum(i["amount"] for i in st.session_state.invoice_items)

    items_for_template = []
    for i in st.session_state.invoice_items:
        items_for_template.append({
            "desc": i["desc"],
            "qty": i["qty"],
            "price_fmt": format_inr(i["price"]),
            "amount_fmt": format_inr(i["amount"])
        })

    html = Template(HTML_TEMPLATE).render(
        invoice_no=invoice_no,
        invoice_date=invoice_date.strftime("%d/%m/%Y"),
        customer_name=customer_name,
        items=items_for_template,
        total_fmt=format_inr(total)
    )
    st.markdown("### Invoice Generated")
    st.success("Your invoice is ready. Tap below to download.")


    # st.subheader("Preview")
    # st.components.v1.html(html, height=900, scrolling=True)

    pdf_buffer = io.BytesIO()
    pisa.CreatePDF(html, dest=pdf_buffer, link_callback=link_callback)

    st.download_button(
        "💾 Download Invoice PDF",
        data=pdf_buffer.getvalue(),
        file_name=f"Invoice_{invoice_no}.pdf",
        mime="application/pdf"
    )
